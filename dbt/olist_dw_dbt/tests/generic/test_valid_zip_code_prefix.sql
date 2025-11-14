{% test valid_zip_code_prefix(model, column_name) %}

-- Test that zip code prefix is exactly 5 digits
-- Brazilian zip code prefixes should be 5-digit integers between 01000 and 99999

SELECT
    {{ column_name }} AS invalid_zip,
    COUNT(*) AS occurrences
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
    AND (
        {{ column_name }} < 1000
        OR {{ column_name }} > 99999
        OR CAST({{ column_name }} AS VARCHAR) NOT LIKE '_____'
    )
GROUP BY {{ column_name }}

{% endtest %}
