# Technical design

## Architecture

```
data_gen/generate.py ──► data/*.csv (seeded, synthetic)
        │  PUT + COPY INTO
        ▼
Snowflake WHOLESALE_DEMO.DW
  STG_*                    raw strings, one table per CSV
  DIM_DATE / DIM_PRODUCT / DIM_CUSTOMER
  FACT_ORDER_LINE / FACT_RETURN_LINE / FACT_INVENTORY_SNAPSHOT
  VW_WHOLESALE_SALES / VW_INVENTORY_POSITION / VW_WEEKLY_WHOLESALE_SUMMARY
        │  role WHS_REPORTING (SELECT on views only)
        ▼
MicroStrategy: attributes, facts, metrics, prompts ──► 3-page dashboard
        │
        └── sql/tests/*.sql + tests/run.py: reconciliation, before/after defect
```

The Snowflake model is treated as an existing, simplified source. The work this demo
focuses on is the reporting layer, validation and support.

## Tables

| Table | Grain | Key |
|---|---|---|
| DIM_DATE | date | DATE_KEY |
| DIM_PRODUCT | SKU (style × color × size) | SKU |
| DIM_CUSTOMER | wholesale account | CUSTOMER_ID |
| FACT_ORDER_LINE | order line | ORDER_LINE_ID |
| FACT_RETURN_LINE | return line → one original order line | RETURN_ID |
| FACT_INVENTORY_SNAPSHOT | SKU × weekly snapshot (Sunday close) | SNAPSHOT_DATE + SKU |

Data volume: 8 customers, 12 styles / 180 SKUs, 26 weeks (2026-01-05 → 2026-07-05),
1,953 order lines, 141 returns, 4,680 inventory rows.

## Key design choices

1. **Aggregate each fact to the reporting grain before combining.** `VW_WHOLESALE_SALES`
   sums sales and returns separately to date × customer × SKU, then full-outer-combines
   them on that key. Inventory is never joined to order lines: a SKU has one snapshot row
   per week but many order lines, so a direct join would multiply both measures.
2. **Returns on return date**, attributed to the original line's customer and SKU.
3. **Inventory is a stock.** `VW_INVENTORY_POSITION` flags the latest snapshot;
   the weekly summary takes only the week-closing snapshot.
4. **Portable SQL.** Everything in `sql/model` and `sql/tests` runs unchanged on
   Snowflake and DuckDB, so the same tests run locally and in the warehouse.
5. **Independent reconciliation.** Tests compute totals straight from the fact tables with
   no dimension joins, so a bad join in the reporting layer can't hide in both sides.

## Security

- Synthetic data only. No credentials in Git (`.gitignore` covers `.env`, config).
- `WHS_LOADER` builds objects; `WHS_REPORTING` (MicroStrategy's service account) gets
  `SELECT` on views only, no tables.
- Row-level security proposal: see `mstr/SEMANTIC_LAYER.md` § Security filter.

## Running

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python data_gen/generate.py
.venv/bin/python tests/run.py                       # local DuckDB
.venv/bin/python tests/run.py --target snowflake    # after running sql/snowflake/00_setup_roles.sql
```

## Not in scope

Production deployment, real integrations or live users; any upgrade or migration;
Pacsun's real model or data.
