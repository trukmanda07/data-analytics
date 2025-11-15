# Dimensional Model Specification

**Document Version:** 1.0
**Last Updated:** 2025-11-08
**Related:** data_warehouse_architecture.md

---

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [Dimension Tables](#dimension-tables)
3. [Fact Tables](#fact-tables)
4. [Relationships and Grain](#relationships-and-grain)
5. [Sample SQL DDL](#sample-sql-ddl)
6. [Data Dictionary](#data-dictionary)
7. [Business Logic Rules](#business-logic-rules)

---

## Schema Overview

### Star Schema Diagram

```
                                    ┌─────────────────┐
                                    │   dim_date      │
                                    │─────────────────│
                                    │ date_key (PK)   │
                                    │ full_date       │
                                    │ year, month     │
                ┌───────────────────┤ quarter, week   │
                │                   │ day_of_week     │
                │                   │ is_weekend      │
                │                   └─────────────────┘
                │
                │
┌───────────────┴────┐                                      ┌─────────────────┐
│  dim_customer      │                                      │  dim_geography  │
│────────────────────│                                      │─────────────────│
│ customer_key (PK)  │                                      │ geography_key   │
│ customer_id (NK)   │                                      │ zip_code_prefix │
│ customer_city      │──────────────────────────────────────┤ city, state     │
│ customer_state     │                                      │ lat, lng        │
│ first_order_date   │                                      │ region          │
│ total_orders       │                                      └─────────────────┘
│ effective_from     │
│ is_current         │
└────────┬───────────┘
         │
         │
         │           ┌──────────────────────────────────────┐
         │           │      fact_order_items                │
         │           │──────────────────────────────────────│
         └───────────┤ order_item_id (PK)                   │
                     │ order_id (DD)                        │
                     │ customer_key (FK) ───────────────────┘
                     │ product_key (FK)  ────────┐
                     │ seller_key (FK)   ─────┐  │
                     │ order_date_key (FK) ───┼──┼──────────┐
                     │ delivery_date_key (FK)─┼──┼──┐       │
                     │ category_key (FK) ─────┼──┼──┼───┐   │
                     │                        │  │  │   │   │
                     │ price                  │  │  │   │   │
                     │ freight_value          │  │  │   │   │
                     └──────────┬─────────────┘  │  │   │   │
                                │                │  │   │   │
                                │                │  │   │   │
┌─────────────────┐             │                │  │   │   │
│  dim_product    │             │                │  │   │   │
│─────────────────│             │                │  │   │   │
│ product_key(PK) │─────────────┘                │  │   │   │
│ product_id (NK) │                              │  │   │   │
│ category_key(FK)│──────────────────────────────┼──┼───┘   │
│ product_weight  │                              │  │       │
│ dimensions      │                              │  │       │
│ effective_from  │                              │  │       │
│ is_current      │                              │  │       │
└─────────────────┘                              │  │       │
                                                 │  │       │
┌─────────────────┐                              │  │       │
│  dim_seller     │                              │  │       │
│─────────────────│                              │  │       │
│ seller_key (PK) │──────────────────────────────┘  │       │
│ seller_id (NK)  │                                 │       │
│ seller_city     │                                 │       │
│ seller_state    │                                 │       │
│ seller_tier     │                                 │       │
│ effective_from  │                                 │       │
│ is_current      │                                 │       │
└─────────────────┘                                 │       │
                                                    │       │
┌─────────────────┐                                 │       │
│  dim_category   │                                 │       │
│─────────────────│                                 │       │
│ category_key(PK)│─────────────────────────────────┘       │
│ category_name_en│                                         │
│ category_name_pt│                                         │
│ category_group  │                                         │
└─────────────────┘                                         │
                                                            │
                                                            │
                          ┌─────────────────┐               │
                          │  fact_orders    │               │
                          │─────────────────│               │
                          │ order_id (PK)   │               │
                          │ customer_key(FK)│───────────────┘
                          │ order_date_key  │
                          │ delivery_date   │
                          │ total_amount    │
                          │ total_items     │
                          │ delivery_days   │
                          └─────────────────┘
                                   │
                                   │
                          ┌────────┴────────┐
                          │                 │
                ┌─────────▼──────┐  ┌───────▼──────────┐
                │ fact_payments  │  │  fact_reviews    │
                │────────────────│  │──────────────────│
                │ payment_id(PK) │  │ review_id (PK)   │
                │ order_id (FK)  │  │ order_id (FK)    │
                │ payment_type   │  │ review_score     │
                │ installments   │  │ review_date_key  │
                │ payment_value  │  │ comment_length   │
                └────────────────┘  └──────────────────┘
```

**Legend:**
- (PK) = Primary Key
- (FK) = Foreign Key
- (NK) = Natural Key
- (DD) = Degenerate Dimension

---

## Dimension Tables

### 1. dim_customer (SCD Type 2)

**Purpose:** Customer master data with historical tracking of changes

**Grain:** One row per customer per effective period

**Type:** Slowly Changing Dimension Type 2

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `customer_key` | BIGINT | NOT NULL | Surrogate key (auto-increment) | Generated |
| `customer_id` | VARCHAR(50) | NOT NULL | Natural key from source | olist_customers_dataset |
| `customer_unique_id` | VARCHAR(50) | NULL | Unique customer identifier | olist_customers_dataset |
| `customer_zip_code_prefix` | VARCHAR(10) | NOT NULL | Zip code (5 digits) | olist_customers_dataset |
| `customer_city` | VARCHAR(100) | NOT NULL | City name | olist_customers_dataset |
| `customer_state` | VARCHAR(2) | NOT NULL | State abbreviation (SP, RJ, etc.) | olist_customers_dataset |
| `customer_region` | VARCHAR(20) | NOT NULL | Geographic region | Derived from state |
| `first_order_date` | DATE | NULL | Date of first order | Derived from orders |
| `last_order_date` | DATE | NULL | Date of most recent order | Derived from orders |
| `total_orders` | INTEGER | NULL | Lifetime order count | Derived from orders |
| `total_spent` | DECIMAL(12,2) | NULL | Lifetime revenue | Derived from orders |
| `avg_order_value` | DECIMAL(10,2) | NULL | Average order value | Derived from orders |
| `customer_segment` | VARCHAR(20) | NULL | NEW/REGULAR/VIP/CHURNED | Business logic |
| `is_repeat_customer` | BOOLEAN | NULL | Has 2+ orders | Derived |
| `effective_from` | TIMESTAMP | NOT NULL | SCD effective start date | ETL timestamp |
| `effective_to` | TIMESTAMP | NULL | SCD effective end date (NULL = current) | ETL timestamp |
| `is_current` | BOOLEAN | NOT NULL | Current record flag | TRUE for current row |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | ETL timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Record update timestamp | ETL timestamp |

#### Business Logic: Customer Segmentation

```sql
CASE
    WHEN total_orders = 0 OR total_orders IS NULL THEN 'NEW'
    WHEN total_orders = 1 THEN 'ONE_TIME'
    WHEN total_orders BETWEEN 2 AND 5 THEN 'REGULAR'
    WHEN total_orders > 5 AND total_spent > 1000 THEN 'VIP'
    WHEN total_orders > 5 THEN 'LOYAL'
    WHEN DATEDIFF(day, last_order_date, CURRENT_DATE) > 180 THEN 'CHURNED'
    ELSE 'ACTIVE'
END as customer_segment
```

#### SCD Type 2 Example

| customer_key | customer_id | customer_city | customer_state | effective_from | effective_to | is_current |
|--------------|-------------|---------------|----------------|----------------|--------------|------------|
| 1 | CUST_001 | São Paulo | SP | 2016-01-01 | 2017-06-30 | FALSE |
| 2 | CUST_001 | Rio de Janeiro | RJ | 2017-07-01 | NULL | TRUE |

**Interpretation:** Customer CUST_001 moved from São Paulo to Rio de Janeiro on July 1, 2017.

---

### 2. dim_product (SCD Type 2)

**Purpose:** Product catalog with attributes and historical changes

**Grain:** One row per product per effective period

**Type:** Slowly Changing Dimension Type 2

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `product_key` | BIGINT | NOT NULL | Surrogate key | Generated |
| `product_id` | VARCHAR(50) | NOT NULL | Natural key | olist_products_dataset |
| `category_key` | INTEGER | NOT NULL | Foreign key to dim_category | Lookup |
| `product_category_name` | VARCHAR(100) | NULL | Category in Portuguese | olist_products_dataset |
| `product_category_name_english` | VARCHAR(100) | NULL | Category in English | Translation table |
| `product_name_length` | INTEGER | NULL | Length of product title | olist_products_dataset |
| `product_description_length` | INTEGER | NULL | Length of description | olist_products_dataset |
| `product_photos_qty` | INTEGER | NULL | Number of product photos | olist_products_dataset |
| `product_weight_g` | DECIMAL(10,2) | NULL | Weight in grams | olist_products_dataset |
| `product_length_cm` | DECIMAL(8,2) | NULL | Length in cm | olist_products_dataset |
| `product_height_cm` | DECIMAL(8,2) | NULL | Height in cm | olist_products_dataset |
| `product_width_cm` | DECIMAL(8,2) | NULL | Width in cm | olist_products_dataset |
| `product_volume_cm3` | DECIMAL(12,2) | NULL | Calculated volume | Derived (L*W*H) |
| `product_weight_tier` | VARCHAR(20) | NULL | LIGHT/MEDIUM/HEAVY | Business logic |
| `product_size_tier` | VARCHAR(20) | NULL | SMALL/MEDIUM/LARGE | Business logic |
| `first_sale_date` | DATE | NULL | First order date | Derived from orders |
| `last_sale_date` | DATE | NULL | Last order date | Derived from orders |
| `total_sales_count` | INTEGER | NULL | Total units sold | Derived from orders |
| `total_revenue` | DECIMAL(12,2) | NULL | Total revenue | Derived from orders |
| `avg_price` | DECIMAL(10,2) | NULL | Average selling price | Derived from orders |
| `avg_review_score` | DECIMAL(3,2) | NULL | Average rating (1-5) | Derived from reviews |
| `effective_from` | TIMESTAMP | NOT NULL | SCD effective start | ETL timestamp |
| `effective_to` | TIMESTAMP | NULL | SCD effective end | ETL timestamp |
| `is_current` | BOOLEAN | NOT NULL | Current record flag | TRUE for current |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp | ETL timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Update timestamp | ETL timestamp |

#### Business Logic: Product Tiers

```sql
-- Weight tier
CASE
    WHEN product_weight_g < 500 THEN 'LIGHT'
    WHEN product_weight_g < 2000 THEN 'MEDIUM'
    WHEN product_weight_g < 10000 THEN 'HEAVY'
    ELSE 'VERY_HEAVY'
END as product_weight_tier

-- Size tier (based on volume)
CASE
    WHEN product_volume_cm3 < 1000 THEN 'SMALL'
    WHEN product_volume_cm3 < 10000 THEN 'MEDIUM'
    WHEN product_volume_cm3 < 100000 THEN 'LARGE'
    ELSE 'VERY_LARGE'
END as product_size_tier
```

---

### 3. dim_seller (SCD Type 2)

**Purpose:** Seller marketplace participants with performance metrics

**Grain:** One row per seller per effective period

**Type:** Slowly Changing Dimension Type 2

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `seller_key` | BIGINT | NOT NULL | Surrogate key | Generated |
| `seller_id` | VARCHAR(50) | NOT NULL | Natural key | olist_sellers_dataset |
| `seller_zip_code_prefix` | VARCHAR(10) | NOT NULL | Zip code | olist_sellers_dataset |
| `seller_city` | VARCHAR(100) | NOT NULL | City name | olist_sellers_dataset |
| `seller_state` | VARCHAR(2) | NOT NULL | State abbreviation | olist_sellers_dataset |
| `seller_region` | VARCHAR(20) | NOT NULL | Geographic region | Derived from state |
| `seller_join_date` | DATE | NULL | First sale date | Derived from orders |
| `seller_last_sale_date` | DATE | NULL | Most recent sale | Derived from orders |
| `seller_tenure_days` | INTEGER | NULL | Days since first sale | Calculated |
| `total_orders` | INTEGER | NULL | Lifetime order count | Derived from orders |
| `total_revenue` | DECIMAL(12,2) | NULL | Lifetime revenue | Derived from orders |
| `total_items_sold` | INTEGER | NULL | Total line items | Derived from orders |
| `avg_order_value` | DECIMAL(10,2) | NULL | Average order value | Derived from orders |
| `avg_review_score` | DECIMAL(3,2) | NULL | Average rating (1-5) | Derived from reviews |
| `on_time_delivery_rate` | DECIMAL(5,2) | NULL | % orders delivered on time | Derived from orders |
| `cancellation_rate` | DECIMAL(5,2) | NULL | % orders cancelled | Derived from orders |
| `seller_tier` | VARCHAR(20) | NULL | BRONZE/SILVER/GOLD/PLATINUM | Business logic |
| `is_active_seller` | BOOLEAN | NULL | Sold in last 90 days | Business logic |
| `unique_products_count` | INTEGER | NULL | Number of unique products | Derived |
| `primary_category` | VARCHAR(100) | NULL | Most sold category | Derived |
| `effective_from` | TIMESTAMP | NOT NULL | SCD effective start | ETL timestamp |
| `effective_to` | TIMESTAMP | NULL | SCD effective end | ETL timestamp |
| `is_current` | BOOLEAN | NOT NULL | Current record flag | TRUE for current |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp | ETL timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Update timestamp | ETL timestamp |

#### Business Logic: Seller Tier

```sql
CASE
    WHEN total_revenue > 50000 AND avg_review_score >= 4.5 THEN 'PLATINUM'
    WHEN total_revenue > 20000 AND avg_review_score >= 4.0 THEN 'GOLD'
    WHEN total_revenue > 5000 AND avg_review_score >= 3.5 THEN 'SILVER'
    ELSE 'BRONZE'
END as seller_tier
```

---

### 4. dim_date (Type 1)

**Purpose:** Calendar dimension for time-based analysis

**Grain:** One row per day

**Type:** Type 1 (static reference data)

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `date_key` | INTEGER | NOT NULL | Primary key (YYYYMMDD format) | Generated |
| `full_date` | DATE | NOT NULL | Actual date | Generated |
| `year` | INTEGER | NOT NULL | Year (2016, 2017, etc.) | Generated |
| `quarter` | INTEGER | NOT NULL | Quarter (1-4) | Generated |
| `month` | INTEGER | NOT NULL | Month (1-12) | Generated |
| `month_name` | VARCHAR(20) | NOT NULL | Month name (January, etc.) | Generated |
| `month_abbr` | VARCHAR(3) | NOT NULL | Month abbreviation (Jan, etc.) | Generated |
| `week_of_year` | INTEGER | NOT NULL | ISO week number (1-53) | Generated |
| `day_of_month` | INTEGER | NOT NULL | Day of month (1-31) | Generated |
| `day_of_week` | INTEGER | NOT NULL | Day of week (1=Monday, 7=Sunday) | Generated |
| `day_name` | VARCHAR(20) | NOT NULL | Day name (Monday, etc.) | Generated |
| `day_abbr` | VARCHAR(3) | NOT NULL | Day abbreviation (Mon, etc.) | Generated |
| `is_weekend` | BOOLEAN | NOT NULL | TRUE if Saturday/Sunday | Generated |
| `is_holiday` | BOOLEAN | NOT NULL | Brazilian public holiday | External source |
| `holiday_name` | VARCHAR(100) | NULL | Holiday name if applicable | External source |
| `fiscal_year` | INTEGER | NOT NULL | Fiscal year (same as calendar) | Generated |
| `fiscal_quarter` | INTEGER | NOT NULL | Fiscal quarter | Generated |
| `year_month` | VARCHAR(7) | NOT NULL | YYYY-MM format | Generated |
| `year_quarter` | VARCHAR(7) | NOT NULL | YYYY-Q format | Generated |
| `is_current_day` | BOOLEAN | NOT NULL | TRUE if today | Derived |
| `is_current_month` | BOOLEAN | NOT NULL | TRUE if current month | Derived |
| `is_current_year` | BOOLEAN | NOT NULL | TRUE if current year | Derived |

#### Pre-Population Script

```sql
-- Generate date dimension for 2016-2025 (10 years)
WITH RECURSIVE date_series AS (
    SELECT DATE '2016-01-01' as dt
    UNION ALL
    SELECT dt + INTERVAL '1 day'
    FROM date_series
    WHERE dt < DATE '2025-12-31'
)
INSERT INTO dim_date (
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    week_of_year,
    day_of_month,
    day_of_week,
    day_name,
    is_weekend
)
SELECT
    CAST(STRFTIME(dt, '%Y%m%d') AS INTEGER) as date_key,
    dt as full_date,
    EXTRACT(YEAR FROM dt) as year,
    EXTRACT(QUARTER FROM dt) as quarter,
    EXTRACT(MONTH FROM dt) as month,
    STRFTIME(dt, '%B') as month_name,
    EXTRACT(WEEK FROM dt) as week_of_year,
    EXTRACT(DAY FROM dt) as day_of_month,
    EXTRACT(ISODOW FROM dt) as day_of_week,
    STRFTIME(dt, '%A') as day_name,
    EXTRACT(ISODOW FROM dt) IN (6, 7) as is_weekend
FROM date_series;
```

---

### 5. dim_geography (Type 1)

**Purpose:** Geographic reference data for Brazilian locations

**Grain:** One row per unique zip code prefix

**Type:** Type 1 (slowly changing attributes updated in place)

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `geography_key` | INTEGER | NOT NULL | Surrogate key | Generated |
| `zip_code_prefix` | VARCHAR(10) | NOT NULL | 5-digit zip code | olist_geolocation_dataset |
| `city` | VARCHAR(100) | NOT NULL | City name | olist_geolocation_dataset |
| `state` | VARCHAR(2) | NOT NULL | State abbreviation | olist_geolocation_dataset |
| `state_name` | VARCHAR(50) | NOT NULL | Full state name | Lookup table |
| `region` | VARCHAR(20) | NOT NULL | Geographic region | Business logic |
| `latitude` | DECIMAL(10,8) | NULL | Latitude coordinate | olist_geolocation_dataset |
| `longitude` | DECIMAL(11,8) | NULL | Longitude coordinate | olist_geolocation_dataset |
| `is_metropolitan` | BOOLEAN | NULL | Major metro area flag | Business logic |
| `population_tier` | VARCHAR(20) | NULL | SMALL/MEDIUM/LARGE city | External source |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp | ETL timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Update timestamp | ETL timestamp |

#### Business Logic: Brazilian Regions

```sql
CASE state
    WHEN 'AC' THEN 'Norte'      -- Acre
    WHEN 'AL' THEN 'Nordeste'   -- Alagoas
    WHEN 'AP' THEN 'Norte'      -- Amapá
    WHEN 'AM' THEN 'Norte'      -- Amazonas
    WHEN 'BA' THEN 'Nordeste'   -- Bahia
    WHEN 'CE' THEN 'Nordeste'   -- Ceará
    WHEN 'DF' THEN 'Centro-Oeste' -- Distrito Federal
    WHEN 'ES' THEN 'Sudeste'    -- Espírito Santo
    WHEN 'GO' THEN 'Centro-Oeste' -- Goiás
    WHEN 'MA' THEN 'Nordeste'   -- Maranhão
    WHEN 'MT' THEN 'Centro-Oeste' -- Mato Grosso
    WHEN 'MS' THEN 'Centro-Oeste' -- Mato Grosso do Sul
    WHEN 'MG' THEN 'Sudeste'    -- Minas Gerais
    WHEN 'PA' THEN 'Norte'      -- Pará
    WHEN 'PB' THEN 'Nordeste'   -- Paraíba
    WHEN 'PR' THEN 'Sul'        -- Paraná
    WHEN 'PE' THEN 'Nordeste'   -- Pernambuco
    WHEN 'PI' THEN 'Nordeste'   -- Piauí
    WHEN 'RJ' THEN 'Sudeste'    -- Rio de Janeiro
    WHEN 'RN' THEN 'Nordeste'   -- Rio Grande do Norte
    WHEN 'RS' THEN 'Sul'        -- Rio Grande do Sul
    WHEN 'RO' THEN 'Norte'      -- Rondônia
    WHEN 'RR' THEN 'Norte'      -- Roraima
    WHEN 'SC' THEN 'Sul'        -- Santa Catarina
    WHEN 'SP' THEN 'Sudeste'    -- São Paulo
    WHEN 'SE' THEN 'Nordeste'   -- Sergipe
    WHEN 'TO' THEN 'Norte'      -- Tocantins
END as region

-- Metropolitan areas (major cities)
city IN (
    'sao paulo', 'rio de janeiro', 'brasilia', 'salvador', 'fortaleza',
    'belo horizonte', 'manaus', 'curitiba', 'recife', 'porto alegre'
) as is_metropolitan
```

---

### 6. dim_category (Type 1)

**Purpose:** Product category taxonomy with translations

**Grain:** One row per product category

**Type:** Type 1 (static reference data)

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `category_key` | INTEGER | NOT NULL | Surrogate key | Generated |
| `category_name_portuguese` | VARCHAR(100) | NOT NULL | Category in Portuguese | product_category_translation |
| `category_name_english` | VARCHAR(100) | NOT NULL | Category in English | product_category_translation |
| `category_group` | VARCHAR(50) | NULL | High-level grouping | Business logic |
| `is_high_value` | BOOLEAN | NULL | High AOV category | Business logic |
| `is_high_volume` | BOOLEAN | NULL | High order volume | Business logic |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp | ETL timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Update timestamp | ETL timestamp |

#### Business Logic: Category Groups

```sql
CASE category_name_english
    WHEN 'computers_accessories', 'telephony', 'electronics', 'consoles_games'
        THEN 'Electronics'
    WHEN 'furniture_decor', 'bed_bath_table', 'garden_tools', 'home_appliances'
        THEN 'Home & Living'
    WHEN 'health_beauty', 'perfumery', 'fashion_bags_accessories', 'fashion_shoes'
        THEN 'Fashion & Beauty'
    WHEN 'sports_leisure', 'toys', 'baby', 'diapers_and_hygiene'
        THEN 'Lifestyle'
    WHEN 'books_general_interest', 'music', 'cds_dvds_musicals', 'art'
        THEN 'Media & Entertainment'
    WHEN 'auto', 'construction_tools_construction', 'industry_commerce_and_business'
        THEN 'Industrial & Automotive'
    ELSE 'Other'
END as category_group
```

---

## Fact Tables

### 1. fact_order_items (Primary Fact Table)

**Purpose:** Granular transaction details at line-item level

**Grain:** One row per order line item (order_id + order_item_id)

**Type:** Transactional fact table

**Update Pattern:** Insert-only (append-only)

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `order_item_key` | BIGINT | NOT NULL | Surrogate key | Generated |
| `order_id` | VARCHAR(50) | NOT NULL | Order identifier (degenerate dimension) | olist_order_items_dataset |
| `order_item_id` | INTEGER | NOT NULL | Line item sequence | olist_order_items_dataset |
| `customer_key` | BIGINT | NOT NULL | FK to dim_customer | Lookup from order |
| `product_key` | BIGINT | NOT NULL | FK to dim_product | Lookup |
| `seller_key` | BIGINT | NOT NULL | FK to dim_seller | Lookup |
| `category_key` | INTEGER | NOT NULL | FK to dim_category | Lookup from product |
| `order_date_key` | INTEGER | NOT NULL | FK to dim_date (order date) | Lookup |
| `shipping_limit_date_key` | INTEGER | NULL | FK to dim_date (shipping deadline) | Lookup |
| `delivery_date_key` | INTEGER | NULL | FK to dim_date (actual delivery) | Lookup |
| `estimated_delivery_date_key` | INTEGER | NULL | FK to dim_date (estimated) | Lookup |
| `geography_key` | INTEGER | NULL | FK to dim_geography (customer location) | Lookup |
| `seller_geography_key` | INTEGER | NULL | FK to dim_geography (seller location) | Lookup |
| **MEASURES** | | | | |
| `price` | DECIMAL(10,2) | NOT NULL | Item price (before discounts) | olist_order_items_dataset |
| `freight_value` | DECIMAL(10,2) | NOT NULL | Shipping cost for item | olist_order_items_dataset |
| `quantity` | INTEGER | NOT NULL | Item quantity (always 1 in dataset) | Default to 1 |
| `total_amount` | DECIMAL(10,2) | NOT NULL | price + freight_value | Calculated |
| `days_to_ship` | INTEGER | NULL | Days from order to shipment | Calculated |
| `days_to_deliver` | INTEGER | NULL | Days from order to delivery | Calculated |
| `delivery_vs_estimate` | INTEGER | NULL | Actual vs estimated (negative = early) | Calculated |
| `is_late_delivery` | BOOLEAN | NULL | TRUE if delivered after estimate | Calculated |
| `is_same_state` | BOOLEAN | NULL | Customer and seller in same state | Calculated |
| `distance_km` | DECIMAL(8,2) | NULL | Haversine distance seller-customer | Calculated |
| **METADATA** | | | | |
| `created_at` | TIMESTAMP | NOT NULL | ETL load timestamp | ETL timestamp |

#### Key Metrics Calculation

```sql
-- Days to deliver
DATEDIFF(day, order_purchase_timestamp, order_delivered_customer_date) as days_to_deliver

-- Late delivery
CASE
    WHEN order_delivered_customer_date > order_estimated_delivery_date THEN TRUE
    ELSE FALSE
END as is_late_delivery

-- Delivery variance
DATEDIFF(day, order_estimated_delivery_date, order_delivered_customer_date) as delivery_vs_estimate

-- Distance calculation (Haversine formula)
2 * 3961 * ASIN(SQRT(
    POWER(SIN((customer_lat - seller_lat) * PI() / 180 / 2), 2) +
    COS(seller_lat * PI() / 180) * COS(customer_lat * PI() / 180) *
    POWER(SIN((customer_lng - seller_lng) * PI() / 180 / 2), 2)
)) * 1.60934 as distance_km  -- Convert miles to km
```

#### Sample Queries

**Revenue by Category (Monthly):**
```sql
SELECT
    d.year_month,
    c.category_name_english,
    COUNT(DISTINCT f.order_id) as order_count,
    SUM(f.total_amount) as total_revenue,
    AVG(f.price) as avg_item_price
FROM fact_order_items f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_category c ON f.category_key = c.category_key
WHERE d.year = 2017
GROUP BY d.year_month, c.category_name_english
ORDER BY total_revenue DESC;
```

**Delivery Performance by State:**
```sql
SELECT
    g.state,
    COUNT(*) as total_orders,
    AVG(f.days_to_deliver) as avg_delivery_days,
    SUM(CASE WHEN f.is_late_delivery THEN 1 ELSE 0 END) / COUNT(*) * 100 as late_delivery_pct
FROM fact_order_items f
JOIN dim_geography g ON f.geography_key = g.geography_key
WHERE f.delivery_date_key IS NOT NULL
GROUP BY g.state
ORDER BY avg_delivery_days DESC;
```

---

### 2. fact_orders (Order-Level Aggregation)

**Purpose:** One row per order with aggregated metrics

**Grain:** One row per order (order_id)

**Type:** Aggregated fact table (snapshot)

**Update Pattern:** Full refresh or incremental merge

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `order_key` | BIGINT | NOT NULL | Surrogate key | Generated |
| `order_id` | VARCHAR(50) | NOT NULL | Order identifier (PK) | olist_orders_dataset |
| `customer_key` | BIGINT | NOT NULL | FK to dim_customer | Lookup |
| `order_date_key` | INTEGER | NOT NULL | FK to dim_date (purchase date) | Lookup |
| `approval_date_key` | INTEGER | NULL | FK to dim_date (payment approval) | Lookup |
| `shipping_date_key` | INTEGER | NULL | FK to dim_date (shipped date) | Lookup |
| `delivery_date_key` | INTEGER | NULL | FK to dim_date (delivery date) | Lookup |
| `estimated_delivery_date_key` | INTEGER | NULL | FK to dim_date (estimated) | Lookup |
| `geography_key` | INTEGER | NULL | FK to dim_geography | Lookup |
| **DEGENERATE DIMENSIONS** | | | | |
| `order_status` | VARCHAR(20) | NOT NULL | delivered, shipped, canceled, etc. | olist_orders_dataset |
| **MEASURES** | | | | |
| `total_items` | INTEGER | NOT NULL | Number of line items | COUNT from items |
| `total_amount` | DECIMAL(12,2) | NOT NULL | Sum of item prices | SUM from items |
| `total_freight` | DECIMAL(12,2) | NOT NULL | Sum of freight values | SUM from items |
| `total_payment` | DECIMAL(12,2) | NULL | Total payment amount | SUM from payments |
| `num_sellers` | INTEGER | NULL | Unique sellers in order | COUNT DISTINCT |
| `num_products` | INTEGER | NULL | Unique products in order | COUNT DISTINCT |
| `avg_item_price` | DECIMAL(10,2) | NULL | Average item price | AVG from items |
| `days_to_approve` | INTEGER | NULL | Order to approval | Calculated |
| `days_to_ship` | INTEGER | NULL | Approval to shipment | Calculated |
| `days_to_deliver` | INTEGER | NULL | Shipment to delivery | Calculated |
| `total_delivery_time` | INTEGER | NULL | Order to delivery | Calculated |
| `delivery_vs_estimate` | INTEGER | NULL | Actual vs estimated | Calculated |
| `is_late_delivery` | BOOLEAN | NULL | Delivered late flag | Calculated |
| `has_review` | BOOLEAN | NULL | Review exists flag | Lookup |
| `review_score` | DECIMAL(3,2) | NULL | Average review score | From reviews |
| `is_multivendor` | BOOLEAN | NULL | Multiple sellers | num_sellers > 1 |
| **METADATA** | | | | |
| `created_at` | TIMESTAMP | NOT NULL | ETL load timestamp | ETL timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | ETL update timestamp | ETL timestamp |

---

### 3. fact_payments

**Purpose:** Payment transaction details

**Grain:** One row per payment transaction (order can have multiple payments)

**Type:** Transactional fact table

**Update Pattern:** Insert-only (append-only)

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `payment_key` | BIGINT | NOT NULL | Surrogate key | Generated |
| `order_id` | VARCHAR(50) | NOT NULL | FK to fact_orders | olist_order_payments_dataset |
| `payment_sequential` | INTEGER | NOT NULL | Payment sequence number | olist_order_payments_dataset |
| `payment_date_key` | INTEGER | NULL | FK to dim_date (payment date) | Lookup from order |
| **DEGENERATE DIMENSIONS** | | | | |
| `payment_type` | VARCHAR(30) | NOT NULL | credit_card, boleto, voucher, debit_card | olist_order_payments_dataset |
| **MEASURES** | | | | |
| `payment_installments` | INTEGER | NOT NULL | Number of installments (1-24) | olist_order_payments_dataset |
| `payment_value` | DECIMAL(10,2) | NOT NULL | Payment amount | olist_order_payments_dataset |
| `installment_amount` | DECIMAL(10,2) | NULL | Value per installment | Calculated |
| `is_installment` | BOOLEAN | NOT NULL | installments > 1 | Calculated |
| **METADATA** | | | | |
| `created_at` | TIMESTAMP | NOT NULL | ETL load timestamp | ETL timestamp |

#### Payment Type Analysis

```sql
-- Payment method distribution
SELECT
    payment_type,
    COUNT(DISTINCT order_id) as order_count,
    SUM(payment_value) as total_value,
    AVG(payment_installments) as avg_installments
FROM fact_payments
GROUP BY payment_type
ORDER BY total_value DESC;
```

---

### 4. fact_reviews

**Purpose:** Customer review and feedback data

**Grain:** One row per review (one review per order)

**Type:** Transactional fact table

**Update Pattern:** Insert-only (append-only)

#### Column Specifications

| Column Name | Data Type | Nullable | Description | Source |
|-------------|-----------|----------|-------------|--------|
| `review_key` | BIGINT | NOT NULL | Surrogate key | Generated |
| `review_id` | VARCHAR(50) | NOT NULL | Natural key | olist_order_reviews_dataset |
| `order_id` | VARCHAR(50) | NOT NULL | FK to fact_orders | olist_order_reviews_dataset |
| `customer_key` | BIGINT | NOT NULL | FK to dim_customer | Lookup from order |
| `review_creation_date_key` | INTEGER | NULL | FK to dim_date (review created) | Lookup |
| `review_answer_date_key` | INTEGER | NULL | FK to dim_date (review answered) | Lookup |
| **MEASURES** | | | | |
| `review_score` | INTEGER | NOT NULL | Rating (1-5 stars) | olist_order_reviews_dataset |
| `review_comment_title_length` | INTEGER | NULL | Length of title | Calculated |
| `review_comment_message_length` | INTEGER | NULL | Length of message | Calculated |
| `has_comment_title` | BOOLEAN | NOT NULL | Title exists | Calculated |
| `has_comment_message` | BOOLEAN | NOT NULL | Message exists | Calculated |
| `days_to_review` | INTEGER | NULL | Order to review days | Calculated |
| `review_sentiment` | VARCHAR(20) | NULL | POSITIVE/NEUTRAL/NEGATIVE | Business logic |
| **TEXT FIELDS** | | | | |
| `review_comment_title` | TEXT | NULL | Review title | olist_order_reviews_dataset |
| `review_comment_message` | TEXT | NULL | Review message | olist_order_reviews_dataset |
| **METADATA** | | | | |
| `created_at` | TIMESTAMP | NOT NULL | ETL load timestamp | ETL timestamp |

#### Business Logic: Review Sentiment

```sql
CASE
    WHEN review_score >= 4 THEN 'POSITIVE'
    WHEN review_score = 3 THEN 'NEUTRAL'
    WHEN review_score <= 2 THEN 'NEGATIVE'
END as review_sentiment
```

---

## Relationships and Grain

### Fact-to-Dimension Relationships

**fact_order_items relationships:**
```
fact_order_items (1) → (0..1) dim_customer
fact_order_items (N) → (1) dim_product
fact_order_items (N) → (1) dim_seller
fact_order_items (N) → (1) dim_category (through product)
fact_order_items (N) → (1) dim_date (order_date)
fact_order_items (N) → (0..1) dim_date (delivery_date)
fact_order_items (N) → (0..1) dim_geography (customer location)
fact_order_items (N) → (0..1) dim_geography (seller location)
```

**fact_orders relationships:**
```
fact_orders (1) → (1) dim_customer
fact_orders (N) → (1) dim_date (order_date)
fact_orders (N) → (0..1) dim_date (multiple date roles)
fact_orders (N) → (0..1) dim_geography
```

**fact_payments relationships:**
```
fact_payments (N) → (1) fact_orders
fact_payments (N) → (0..1) dim_date (payment_date)
```

**fact_reviews relationships:**
```
fact_reviews (1) → (1) fact_orders
fact_reviews (1) → (1) dim_customer
fact_reviews (N) → (0..1) dim_date (review_date)
```

### Grain Definitions Summary

| Fact Table | Grain | Primary Use Case |
|------------|-------|------------------|
| `fact_order_items` | One row per order line item | Detailed product/seller analytics |
| `fact_orders` | One row per order | Order-level metrics, customer behavior |
| `fact_payments` | One row per payment transaction | Payment method analysis |
| `fact_reviews` | One row per review | Customer satisfaction analysis |

### Conforming Dimensions

Dimensions shared across multiple fact tables:
- `dim_customer` - Used by all fact tables (through order)
- `dim_date` - Used by all fact tables (multiple roles)
- `dim_geography` - Used by orders and items
- `dim_product` - Used by order items only
- `dim_seller` - Used by order items only
- `dim_category` - Used by order items (through product)

---

## Sample SQL DDL

### DuckDB Implementation

```sql
-- ============================================
-- DIMENSION TABLES
-- ============================================

-- dim_date
CREATE TABLE core.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    month_abbr VARCHAR(3) NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    day_abbr VARCHAR(3) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN NOT NULL DEFAULT FALSE,
    holiday_name VARCHAR(100),
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    year_quarter VARCHAR(7) NOT NULL
);

-- dim_customer (SCD Type 2)
CREATE TABLE core.dim_customer (
    customer_key BIGINT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix VARCHAR(10) NOT NULL,
    customer_city VARCHAR(100) NOT NULL,
    customer_state VARCHAR(2) NOT NULL,
    customer_region VARCHAR(20) NOT NULL,
    first_order_date DATE,
    last_order_date DATE,
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0,
    avg_order_value DECIMAL(10,2),
    customer_segment VARCHAR(20),
    is_repeat_customer BOOLEAN,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- dim_product (SCD Type 2)
CREATE TABLE core.dim_product (
    product_key BIGINT PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    category_key INTEGER NOT NULL,
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100),
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g DECIMAL(10,2),
    product_length_cm DECIMAL(8,2),
    product_height_cm DECIMAL(8,2),
    product_width_cm DECIMAL(8,2),
    product_volume_cm3 DECIMAL(12,2),
    product_weight_tier VARCHAR(20),
    product_size_tier VARCHAR(20),
    first_sale_date DATE,
    last_sale_date DATE,
    total_sales_count INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    avg_price DECIMAL(10,2),
    avg_review_score DECIMAL(3,2),
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- dim_seller (SCD Type 2)
CREATE TABLE core.dim_seller (
    seller_key BIGINT PRIMARY KEY,
    seller_id VARCHAR(50) NOT NULL,
    seller_zip_code_prefix VARCHAR(10) NOT NULL,
    seller_city VARCHAR(100) NOT NULL,
    seller_state VARCHAR(2) NOT NULL,
    seller_region VARCHAR(20) NOT NULL,
    seller_join_date DATE,
    seller_last_sale_date DATE,
    seller_tenure_days INTEGER,
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    total_items_sold INTEGER DEFAULT 0,
    avg_order_value DECIMAL(10,2),
    avg_review_score DECIMAL(3,2),
    on_time_delivery_rate DECIMAL(5,2),
    cancellation_rate DECIMAL(5,2),
    seller_tier VARCHAR(20),
    is_active_seller BOOLEAN,
    unique_products_count INTEGER,
    primary_category VARCHAR(100),
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- dim_geography
CREATE TABLE core.dim_geography (
    geography_key INTEGER PRIMARY KEY,
    zip_code_prefix VARCHAR(10) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    state_name VARCHAR(50) NOT NULL,
    region VARCHAR(20) NOT NULL,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    is_metropolitan BOOLEAN,
    population_tier VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- dim_category
CREATE TABLE core.dim_category (
    category_key INTEGER PRIMARY KEY,
    category_name_portuguese VARCHAR(100) NOT NULL,
    category_name_english VARCHAR(100) NOT NULL,
    category_group VARCHAR(50),
    is_high_value BOOLEAN,
    is_high_volume BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FACT TABLES
-- ============================================

-- fact_order_items (Primary Fact)
CREATE TABLE core.fact_order_items (
    order_item_key BIGINT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    order_item_id INTEGER NOT NULL,
    customer_key BIGINT NOT NULL,
    product_key BIGINT NOT NULL,
    seller_key BIGINT NOT NULL,
    category_key INTEGER NOT NULL,
    order_date_key INTEGER NOT NULL,
    shipping_limit_date_key INTEGER,
    delivery_date_key INTEGER,
    estimated_delivery_date_key INTEGER,
    geography_key INTEGER,
    seller_geography_key INTEGER,

    -- Measures
    price DECIMAL(10,2) NOT NULL,
    freight_value DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    total_amount DECIMAL(10,2) NOT NULL,
    days_to_ship INTEGER,
    days_to_deliver INTEGER,
    delivery_vs_estimate INTEGER,
    is_late_delivery BOOLEAN,
    is_same_state BOOLEAN,
    distance_km DECIMAL(8,2),

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (seller_key) REFERENCES dim_seller(seller_key),
    FOREIGN KEY (category_key) REFERENCES dim_category(category_key),
    FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (delivery_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (geography_key) REFERENCES dim_geography(geography_key),
    FOREIGN KEY (seller_geography_key) REFERENCES dim_geography(geography_key)
);

-- fact_orders
CREATE TABLE core.fact_orders (
    order_key BIGINT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    customer_key BIGINT NOT NULL,
    order_date_key INTEGER NOT NULL,
    approval_date_key INTEGER,
    shipping_date_key INTEGER,
    delivery_date_key INTEGER,
    estimated_delivery_date_key INTEGER,
    geography_key INTEGER,

    -- Degenerate dimension
    order_status VARCHAR(20) NOT NULL,

    -- Measures
    total_items INTEGER NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    total_freight DECIMAL(12,2) NOT NULL,
    total_payment DECIMAL(12,2),
    num_sellers INTEGER,
    num_products INTEGER,
    avg_item_price DECIMAL(10,2),
    days_to_approve INTEGER,
    days_to_ship INTEGER,
    days_to_deliver INTEGER,
    total_delivery_time INTEGER,
    delivery_vs_estimate INTEGER,
    is_late_delivery BOOLEAN,
    has_review BOOLEAN,
    review_score DECIMAL(3,2),
    is_multivendor BOOLEAN,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (geography_key) REFERENCES dim_geography(geography_key)
);

-- fact_payments
CREATE TABLE core.fact_payments (
    payment_key BIGINT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_date_key INTEGER,

    -- Degenerate dimension
    payment_type VARCHAR(30) NOT NULL,

    -- Measures
    payment_installments INTEGER NOT NULL,
    payment_value DECIMAL(10,2) NOT NULL,
    installment_amount DECIMAL(10,2),
    is_installment BOOLEAN NOT NULL,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    FOREIGN KEY (payment_date_key) REFERENCES dim_date(date_key)
);

-- fact_reviews
CREATE TABLE core.fact_reviews (
    review_key BIGINT PRIMARY KEY,
    review_id VARCHAR(50) NOT NULL UNIQUE,
    order_id VARCHAR(50) NOT NULL,
    customer_key BIGINT NOT NULL,
    review_creation_date_key INTEGER,
    review_answer_date_key INTEGER,

    -- Measures
    review_score INTEGER NOT NULL,
    review_comment_title_length INTEGER,
    review_comment_message_length INTEGER,
    has_comment_title BOOLEAN NOT NULL,
    has_comment_message BOOLEAN NOT NULL,
    days_to_review INTEGER,
    review_sentiment VARCHAR(20),

    -- Text fields
    review_comment_title TEXT,
    review_comment_message TEXT,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (review_creation_date_key) REFERENCES dim_date(date_key)
);

-- ============================================
-- INDEXES
-- ============================================

-- dim_customer indexes
CREATE INDEX idx_dim_customer_id ON dim_customer(customer_id);
CREATE INDEX idx_dim_customer_current ON dim_customer(is_current) WHERE is_current = TRUE;
CREATE INDEX idx_dim_customer_state ON dim_customer(customer_state);

-- dim_product indexes
CREATE INDEX idx_dim_product_id ON dim_product(product_id);
CREATE INDEX idx_dim_product_category ON dim_product(category_key);
CREATE INDEX idx_dim_product_current ON dim_product(is_current) WHERE is_current = TRUE;

-- dim_seller indexes
CREATE INDEX idx_dim_seller_id ON dim_seller(seller_id);
CREATE INDEX idx_dim_seller_current ON dim_seller(is_current) WHERE is_current = TRUE;

-- fact_order_items indexes
CREATE INDEX idx_fact_items_order ON fact_order_items(order_id);
CREATE INDEX idx_fact_items_customer ON fact_order_items(customer_key);
CREATE INDEX idx_fact_items_product ON fact_order_items(product_key);
CREATE INDEX idx_fact_items_seller ON fact_order_items(seller_key);
CREATE INDEX idx_fact_items_date ON fact_order_items(order_date_key);
CREATE INDEX idx_fact_items_category ON fact_order_items(category_key);

-- fact_orders indexes
CREATE INDEX idx_fact_orders_customer ON fact_orders(customer_key);
CREATE INDEX idx_fact_orders_date ON fact_orders(order_date_key);
CREATE INDEX idx_fact_orders_status ON fact_orders(order_status);

-- fact_payments indexes
CREATE INDEX idx_fact_payments_order ON fact_payments(order_id);
CREATE INDEX idx_fact_payments_type ON fact_payments(payment_type);

-- fact_reviews indexes
CREATE INDEX idx_fact_reviews_order ON fact_reviews(order_id);
CREATE INDEX idx_fact_reviews_customer ON fact_reviews(customer_key);
CREATE INDEX idx_fact_reviews_score ON fact_reviews(review_score);
```

---

## Data Dictionary

### Complete Attribute Reference

Download full data dictionary: `data_dictionary.xlsx` (to be generated)

### Key Naming Conventions

**Surrogate Keys:** `<table_name>_key`
- Example: `customer_key`, `product_key`

**Natural Keys:** `<entity>_id`
- Example: `customer_id`, `order_id`

**Foreign Keys:** Match dimension key name
- Example: FK to `customer_key` named `customer_key`

**Dates:** `<event>_date` or `<event>_date_key`
- Example: `order_date_key`, `first_order_date`

**Flags:** `is_<condition>` or `has_<attribute>`
- Example: `is_current`, `has_review`

**Counts:** `num_<items>` or `<item>_count`
- Example: `num_sellers`, `total_orders`

**Amounts:** `<type>_amount` or `<type>_value`
- Example: `total_amount`, `payment_value`

---

## Business Logic Rules

### Customer Segmentation

```sql
-- RFM-inspired segmentation
CASE
    WHEN DATEDIFF(day, last_order_date, CURRENT_DATE) > 180 THEN 'CHURNED'
    WHEN total_orders >= 10 AND total_spent > 2000 THEN 'VIP'
    WHEN total_orders >= 5 THEN 'LOYAL'
    WHEN total_orders >= 2 THEN 'REGULAR'
    WHEN total_orders = 1 THEN 'ONE_TIME'
    ELSE 'NEW'
END
```

### Seller Tier Classification

```sql
CASE
    WHEN total_revenue > 50000 AND avg_review_score >= 4.5 AND on_time_delivery_rate >= 95 THEN 'PLATINUM'
    WHEN total_revenue > 20000 AND avg_review_score >= 4.0 AND on_time_delivery_rate >= 90 THEN 'GOLD'
    WHEN total_revenue > 5000 AND avg_review_score >= 3.5 AND on_time_delivery_rate >= 85 THEN 'SILVER'
    ELSE 'BRONZE'
END
```

### Late Delivery Definition

```sql
-- Order is late if delivered after estimated date
order_delivered_customer_date > order_estimated_delivery_date
```

### Active Seller Definition

```sql
-- Seller is active if they had a sale in the last 90 days
seller_last_sale_date >= CURRENT_DATE - INTERVAL '90 days'
```

### Product Lifecycle Stages

```sql
CASE
    WHEN first_sale_date IS NULL THEN 'NEVER_SOLD'
    WHEN DATEDIFF(day, first_sale_date, CURRENT_DATE) <= 30 THEN 'NEW'
    WHEN DATEDIFF(day, last_sale_date, CURRENT_DATE) > 180 THEN 'DISCONTINUED'
    WHEN total_sales_count >= 100 THEN 'BESTSELLER'
    WHEN total_sales_count < 10 THEN 'LOW_PERFORMER'
    ELSE 'ACTIVE'
END
```

---

## Related Documents

- **data_warehouse_architecture.md** - Overall architecture and technology choices
- **etl_pipeline.md** - ETL/ELT process design
- **implementation_plan.md** - Phased implementation roadmap

---

**End of Dimensional Model Specification**
