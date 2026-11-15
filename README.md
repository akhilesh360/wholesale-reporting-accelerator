# Wholesale Reporting and Reconciliation Accelerator

A demo of taking a wholesale reporting request from requirements to a validated dashboard
on Snowflake, then investigating a reporting discrepancy. **All data is synthetic.** It does
not represent Pacsun's systems or data.

| Read | For |
|---|---|
| [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md) | **start here:** the six demo talking points with live results |
| [docs/REQUIREMENTS_AND_METRICS.md](docs/REQUIREMENTS_AND_METRICS.md) | business request, decisions, metric definitions |
| [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md) | architecture, grain, design choices, security |
| [mstr/SEMANTIC_LAYER.md](mstr/SEMANTIC_LAYER.md) | MicroStrategy objects, dashboard spec, validation table |
| [docs/TROUBLESHOOTING_RUNBOOK.md](docs/TROUBLESHOOTING_RUNBOOK.md) | the $16,656 discrepancy: cause, fix, prevention |
| [docs/TEST_RESULTS.md](docs/TEST_RESULTS.md) | generated test output, before and after the defect |

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python data_gen/generate.py
.venv/bin/python tests/run.py
```

## Layout

```
data_gen/        synthetic data generator (seeded)
data/            generated CSVs
sql/snowflake/   Snowflake-only: roles, warehouse, stage + COPY INTO
sql/model/       tables and reporting views (portable SQL)
sql/tests/       reconciliation suite, known-row test, dashboard expected values
sql/scenario/    inject defect → investigate → fix
tests/run.py     runs everything on DuckDB or Snowflake, writes docs/TEST_RESULTS.md
mstr/            MicroStrategy semantic layer and dashboard spec
```

## Running on Snowflake

Key-pair login (no password; the key lives in `.keys/`, which git ignores):

```bash
mkdir -p .keys && openssl genrsa 2048 | openssl pkcs8 -topk8 -nocrypt -out .keys/snowflake_rsa_key.p8
openssl rsa -in .keys/snowflake_rsa_key.p8 -pubout   # paste the body into: ALTER USER <name> SET RSA_PUBLIC_KEY='...';
SNOWFLAKE_ACCOUNT=<org-account> SNOWFLAKE_USER=<login_name> SNOWFLAKE_PRIVATE_KEY_FILE=.keys/snowflake_rsa_key.p8 \
  .venv/bin/python tests/run.py --target snowflake --setup   # --setup only the first time (needs ACCOUNTADMIN)
```

`SNOWFLAKE_USER` is the **login name** (`SHOW USERS` → `login_name`), which can diffe