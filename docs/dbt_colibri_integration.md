# dbt-colibri Integration Guide

## Overview

**dbt-colibri** is a lightweight Python-based tool for extracting and analyzing data column lineage for dbt projects. It provides transparent, flexible lineage tracking without vendor lock-in or complex enterprise tooling.

## What is Column Lineage?

Column lineage tracks how individual data columns flow through transformations in your dbt project:
- Which source columns feed into which downstream columns
- How transformations modify or combine columns
- Dependencies between columns across models
- Complete end-to-end column-level data flow

This is different from model-level lineage (which dbt docs already provides) - it goes deeper to show column-by-column relationships.

## Key Features

### 1. Complete Visibility
- Track how every column flows through dbt transformations
- Interactive UI to explore column dependencies
- Visual representation of column-level lineage

### 2. Fast & Lightweight
- Generates reports in seconds from existing dbt artifacts
- No heavy infrastructure required
- Uses your existing `manifest.json` and `catalog.json`

### 3. Self-Hosted
- No cloud dependencies
- No external services required
- Complete control over your lineage data
- Works entirely offline

### 4. Output Formats
- **Interactive HTML dashboard** - Visualize and explore lineage
- **JSON data file** - Programmatic access to lineage information

## Technical Requirements

### Python Versions
- Python 3.9, 3.11, or 3.13

### Supported dbt Adapters
- ✅ Snowflake
- ✅ BigQuery
- ✅ Redshift
- ✅ DuckDB (our adapter!)
- ✅ Postgres
- ✅ Databricks (SQL models only)
- ✅ Athena
- ✅ Trino

### dbt Versions
- dbt 1.8.x
- dbt 1.9.x
- dbt 1.10.x

## Installation

### Using uv (Recommended)
```bash
source .venv/bin/activate
uv pip install dbt-colibri
```

### Using pip
```bash
source .venv/bin/activate
pip install dbt-colibri
```

## Usage

### Step 1: Generate dbt Artifacts
First, you need to compile your dbt project and generate documentation:

```bash
cd dbt/olist_dw_dbt

# Compile the project (generates manifest.json)
dbt compile

# Generate documentation (generates catalog.json)
dbt docs generate
```

This creates two files in `dbt/olist_dw_dbt/target/`:
- `manifest.json` - Contains model definitions and transformations
- `catalog.json` - Contains column metadata and schemas

### Step 2: Generate Lineage Report
Run Colibri to extract column lineage:

```bash
# From the dbt project directory
cd dbt/olist_dw_dbt

# Generate lineage report
colibri generate
```

### Step 3: View the Report
Open the generated HTML dashboard:

```bash
# Open in default browser (Linux)
xdg-open dist/index.html

# Or manually open the file in your browser
# Location: dbt/olist_dw_dbt/dist/index.html
```

## Command Options

```bash
colibri generate [OPTIONS]
```

### Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `--manifest-path` | Path to manifest.json | `target/manifest.json` |
| `--catalog-path` | Path to catalog.json | `target/catalog.json` |
| `--output-dir` | Output directory for reports | `dist/` |
| `--light` | Lightweight mode for large projects | `false` |

### Example with Custom Paths
```bash
colibri generate \
  --manifest-path=/custom/path/manifest.json \
  --catalog-path=/custom/path/catalog.json \
  --output-dir=/output/lineage
```

## Use Cases for Our Olist Project

### 1. Understanding Data Flow
**Scenario:** You want to understand how `customer_state` flows from raw data to marts.

**How Colibri Helps:**
- Trace `customer_state` from `stg_customers` → `dim_customers` → `mart_executive_dashboard`
- See all transformations applied to this column
- Identify which models use this column

### 2. Impact Analysis
**Scenario:** You're changing the logic for calculating `total_price` in staging.

**How Colibri Helps:**
- See all downstream models that depend on `total_price`
- Identify which mart columns will be affected
- Plan testing strategy based on dependencies

### 3. Data Quality Investigations
**Scenario:** You notice incorrect values in `mart_customer_analytics.avg_order_value`.

**How Colibri Helps:**
- Trace back to source columns
- Identify all intermediate transformations
- Pinpoint where the issue might be introduced

### 4. Documentation
**Scenario:** New team member needs to understand the data model.

**How Colibri Helps:**
- Visual lineage makes relationships clear
- Interactive exploration of column dependencies
- Complements dbt's model-level lineage

### 5. Refactoring
**Scenario:** You want to refactor intermediate models.

**How Colibri Helps:**
- See which columns are actually used downstream
- Identify unused columns that can be removed
- Ensure you don't break dependencies

## Project Structure After Adding Colibri

```
dbt/olist_dw_dbt/
├── models/
│   ├── staging/
│   ├── intermediate/
│   ├── core/
│   └── marts/
├── target/
│   ├── manifest.json      # Generated by dbt compile
│   ├── catalog.json       # Generated by dbt docs generate
│   └── ...
├── dist/                  # Generated by Colibri
│   ├── index.html        # Interactive lineage dashboard
│   └── lineage.json      # JSON lineage data
└── dbt_project.yml
```

## Architecture

### How Colibri Works

1. **SQL Parsing** - Uses SQLGlot to parse SQL models
2. **Metadata Extraction** - Reads dbt's manifest.json and catalog.json
3. **Lineage Graph Construction** - Builds column-level dependency graph
4. **Report Generation** - Creates interactive HTML dashboard and JSON export

### What Gets Analyzed
- ✅ SELECT statements and column transformations
- ✅ CTEs (Common Table Expressions)
- ✅ JOINs and column mappings
- ✅ Column aliases and renames
- ✅ Calculated columns (expressions)
- ❌ Dynamic SQL (limited support)
- ❌ Jinja macros (shows macro usage, not expansion)

## Best Practices

### 1. Regular Updates
Regenerate lineage after major changes:
```bash
dbt compile && dbt docs generate && colibri generate
```

### 2. Include in CI/CD
Add to your deployment pipeline:
```yaml
# Example GitHub Actions workflow
- name: Generate column lineage
  run: |
    cd dbt/olist_dw_dbt
    dbt compile
    dbt docs generate
    colibri generate
```

### 3. Version Control
Consider adding to `.gitignore`:
```
# .gitignore
dbt/olist_dw_dbt/dist/
```

Or commit for historical tracking:
- Pros: Track lineage changes over time
- Cons: Large HTML files in git history

### 4. Large Projects
Use `--light` mode for faster generation:
```bash
colibri generate --light
```

## Comparison with dbt Docs

| Feature | dbt Docs | dbt-colibri |
|---------|----------|-------------|
| Model lineage | ✅ | ❌ |
| Column lineage | ❌ | ✅ |
| Test documentation | ✅ | ❌ |
| Model descriptions | ✅ | ❌ |
| Column descriptions | ✅ | ✅ |
| Interactive exploration | ✅ | ✅ |
| Source mapping | ✅ | ✅ |

**Recommendation:** Use both! They complement each other:
- **dbt docs** - Model-level lineage, documentation, tests
- **dbt-colibri** - Column-level lineage, detailed data flow

## Troubleshooting

### "Command not found: colibri"
**Solution:** Activate virtual environment first
```bash
source .venv/bin/activate
colibri generate
```

### "File not found: manifest.json"
**Solution:** Run dbt compile first
```bash
dbt compile
dbt docs generate
colibri generate
```

### "Parsing error in model X"
**Solution:** Check SQL syntax in that model. Colibri uses SQLGlot which may have different parsing rules than your database.

### Large project is slow
**Solution:** Use lightweight mode
```bash
colibri generate --light
```

## Example Workflow

Here's a complete workflow for our Olist project:

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Navigate to dbt project
cd dbt/olist_dw_dbt

# 3. Make changes to models
# ... edit SQL files ...

# 4. Build and test
dbt build
dbt test

# 5. Generate documentation and lineage
dbt docs generate  # Model-level lineage
colibri generate   # Column-level lineage

# 6. View reports
dbt docs serve &            # Open on port 8080
xdg-open dist/index.html   # Open Colibri dashboard

# 7. Explore lineage
# - Use dbt docs for model relationships
# - Use Colibri for column-level flow
```

## Integration with Our Star Schema

### Example: Tracing Order Revenue

**Question:** How does `price` from the source CSV become `total_revenue` in the executive dashboard?

**Colibri shows:**
```
Source: olist_order_items_dataset.csv
  └─ price
      └─ stg_order_items.price
          └─ int_order_items_enriched.price
              └─ fct_order_items.price
                  └─ mart_executive_dashboard.total_revenue
                      (aggregated as SUM(price + freight_value))
```

### Example: Customer Dimension

**Question:** Which columns from staging are used in customer analytics?

**Colibri shows:**
```
stg_customers.*
  └─ customer_id → dim_customers.customer_key
  └─ customer_zip_code_prefix → dim_customers.customer_zip_code_prefix
  └─ customer_city → dim_customers.customer_city
  └─ customer_state → dim_customers.customer_state
      └─ Used in:
          - mart_customer_analytics.customer_state
          - mart_executive_dashboard.top_states
          - mart_geographic_analytics.state_metrics
```

## Resources

- **GitHub Repository:** https://github.com/b-ned/dbt-colibri
- **dbt Documentation:** https://docs.getdbt.com
- **SQLGlot (Parser):** https://github.com/tobymao/sqlglot

## Summary

**dbt-colibri** adds column-level lineage tracking to our Olist dbt project, enabling:
- 🔍 Deep visibility into data transformations
- 📊 Visual exploration of column dependencies
- 🎯 Impact analysis for changes
- 🐛 Data quality investigation
- 📚 Enhanced documentation for team onboarding

**Next Steps:**
1. Install: `uv pip install dbt-colibri`
2. Generate artifacts: `dbt compile && dbt docs generate`
3. Create lineage: `colibri generate`
4. Explore: Open `dist/index.html`

---

**Created:** 2025-11-15
**Author:** Documentation for Olist EDA Project
**Tool Version:** dbt-colibri (latest)
