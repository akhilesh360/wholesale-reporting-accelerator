"""Generate deterministic synthetic wholesale apparel data as CSV.

All data is fictional. Seeded so every run produces identical files,
which makes reconciliation results reproducible.
"""
import csv, random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
START = date(2026, 1, 5)   # Monday
WEEKS = 26
OUT = Path(__file__).resolve().parent.parent / "data"

CUSTOMERS = [
    ("C001", "Harbor Lane Boutiques", "Specialty", "West"),
    ("C002", "Northline Department Stores", "Department", "Northeast"),
    ("C003", "Sunset Surf Co", "Specialty", "West"),
    ("C004", "Midway Outfitters", "Specialty", "Midwest"),
    ("C005", "Gulf Coast Apparel", "Off-Price", "South"),
    ("C006", "Peak Online Retail", "E-commerce", "National"),
    ("C007", "Campus Threads", "Specialty", "Midwest"),
    ("C008", "Atlantic Value Stores", "Off-Price", "Northeast"),
]
STYLES = [  # style, name, category, season, unit cost, wholesale price
    ("ST100", "Classic Logo Tee", "Tops", "SS26", 6.50, 14.00),
    ("ST101", "Boxy Pocket Tee", "Tops", "SS26", 7.25, 16.00),
    ("ST102", "Waffle Henley", "Tops", "SS26", 9.80, 22.00),
    ("ST110", "Relaxed Hoodie", "Fleece", "FW26", 15.40, 34.00),
    ("ST111", "Crew Sweatshirt", "Fleece", "FW26", 12.90, 28.00),
    ("ST120", "Baggy Denim", "Bottoms", "SS26", 18.20, 40.00),
    ("ST121", "Cargo Pant", "Bottoms", "SS26", 16.75, 36.00),
    ("ST122", "Board Short", "Bottoms", "SS26", 10.10, 24.00),
    ("ST130", "Slip Dress", "Dresses", "SS26", 14.30, 32.00),
    ("ST131", "Knit Midi Dress", "Dresses", "FW26", 17.60, 38.00),
    ("ST140", "Canvas Tote", "Accessories", "SS26", 4.20, 11.00),
    ("ST141", "Dad Cap", "Accessories", "SS26", 3.90, 10.00),
]
COLORS = ["BLK", "WHT", "SAND"]
SIZES = ["XS", "S", "M", "L", "XL"]
SIZE_WEIGHT = {"XS": 0.6, "S": 1.0, "M": 1.4, "L": 1.2, "XL": 0.7}


def write(name, header, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


def main():
    rnd = random.Random(SEED)
    OUT.mkdir(exist_ok=True)
    end = START + timedelta(weeks=WEEKS) - timedelta(days=1)

    # DIM_DATE (ISO week start = Monday)
    dates, d = [], START - timedelta(weeks=1)
    while d <= end + timedelta(days=30):
        wk = d - timedelta(days=d.weekday())
        dates.append((d.isoformat(), wk.isoformat(), d.isocalendar()[1],
                      d.strftime("%Y-%m"), f"{d.year}-Q{(d.month-1)//3+1}", d.year,
                      d.strftime("%a")))
        d += timedelta(days=1)
    write("dim_date.csv", ["DATE_KEY", "WEEK_START", "ISO_WEEK", "YEAR_MONTH",
                           "YEAR_QUARTER", "YEAR", "DAY_NAME"], dates)

    write("dim_customer.csv", ["CUSTOMER_ID", "CUSTOMER_NAME", "CHANNEL", "REGION"], CUSTOMERS)

    products, sku_info = [], {}
    for st, nm, cat, season, cost, price in STYLES:
        for c in COLORS:
            for s in SIZES:
                sku = f"{st}-{c}-{s}"
                products.append((sku, st, nm, c, s, cat, season, cost, price))
                sku_info[sku] = (st, s, cost, price, season)
    write("dim_product.csv", ["SKU", "STYLE_ID", "STYLE_NAME", "COLOR", "SIZE",
                              "CATEGORY", "SEASON", "UNIT_COST", "WHOLESALE_PRICE"], products)

    skus = list(sku_info)
    weights = [SIZE_WEIGHT[sku_info[k][1]] for k in skus]
    orders, returns = [], []
    order_n = ret_n = 0
    for day in range((end - START).days + 1):
        od = START + timedelta(days=day)
        if od.weekday() >= 5:
            continue
        for cust in CUSTOMERS:
            if rnd.random() > 0.35:
                continue
            order_n += 1
            oid = f"SO{order_n:06d}"
            disc_rate = {"Off-Price": 0.12, "Department": 0.08}.get(cust[2], 0.04)
            for line, sku in enumerate(rnd.choices(skus, weights, k=rnd.randint(3, 8)), 1):
                _, _, cost, price, season = sku_info[sku]
                # FW styles ramp up later in the half
                if season == "FW26" and day < 90 and rnd.random() < 0.7:
                    continue
                units = rnd.choice([6, 12, 12, 24, 24, 36, 48])
                gross = round(units * price, 2)
                disc = round(gross * disc_rate, 2)
                ext_cost = round(units * cost, 2)
                lid = f"{oid}-{line:02d}"
                orders.append((oid, lid, od.isoformat(), cust[0], sku, units,
                               f"{price:.2f}", f"{gross:.2f}", f"{disc:.2f}", f"{ext_cost:.2f}"))
                if rnd.random() < 0.07:
                    ret_n += 1
                    ru = max(1, units // rnd.choice([2, 3, 4, 6]))
                    rd = od + timedelta(days=rnd.randint(5, 30))
                    if rd > end:
                        continue
                    net_unit = (gross - disc) / units
                    returns.append((f"RT{ret_n:06d}", lid, rd.isoformat(), ru,
                                    f"{ru*net_unit:.2f}", f"{ru*cost:.2f}"))
    write("fact_order_line.csv", ["ORDER_ID", "ORDER_LINE_ID", "ORDER_DATE", "CUSTOMER_ID",
                                  "SKU", "UNITS", "UNIT_PRICE", "GROSS_SALES",
                                  "DISCOUNT_AMOUNT", "EXTENDED_COST"], orders)
    write("fact_return_line.csv", ["RETURN_ID", "ORDER_LINE_ID", "RETURN_DATE",
                                   "RETURNED_UNITS", "REFUND_AMOUNT", "RETURNED_COST"], returns)

    # Weekly inventory snapshots (Sunday close). On hand evolves with receipts minus shipments.
    shipped = {}
    for o in orders:
        wk = date.fromisoformat(o[2])
        wk = wk - timedelta(days=wk.weekday()) + timedelta(days=6)
        shipped[(wk, o[4])] = shipped.get((wk, o[4]), 0) + o[5]
    snaps, on_hand = [], {k: rnd.randint(400, 900) for k in skus}
    for w in range(WEEKS):
        snap = START + timedelta(weeks=w, days=6)
        for k in skus:
            receipt = rnd.choice([0, 0, 0, 120, 240]) if on_hand[k] < 600 else 0
            on_hand[k] = max(0, on_hand[k] + receipt - shipped.get((snap, k), 0))
            snaps.append((snap.isoformat(), k, on_hand[k], f"{on_hand[k]*sku_info[k][2]:.2f}"))
    write("fact_inventory_snapshot.csv", ["SNAPSHOT_DATE", "SKU", "UNITS_ON_HAND",
                                          "INVENTORY_COST"], snaps)


if __name__ == "__main__":
    main()
