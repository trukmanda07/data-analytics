# Data Quality Framework V2 - Quality as First-Class Citizen

**Version:** 2.0
**Created:** 2025-11-09

---

## V1 Problem: Quality as Afterthought

**V1 Approach:** dbt tests only
- No quality domain model
- No failure handling strategy
- No quality metrics tracked over time
- No ownership model

**V2 Approach:** Data Quality as Bounded Context

---

## Quality Bounded Context

### Domain Model

```python
# domain/quality/aggregates/quality_rule.py

@dataclass
class QualityRule:
    """Aggregate root for quality rules"""
    rule_id: UUID
    name: str
    severity: Severity  # CRITICAL, HIGH, MEDIUM, LOW
    dimension: QualityDimension  # COMPLETENESS, ACCURACY, CONSISTENCY, TIMELINESS

    def validate(self, dataset: DataFrame) -> ValidationResult:
        """Execute quality rule (abstract method)"""
        raise NotImplementedError

class CompletenessRule(QualityRule):
    """Check for NULL values"""
    def __init__(self, column: str, threshold: float = 1.0):
        super().__init__(
            name=f"{column}_completeness",
            severity=Severity.HIGH,
            dimension=QualityDimension.COMPLETENESS
        )
        self.column = column
        self.threshold = threshold  # 1.0 = 100% complete

    def validate(self, dataset: DataFrame) -> ValidationResult:
        total = len(dataset)
        non_null = dataset[self.column].notna().sum()
        completeness = non_null / total if total > 0 else 0

        passed = completeness >= self.threshold

        return ValidationResult(
            rule=self,
            passed=passed,
            score=completeness,
            details={
                "completeness": completeness,
                "threshold": self.threshold,
                "null_count": total - non_null
            }
        )
```

### Quality Dimensions

| Dimension | Definition | Measurement | SLA |
|-----------|------------|-------------|-----|
| **Completeness** | No missing values in required fields | % non-null | >98% |
| **Accuracy** | Values match source of truth | % matching | >99.5% |
| **Consistency** | No contradictions across tables | Zero violations | 100% |
| **Timeliness** | Data loaded within SLA | Minutes since source update | <4 hours |
| **Uniqueness** | No duplicate primary keys | Zero duplicates | 100% |
| **Validity** | Values in expected range/format | % valid | >99% |

---

## Quality Service

```python
# application/quality/quality_service.py

class DataQualityService:
    """Application service for quality assessment"""

    def __init__(
        self,
        rules: List[QualityRule],
        quality_repo: QualityReportRepository
    ):
        self.rules = rules
        self.quality_repo = quality_repo

    def assess_quality(self, dataset: DataFrame, table_name: str) -> QualityReport:
        """Run all quality rules"""
        results = []

        for rule in self.rules:
            try:
                result = rule.validate(dataset)
                results.append(result)

                # Handle failures
                if not result.passed:
                    self._handle_failure(result)

            except Exception as e:
                logger.error(f"Quality rule {rule.name} failed: {e}")
                results.append(ValidationResult(
                    rule=rule,
                    passed=False,
                    error=str(e)
                ))

        report = QualityReport(
            table_name=table_name,
            results=results,
            overall_score=self._calculate_score(results),
            timestamp=datetime.now()
        )

        # Persist report
        self.quality_repo.save(report)

        return report

    def _handle_failure(self, result: ValidationResult):
        """Handle quality check failure"""
        if result.rule.severity == Severity.CRITICAL:
            # Quarantine data
            self._quarantine_data(result)

            # Stop pipeline
            raise DataQualityError(f"Critical quality check failed: {result.rule.name}")

        elif result.rule.severity == Severity.HIGH:
            # Alert team
            self._send_alert(result)

            # Log warning
            logger.warning(f"High severity quality issue: {result.rule.name}")

        else:
            # Just log
            logger.info(f"Quality issue detected: {result.rule.name}")

    def _calculate_score(self, results: List[ValidationResult]) -> float:
        """Calculate overall quality score (weighted)"""
        weights = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 2,
            Severity.MEDIUM: 1,
            Severity.LOW: 0.5
        }

        weighted_sum = sum(
            r.score * weights[r.rule.severity]
            for r in results if r.score is not None
        )

        total_weight = sum(weights[r.rule.severity] for r in results)

        return weighted_sum / total_weight if total_weight > 0 else 0
```

---

## Great Expectations Integration

```yaml
# great_expectations/expectations/dim_customer_suite.yaml
expectations:
  - expectation_type: expect_table_row_count_to_be_between
    kwargs:
      min_value: 95000  # We know Olist has ~99k customers
      max_value: 105000

  - expectation_type: expect_column_values_to_not_be_null
    kwargs:
      column: customer_id

  - expectation_type: expect_column_values_to_be_unique
    kwargs:
      column: customer_id

  - expectation_type: expect_column_values_to_be_in_set
    kwargs:
      column: customer_state
      value_set: ['SP', 'RJ', 'MG', 'BA', 'SC', 'PR', ...]  # All Brazilian states

  - expectation_type: expect_column_values_to_match_regex
    kwargs:
      column: customer_zip_code_prefix
      regex: '^\d{5}$'  # 5-digit ZIP code

  - expectation_type: expect_column_values_to_be_in_set
    kwargs:
      column: customer_segment
      value_set: ['NEW', 'ONE_TIME', 'REGULAR', 'LOYAL', 'VIP', 'CHURNED']
```

---

## Quality SLAs

```python
# config/quality_slas.py

QUALITY_SLAS = {
    'dim_customer': {
        'completeness': {
            'customer_id': 1.0,  # 100% required
            'customer_city': 0.99,
            'customer_state': 1.0,
            'customer_zip_code_prefix': 0.98
        },
        'uniqueness': {
            'customer_id': 1.0  # No duplicates
        },
        'validity': {
            'customer_state': 1.0,  # Must be valid Brazilian state
            'customer_segment': 1.0  # Must be valid segment
        }
    },
    'fact_orders': {
        'completeness': {
            'order_id': 1.0,
            'customer_id': 1.0,
            'total_amount': 1.0
        },
        'consistency': {
            'total_amount_matches_items': 1.0  # total = sum(items)
        },
        'timeliness': {
            'max_lag_hours': 4  # Data loaded within 4 hours
        }
    }
}
```

---

## Quality Dashboard

```python
# dashboards/quality_dashboard.py (Marimo)

import marimo as mo
import plotly.express as px

app = mo.App()

@app.cell
def __():
    # Fetch quality reports
    reports = quality_repo.get_recent_reports(days=30)

    # Calculate trend
    quality_trend = [
        {"date": r.timestamp, "score": r.overall_score, "table": r.table_name}
        for r in reports
    ]

    # Visualize
    fig = px.line(
        quality_trend,
        x='date',
        y='score',
        color='table',
        title='Data Quality Score (Last 30 Days)'
    )

    fig.add_hline(y=0.95, line_dash="dash", line_color="red", annotation_text="SLA: 95%")
    fig
    return

@app.cell
def __():
    # Show failures
    failures = [r for r in reports if r.overall_score < 0.95]

    mo.md(f"""
    ## Quality Failures (Last 30 Days)

    **Total Failures:** {len(failures)}

    **By Table:**
    {failure_summary_table(failures)}
    """)
    return
```

---

## Conclusion

Data quality is now a first-class citizen:
- Quality bounded context with domain model
- Automated checks with Great Expectations
- Quality SLAs tracked over time
- Failure handling strategy
- Quality dashboard for visibility
