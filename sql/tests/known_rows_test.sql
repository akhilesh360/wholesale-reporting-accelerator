-- Metric calculation test against hand-computed values for a known order line and its return.
-- Expected values are computed in tests/run_local.py from the CSV with plain Python arithmetic.
SELECT ORDER_LINE_ID, o.GROSS_SALES, o.DISCOUNT_AMOUNT, o.EXTENDED_COST, o.UNITS,
       r.RETURNED_UNITS, r.REFUND_AMOUNT, r.RETURNED_COST
FROM FACT_ORDER_LINE o JOIN FACT_RETURN_LINE r USING (ORDER_LINE_ID)
WHERE ORDER_LINE_ID = (SELECT MIN(ORDER_LINE_ID) FROM FACT_RETURN_LINE);
