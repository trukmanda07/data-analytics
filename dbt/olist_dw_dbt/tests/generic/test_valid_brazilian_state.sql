{% test valid_brazilian_state(model, column_name) %}

-- Test that state codes are valid Brazilian states
-- Valid states: AC, AL, AP, AM, BA, CE, DF, ES, GO, MA, MT, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, RO, RR, SC, SP, SE, TO

SELECT
    {{ column_name }} AS invalid_state,
    COUNT(*) AS occurrences
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
    AND {{ column_name }} NOT IN (
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    )
GROUP BY {{ column_name }}

{% endtest %}
