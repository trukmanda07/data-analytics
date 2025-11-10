# Available Analysis - Based on dim_customers & fct_orders

**Last Updated:** 2025-11-10
**Data Tables:** `dim_customers` (99,441 rows) | `fct_orders` (99,992 rows)
**Status:** ✅ Ready for Analysis

---

## 📊 Analysis Groups & Marimo Notebooks Plan

### **Notebook 1: Executive Dashboard**
**File:** `executive_dashboard.py`
**Priority:** TIER 1 - Weekly Review

**Answerable Questions:**
1. ✅ **Q1:** Month-over-month and year-over-year revenue growth trend
2. ✅ **Q2:** New customers acquired monthly (customer acquisition trend)
3. ✅ **Q3:** Marketplace GMV (Gross Merchandise Value) trajectory
4. ✅ **Q5:** Order volume growth trend by month/quarter/year
5. ✅ **Q6:** Average order value (AOV) and trend over time
6. ✅ **Q21:** Average delivery time vs promised delivery time
7. ✅ **Q31:** Overall customer satisfaction score (NPS proxy from review ratings)

**Key Metrics:**
- Total GMV, Monthly Revenue, YoY/MoM Growth %
- Total Orders, New Customers, AOV
- Delivery Performance (on-time %, avg days)
- Customer Satisfaction Score (avg review)

---

### **Notebook 2: Revenue & Financial Analysis**
**File:** `revenue_financial_analysis.py`
**Priority:** TIER 2 - Monthly Review

**Answerable Questions:**
9. ✅ **Q9:** Payment method distribution and cash flow impact
10. ✅ **Q10:** Average payment installment plan and working capital impact
13. ✅ **Q13:** Correlation between price point and conversion rates
14. ✅ **Q14:** Price ranges generating highest volume vs highest revenue
15. ✅ **Q15:** Average freight cost as percentage of order value
17. ✅ **Q17:** Seasonal revenue patterns for planning
18. ✅ **Q18:** Revenue per customer (lifetime value proxy)
20. ✅ **Q20:** Revenue impact of different delivery speeds
90. ✅ **Q90:** Average order value for different payment methods

**Analysis Includes:**
- Revenue distribution by payment method
- Installment analysis (credit risk assessment)
- Price elasticity and volume/revenue optimization
- Freight cost economics
- Customer LTV segments

---

### **Notebook 3: Delivery & Operations Performance**
**File:** `delivery_operations_analysis.py`
**Priority:** TIER 2 - Monthly Review

**Answerable Questions:**
21. ✅ **Q21:** Average delivery time vs promised delivery time
22. ✅ **Q22:** Percentage of orders delivered late (trend)
23. ✅ **Q23:** States/regions with best and worst delivery performance
24. ✅ **Q24:** Correlation between delivery time and customer satisfaction
25. ✅ **Q25:** Relationship between freight cost and delivery time
26. ✅ **Q26:** Order fulfillment cycle time (purchase to delivery)
28. ✅ **Q28:** Geographical distribution of delivery delays

**Analysis Includes:**
- On-time delivery rate by state
- Delivery time distribution
- Late delivery hotspots (geographic heatmap)
- Freight cost vs speed trade-off
- Satisfaction impact of delivery performance

---

### **Notebook 4: Customer Satisfaction & Experience**
**File:** `customer_satisfaction_analysis.py`
**Priority:** TIER 1 - Weekly Review

**Answerable Questions:**
31. ✅ **Q31:** Overall customer satisfaction score (NPS proxy)
32. ✅ **Q32:** Correlation between delivery time and review scores
64. ✅ **Q64:** Customer satisfaction variation by region
100. ✅ **Q100:** Factors most strongly predicting customer satisfaction

**Analysis Includes:**
- NPS calculation from review scores
- Satisfaction drivers (delivery, price, payment)
- Regional satisfaction benchmarks
- Review sentiment distribution
- Correlation analysis (delivery time, order value, payment method vs satisfaction)

---

### **Notebook 5: Customer Behavior & Retention**
**File:** `customer_retention_cohort_analysis.py`
**Priority:** TIER 2 - Monthly Review

**Answerable Questions:**
36. ✅ **Q36:** Customer repeat purchase rate
37. ✅ **Q37:** Average time between first and second purchase
39. ✅ **Q39:** Customer churn rate month-over-month
40. ✅ **Q40:** Do customers who write reviews have different purchasing patterns?
72. ✅ **Q72:** Customer cohort retention analysis (monthly cohorts)
75. ✅ **Q75:** First-time buyer behaviors vs repeat customers

**Analysis Includes:**
- Cohort retention curves
- Repeat purchase rate by cohort
- Customer segmentation (One Time, Second Time, Repeat)
- Churn analysis
- Review-writer behavior patterns

---

### **Notebook 6: Geographic & Market Distribution**
**File:** `geographic_market_analysis.py`
**Priority:** TIER 3 - Quarterly Review

**Answerable Questions:**
61. ✅ **Q61:** Revenue distribution across Brazilian states
62. ✅ **Q62:** Cities generating the most orders and revenue
64. ✅ **Q64:** Customer satisfaction variation by region
67. ✅ **Q67:** Regions with highest growth rates
70. ✅ **Q70:** Regions with best unit economics

**Analysis Includes:**
- State-level revenue heatmap
- Top cities by GMV and order volume
- Regional growth rates (YoY, MoM)
- Geographic satisfaction scores
- Unit economics by region (AOV, freight %, satisfaction)

---

### **Notebook 7: Order Status & Risk Management**
**File:** `order_risk_cancellation_analysis.py`
**Priority:** TIER 2 - Monthly Review

**Answerable Questions:**
81. ✅ **Q81:** Order cancellation rate and main reasons
82. ✅ **Q82:** Patterns in cancelled orders (price, region)
86. ✅ **Q86:** Payment failure rate by payment method
87. ✅ **Q87:** Geographic patterns in payment issues
88. ✅ **Q88:** Distribution of installment payments (credit risk)
89. ✅ **Q89:** High-installment orders vs low-installment performance

**Analysis Includes:**
- Cancellation rate trends
- Cancellation patterns (by state, order value, payment method)
- Payment method risk profile
- Installment distribution and default proxy
- Geographic risk assessment

---

### **Notebook 8: Marketing & Sales Optimization**
**File:** `marketing_sales_timing_analysis.py`
**Priority:** TIER 2 - Monthly Review

**Answerable Questions:**
76. ✅ **Q76:** Peak sales periods (day of week, month, season)
17. ✅ **Q17:** Seasonal revenue patterns for campaign planning
80. ✅ **Q80:** Customer segments to target for reactivation

**Analysis Includes:**
- Day of week / hour of day patterns
- Monthly seasonality analysis
- Holiday impact analysis
- Customer reactivation opportunities (dormant segments)
- Best timing for campaigns

---

### **Notebook 9: Payment & Financial Risk**
**File:** `payment_method_financial_analysis.py`
**Priority:** TIER 2 - Monthly Review

**Answerable Questions:**
9. ✅ **Q9:** Payment method distribution
10. ✅ **Q10:** Average installment plan impact on working capital
86. ✅ **Q86:** Payment failure rate by payment method
88. ✅ **Q88:** Installment payment distribution
89. ✅ **Q89:** High-installment vs low-installment performance
90. ✅ **Q90:** Average order value by payment method

**Analysis Includes:**
- Payment method mix (credit card, boleto, voucher)
- Installment analysis (2x, 3x, 6x, 10x+)
- Working capital impact calculation
- Payment method preferences by order value
- Risk assessment by payment type

---

## ❌ Questions NOT Answerable (Missing Data)

### Missing Product/Category Data:
- Q7, Q8: Revenue breakdown by product category
- Q11: Take rate/commission by category
- Q34: Satisfaction by product category
- Q38: Categories driving retention
- Q41-50: All product catalog questions
- Q73-74: Category-based acquisition/retention
- Q77-79: Category pricing and market basket

### Missing Seller Data:
- Q4: Seller churn rate
- Q27: Sellers meeting delivery commitments
- Q30: Logistics partner allocation
- Q35: Review scores by seller
- Q51-60: All seller performance questions

### Missing Detailed Item Data:
- Q45: Correlation with product photos
- Q78: Market basket analysis (frequently bought together)

### Requires External Data:
- Q2 (CAC calculation - need marketing spend)
- Q11 (Commission structure - need Olist's pricing model)
- Q63: Underserved regions (need market size data)
- Q66: Market penetration (need TAM data)
- Q91-99: Predictive models (can build, but need validation data)

---

## 🎯 Priority Implementation Order

### Phase 1 - Week 1 (Executive Priorities)
1. ✅ **Executive Dashboard** - Core metrics for leadership
2. ✅ **Customer Satisfaction Analysis** - NPS and experience drivers
3. ✅ **Delivery Operations** - Critical operational KPI

### Phase 2 - Week 2 (Financial & Customer Insights)
4. ✅ **Revenue & Financial Analysis** - Monetization deep-dive
5. ✅ **Customer Retention & Cohort** - Retention economics
6. ✅ **Payment Method Analysis** - Financial risk assessment

### Phase 3 - Week 3 (Strategic & Geographic)
7. ✅ **Geographic Market Analysis** - Regional expansion insights
8. ✅ **Order Risk & Cancellation** - Risk management
9. ✅ **Marketing & Sales Timing** - Campaign optimization

---

## 📈 Total Coverage

**Answerable Questions:** 45 out of 100 (45%)
**High-Priority (Tier 1-2) Questions Covered:** ~80%
**Limitations:** No product/category or seller-level analysis without additional dimensions

---

## 🚀 Next Steps

1. **Choose Priority Notebook:** Which analysis should we build first?
2. **Define Interactivity:** Date range filters? State selectors? Customer segment filters?
3. **Set Baseline Metrics:** Define what "good" looks like for each KPI
4. **Generate Notebook:** I'll create the complete marimo notebook with queries and visualizations

**Ready to build! Which notebook should we start with?**
