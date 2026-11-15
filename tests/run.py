"""Build the model, run the test suite and the defect scenario, write docs/TEST_RESULTS.md.

  python tests/run.py                     # local DuckDB (no credentials needed)
  python tests/run.py --target snowflake  # real Snowflake; reads connection from env vars

Snowflake env vars: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER. Password is prompted (or SNOWFLAKE_PASSWORD);
set SNOWFLAKE_AUTHENTICATOR=externalbrowser only for SSO accounts. Optional: SNOWFLAKE_ROLE (default WHS_LOADER),
SNOWFLAKE_WAREHOUSE (default WHS_DEMO_WH). Never commit these.
"""
import argparse, csv, os, re, sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, SQL = ROOT / "data", ROOT / "sql"
STG = {  # staging table -> csv
    "STG_DATE": "dim_date.csv", "STG_CUSTOMER": "dim_customer.csv",
    "STG_PRODUCT": "dim_product.csv", "STG_ORDER_LINE": "fact_order_line.csv",
    "STG_RETURN_LINE": "fact_return_line.csv", "STG_INVENTORY_SNAPSHOT": "fact_inventory_snapshot.csv",
}


def statements(path):
    text = re.sub(r"--[^\n]*", "", path.read_text())
    return [s.strip() for s in text.split(";") if s.strip()]


class Duck:
    name = "DuckDB (local)"
    def __init__(self):
        import duckdb
        self.con = duckdb.connect()
    def load_staging(self):
        for t, f in STG.items():
            self.con.execute(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM read_csv('{DATA/f}', all_varchar=true, header=true)")
    def query(self, sql):
        cur = self.con.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, cur.fetchall() if cols else []


class Snow:
    name = "Snowflake"
    def __init__(self, database="WHOLESALE_DEMO", schema="DW"):
        import snowflake.connector
        kw = dict(account=os.environ["SNOWFLAKE_ACCOUNT"], user=os.environ["SNOWFLAKE_USER"],
                  role=os.environ.get("SNOWFLAKE_ROLE", "WHS_LOADER"),
                  warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "WHS_DEMO_WH"),
                  client_store_temporary_credential=True)
        if database:
            kw.update(database=database, schema=schema)
        key = os.environ.get("SNOWFLAKE_PRIVATE_KEY_FILE")
        if key:
            kw["private_key_file"] = key
        elif os.environ.get("SNOWFLAKE_AUTHENTICATOR"):
            kw["authenticator"] = os.environ["SNOWFLAKE_AUTHENTICATOR"]
        else:
            if not os.environ.get("SNOWFLAKE_PASSWORD"):
                import getpass  # asked once, kept only in this process
                os.environ["SNOWFLAKE_PASSWORD"] = getpass.getpass(f"Snowflake password for {kw['user']}: ")
            kw["password"] = os.environ["SNOWFLAKE_PASSWORD"]
            if os.environ.get("SNOWFLAKE_MFA_PASSCODE"):
                kw["passcode"] = os.environ["SNOWFLAKE_MFA_PASSCODE"]
        self.con = snowflake.connector.connect(**kw)
    def load_staging(self):
        cur = self.con.cursor()
        cur.execute("CREATE OR REPLACE FILE FORMAT CSV_FMT TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '\"'")
        cur.execute("CREATE STAGE IF NOT EXISTS WHS_STAGE FILE_FORMAT = CSV_FMT")
        for f in STG.values():
            cur.execute(f"PUT 'file://{DATA/f}' @WHS_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE")
        for s in statements(SQL / "snowflake" / "01_stage_and_load.sql"):
            if not s.upper().startswith(("USE ", "CREATE OR REPLACE FILE FORMAT", "CREATE STAGE")):
                cur.execute(s)
    def query(self, sql):
        cur = self.con.cursor().execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, cur.fetchall() if cols else []


def run_file(db, path):
    out = []
    for s in statements(path):
        out.append(db.query(s))
    return out


def run_tests(db):
    return [rows[0] for _, rows in run_file(db, SQL / "tests" / "reconciliation_tests.sql")]


def known_row_test(db):
    """Hand-computed metric check on one order line with a return."""
    cols, rows = db.query((SQL / "tests" / "known_rows_test.sql").read_text().split(";")[0].split("\n", 2)[2])
    r = dict(zip([c.upper() for c in cols], rows[0]))
    with open(DATA / "fact_order_line.csv") as f:
        o = next(x for x in csv.DictReader(f) if x["ORDER_LINE_ID"] == r["ORDER_LINE_ID"])
    with open(DATA / "fact_return_line.csv") as f:
        rt = [x for x in csv.DictReader(f) if x["ORDER_LINE_ID"] == r["ORDER_LINE_ID"]]
    D = Decimal
    exp_net_sales = D(o["GROSS_SALES"]) - D(o["DISCOUNT_AMOUNT"]) - sum(D(x["REFUND_AMOUNT"]) for x in rt)
    exp_net_cost = D(o["EXTENDED_COST"]) - sum(D(x["RETURNED_COST"]) for x in rt)
    exp_net_units = int(o["UNITS"]) - sum(int(x["RETURNED_UNITS"]) for x in rt)
    got_net_sales = D(str(r["GROSS_SALES"])) - D(str(r["DISCOUNT_AMOUNT"])) - D(str(r["REFUND_AMOUNT"]))
    got_net_cost = D(str(r["EXTENDED_COST"])) - D(str(r["RETURNED_COST"]))
    got_units = int(r["UNITS"]) - int(r["RETURNED_UNITS"])
    ok = (got_net_sales == exp_net_sales and got_net_cost == exp_net_cost and got_units == exp_net_units)
    gm = exp_net_sales - exp_net_cost
    detail = (f"line {r['ORDER_LINE_ID']}: net sales {exp_net_sales}, net cost {exp_net_cost}, "
              f"net units {exp_net_units}, gross margin {gm}, GM% {gm / exp_net_sales:.4f}")
    return ("T15_KNOWN_ROW_METRIC_CALC", "PASS" if ok else "FAIL", detail)


def md_table(cols, rows):
    fmt = lambda v: f"{v:,.2f}" if isinstance(v, (float, Decimal)) else str(v)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["local", "snowflake"], default="local")
    ap.add_argument("--setup", action="store_true",
                    help="snowflake only: run sql/snowflake/00_setup_roles.sql as ACCOUNTADMIN first")
    args = ap.parse_args()
    if args.setup and args.target == "snowflake":
        os.environ["SNOWFLAKE_ROLE"] = "ACCOUNTADMIN"
        admin = Snow(database=None, schema=None)
        for s in statements(SQL / "snowflake" / "00_setup_roles.sql"):
            admin.query(s)
        me = admin.query("SELECT CURRENT_USER()")[1][0][0]  # user name can differ from login name
        admin.query(f'GRANT ROLE WHS_LOADER TO USER "{me}"')
        admin.con.close()
        os.environ["SNOWFLAKE_ROLE"] = "WHS_LOADER"
    db = Duck() if args.target == "local" else Snow()

    db.load_staging()
    run_file(db, SQL / "model" / "02_tables.sql")
    run_file(db, SQL / "model" / "03_views.sql")

    baseline = run_tests(db) + [known_row_test(db)]
    run_file(db, SQL / "scenario" / "01_inject_defect.sql")
    broken = run_tests(db)
    investigation = run_file(db, SQL / "scenario" / "02_investigate.sql")
    run_file(db, SQL / "scenario" / "03_fix_defect.sql")
    fixed = run_tests(db)

    hdr = ["TEST_NAME", "STATUS", "DETAIL"]
    rep = [f"# Test results\n\nEngine: **{db.name}** · generated {datetime.now():%Y-%m-%d %H:%M}"
           " by `tests/run.py`. Do not edit by hand.\n",
           "## 1. Baseline (clean load)\n", md_table(hdr, baseline),
           "\n## 2. After injecting the defect (`sql/scenario/01_inject_defect.sql`)\n", md_table(hdr, broken),
           "\n## 3. Investigation output (`sql/scenario/02_investigate.sql`)\n"]
    for cols, rows in investigation:
        rep.append(md_table(cols, rows) if rows else "_(no rows)_")
        rep.append("")
    rep += ["## 4. After the fix (`sql/scenario/03_fix_defect.sql`)\n", md_table(hdr, fixed)]
    out = ROOT / "docs" / ("TEST_RESULTS.md" if args.target == "local" else "TEST_RESULTS_SNOWFLAKE.md")
    out.write_text("\n".join(rep) + "\n")

    fails = [t for t in baseline + fixed if t[1] != "PASS"]
    caught = [t[0] for t in broken if t[1] == "FAIL"]
    print(f"baseline: {sum(t[1]=='PASS' for t in baseline)}/{len(baseline)} pass")
    print(f"defect caught by: {caught}")
    print(f"after fix: {sum(t[1]=='PASS' for t in fixed)}/{len(fixed)} pass")
    print(f"wrote {out.relative_to(ROOT)}")
    sys.exit(1 if fails or not caught else 0)


if __name__ == "__main__":
    main()
