{{
    config(
        materialized='table',
        tags=['dimension', 'core', 'category']
    )
}}

-- Category dimension with sales performance metrics
WITH category_translation AS (
    SELECT * FROM {{ ref('stg_category_translation') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

-- Get category-level metrics from products and order items
category_product_counts AS (
    SELECT
        product_category_name,
        COUNT(DISTINCT product_id) AS total_products
    FROM products
    WHERE product_category_name IS NOT NULL
    GROUP BY product_category_name
),

category_sales_metrics AS (
    SELECT
        p.product_category_name,
        COUNT(DISTINCT oi.order_id) AS total_orders,
        COUNT(*) AS total_items_sold,
        SUM(oi.price) AS total_revenue,
        AVG(oi.price) AS avg_item_price,
        MIN(oi.price) AS min_item_price,
        MAX(oi.price) AS max_item_price,
        SUM(oi.freight_value) AS total_freight,
        AVG(oi.freight_value) AS avg_freight
    FROM order_items oi
    INNER JOIN products p ON oi.product_id = p.product_id
    WHERE p.product_category_name IS NOT NULL
    GROUP BY p.product_category_name
),

category_dimension AS (
    SELECT
        -- Primary key
        ct.product_category_name,

        -- Category names
        ct.product_category_name_english,
        ct.category_display_name,

        -- Product counts
        COALESCE(cpc.total_products, 0) AS total_products,

        -- Sales metrics
        COALESCE(csm.total_orders, 0) AS total_orders,
        COALESCE(csm.total_items_sold, 0) AS total_items_sold,
        COALESCE(csm.total_revenue, 0) AS total_revenue,
        csm.avg_item_price,
        csm.min_item_price,
        csm.max_item_price,
        COALESCE(csm.total_freight, 0) AS total_freight,
        csm.avg_freight,

        -- Revenue per product
        CASE
            WHEN cpc.total_products > 0
            THEN COALESCE(csm.total_revenue, 0) / cpc.total_products
            ELSE 0
        END AS revenue_per_product,

        -- Category performance tier based on revenue
        CASE
            WHEN csm.total_revenue >= 100000 THEN 'Top Category'
            WHEN csm.total_revenue >= 50000 THEN 'High Revenue'
            WHEN csm.total_revenue >= 10000 THEN 'Medium Revenue'
            WHEN csm.total_revenue >= 1000 THEN 'Low Revenue'
            WHEN csm.total_revenue > 0 THEN 'Minimal Revenue'
            ELSE 'No Sales'
        END AS revenue_tier,

        -- Category size based on items sold
        CASE
            WHEN csm.total_items_sold >= 1000 THEN 'Large Category'
            WHEN csm.total_items_sold >= 500 THEN 'Medium Category'
            WHEN csm.total_items_sold >= 100 THEN 'Small Category'
            WHEN csm.total_items_sold >= 1 THEN 'Niche Category'
            ELSE 'No Sales'
        END AS category_size_tier,

        -- Price range category
        CASE
            WHEN csm.avg_item_price IS NULL THEN 'Unknown'
            WHEN csm.avg_item_price >= 200 THEN 'Premium'
            WHEN csm.avg_item_price >= 100 THEN 'High'
            WHEN csm.avg_item_price >= 50 THEN 'Medium'
            WHEN csm.avg_item_price >= 20 THEN 'Low'
            ELSE 'Budget'
        END AS price_tier,

        -- Freight category (shipping cost indicator)
        CASE
            WHEN csm.avg_freight IS NULL THEN 'Unknown'
            WHEN csm.avg_freight >= 30 THEN 'High Shipping'
            WHEN csm.avg_freight >= 15 THEN 'Medium Shipping'
            ELSE 'Low Shipping'
        END AS freight_tier,

        -- Category group (high-level categorization)
        CASE
            WHEN ct.product_category_name_english IN (
                'bed_bath_table', 'furniture_decor', 'housewares', 'home_construction',
                'furniture_bedroom', 'furniture_living_room', 'home_comfort_2',
                'garden_tools', 'home_confort', 'flowers', 'furniture_mattress_and_upholstery'
            ) THEN 'Home & Furniture'

            WHEN ct.product_category_name_english IN (
                'health_beauty', 'perfumery', 'diapers_and_hygiene'
            ) THEN 'Health & Beauty'

            WHEN ct.product_category_name_english IN (
                'sports_leisure', 'toys', 'baby', 'fashion_sport'
            ) THEN 'Sports & Leisure'

            WHEN ct.product_category_name_english IN (
                'computers_accessories', 'telephony', 'electronics', 'computers',
                'tablets_printing_image', 'fixed_telephony', 'consoles_games',
                'pc_gamer', 'signaling_and_security', 'security_and_services'
            ) THEN 'Electronics & Computers'

            WHEN ct.product_category_name_english IN (
                'watches_gifts', 'fashion_bags_accessories', 'fashion_shoes',
                'fashion_male_clothing', 'fashion_underwear_beach', 'fashion_childrens_clothes',
                'fashio_female_clothing'
            ) THEN 'Fashion & Accessories'

            WHEN ct.product_category_name_english IN (
                'auto', 'automotive'
            ) THEN 'Automotive'

            WHEN ct.product_category_name_english IN (
                'books_general_interest', 'books_technical', 'books_imported',
                'audio', 'music', 'cds_dvds_musicals', 'dvds_blu_ray'
            ) THEN 'Books & Media'

            WHEN ct.product_category_name_english IN (
                'cool_stuff', 'art', 'arts_and_craftmanship', 'christmas_supplies',
                'party_supplies', 'cine_photo'
            ) THEN 'Arts & Gifts'

            WHEN ct.product_category_name_english IN (
                'pet_shop', 'food', 'food_drink', 'drinks'
            ) THEN 'Food & Pets'

            WHEN ct.product_category_name_english IN (
                'office_furniture', 'stationery', 'industry_commerce_and_business',
                'construction_tools_safety', 'construction_tools_construction',
                'construction_tools_tools', 'construction_tools_lights',
                'la_cuisine', 'small_appliances', 'small_appliances_home_oven_and_coffee',
                'air_conditioning', 'kitchen_dining_laundry_garden_furniture'
            ) THEN 'Office & Tools'

            ELSE 'Other'
        END AS category_group,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM category_translation ct
    LEFT JOIN category_product_counts cpc ON ct.product_category_name = cpc.product_category_name
    LEFT JOIN category_sales_metrics csm ON ct.product_category_name = csm.product_category_name
)

SELECT * FROM category_dimension
