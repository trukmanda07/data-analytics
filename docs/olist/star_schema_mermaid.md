# Olist Data Warehouse - Star Schema (Mermaid Diagrams)

**Last Updated:** 2025-11-11
**Architecture:** Kimball Dimensional Model (Star Schema)
**Tool Stack:** DBT + DuckDB

---

## Schema Overview

The Olist data warehouse is built using a star schema design with:
- **6 Dimension Tables** (Customer, Product, Seller, Geography, Category, Date)
- **4 Fact Tables** (Orders, Order Items, Payments, Reviews)
- **4 Mart Tables** (Pre-aggregated business views)

---

## Star Schema Diagram

```mermaid
erDiagram
    %% Fact Tables
    fct_orders {
        VARCHAR order_id PK
        VARCHAR customer_id FK
        INTEGER order_date_key FK
        DECIMAL total_order_value
        DECIMAL total_freight
        DECIMAL total_payment_value
        INTEGER item_count
        INTEGER days_to_delivery
        VARCHAR delivery_performance
        BOOLEAN is_delivered
        BOOLEAN is_canceled
        BOOLEAN used_installments
        BOOLEAN has_review
        BOOLEAN has_comment
        TIMESTAMP order_purchase_timestamp
        TIMESTAMP order_delivered_timestamp
        INTEGER review_score
        INTEGER max_installments
    }

    fct_order_items {
        VARCHAR order_id PK
        INTEGER order_item_id PK
        VARCHAR product_id FK
        VARCHAR seller_id FK
        DECIMAL item_price
        DECIMAL freight_value
        DECIMAL freight_percentage
        INTEGER days_to_deliver
        BOOLEAN is_delivered
        BOOLEAN is_canceled
        BOOLEAN is_on_time_delivery
        BOOLEAN is_same_state
        BOOLEAN is_same_city
        VARCHAR product_category_name
        VARCHAR product_category_name_english
        VARCHAR customer_state
        VARCHAR customer_zip_code_prefix
        VARCHAR seller_state
        TIMESTAMP order_purchase_timestamp
        TIMESTAMP shipping_limit_date
    }

    fct_payments {
        VARCHAR order_id PK
        INTEGER payment_sequential PK
        DECIMAL payment_value
        INTEGER payment_installments
        VARCHAR payment_type
        BOOLEAN is_primary_payment
        BOOLEAN is_credit_card
        BOOLEAN is_boleto
        BOOLEAN is_voucher
        BOOLEAN is_debit_card
        BOOLEAN uses_installments
    }

    fct_reviews {
        VARCHAR review_id PK
        VARCHAR order_id FK
        INTEGER review_score
        INTEGER days_delivery_to_review
        BOOLEAN is_positive
        BOOLEAN is_neutral
        BOOLEAN is_negative
        BOOLEAN has_title
        BOOLEAN has_comment
        VARCHAR review_comment_title
        VARCHAR review_comment_message
        TIMESTAMP review_creation_date
        TIMESTAMP review_answer_timestamp
    }

    %% Dimension Tables
    dim_customers {
        VARCHAR customer_id PK
        VARCHAR customer_unique_id
        VARCHAR customer_zip_code_prefix FK
        VARCHAR customer_city
        VARCHAR customer_state
        VARCHAR customer_state_clean
        VARCHAR customer_segment
        INTEGER days_since_last_order
        TIMESTAMP dbt_updated_at
    }

    dim_products {
        VARCHAR product_id PK
        VARCHAR product_category_name FK
        VARCHAR product_category_name_english
        VARCHAR category_display_name
        INTEGER product_weight_g
        INTEGER product_length_cm
        INTEGER product_height_cm
        INTEGER product_width_cm
        DECIMAL product_volume_cm3
        INTEGER product_name_lenght
        INTEGER product_description_lenght
        INTEGER product_photos_qty
        VARCHAR product_size_category
        VARCHAR product_weight_category
        DECIMAL product_completeness_score
        VARCHAR product_quality_tier
        TIMESTAMP dbt_updated_at
    }

    dim_sellers {
        VARCHAR seller_id PK
        VARCHAR seller_zip_code_prefix FK
        VARCHAR seller_city
        VARCHAR seller_state
        VARCHAR seller_state_clean
        INTEGER total_orders
        INTEGER total_items_sold
        DECIMAL total_revenue
        DECIMAL avg_item_price
        DECIMAL total_freight
        DECIMAL avg_freight
        DECIMAL avg_review_score
        INTEGER positive_reviews
        INTEGER negative_reviews
        INTEGER total_reviews
        DECIMAL positive_review_rate
        DECIMAL avg_delivery_days
        INTEGER on_time_deliveries
        INTEGER total_delivered_orders
        DECIMAL on_time_delivery_rate
        DATE first_sale_date
        DATE last_sale_date
        INTEGER days_active
        INTEGER unique_products_sold
        VARCHAR seller_performance_tier
        VARCHAR seller_size_tier
        TIMESTAMP dbt_updated_at
    }

    dim_geography {
        VARCHAR zip_code_prefix PK
        VARCHAR city
        VARCHAR state
        VARCHAR state_code
        DECIMAL latitude
        DECIMAL longitude
        VARCHAR region
        VARCHAR city_size_tier
        TIMESTAMP dbt_updated_at
    }

    dim_category {
        VARCHAR product_category_name PK
        VARCHAR product_category_name_english
        VARCHAR category_display_name
        INTEGER total_products
        DECIMAL total_revenue
        INTEGER total_orders
        DECIMAL avg_product_price
        VARCHAR category_group
        VARCHAR revenue_tier
        VARCHAR category_size_tier
        TIMESTAMP dbt_updated_at
    }

    dim_date {
        INTEGER date_key PK
        DATE date_day
        INTEGER year
        INTEGER quarter
        INTEGER month
        VARCHAR month_name
        VARCHAR year_month
        INTEGER day_of_month
        INTEGER day_of_week
        VARCHAR day_name
        INTEGER week_of_year
        BOOLEAN is_weekend
        BOOLEAN is_month_start
        BOOLEAN is_month_end
        BOOLEAN is_quarter_start
        BOOLEAN is_quarter_end
        BOOLEAN is_year_start
        BOOLEAN is_year_end
        BOOLEAN is_holiday
        VARCHAR holiday_name
        TIMESTAMP dbt_updated_at
    }

    %% Relationships
    fct_orders ||--|| dim_customers : "customer_id"
    fct_orders ||--|| dim_date : "order_date_key"
    fct_order_items }o--|| fct_orders : "order_id"
    fct_order_items ||--|| dim_products : "product_id"
    fct_order_items ||--|| dim_sellers : "seller_id"
    fct_payments }o--|| fct_orders : "order_id"
    fct_reviews }o--|| fct_orders : "order_id"
    dim_customers ||--|| dim_geography : "zip_code_prefix"
    dim_sellers ||--|| dim_geography : "zip_code_prefix"
    dim_products ||--|| dim_category : "product_category_name"
```

**Table Notes:**
- **fct_orders:** Grain = One row per order | ~99,992 rows | Period: 2016-09 to 2018-08
- **fct_order_items:** Grain = One row per order line item | ~112,650 rows
- **dim_date:** Type = Calendar dimension | Coverage: 2016-2019 | Granularity: Daily

---

## Mart Tables (Pre-Aggregated Views)

```mermaid
erDiagram
    mart_executive_dashboard {
        DATE date_day PK "Daily metrics grain"
        INTEGER year
        INTEGER quarter
        VARCHAR month_name
        VARCHAR year_month
        VARCHAR day_name
        BOOLEAN is_weekend
        BOOLEAN is_holiday
        INTEGER total_orders
        INTEGER delivered_orders
        INTEGER canceled_orders
        INTEGER unique_customers
        INTEGER total_items
        DECIMAL avg_items_per_order
        DECIMAL total_revenue
        DECIMAL total_freight
        DECIMAL total_payments
        DECIMAL avg_order_value
        DECIMAL revenue_per_customer
        INTEGER total_reviews
        DECIMAL avg_review_score
        INTEGER positive_reviews
        INTEGER negative_reviews
        DECIMAL positive_review_rate
        DECIMAL avg_delivery_days
        INTEGER on_time_deliveries
        DECIMAL on_time_delivery_rate
        INTEGER credit_card_orders
        INTEGER boleto_orders
        INTEGER installment_orders
        DECIMAL installment_usage_rate
        DECIMAL delivery_rate
        DECIMAL cancellation_rate
        DECIMAL ma7_orders "7-day moving avg"
        DECIMAL ma7_revenue
        DECIMAL ma7_review_score
        DECIMAL ma30_orders "30-day moving avg"
        DECIMAL ma30_revenue
        DECIMAL ytd_revenue
        INTEGER ytd_orders
    }

    mart_customer_analytics {
        VARCHAR customer_id PK "One row per customer"
        VARCHAR customer_unique_id
        VARCHAR customer_state
        VARCHAR region
        VARCHAR city_size_tier
        INTEGER total_orders
        INTEGER delivered_orders
        INTEGER canceled_orders
        DATE first_order_date
        DATE last_order_date
        DECIMAL lifetime_value
        DECIMAL avg_order_value
        INTEGER total_items
        DECIMAL total_freight
        INTEGER recency_days "Days since last purchase"
        INTEGER frequency "Number of orders"
        DECIMAL monetary_value "Total spend"
        INTEGER recency_score "1-5 scale"
        INTEGER frequency_score "1-5 scale"
        INTEGER monetary_score "1-5 scale"
        INTEGER rfm_total_score
        VARCHAR rfm_segment "Champions, Loyal, At Risk, Lost, etc"
        VARCHAR lifecycle_stage "Active, Cooling, At Risk, Dormant"
        VARCHAR value_tier "VIP, High, Medium, Low"
        DECIMAL avg_days_between_orders
        INTEGER installment_orders
        DECIMAL avg_review_score
        INTEGER orders_with_comments
        INTEGER unique_products_purchased
        INTEGER unique_categories_purchased
        VARCHAR favorite_category
        DECIMAL avg_delivery_days
        INTEGER on_time_deliveries
        DECIMAL on_time_delivery_rate
    }

    mart_product_performance {
        VARCHAR product_id PK "One row per product"
        VARCHAR product_category_name_english
        VARCHAR category_display_name
        VARCHAR category_group
        VARCHAR category_revenue_tier
        VARCHAR category_size_tier
        INTEGER product_weight_g
        DECIMAL product_volume_cm3
        VARCHAR product_size_category
        VARCHAR product_weight_category
        VARCHAR product_quality_tier
        INTEGER total_orders
        INTEGER total_units_sold
        DECIMAL total_revenue
        DECIMAL avg_price
        DECIMAL min_price
        DECIMAL max_price
        DECIMAL total_freight
        DECIMAL avg_freight
        DECIMAL avg_freight_percentage
        DATE first_sale_date
        DATE last_sale_date
        INTEGER days_on_sale
        INTEGER delivered_orders
        INTEGER canceled_orders
        INTEGER on_time_deliveries
        DECIMAL delivery_rate
        DECIMAL cancellation_rate
        DECIMAL on_time_delivery_rate
        DECIMAL avg_delivery_days
        INTEGER total_reviews
        DECIMAL avg_review_score
        INTEGER positive_reviews
        INTEGER negative_reviews
        DECIMAL positive_review_rate
        INTEGER reviews_with_comments
        INTEGER unique_customer_locations
        INTEGER unique_customer_states
        VARCHAR top_customer_state
        INTEGER same_state_sales
        DECIMAL same_state_sales_rate
        INTEGER unique_sellers
        VARCHAR primary_seller_id
        VARCHAR sales_tier "Best Seller, Top, Good, Low"
        VARCHAR review_tier "Excellent, Very Good, Good, etc"
        DECIMAL performance_score
        DECIMAL revenue_per_unit
    }

    mart_seller_scorecard {
        VARCHAR seller_id PK "One row per seller"
        VARCHAR seller_state
        VARCHAR region
        VARCHAR city_size_tier
        VARCHAR seller_performance_tier
        VARCHAR seller_size_tier
        INTEGER total_orders
        INTEGER total_items_sold
        DECIMAL total_revenue
        DECIMAL avg_item_price
        DECIMAL total_freight
        DATE first_sale_date
        DATE last_sale_date
        INTEGER days_active
        INTEGER active_months
        INTEGER orders_last_30_days
        INTEGER orders_last_90_days
        INTEGER orders_last_180_days
        VARCHAR activity_status "Active 30d, Recent 90d, etc"
        INTEGER unique_products_sold
        INTEGER unique_categories
        VARCHAR top_category
        VARCHAR product_diversity_type "Specialist, Focused, Diverse, Generalist"
        DECIMAL avg_product_price
        DECIMAL min_product_price
        DECIMAL max_product_price
        DECIMAL price_stddev
        DECIMAL avg_freight_percentage
        INTEGER unique_customer_locations
        INTEGER unique_customer_states
        VARCHAR top_customer_state
        INTEGER same_state_orders
        DECIMAL same_state_order_rate
        VARCHAR geographic_focus "Local Focused, Regional, National"
        DECIMAL avg_review_score
        INTEGER positive_reviews
        INTEGER negative_reviews
        INTEGER total_reviews
        DECIMAL positive_review_rate
        DECIMAL avg_delivery_days
        INTEGER on_time_deliveries
        INTEGER total_delivered_orders
        DECIMAL on_time_delivery_rate
        DECIMAL revenue_per_item
        DECIMAL revenue_per_order
        DECIMAL revenue_per_day_active
        DECIMAL revenue_per_month
        DECIMAL revenue_percentile "0-100 scale"
        DECIMAL review_score_100 "0-100 scale"
        DECIMAL delivery_score_100 "0-100 scale"
        DECIMAL overall_performance_score
        VARCHAR seller_health "Excellent, Good, Average, Needs Improvement"
    }
```

**Mart Notes:**
- **mart_executive_dashboard:** Daily KPI dashboard | Refresh: Daily batch | Users: Executives, Leadership
- **mart_customer_analytics:** RFM & customer lifecycle | Refresh: Weekly batch | Users: Marketing, CRM teams
- **mart_product_performance:** Product & category analysis | Refresh: Daily batch | Users: Product managers, Buyers
- **mart_seller_scorecard:** Seller performance tracking | Refresh: Daily batch | Users: Marketplace ops, Seller relations

---

## Data Flow Architecture

```mermaid
flowchart TB
    subgraph source["Source Layer"]
        csv1[customers.csv]
        csv2[orders.csv]
        csv3[order_items.csv]
        csv4[payments.csv]
        csv5[reviews.csv]
        csv6[products.csv]
        csv7[sellers.csv]
        csv8[geolocation.csv]
        csv9[category_translation.csv]
    end

    subgraph staging["Staging Layer (DBT)"]
        stg1[stg_customers]
        stg2[stg_orders]
        stg3[stg_order_items]
        stg4[stg_payments]
        stg5[stg_reviews]
        stg6[stg_products]
        stg7[stg_sellers]
        stg8[stg_geolocation]
        stg9[stg_category_translation]
    end

    subgraph intermediate["Intermediate Layer (DBT)"]
        int1[int_orders_enriched]
        int2[int_order_items_enriched]
        int3[int_order_payments_aggregated]
    end

    subgraph dims["Core Layer - Dimensions"]
        dim1[dim_customers]
        dim2[dim_products]
        dim3[dim_sellers]
        dim4[dim_geography]
        dim5[dim_category]
        dim6[dim_date]
    end

    subgraph facts["Core Layer - Facts"]
        fct1[fct_orders]
        fct2[fct_order_items]
        fct3[fct_payments]
        fct4[fct_reviews]
    end

    subgraph marts["Marts Layer (DBT)"]
        mart1[mart_executive_dashboard]
        mart2[mart_customer_analytics]
        mart3[mart_product_performance]
        mart4[mart_seller_scorecard]
    end

    subgraph analytics["Analytics Layer"]
        nb1[Executive Dashboard]
        nb2[Customer RFM]
        nb3[Product Analysis]
        nb4[Seller Scorecard]
        nb5[+ 7 other notebooks]
    end

    %% Data flow
    csv1 & csv2 & csv3 & csv4 & csv5 & csv6 & csv7 & csv8 & csv9 -->|dbt source| staging
    staging -->|dbt transform| intermediate
    intermediate -->|dbt model| dims
    intermediate -->|dbt model| facts
    facts & dims -->|dbt aggregate & join| marts
    marts & facts -->|DuckDB query| analytics

    %% Styling
    classDef sourceClass fill:#E8F4F8,stroke:#2C3E50,stroke-width:2px
    classDef stagingClass fill:#D5E8F7,stroke:#2980B9,stroke-width:2px
    classDef intermediateClass fill:#C3DCF0,stroke:#3498DB,stroke-width:2px
    classDef coreClass fill:#A8D5E2,stroke:#16A085,stroke-width:2px
    classDef martClass fill:#FFF4E6,stroke:#E67E22,stroke-width:2px
    classDef analyticsClass fill:#E8F8F5,stroke:#27AE60,stroke-width:2px

    class csv1,csv2,csv3,csv4,csv5,csv6,csv7,csv8,csv9 sourceClass
    class stg1,stg2,stg3,stg4,stg5,stg6,stg7,stg8,stg9 stagingClass
    class int1,int2,int3 intermediateClass
    class dim1,dim2,dim3,dim4,dim5,dim6,fct1,fct2,fct3,fct4 coreClass
    class mart1,mart2,mart3,mart4 martClass
    class nb1,nb2,nb3,nb4,nb5 analyticsClass
```

**Data Flow Notes:**
- **Staging:** Data cleaning & standardization (type casting, null handling, column renaming)
- **Intermediate:** Business logic & enrichment (joins, derived fields, business flags)
- **Dimensions:** Master data & attributes (slowly changing, descriptive, hierarchies)
- **Facts:** Transaction & event data (high volume, immutable, foreign keys, measures)
- **Marts:** Business-specific aggregations (pre-calculated, denormalized, optimized)

---

## Complete Architecture View (with Marts)

```mermaid
graph TB
    subgraph facts["FACT TABLES"]
        direction LR
        F1[fct_orders<br/>~100K rows]
        F2[fct_order_items<br/>~113K rows]
        F3[fct_payments<br/>~104K rows]
        F4[fct_reviews<br/>~99K rows]
    end

    subgraph dims["DIMENSION TABLES"]
        direction TB
        D1[dim_customers<br/>99K]
        D2[dim_products<br/>33K]
        D3[dim_sellers<br/>3K]
        D4[dim_geography<br/>20K]
        D5[dim_category<br/>71]
        D6[dim_date<br/>1K]
    end

    subgraph marts["MART TABLES (Pre-Aggregated)"]
        direction TB
        M1[mart_executive_dashboard<br/>Daily metrics]
        M2[mart_customer_analytics<br/>RFM + Lifecycle]
        M3[mart_product_performance<br/>Product KPIs]
        M4[mart_seller_scorecard<br/>Seller KPIs]
    end

    %% Core star schema relationships
    F1 -->|customer_id| D1
    F1 -->|order_date_key| D6
    F2 -->|order_id| F1
    F2 -->|product_id| D2
    F2 -->|seller_id| D3
    F3 -->|order_id| F1
    F4 -->|order_id| F1
    D1 -->|zip_code_prefix| D4
    D3 -->|zip_code_prefix| D4
    D2 -->|category_name| D5

    %% Mart dependencies
    F1 & D1 & D6 -.->|aggregates| M1
    F1 & F2 & D1 & D4 -.->|aggregates + RFM| M2
    F2 & F4 & D2 & D5 -.->|aggregates + metrics| M3
    F2 & F4 & D3 & D4 -.->|aggregates + scores| M4

    classDef factStyle fill:#E8F4F8,stroke:#2C3E50,stroke-width:3px,color:#000
    classDef dimStyle fill:#FFF4E6,stroke:#E67E22,stroke-width:2px,color:#000
    classDef martStyle fill:#D5F5E3,stroke:#27AE60,stroke-width:3px,color:#000

    class F1,F2,F3,F4 factStyle
    class D1,D2,D3,D4,D5,D6 dimStyle
    class M1,M2,M3,M4 martStyle
```

**Legend:**
- **Blue boxes** = Fact tables (transaction data)
- **Orange boxes** = Dimension tables (master data)
- **Green boxes** = Mart tables (pre-aggregated for fast queries)
- **Solid lines** = Direct relationships (foreign keys)
- **Dashed lines** = Aggregation/derivation (marts built from facts + dims)

---

## Key Design Decisions

### 1. Star Schema Benefits
- **Simple queries** - Easy joins for analysts
- **Fast aggregations** - Pre-calculated dimensions
- **Business alignment** - Matches how business thinks
- **Scalable** - Can add new facts/dimensions easily

### 2. Grain Definitions
- **fct_orders** - One row per order (order-level metrics)
- **fct_order_items** - One row per order line item (product-level detail)
- **fct_payments** - One row per payment transaction (payment-level)
- **fct_reviews** - One row per review (review-level)

### 3. Dimension Hierarchies
- **Geography** - Zip → City → State → Region
- **Date** - Day → Week → Month → Quarter → Year
- **Category** - Category → Category Group
- **Product** - Product → Category → Category Group

### 4. Denormalization Strategy
- Fact tables include commonly used dimension attributes (e.g., product_category_name_english in fct_order_items)
- Reduces join complexity for common queries
- Trade-off: Storage space vs query performance

### 5. Pre-Aggregated Marts
- **Purpose:** Avoid expensive aggregations at query time
- **Trade-off:** Slightly stale data (daily/weekly batch) vs real-time
- **Benefit:** Consistent business logic, validated metrics

---

## Schema Statistics

| Layer | Tables | Approx Rows | Purpose |
|-------|--------|-------------|---------|
| **Staging** | 9 | 1.4M total | Clean raw data |
| **Intermediate** | 3 | ~300K | Enriched joins |
| **Dimensions** | 6 | ~135K | Master data |
| **Facts** | 4 | ~315K | Transactions |
| **Marts** | 4 | ~132K | Business views |

---

## Usage Recommendations

### For Ad-Hoc Analysis
✅ Use **Fact tables** + **Dimension tables**
- Full flexibility
- Can create custom aggregations
- Access to all detail

### For Standard Reporting
✅ Use **Mart tables**
- Pre-calculated metrics
- Faster performance
- Consistent definitions

### For Dashboards
✅ Use **Mart tables** primarily
- Optimized for visualization tools
- Stable schema
- Business-friendly column names

---

**Schema Version:** 1.0
**Last Updated:** 2025-11-11
**Maintained By:** DBT transformations
**Documentation:** See individual model files in `dbt/olist_dw_dbt/models/`
