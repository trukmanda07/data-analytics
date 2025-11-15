# Available Analysis - Complete Olist Dataset

**Last Updated:** 2025-11-11
**Data Source:** Raw CSV files + DBT transformed models
**Status:** ✅ Full dataset with 9 tables + DBT Star Schema

---

## 📊 Dataset Overview

### Raw Source Tables (9 tables)

**Customer & Orders (99,441 rows each)**
- `customers` - Customer location information
- `orders` - Order details with timestamps and status

**Transaction Details**
- `order_items` (112,650 rows) - Line items with products, sellers, prices, freight
- `payments` (103,886 rows) - Payment methods and installments
- `reviews` (99,224 rows) - Customer review scores and comments

**Product & Seller Master Data**
- `products` (32,951 rows) - Product catalog with dimensions and categories
- `sellers` (3,095 rows) - Seller location information
- `category_translation` (71 rows) - Portuguese to English category mapping

**Geographic Reference**
- `geolocation` (1,000,163 rows) - Brazilian zip code coordinates

---

## 🏗️ DBT Transformed Models

### Staging Layer (9 models)
Clean, standardized source data:
- `stg_customers`, `stg_orders`, `stg_order_items`
- `stg_payments`, `stg_reviews`, `stg_products`
- `stg_sellers`, `stg_geolocation`, `stg_category_translation`

### Intermediate Layer (3 models)
Pre-joined and enriched data:
- `int_orders_enriched` - Orders with customer, payment, review data
- `int_order_items_enriched` - Items with product, seller, geography data
- `int_order_payments_aggregated` - Aggregated payment data per order

### Core Layer - Star Schema

**Dimensions (6 models)**
1. **`dim_customers`** - Customer profiles with RFM segmentation
2. **`dim_products`** - Product catalog with attributes and categories
3. **`dim_sellers`** - Seller profiles with performance metrics
4. **`dim_geography`** - Brazilian location hierarchy with regions
5. **`dim_category`** - Product category master with translations
6. **`dim_date`** - Date dimension with calendar attributes

**Facts (4 models)**
1. **`fct_orders`** - Order-level metrics (revenue, delivery, satisfaction)
2. **`fct_order_items`** - Item-level sales details
3. **`fct_payments`** - Payment transactions
4. **`fct_reviews`** - Customer review events

### Marts Layer - Business Analysis Ready (4 models)

1. **`mart_executive_dashboard`**
   - Daily business metrics with moving averages
   - Revenue, orders, customers, satisfaction trends
   - YTD running totals
   - Delivery and payment performance

2. **`mart_customer_analytics`**
   - RFM analysis (Recency, Frequency, Monetary)
   - Customer segmentation (Champions, Loyal, At Risk, Lost)
   - Lifetime value and behavior metrics
   - Product preferences and review behavior

3. **`mart_product_performance`**
   - Product sales and revenue metrics
   - Review scores and sentiment
   - Delivery performance by product
   - Geographic reach and seller diversity

4. **`mart_seller_scorecard`**
   - Comprehensive seller performance metrics
   - Revenue efficiency and growth indicators
   - Product diversity and specialization
   - Geographic focus analysis
   - Health scores and activity status

---

## 📊 Analysis Capabilities by Domain

### 1. Executive & Strategic Analysis

**Revenue & Growth Metrics**
- ✅ Total GMV, revenue by day/month/quarter/year
- ✅ MoM and YoY growth rates
- ✅ Average order value (AOV) trends
- ✅ Revenue per customer (lifetime value)
- ✅ Revenue by payment method, category, region
- ✅ Moving averages (7-day, 30-day)
- ✅ YTD running totals

**Order Volume & Trends**
- ✅ Order volume by time period
- ✅ Order status distribution (delivered, canceled, processing)
- ✅ Orders by day of week, hour, seasonality
- ✅ Peak sales periods identification
- ✅ Order cancellation rates and patterns

**Customer Acquisition & Retention**
- ✅ New vs repeat customers
- ✅ Customer acquisition trends
- ✅ Unique customers per period
- ✅ Retention metrics from RFM analysis

---

### 2. Customer Analytics

**RFM Segmentation**
- ✅ Recency, Frequency, Monetary scores (1-5)
- ✅ Customer segments: Champions, Loyal, At Risk, Lost, New
- ✅ Segment distribution and trends
- ✅ Migration between segments

**Customer Behavior**
- ✅ Purchase frequency and patterns
- ✅ Average days between orders
- ✅ Items per order
- ✅ Preferred payment methods
- ✅ Installment usage patterns
- ✅ Product category preferences
- ✅ Cross-category purchasing

**Customer Value**
- ✅ Lifetime value (LTV) distribution
- ✅ Value tiers: VIP, High, Medium, Low
- ✅ Revenue per customer
- ✅ Customer profitability analysis

**Customer Lifecycle**
- ✅ Lifecycle stages: Active, Cooling Down, At Risk, Dormant
- ✅ Churn prediction indicators
- ✅ Reactivation opportunities
- ✅ First purchase to repeat purchase time

**Customer Geography**
- ✅ Customer distribution by state/city
- ✅ Regional customer preferences
- ✅ Urban vs rural customer behavior

---

### 3. Product & Category Analysis

**Product Performance**
- ✅ Sales volume by product/category
- ✅ Revenue by product/category
- ✅ Best sellers and slow movers
- ✅ Product lifecycle analysis (first/last sale date)
- ✅ Units sold and revenue per unit
- ✅ Price distribution (min, max, avg)

**Product Attributes Impact**
- ✅ Sales by product size/weight
- ✅ Product dimensions correlation with sales
- ✅ Product completeness score impact
- ✅ Photo quantity impact (available in raw data)

**Category Insights**
- ✅ Category revenue contribution
- ✅ Category growth rates
- ✅ Category seasonality
- ✅ Category-level margins (price vs freight)
- ✅ Cross-category purchasing patterns

**Product Reviews**
- ✅ Average review score by product/category
- ✅ Review sentiment distribution
- ✅ Products with highest/lowest ratings
- ✅ Review volume by product
- ✅ Correlation: product attributes vs ratings

---

### 4. Seller Performance

**Seller Metrics**
- ✅ Total sellers active
- ✅ Revenue per seller
- ✅ Orders per seller
- ✅ Average order value by seller
- ✅ Seller performance tiers

**Seller Health Scorecards**
- ✅ Overall performance score (weighted)
- ✅ Revenue percentile ranking
- ✅ Review score (0-100 scale)
- ✅ Delivery score (on-time rate)
- ✅ Health status: Excellent, Good, Average, Needs Improvement

**Seller Activity**
- ✅ Active vs inactive sellers
- ✅ Activity status: Active (30d), Recent (90d), Cooling, Inactive
- ✅ First and last sale dates
- ✅ Days active and active months
- ✅ Recent activity trends (30/90/180 days)

**Seller Specialization**
- ✅ Product diversity (unique products/categories)
- ✅ Specialization type: Specialist, Focused, Diverse, Generalist
- ✅ Top category per seller
- ✅ Category concentration

**Seller Geography**
- ✅ Seller location distribution
- ✅ Geographic reach (states served)
- ✅ Same-state vs cross-state sales
- ✅ Geographic focus: Local, Regional, National
- ✅ Top customer state per seller

**Seller Efficiency**
- ✅ Revenue per item/order/day/month
- ✅ Delivery performance (on-time rate)
- ✅ Average delivery days
- ✅ Freight costs relative to price
- ✅ Price range and consistency

**Seller Growth**
- ✅ Volume trends over time
- ✅ Order growth rates
- ✅ Customer acquisition by seller
- ✅ Seller churn identification

---

### 5. Delivery & Logistics

**Delivery Performance**
- ✅ Average delivery time vs estimated time
- ✅ On-time delivery rate
- ✅ Late delivery rate and trends
- ✅ Delivery time distribution
- ✅ Days from purchase to delivery

**Geographic Delivery Analysis**
- ✅ Delivery performance by state/region
- ✅ Best and worst performing regions
- ✅ Same-state vs cross-state delivery times
- ✅ Distance impact on delivery time
- ✅ Geographic delivery heatmaps

**Freight Economics**
- ✅ Freight cost as % of order value
- ✅ Average freight by product/category
- ✅ Freight vs delivery speed correlation
- ✅ Freight cost by distance/region
- ✅ Freight optimization opportunities

**Delivery Impact**
- ✅ Delivery time vs customer satisfaction correlation
- ✅ Late delivery impact on reviews
- ✅ Delivery performance impact on repeat purchases

---

### 6. Payment & Financial Analysis

**Payment Methods**
- ✅ Payment method distribution (credit card, boleto, voucher, debit)
- ✅ AOV by payment method
- ✅ Payment method preferences by region/segment
- ✅ Payment method trends over time

**Installment Analysis**
- ✅ Installment usage rate
- ✅ Average installments per order
- ✅ Installment distribution (1x, 2x, 3x, ... 24x)
- ✅ High-installment vs low-installment performance
- ✅ Installments by order value correlation
- ✅ Working capital impact calculation

**Payment Risk**
- ✅ Payment method by cancellation rate
- ✅ High-installment order risk assessment
- ✅ Geographic payment patterns
- ✅ Payment value vs order value discrepancies

**Revenue Recognition**
- ✅ Total payment value vs order value
- ✅ Payment timing analysis
- ✅ Cash flow implications by payment method

---

### 7. Customer Satisfaction & Reviews

**Review Metrics**
- ✅ Overall NPS proxy (average review score)
- ✅ Review score distribution (1-5 stars)
- ✅ Positive review rate (4-5 stars)
- ✅ Negative review rate (1-2 stars)
- ✅ Neutral reviews (3 stars)
- ✅ Review volume trends

**Satisfaction Drivers**
- ✅ Delivery time impact on review scores
- ✅ On-time delivery correlation with satisfaction
- ✅ Order value impact on reviews
- ✅ Payment method impact on satisfaction
- ✅ Product category satisfaction differences
- ✅ Seller performance impact on reviews

**Review Behavior**
- ✅ Review rate (% of orders with reviews)
- ✅ Time from delivery to review
- ✅ Customers who write reviews vs those who don't
- ✅ Comment frequency and patterns
- ✅ Title vs comment presence

**Geographic Satisfaction**
- ✅ Review scores by state/region
- ✅ Regional satisfaction benchmarks
- ✅ Urban vs rural satisfaction
- ✅ Correlation with delivery performance

---

### 8. Geographic & Market Distribution

**Regional Revenue**
- ✅ Revenue by state/city
- ✅ Top revenue-generating cities
- ✅ State-level market share
- ✅ Regional contribution to GMV

**Market Penetration**
- ✅ Orders by state/city
- ✅ Customer density by region
- ✅ Seller distribution by state
- ✅ Market concentration analysis

**Regional Characteristics**
- ✅ AOV by region
- ✅ Product preferences by region
- ✅ Payment method preferences by region
- ✅ Category popularity by region

**Growth Opportunities**
- ✅ High-growth regions identification
- ✅ Underserved areas (low seller/high customer)
- ✅ Regional expansion opportunities
- ✅ Best unit economics by region

**Regional Operations**
- ✅ Regional delivery performance
- ✅ Regional freight costs
- ✅ Regional satisfaction scores
- ✅ Regional logistics efficiency

---

### 9. Time-Series & Seasonality Analysis

**Temporal Patterns**
- ✅ Sales by year/quarter/month
- ✅ Day of week patterns
- ✅ Weekend vs weekday performance
- ✅ Holiday impact analysis (with dim_date)
- ✅ Hourly patterns (if timestamp available)

**Seasonality**
- ✅ Monthly seasonality identification
- ✅ Quarterly trends
- ✅ Year-over-year comparisons
- ✅ Seasonal product/category performance

**Trending Analysis**
- ✅ Moving averages (7-day, 30-day)
- ✅ Growth rates (MoM, YoY)
- ✅ Trend detection (up, down, stable)
- ✅ Anomaly detection opportunities

---

### 10. Risk & Operations Management

**Order Risk**
- ✅ Cancellation rate and trends
- ✅ Cancellation patterns by region/category/value
- ✅ High-risk order characteristics
- ✅ Cancellation reasons (if available in status)

**Inventory & Supply**
- ✅ Days on sale by product
- ✅ Product lifecycle stages
- ✅ Seller reliability (fulfillment rate)
- ✅ Stock-out indicators (no recent sales)

**Operational Efficiency**
- ✅ Order fulfillment cycle time
- ✅ Processing time before shipping
- ✅ Carrier handoff time
- ✅ End-to-end delivery time

---

## 🎯 Recommended Marimo Notebooks

Based on the available data, here are the recommended notebooks:

### Tier 1: Executive Priority (Weekly Review)

**1. Executive Dashboard (`executive_dashboard.py`)**
- Uses: `mart_executive_dashboard`
- Key Metrics: GMV, Revenue, Orders, AOV, Customer Satisfaction
- Moving averages and YTD tracking
- Daily/Weekly/Monthly views

**2. Customer Satisfaction Deep Dive (`customer_satisfaction_analysis.py`)**
- Uses: `fct_reviews`, `fct_orders`, `dim_geography`
- NPS proxy calculation
- Satisfaction drivers analysis
- Regional satisfaction benchmarks

**3. Revenue & Financial Analysis (`revenue_financial_analysis.py`)**
- Uses: `mart_executive_dashboard`, `fct_payments`
- Revenue trends and growth rates
- Payment method analysis
- Installment impact on cash flow

---

### Tier 2: Business Intelligence (Monthly Review)

**4. Customer Analytics & RFM (`customer_rfm_analysis.py`)**
- Uses: `mart_customer_analytics`
- RFM segmentation dashboard
- Customer lifecycle analysis
- Retention and churn insights
- Reactivation opportunities

**5. Product Performance Analysis (`product_performance_analysis.py`)**
- Uses: `mart_product_performance`
- Best sellers and slow movers
- Category performance comparison
- Product attribute impact
- Review analysis by product

**6. Seller Scorecard (`seller_performance_scorecard.py`)**
- Uses: `mart_seller_scorecard`
- Comprehensive seller KPIs
- Health scores and rankings
- Activity trends
- Specialization analysis

**7. Delivery & Operations (`delivery_operations_analysis.py`)**
- Uses: `fct_orders`, `fct_order_items`, `dim_geography`
- On-time delivery tracking
- Geographic delivery performance
- Freight cost analysis
- Delivery time trends

**8. Payment Method & Risk (`payment_risk_analysis.py`)**
- Uses: `fct_payments`, `fct_orders`
- Payment method preferences
- Installment analysis
- Payment risk assessment
- Working capital impact

---

### Tier 3: Strategic Planning (Quarterly Review)

**9. Geographic Market Analysis (`geographic_market_analysis.py`)**
- Uses: `dim_geography`, all fact tables
- State/city revenue heatmaps
- Regional growth rates
- Market penetration analysis
- Expansion opportunities

**10. Customer Cohort Analysis (`customer_cohort_retention.py`)**
- Uses: `mart_customer_analytics`, `fct_orders`
- Cohort retention curves
- Lifetime value by cohort
- Cohort behavior comparison
- Predictive churn modeling

**11. Seasonality & Marketing Timing (`seasonality_marketing_analysis.py`)**
- Uses: `mart_executive_dashboard`, `dim_date`
- Seasonal patterns identification
- Day of week/month analysis
- Holiday impact
- Campaign timing optimization

---

## 📈 Advanced Analytics Opportunities

### Predictive Models (Can Build)
- ✅ Customer churn prediction (RFM + behavior)
- ✅ LTV prediction models
- ✅ Review score prediction
- ✅ Delivery time prediction
- ✅ Order cancellation risk scoring
- ✅ Next purchase prediction

### Clustering Analysis
- ✅ Customer segmentation (beyond RFM)
- ✅ Product clustering
- ✅ Seller clustering
- ✅ Geographic market segmentation

### Correlation Analysis
- ✅ Price vs satisfaction
- ✅ Delivery time vs reviews
- ✅ Freight cost vs order value
- ✅ Product attributes vs performance
- ✅ Multi-factor satisfaction drivers

---

## ❌ Limitations & Missing Data

### Cannot Answer (Missing External Data)
- CAC (Customer Acquisition Cost) - need marketing spend
- ROI/ROAS - need campaign data
- Actual commission rates - need Olist's pricing model
- Market size/TAM - need external market research
- Competitor benchmarks - need competitive data

### Limited Analysis (Data Quality Issues)
- Product descriptions are length only (not actual text)
- Review comments are available but require NLP
- Geolocation is extensive but may have duplicates
- Some products missing category assignments

---

## 🚀 Getting Started

### Quick Analysis with Marimo Notebooks

1. **Activate environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Use the utility module for fast setup:**
   ```python
   from olist_utils import marimo_setup
   con, dataset_path = marimo_setup()
   ```

3. **Query the marts directly:**
   ```sql
   SELECT * FROM mart_executive_dashboard
   WHERE date_day >= '2018-01-01'
   ORDER BY date_day DESC
   ```

4. **Create visualizations:**
   ```python
   import plotly.express as px
   fig = px.line(df, x='date_day', y='total_revenue', title='Daily Revenue')
   ```

---

## 📚 Schema Quick Reference

### Key Relationships

**Customer Journey:**
```
customers → orders → order_items → products
                   → payments
                   → reviews
          → geography
```

**Seller Flow:**
```
sellers → order_items → products
       → geography
```

**Star Schema (Marts):**
```
fct_orders ─┬─ dim_customers
            ├─ dim_geography
            ├─ dim_date
            └─ (through order_items)
               ├─ dim_products
               ├─ dim_category
               └─ dim_sellers
```

---

## 💡 Pro Tips

1. **Always filter on delivered orders** for revenue analysis:
   ```sql
   WHERE is_delivered = true
   ```

2. **Use marts for complex analysis** instead of joining raw tables

3. **Leverage RFM segments** for customer targeting:
   - Champions: Reward and retain
   - At Risk: Reactivation campaigns
   - Lost: Win-back offers

4. **Monitor these key metrics daily:**
   - Total GMV and orders
   - Average review score
   - On-time delivery rate
   - Cancellation rate

5. **Use moving averages** to smooth daily volatility

---

**Last Updated:** 2025-11-11
**Dataset Period:** 2016-09 to 2018-08 (24 months)
**Total Orders:** 99,441
**Total Customers:** 99,441 (96,096 unique)
**Total Products:** 32,951
**Total Sellers:** 3,095

✅ **Ready for comprehensive business intelligence and advanced analytics!**
