# Requirements and metric definitions

> Synthetic apparel data. Not Pacsun's systems, data or wholesale model.

## Simulated business request

*From: Wholesale planning lead (simulated)*

> Each Monday I need one place to see how wholesale did last week by account, product and
> week, how that compares with the prior week, what is selling by style and size, and how
> much inventory we have left. When an executive's number doesn't match finance's, I need
> to know why within the hour.

## Business questions → where they're answered

| Question | Answered by |
|---|---|
| Revenue and gross margin by customer, product and week | Page 1 (overview), `VW_WHOLESALE_SALES` |
| Styles and sizes with highest sales and remaining inventory | Page 2 (product & inventory), `VW_INVENTORY_POSITION` |
| Current vs prior period | Page 1 trend, `VW_WEEKLY_WHOLESALE_SUMMARY` (prior-week columns) |
| Why a reported total differs from source | Page 3 (data quality), `docs/TROUBLESHOOTING_RUNBOOK.md` |

## Decisions confirmed with the simulated user

| Topic | Decision |
|---|---|
| Returns timing | Reported on **return date** (when the refund is issued), attributed to the original order line's customer and SKU. Matches how finance books refunds; means a week's net sales can drop because of returns on older orders. |
| Week | ISO week, Monday start. |
| Prior period | Prior week for the same filters. |
| Currency / rounding | USD, two decimals. Reconciliation tolerance: $0.01 on any total. |
| Inventory | Stock measure. Show the latest snapshot in the selected range; never sum snapshots across dates. |
| Sell-through | Deferred. Needs agreement on period and denominator (beginning-of-period on hand + receipts is the likely choice). |

## Metric definitions

| Metric | Definition | Source columns |
|---|---|---|
| Gross sales | Σ order-line sales before discounts and returns | `GROSS_SALES` |
| Discount | Σ order-line discount | `DISCOUNT_AMOUNT` |
| Refund | Σ refund amount on return lines, by return date | `REFUND_AMOUNT` |
| Net sales | Gross sales − discount − refund | |
| Net units | Units sold − units returned | `UNITS`, `RETURNED_UNITS` |
| Net cost | Cost of units sold − cost of units returned | `EXTENDED_COST`, `RETURNED_COST` |
| Gross margin | Net sales − net cost | |
| Gross margin % | Gross margin ÷ net sales; **null when net sales = 0** | |
| Inventory on hand | Units on the latest snapshot in the selected range | `UNITS_ON_HAND` |

Gross margin % is a ratio of sums, never an average of row-level percentages — the
MicroStrategy metric must be defined as `GM / NetSales` at the report level (see
`mstr/SEMANTIC_LAYER.md`).
