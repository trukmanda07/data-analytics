# Claude Code Agent Instructions
## Automated Marimo Notebook Generation for Olist Dataset Analysis

This file contains instructions for Claude Code to automatically generate marimo notebooks for analyzing the Olist Brazilian E-Commerce dataset.

---

## 📋 Context & Setup

**Dataset Path:** `/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/`

**Available Tables:**
- `customers` - Customer information
- `orders` - Order details with status and timestamps
- `order_items` - Line items for each order (products, prices, freight)
- `payments` - Payment method and installment details
- `reviews` - Customer review scores and comments
- `products` - Product catalog with categories
- `sellers` - Seller location information
- `geolocation` - Brazilian zip code coordinates
- `category_translation` - Portuguese to English category names

**Environment:**
- Python virtual environment: `.venv` (created with uv)
- Required packages: `marimo`, `duckdb`, `pandas`, `plotly`, `polars`, `matplotlib`, `seaborn`

---

## 🎯 Your Role

When the user requests analysis or wants to explore business questions:

1. **Understand the Request**: Identify which business question(s) from `available_analysis.md` are relevant, if not please add it to the list.
2. **Generate Marimo Notebook**: Create a complete, executable `.py` file with marimo cells
3. **Include Visualizations**: Add appropriate charts and tables
4. **Make it Interactive**: Use marimo UI elements where beneficial
5. **Document**: Add markdown cells explaining the analysis

---

## 📝 Marimo Notebook Template Structure

Every notebook you generate should follow this structure:

```python
import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import duckdb
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return mo, duckdb, pd, px, go


@app.cell
def __(mo):
    mo.md("""
    # [Analysis Title]

    **Business Question:** [State the question being answered]

    **Objective:** [Brief description of what this analysis aims to discover]
    """)
    return


@app.cell
def __():
    # Import the Olist utilities module
    import sys
    sys.path.append('/home/dhafin/Documents/Projects/EDA')
    from olist_utils import marimo_setup

    # Quick setup - loads all tables and creates common views
    con, dataset_path = marimo_setup()
    return con, dataset_path


# [Add analysis cells here - queries, visualizations, insights]


@app.cell
def __(mo):
    mo.md("""
    ## Key Insights

    1. [First insight]
    2. [Second insight]
    3. [Third insight]
    """)
    return


if __name__ == "__main__":
    app.run()
```

---

## 🎨 Common Patterns to Include

### Pattern 1: Query + DataFrame Display
```python
@app.cell
def __(con):
    result_df = con.execute("""
        SELECT
            -- your query here
        FROM table_name
    """).df()
    result_df
    return result_df
```

### Pattern 2: Query + Visualization
```python
@app.cell
def __(con, px):
    data = con.execute("""
        SELECT -- query
    """).df()

    fig = px.bar(data, x='column1', y='column2', title='Chart Title')
    fig
    return data, fig
```

### Pattern 3: Interactive UI Element
```python
@app.cell
def __(mo):
    date_range = mo.ui.date_range(
        start="2016-01-01",
        end="2018-12-31",
        label="Select Date Range"
    )
    date_range
    return date_range


@app.cell
def __(con, date_range):
    filtered = con.execute(f"""
        SELECT *
        FROM orders
        WHERE order_purchase_timestamp BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    """).df()
    return filtered
```

### Pattern 4: Multiple Metrics Display
```python
@app.cell
def __(mo, metric1, metric2, metric3):
    mo.hstack([
        mo.stat(label="Total Revenue", value=f"R$ {metric1:,.2f}"),
        mo.stat(label="Total Orders", value=f"{metric2:,}"),
        mo.stat(label="Avg Order Value", value=f"R$ {metric3:,.2f}")
    ])
    return
```

---

## 🚀 Generation Workflow

When user requests analysis, follow these steps:

### Step 1: Clarify Requirements
Ask if needed:
- Which specific business question(s) to address?
- What time period to focus on?
- Any specific filters (state, category, etc.)?
- Desired output format (dashboard, report, deep-dive)?

### Step 2: Plan the Notebook
Outline:
- Main sections and cells
- Key queries needed
- Visualizations to include
- Interactive elements to add

### Step 3: Generate Complete File
Create the `.py` file with:
- Descriptive filename (e.g., `revenue_analysis.py`, `executive_dashboard.py`)
- All necessary imports
- Dataset loading cells
- Analysis cells with queries
- Visualization cells
- Markdown documentation cells
- Key insights summary

### Step 4: Provide Usage Instructions
Tell the user:
```bash
# Activate environment
source .venv/bin/activate

# Run the notebook
marimo edit [filename].py
```

---

## 💡 Best Practices

### SQL Queries
- Always filter `order_status = 'delivered'` for completed transactions
- Use `CAST(...AS TIMESTAMP)` for date operations
- Round financial values to 2 decimals
- Use `COUNT(DISTINCT ...)` for counting unique entities
- Join with `category_translation` for English category names

### Visualizations
- Use Plotly for interactive charts
- Include clear titles and axis labels
- Use appropriate chart types:
  - Line charts for trends over time
  - Bar charts for comparisons
  - Pie/donut charts for composition
  - Scatter plots for correlations
  - Heatmaps for geographic data
  - Box plots for distributions

### Marimo UI Elements
Available components:
- `mo.ui.dropdown()` - Select from options
- `mo.ui.date_range()` - Date range picker
- `mo.ui.slider()` - Numeric range selection
- `mo.ui.multiselect()` - Multiple selections
- `mo.ui.text()` - Text input
- `mo.stat()` - Metric display cards
- `mo.hstack()` / `mo.vstack()` - Layout containers

### Documentation
- Start with clear title and objective
- Explain complex queries with comments
- Add interpretation after each visualization
- End with key insights summary
- Include assumptions and data quality notes

### Markdown Formatting in Marimo

**IMPORTANT:** Marimo renders markdown differently than GitHub. Follow these guidelines:

#### ✅ DO - Use These Patterns:

**Lists with Bold Headers:**
```python
mo.md("""
## Benefits of Using olist_utils

**Single import** - No need to copy/paste setup code

**Automatic table loading** - All 9 tables loaded as views

**Common joins pre-created** - Use `orders_complete`, `order_items_complete`, etc.

**Easy maintenance** - Update path in one place (`.env` or `olist_utils.py`)

**No breaking changes** - All notebooks stay functional when paths change
""")
```

**Numbered Lists:**
```python
mo.md("""
## Key Steps

1. Load the data using `marimo_setup()`
2. Write your SQL query
3. Visualize the results
4. Share your insights
""")
```

**Code Blocks:**
```python
mo.md("""
## Example Usage

Use this pattern:

\`\`\`python
from olist_utils import marimo_setup
con, dataset_path = marimo_setup()
\`\`\`
""")
```

**Tables:**
```python
mo.md("""
| Column | Description |
|--------|-------------|
| order_id | Unique order identifier |
| customer_id | Customer reference |
| order_status | Current order state |
""")
```

#### ❌ DON'T - Avoid These Patterns:

**Checkbox Lists (not rendered properly):**
```python
# DON'T USE THIS
mo.md("""
- ✅ Feature 1
- ✅ Feature 2
- ❌ Feature 3
""")
```

**Emoji-heavy formatting:**
```python
# DON'T USE THIS
mo.md("""
🎯 Goal
🚀 Action
✨ Result
""")
```

Instead, use bold headers or regular lists.

#### Best Practices for Marimo Markdown:

1. **Use `mo.md()` for all markdown content**
2. **Keep it simple** - Plain markdown renders best
3. **Use bold for emphasis** - `**text**` instead of emojis
4. **Test rendering** - Run the notebook to see how it looks
5. **Separate content** - Use multiple cells for better organization

#### Example: Well-Formatted Benefits Section

```python
@app.cell
def __(mo):
    mo.md("""
    ## Benefits of Using olist_utils

    **Single import** - No need to copy/paste setup code

    **Automatic table loading** - All 9 tables loaded as views

    **Common joins pre-created** - Use `orders_complete`, `order_items_complete`, etc.

    **Easy maintenance** - Update path in one place (`.env` or `olist_utils.py`)

    **No breaking changes** - All notebooks stay functional when paths change

    ---

    ## Alternative Setup Methods

    If you need more control, you can use individual functions:

    \`\`\`python
    from olist_utils import setup_duckdb, load_all_tables, create_common_views

    # Manual setup
    con = setup_duckdb()
    load_all_tables(con)
    create_common_views(con)
    \`\`\`
    """)
    return
```

---

## 🔧 Technical Notes

### DuckDB Performance Tips
- Use views for reusable query patterns
- Create materialized tables for heavy computations
- Leverage `read_csv_auto()` for automatic type inference
- Use `EXPLAIN` to optimize complex queries

### Marimo Reactivity
- Variables returned from cells are automatically tracked
- Cells re-execute when dependencies change
- UI elements automatically trigger re-computation
- Use `mo.stop()` to halt execution conditionally

### File Naming Convention
- `executive_dashboard.py` - High-level overview
- `revenue_analysis.py` - Revenue deep-dive
- `customer_cohort_analysis.py` - Customer behavior
- `delivery_performance.py` - Logistics analysis
- `seller_scorecard.py` - Seller performance
- `product_insights.py` - Product analysis
- `geographic_distribution.py` - Regional analysis

---

## ✅ Pre-flight Checklist

Before generating a notebook, ensure:

- [ ] Clear business question identified
- [ ] Required tables mapped out
- [ ] Query logic planned
- [ ] Visualization types selected
- [ ] Interactive elements designed (if needed)
- [ ] File name chosen
- [ ] Key insights framework prepared

---

## 🎬 Example Generation Request

**User:** "Create analysis for monthly revenue trends"

**Your Response:**
1. Acknowledge the request
2. Ask clarifying questions if needed (date range, granularity, etc.)
3. Create `revenue_trends_monthly.py` with:
   - Monthly revenue calculation
   - Line chart visualization
   - YoY and MoM growth metrics
   - Revenue by category breakdown
   - Key insights summary
4. Provide run instructions
5. Offer to add more analysis if needed

---

## 🚨 Important Reminders

1. **Always load ALL tables** in the data loading cell, even if not all are used
2. **Use parameterized queries** to prevent SQL injection with UI inputs
3. **Handle NULL values** in date calculations
4. **Test queries** with LIMIT first for large datasets
5. **Add error handling** for edge cases
6. **Document assumptions** about data quality
7. **Include data freshness note** (dataset is 2016-2018)

---

**Ready to generate insights!** 🚀

When the user requests analysis, use this guide to create complete, professional, executable marimo notebooks that answer their business questions with clear visualizations and actionable insights.
