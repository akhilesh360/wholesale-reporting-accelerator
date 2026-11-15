-- FIX: keep one row per SKU. Business rule agreed for the demo: the source product master
-- (STG_PRODUCT) is authoritative, so rebuild the dimension from it and de-duplicate defensively.
-- Prevention: T02_PK_DIM_PRODUCT runs after every load and blocks the dashboard refresh on FAIL.
CREATE OR REPLACE TABLE DIM_PRODUCT AS
SELECT SKU, STYLE_ID, STYLE_NAME, COLOR, SIZE, CATEGORY, SEASON,
       CAST(UNIT_COST AS DECIMAL(12,2)) AS UNIT_COST,
       CAST(WHOLESALE_PRICE AS DECIMAL(12,2)) AS WHOLESALE_PRICE
FROM STG_PRODUCT
QUALIFY ROW_NUMBER() OVER (PARTITION BY SKU ORDER BY SEASON DESC) = 1;
