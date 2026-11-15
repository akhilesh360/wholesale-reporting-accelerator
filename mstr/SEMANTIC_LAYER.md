# MicroStrategy semantic layer and dashboard spec

> **Status (2026-11-15): partly built and validated.** A Strategy Cloud trial dashboard,
> "Wholesale Reporting Dashboard", connects **live** to `VW_WHOLESALE_SALES` through the
> read-only service login `STRATEGY_REPORTING`. Built: attributes, base metrics, Gross Margin,
> Gross Margin %, Category and Customer filters, a customer grid and a weekly trend line.
> Still spec only: hierarchies, prior-week metric, date-range prompt, inventory dataset,
> security filter. See the validation table at the bottom.

## Connection

- Datasource "Wholesale Demo Snowflake": database `WHOLESALE_DEMO`, schema `DW`, warehouse
  `WHS_DEMO_WH`, role `WHS_REPORTING` (views only), user `STRATEGY_REPORTING`
  (`sql/snowflake/04_strategy_service_user.sql`). Its token is stored in Strategy, not Git.
  Data access mode: **Connect Live**.
- Tables to import into the project schema: `VW_WHOLESALE_SALES`, `VW_INVENTORY_POSITION`,
  plus `DIM_DATE`, `DIM_PRODUCT`, `DIM_CUSTOMER` if you prefer normalized lookups (needs a
  `SELECT` grant on those three tables; otherwise use the descriptive columns in the views).

## Attributes

| Attribute | ID form | Description form | Source column(s) |
|---|---|---|---|
| Year | YEAR | | YEAR |
| Month | YEAR_MONTH | | YEAR_MONTH |
| Week | WEEK_START | "Wk of " + WEEK_START | WEEK_START |
| Date | ACTIVITY_DATE / SNAPSHOT_DATE | | heterogeneous mapping |
| Customer | CUSTOMER_ID | CUSTOMER_NAME | |
| Channel | CHANNEL | | |
| Region | REGION | | |
| Category | CATEGORY | | |
| Season | SEASON | | |
| Style | STYLE_ID | STYLE_NAME | |
| Color | COLOR | | |
| Size | SIZE | | sort: XS, S, M, L, XL |
| SKU | SKU | | |

**Hierarchies:** Category → Style → SKU (Color, Size as SKU properties);
Year → Month → Week → Date.

## Facts

| Fact | Expression | Table |
|---|---|---|
| Gross Sales | GROSS_SALES | VW_WHOLESALE_SALES |
| Discount | DISCOUNT_AMOUNT | VW_WHOLESALE_SALES |
| Refund | REFUND_AMOUNT | VW_WHOLESALE_SALES |
| Units Sold | UNITS_SOLD | VW_WHOLESALE_SALES |
| Units Returned | UNITS_RETURNED | VW_WHOLESALE_SALES |
| Sold Cost | SOLD_COST | VW_WHOLESALE_SALES |
| Returned Cost | RETURNED_COST | VW_WHOLESALE_SALES |
| Order Line Count | ORDER_LINE_COUNT | VW_WHOLESALE_SALES |
| Units On Hand | UNITS_ON_HAND | VW_INVENTORY_POSITION |
| Inventory Cost | INVENTORY_COST | VW_INVENTORY_POSITION |

## Metrics

| Metric | Formula | Notes |
|---|---|---|
| Net Sales | `Sum(Gross Sales) - Sum(Discount) - Sum(Refund)` | |
| Net Units | `Sum(Units Sold) - Sum(Units Returned)` | |
| Net Cost | `Sum(Sold Cost) - Sum(Returned Cost)` | |
| Gross Margin | `[Net Sales] - [Net Cost]` | compound |
| Gross Margin % | `IF([Net Sales] = 0, NULL, [Gross Margin] / [Net Sales])` | compound, smart metric ON so subtotals are ratio of sums |
| Net Sales (Prior Week) | Net Sales with a transformation: Week − 1 | |
| Net Sales WoW % | `([Net Sales] - [Net Sales (Prior Week)]) / [Net Sales (Prior Week)]` | |
| Inventory On Hand | `Sum(Units On Hand) {~+, Date}` with **dimensionality Date: Last value** (non-aggregatable over Date) | never sums snapshots across dates |
| Order Line Count | `Sum(Order Line Count)` | data-quality page |

## Prompts / filters

| Prompt | Type | Default |
|---|---|---|
| Date range | Attribute qualification on Date (between) | full period |
| Customer | Element list, multi-select | all |
| Category | Element list | all |
| Season | Element list | all |

## Security filter (proposed)

- Filter `SF_REGION_WEST`: Region = West. Assign to test user A.
- Filter `SF_REGION_NE`: Region = Northeast. Assign to test user B.
- Test: run Page 1 as each user; Net Sales must equal the region total from
  `SELECT REGION, SUM(NET_SALES) FROM VW_WHOLESALE_SALES GROUP BY REGION`.
  Record the result here; don't claim it works until tested.

## Dashboard

**Page 1 – Wholesale overview:** KPI cards (Net Sales, Net Units, Gross Margin, GM %, each
with WoW %); line/bar combo of Net Sales and GM % by Week; grid of Net Sales and Gross
Margin by Customer × Category.

**Page 2 – Product & inventory:** grid of Net Sales, Net Units, GM % by Style → Color → Size
(drill Style → SKU); heatmap of Net Units by Style × Size; grid of Inventory On Hand by SKU
for the latest snapshot.

**Page 3 – Data quality:** latest reconciliation results (import `docs/TEST_RESULTS.md`
§1 table, or a Snowflake table written by the runner later); Order Line Count vs fact count;
text box summarizing the ST120-BLK-M duplicate case from `docs/TROUBLESHOOTING_RUNBOOK.md`.

## Validation (fill in after build)

Expected values from `sql/tests/dashboard_expected_values.sql` on the clean dataset:

| Check (default prompts) | Expected | Dashboard | Match? |
|---|---|---|---|
| Net Sales | 1,