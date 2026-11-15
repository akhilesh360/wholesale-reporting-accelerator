# Test results

Engine: **DuckDB (local)** · generated 2026-11-15 15:48 by `tests/run.py`. Do not edit by hand.

## 1. Baseline (clean load)

| TEST_NAME | STATUS | DETAIL |
|---|---|---|
| T01_PK_FACT_ORDER_LINE | PASS | 0 duplicate keys |
| T02_PK_DIM_PRODUCT | PASS | 0 duplicate SKUs |
| T03_PK_DIM_CUSTOMER | PASS | 0 duplicate customers |
| T04_PK_INVENTORY_SNAPSHOT | PASS | 0 duplicate date/SKU rows |
| T05_REQUIRED_FIELDS_ORDER_LINE | PASS | 0 rows with nulls |
| T06_ORPHAN_ORDER_LINES | PASS | 0 orphan rows |
| T07_ORPHAN_RETURN_LINES | PASS | 0 returns without an order line |
| T08_VIEW_DOES_NOT_MULTIPLY_ORDER_LINES | PASS | view=1953 fact=1953 |
| T09_RECON_NET_SALES_TOTAL | PASS | view=1045629.04 independent=1045629.04 |
| T10_RECON_GROSS_MARGIN_TOTAL | PASS | view=543868.64 independent=543868.64 |
| T11_RECON_FILTERED_C002_2026_03 | PASS | view=25507.92 independent=25507.92 |
| T12_WEEKLY_SUMMARY_TIES_TO_DETAIL | PASS | weekly=1045629.04 detail=1045629.04 |
| T13_INVENTORY_LATEST_SNAPSHOT_ONLY | PASS | latest flag units=121957 max-date units=121957 distinct dates flagged=1 |
| T14_RETURNS_NOT_EXCEED_SOLD | PASS | 0 over-returned lines |
| T15_KNOWN_ROW_METRIC_CALC | PASS | line SO000004-03: net sales 207.36, net cost 90.90, net units 9, gross margin 116.46, GM% 0.5616 |

## 2. After injecting the defect (`sql/scenario/01_inject_defect.sql`)

| TEST_NAME | STATUS | DETAIL |
|---|---|---|
| T01_PK_FACT_ORDER_LINE | PASS | 0 duplicate keys |
| T02_PK_DIM_PRODUCT | FAIL | 1 duplicate SKUs |
| T03_PK_DIM_CUSTOMER | PASS | 0 duplicate customers |
| T04_PK_INVENTORY_SNAPSHOT | PASS | 0 duplicate date/SKU rows |
| T05_REQUIRED_FIELDS_ORDER_LINE | PASS | 0 rows with nulls |
| T06_ORPHAN_ORDER_LINES | PASS | 0 orphan rows |
| T07_ORPHAN_RETURN_LINES | PASS | 0 returns without an order line |
| T08_VIEW_DOES_NOT_MULTIPLY_ORDER_LINES | FAIL | view=1973 fact=1953 |
| T09_RECON_NET_SALES_TOTAL | FAIL | view=1062285.04 independent=1045629.04 |
| T10_RECON_GROSS_MARGIN_TOTAL | FAIL | view=552243.64 independent=543868.64 |
| T11_RECON_FILTERED_C002_2026_03 | FAIL | view=25728.72 independent=25507.92 |
| T12_WEEKLY_SUMMARY_TIES_TO_DETAIL | PASS | weekly=1062285.04 detail=1062285.04 |
| T13_INVENTORY_LATEST_SNAPSHOT_ONLY | FAIL | latest flag units=122582 max-date units=121957 distinct dates flagged=1 |
| T14_RETURNS_NOT_EXCEED_SOLD | PASS | 0 over-returned lines |

## 3. Investigation output (`sql/scenario/02_investigate.sql`)

| STEP | DASHBOARD_NET_SALES | INDEPENDENT_NET_SALES | DIFF |
|---|---|---|---|
| STEP1_TOTAL | 1,062,285.04 | 1,045,629.04 | 16,656.00 |

| STEP | WEEK_START | VIEW_SALES | FACT_SALES | DIFF |
|---|---|---|---|---|
| STEP2_BY_WEEK | 2026-01-12 | 42,514.08 | 39,557.28 | 2,956.80 |
| STEP2_BY_WEEK | 2026-05-11 | 67,212.72 | 65,023.92 | 2,188.80 |
| STEP2_BY_WEEK | 2026-05-25 | 48,787.20 | 46,944.00 | 1,843.20 |
| STEP2_BY_WEEK | 2026-01-19 | 31,502.40 | 29,812.80 | 1,689.60 |
| STEP2_BY_WEEK | 2026-03-09 | 50,937.12 | 49,372.32 | 1,564.80 |

| STEP | CUSTOMER_ID | DIFF |
|---|---|---|
| STEP3_BY_CUSTOMER | C008 | 5,913.60 |
| STEP3_BY_CUSTOMER | C005 | 2,956.80 |
| STEP3_BY_CUSTOMER | C004 | 2,304.00 |
| STEP3_BY_CUSTOMER | C001 | 2,073.60 |
| STEP3_BY_CUSTOMER | C003 | 2,073.60 |
| STEP3_BY_CUSTOMER | C007 | 921.60 |
| STEP3_BY_CUSTOMER | C006 | 230.40 |
| STEP3_BY_CUSTOMER | C002 | 220.80 |

| STEP | SKU | VIEW_LINE_COUNT | FACT_LINE_COUNT | DIFF |
|---|---|---|---|---|
| STEP4_BY_SKU | ST120-BLK-M | 40 | 20 | 16,694.40 |

| STEP | TBL | KEY_VALUE | ROWS_PER_KEY |
|---|---|---|---|
| STEP5_DUP_KEYS | DIM_PRODUCT | ST120-BLK-M | 2 |

| STEP | SKU | STYLE_NAME | SEASON |
|---|---|---|---|
| STEP6_DUP_ROWS | ST120-BLK-M | Baggy Denim | SS26 |
| STEP6_DUP_ROWS | ST120-BLK-M | Baggy Denim | FW26 |

## 4. After the fix (`sql/scenario/03_fix_defect.sql`)

| TEST_NAME | STATUS | DETAIL |
|---|---|---|
| T01_PK_FACT_ORDER_LINE | PASS | 0 duplicate keys |
| T02_PK_DIM_PRODUCT | PASS | 0 duplicate SKUs |
| T03_PK_DIM_CUSTOMER | PASS | 0 duplicate customers |
| T04_PK_INVENTORY_SNAPSHOT | PASS | 0 duplicate date/SKU rows |
| T05_REQUIRED_FIELDS_ORDER_LINE | PASS | 0 rows with nulls |
| T06_ORPHAN_ORDER_LINES | PASS | 0 orphan rows |
| T07_ORPHAN_RETURN_LINES | PASS | 0 returns without an order line |
| T08_VIEW_DOES_NOT_MULTIPLY_ORDER_LINES | PASS | view=1953 fact=1953 |
| T09_RECON_NET_SALES_TOTAL | PASS | view=1045629.04 independent=1045629.04 |
| T10_RECON_GROSS_MARGIN_TOTAL | PASS | view=543868.64 independent=543868.64 |
| T11_RECON_FILTERED_C002_2026_03 | PASS | view=25507.92 independent=25507.92 |
| T12_WEEKLY_SUMMARY_TIES_TO_DETAIL | PASS | weekly=1045629.04 detail=1045629.04 |
| T13_INVENTORY_LATEST_SNAPSHOT_ONLY | PASS | latest flag units=121957 max-date units=121957 distinct dates flagged=1 |
| T14_RETURNS_NOT_EXCEED_SOLD | PASS | 0 over-returned lines |
