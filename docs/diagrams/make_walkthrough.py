"""Build docs/walkthrough.gif (60 s): architecture first, then the demo story.

Each slide is a small HTML page rendered to PNG with headless Chrome, then the
frames are stitched into a GIF with Pillow. Run from the repo root:
    python docs/diagrams/make_walkthrough.py
"""
import subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "diagrams" / "frames"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1400, 760

CSS = """
*{box-sizing:border-box}body{margin:0;width:1400px;height:760px;background:#fff;
font-family:-apple-system,Helvetica,Arial,sans-serif;color:#1f2328;padding:56px 72px}
.k{font-size:15px;letter-spacing:.08em;text-transform:uppercase;color:#7c5cd6;font-weight:700}
h1{font-size:44px;margin:10px 0 26px;line-height:1.15}
p,li{font-size:25px;line-height:1.5}ul{padding-left:28px;margin:0}li{margin:6px 0}
table{border-collapse:collapse;font-size:22px;width:100%}td,th{border-bottom:1px solid #ddd;padding:10px 12px;text-align:left}
th{color:#555;font-weight:600}.big{font-size:56px;font-weight:700;color:#1f9d55}
.bad{color:#d4442e;font-weight:700}.good{color:#1f9d55;font-weight:700}
code{font-family:Menlo,monospace;font-size:.9em;background:#f3f1fb;padding:1px 6px;border-radius:4px}
.foot{position:absolute;left:72px;bottom:30px;font-size:16px;color:#888}
"""

def page(kicker, title, body):
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>"
            f"<div class='k'>{kicker}</div><h1>{title}</h1>{body}"
            "<div class='foot'>Wholesale Reporting Accelerator · synthetic apparel data</div></body></html>")

SLIDES = [  # (name, seconds, html or image path)
    ("01_architecture", 5, ROOT / "docs" / "architecture.png"),
    ("02_flow", 5, ROOT / "docs" / "flow.png"),
    ("02b_problem", 0, page("The problem", "Numbers executives can trust,<br>and a fast answer when they don't match",
        "<ul><li>Wholesale reporting on an <b>existing</b> Snowflake model, not a new warehouse</li>"
        "<li>Revenue and margin by customer, product and week, vs prior week</li>"
        "<li>When a total looks wrong: find the cause in minutes, with SQL</li></ul>")),
    ("03_grain", 6, page("Data model and grain", "One row means one thing",
        "<table><tr><th>Table</th><th>One row =</th></tr>"
        "<tr><td><code>FACT_ORDER_LINE</code></td><td>one order line</td></tr>"
        "<tr><td><code>FACT_RETURN_LINE</code></td><td>one return against one order line</td></tr>"
        "<tr><td><code>FACT_INVENTORY_SNAPSHOT</code></td><td>one SKU at one weekly close</td></tr></table>"
        "<p>Sum each fact to date × customer × SKU <b>before</b> combining. Never join orders to inventory. "
        "Inventory = latest snapshot, never summed.</p>")),
    ("04_dash_overview", 7, ROOT / "docs" / "screenshots" / "dashboard_overview.jpg"),
    ("05_dash_filter", 4, ROOT / "docs" / "screenshots" / "dashboard_filter_panel.jpg"),
    ("06_dash_bottoms", 7, ROOT / "docs" / "screenshots" / "dashboard_filtered_bottoms.jpg"),
    ("07_metrics", 6, page("Strategy semantic layer", "Metrics defined once, live on Snowflake",
        "<table><tr><th>Metric</th><th>Definition</th></tr>"
        "<tr><td>Net sales</td><td>Gross − discount − refunds (returns on return date)</td></tr>"
        "<tr><td>Gross margin</td><td>Sum(Net Sales) − Sum(Net Cost)</td></tr>"
        "<tr><td>Gross margin %</td><td>ratio of totals, null when net sales = 0</td></tr></table>"
        "<p>Dashboard net sales <span class='good'>$1,045,629.04</span> = Snowflake = local test run, to the cent.</p>")),
    ("08_symptom", 5, page("Troubleshooting drill", "An executive's total is wrong",
        "<p>Dashboard: <span class='bad'>$1,062,285.04</span><br>Source system: <span class='good'>$1,045,629.04</span></p>"
        "<p class='big' style='color:#d4442e'>+$16,656 (1.6%)</p>")),
    ("09_root_cause", 7, page("Root cause in 5 SQL steps", "Narrow it down, don't guess",
        "<table><tr><th>Step</th><th>Finding</th></tr>"
        "<tr><td>1 · Dashboard vs independent fact total</td><td>reporting layer adds $16,656</td></tr>"
        "<tr><td>2 · By week</td><td>many weeks, not one bad load</td></tr>"
        "<tr><td>3 · By customer</td><td>all 8 customers</td></tr>"
        "<tr><td>4 · By SKU + line count</td><td><b>ST120-BLK-M: 40 lines vs 20</b></td></tr>"
        "<tr><td>5 · Duplicate keys</td><td><b>DIM_PRODUCT has 2 rows for that SKU</b></td></tr></table>")),
    ("10_fix", 4, page("Fix and validation", "Back to the cent",
        "<ul><li>Rebuild <code>DIM_PRODUCT</code>, one row per SKU</li>"
        "<li>Rerun: <span class='good'>15/15 tests pass</span>, net sales $1,045,629.04</li>"
        "<li>Prevention: unique-key + no-fan-out tests block the refresh</li>"
        "<li>Lesson: a summary that reads the same broken view will still \"tie out\"</li></ul>")),
    ("11_security", 4, page("Security and performance", "Least privilege, proven",
        "<ul><li>Strategy uses <code>STRATEGY_REPORTING</code>: SELECT on 3 views only, tables invisible</li>"
        "<li>Snowflake query history confirms every dashboard query runs as that user</li>"
        "<li>No secrets in Git; token scoped to the reporting role, 30-day expiry</li>"
        "<li>Slow report? Query history → profile → warehouse → model</li></ul>")),
]


def render(name, src):
    png = OUT / f"{name}.png"
    if isinstance(src, Path):
        return src
    html = OUT / f"{name}.html"
    html.write_text(src)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={W},{H}", f"--screenshot={png}", html.as_uri()],
                   check=True, capture_output=True)
    return png


def fit(path):
    img = Image.open(path).convert("RGB")
    img.thumbnail((W, H))
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
    return canvas.resize((1000, 543), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames, durations = [], []
    for name, secs, src in SLIDES:
        if secs == 0:
            continue
        frames.append(fit(render(name, src)).quantize(colors=128, method=Image.Quantize.MEDIANCUT))
        durations.append(secs * 1000)
    total = sum(d for d in durations) / 1000
    gif = ROOT / "docs" / "walkthrough.gif"
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"{gif.relative_to(ROOT)}: {len(frames)} slides, {total:.0f} s, {gif.stat().st_size // 1024} KB")


if __name__ == "__main__":
    sys.exit(main())
