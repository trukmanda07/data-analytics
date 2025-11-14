-- Test that review sentiment aligns with review scores
-- positive: 4-5, neutral: 3, negative: 1-2

SELECT
    review_id,
    order_id,
    review_score,
    review_sentiment,
    CASE
        WHEN review_score >= 4 THEN 'positive'
        WHEN review_score = 3 THEN 'neutral'
        ELSE 'negative'
    END AS expected_sentiment
FROM {{ ref('fct_reviews') }}
WHERE review_sentiment != CASE
        WHEN review_score >= 4 THEN 'positive'
        WHEN review_score = 3 THEN 'neutral'
        ELSE 'negative'
    END
