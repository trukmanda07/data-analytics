{% test percentage_range(model, column_name, min_value=0, max_value=100) %}

-- Test that percentage values are within valid range (default 0-100)

SELECT
    {{ column_name }} AS invalid_percentage,
    COUNT(*) AS occurrences
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
    AND (
        {{ column_name }} < {{ min_value }}
        OR {{ column_name }} > {{ max_value }}
    )
GROUP BY {{ column_name }}

{% endtest %}
