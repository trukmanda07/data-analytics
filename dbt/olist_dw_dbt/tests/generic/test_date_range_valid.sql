{% test date_range_valid(model, column_name, min_date='2016-01-01', max_date='2019-12-31') %}

-- Test that dates fall within expected range for the Olist dataset
-- Default range: 2016-01-01 to 2019-12-31

SELECT
    {{ column_name }} AS invalid_date,
    COUNT(*) AS occurrences
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
    AND (
        CAST({{ column_name }} AS DATE) < CAST('{{ min_date }}' AS DATE)
        OR CAST({{ column_name }} AS DATE) > CAST('{{ max_date }}' AS DATE)
    )
GROUP BY {{ column_name }}

{% endtest %}
