# Troubleshooting: dashboard net sales doesn't match source

Reproduced end to end by `tests/run.py`; outputs in `TEST_RESULTS.md` §2–4.

## Symptom

An executive reports that dashboard net sales for the half is **$1,062,285.04**, but
finance's extract from the order system says **$1,045,629.04**. Difference: **$16,656.00 (1.6%)**.

## Investigation (`sql/scenario/02_investigate.sql`)

| Step | Check | Finding |
|---|---|---|
| 1 | Dashboard total vs an independent total from the fact tables, same filters | Dashboard is $16,656 high. Source facts are right; the reporting layer adds money. |
| 2 | Difference by week | Spread across many weeks, not one load date → not a single bad batch. |
| 3 | Difference by customer | All 8 customers affected → not a customer mapping issue. |
| 4 | Difference and order-line counts by SKU | One SKU, **ST120-BLK-M**: 40 lines in the view vs 20 in the fact. Every line is counted twice. |
| 5 | Duplicate keys on every table the view joins | `DIM_PRODUCT` has 2 rows for ST120-BLK-M. |
| 6 | Inspect the rows | Same SKU, season SS26 and FW26: a product-master reload inserted a re-seasoned row instead of updating. |

Steps 4 and 5 differ ($16,694.40 vs $16,656.00) because step 4 compares sales before
returns; refunds on that SKU were doubled too.

## Root cause

The view joins facts to `DIM_PRODUCT` on SKU. A duplicate SKU in the dimension turns that
join into one-to-many, doubling every sales and return row for the SKU. The same duplicate
also inflated latest inventory by 625 units.

## Fix (`sql/scenario/03_fix_defect.sql`)

Rebuild `DIM_PRODUCT` from the source master with one row per SKU. After the fix every test
passes and dashboard net sales = $1,045,629.04, matching the independent total exactly.

## Prevention

- `T02_PK_DIM_PRODUCT` runs after every load; a FAIL blocks the dashboard cube refresh.
- `T08` (order lines through the view = lines in the fact) catches any future fan-out
  regardless of which dimension causes it.
- Note: `T12` (weekly summary = detail view) **passed** during the defect, because both
  read the same broken view. Tie-outs must compare against an independent source.

## Before / after

| Test | Before fix | After fix |
|---|---|---|
| T02 PK DIM_PRODUCT | FAIL (1 dup) | PASS |
| T08 no line multiplication | FAIL (1,973 vs 1,953) | PASS |
| T09 net sales recon | FAIL (+$16,656.00) | PASS |
| T10 gross margin recon | FAIL (+$8,375.00) | PASS |
| T11 filtered recon (C002, Mar) | FAIL (+$220.80) | PASS |
| T13 latest inventory | FAIL (+625 units) | PASS |
