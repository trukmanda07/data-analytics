Welcome to your new dbt project!

### Using the starter project

Try running the following commands:
- dbt run
- dbt test


### Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

===========================================
   dbt Test Suite Summary for Olist Data Warehouse
   ===========================================

   Created test files:
   -------------------

   1. SCHEMA TESTS (in YAML files)
      ├── dbt/olist_dw_dbt/models/core/dimensions/schema.yml
      │   ├── dim_category: 18 tests
      │   ├── dim_date: 13 tests
      │   ├── dim_geography: 14 tests
      │   ├── dim_products: 11 tests
      │   └── dim_sellers: 16 tests
      │
      └── dbt/olist_dw_dbt/models/core/facts/schema.yml
          ├── fct_order_items: 17 tests
          ├── fct_payments: 14 tests
          └── fct_reviews: 17 tests

   2. GENERIC TESTS (reusable test macros)
      └── dbt/olist_dw_dbt/tests/generic/
          ├── test_valid_brazilian_state.sql
          ├── test_valid_zip_code_prefix.sql
          ├── test_date_range_valid.sql
          └── test_percentage_range.sql

   3. SINGULAR TESTS (business logic validation)
      └── dbt/olist_dw_dbt/tests/singular/
          ├── test_order_items_total_matches_payments.sql
          ├── test_delivery_dates_logical_order.sql
          ├── test_reviews_only_for_valid_orders.sql
          ├── test_product_category_consistency.sql
          ├── test_seller_metrics_match_facts.sql
          ├── test_category_metrics_match_facts.sql
          ├── test_review_dates_after_purchase.sql
          ├── test_no_negative_values.sql
          ├── test_review_score_sentiment_alignment.sql
          ├── test_date_keys_exist_in_dim_date.sql
          └── test_geography_entity_counts_positive.sql

   4. DOCUMENTATION
      └── dbt/olist_dw_dbt/tests/README.md

   Total Test Coverage: 120+ tests
   -------------------

   Test Categories:
   • Primary key validation (uniqueness, not null)
   • Foreign key relationships (referential integrity)
   • Data ranges and boundaries
   • Business logic validation
   • Metric aggregation consistency
   • Date and timestamp logic
   • Financial calculations
   • Category and tier classifications
   • Brazilian-specific validations (states, zip codes)

   Next Steps:
   -----------
   1. Run all tests: cd dbt/olist_dw_dbt && dbt test
   2. Review test results
   3. Fix any failing tests
   4. Integrate tests into CI/CD pipeline