"""Build docs/demo.mp4: a captioned walkthrough (under 2 minutes) of the real
Snowflake and Strategy screens. Needs Pillow and imageio-ffmpeg.

    python docs/video/make_video.py
"""
import subprocess, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent
S = HERE / "screens"
OUT = HERE / "frames"
W, H, BAND = 1280, 720, 168
FONT = "/System/Library/Fonts/Helvetica.ttc"

SCENES = [  # (image, seconds, section, title, caption)
    (DOCS / "architecture.png", 8, "OVERVIEW", "Architecture",
     "Synthetic CSVs load into Snowflake. Reporting views fix the grain. Strategy reads only those views "
     "through a read-only login, and SQL tests reconcile every total."),
    (DOCS / "flow.png", 6, "OVERVIEW", "The story in six steps",
     "Executives see mismatched totals. The fix: one clean grain, metrics defined once, reconciliation "
     "tests, a repeatable troubleshooting path, and least-privilege access."),
    (S / "03_snowflake_schema.jpg", 9, "SNOWFLAKE", "The warehouse: WHOLESALE_DEMO.DW",
     "Raw STG_ tables, 3 facts (orders, returns, inventory), 3 dimensions and 3 reporting views. "
     "The views sum each fact to date x customer x SKU before joining, so totals can't multiply."),
    (S / "04_snowflake_recon_ok.jpg", 9, "SNOWFLAKE", "Reconciliation check: difference = 0.00",
     "The dashboard's view total is compared with an independent total built straight from the raw facts. "
     "Both are $1,045,629.04."),
    (S / "05_dashboard.jpg", 10, "STRATEGY", "The live wholesale dashboard",
     "Net sales, cost, gross margin and margin % by customer, plus a weekly trend. "
     "Connected live to Snowflake, so it can never drift from the warehouse."),
    (S / "06_dashboard_filter.jpg", 5, "STRATEGY", "Filters a planner would use",
     "Category and customer filters. Each change sends a new query to Snowflake."),
    (S / "07_dashboard_bottoms.jpg", 8, "STRATEGY", "Filtered to Bottoms",
     "Every number and the trend line recalculate for one category, with no extract or refresh needed."),
    (S / "08_strategy_metric_editor.jpg", 8, "STRATEGY", "Metrics defined once: Gross Margin %",
     "(Net sales - net cost) / net sales, as a ratio of totals, and null when net sales is zero. "
     "Every page reuses the same definition."),
    (S / "09_snowflake_defect.jpg", 7, "TROUBLESHOOTING", "Simulating a real defect",
     "A product reload inserts a second row for one SKU instead of updating it. "
     "This is a common production bug."),
    (S / "10_dashboard_inflated.jpg", 9, "TROUBLESHOOTING", "The executive sees the wrong number",
     "Dashboard totals jump. Atlantic Value Stores goes from $139,964 to $145,878. "
     "Net sales are now overstated by $16,656."),
    (S / "11_snowflake_root_cause.jpg", 9, "TROUBLESHOOTING", "Root cause SQL: compare line counts",
     "Order lines in the view vs the fact table, by SKU. One SKU, ST120-BLK-M, has 40 lines instead of 20."),
    (S / "12_snowflake_dup_keys.jpg", 8, "TROUBLESHOOTING", "Why: a duplicate key in DIM_PRODUCT",
     "The product dimension has two rows for that SKU (SS26 and FW26), so the join doubles every sale."),
    (S / "13_snowflake_fixed.jpg", 8, "TROUBLESHOOTING", "Fix and validate",
     "Rebuild the dimension with one row per SKU and rerun the reconciliation. Difference is back to 0.00. "
     "A unique-key test now blocks this before the dashboard refreshes."),
    (S / "14_snowflake_query_history.jpg", 8, "SECURITY", "Least privilege, proven",
     "Snowflake query history: every dashboard query runs as STRATEGY_REPORTING, a login that can read "
     "the 3 views and nothing else."),
]


def font(size, bold=False):
    return ImageFont.truetype(FONT, size, index=1 if bold else 0)


def frame(i, n, img_path, section, title, caption):
    canvas = Image.new("RGB", (W, H), "white")
    img = Image.open(img_path).convert("RGB")
    img.thumbnail((W - 40, H - BAND - 30), Image.LANCZOS)
    canvas.paste(img, ((W - img.width) // 2, 15 + (H - BAND - 30 - img.height) // 2))
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, H - BAND, W, H], fill=(20, 26, 43))
    d.text((40, H - BAND + 18), f"{section}  ·  {i}/{n}", font=font(17, True), fill=(167, 139, 250))
    d.text((40, H - BAND + 44), title, font=font(30, True), fill="white")
    y = H - BAND + 88
    for line in textwrap.wrap(caption, 108):
        d.text((40, y), line, font=font(20), fill=(214, 219, 230))
        y += 27
    return canvas


def main():
    OUT.mkdir(exist_ok=True)
    listing = []
    for i, (path, secs, section, title, caption) in enumerate(SCENES, 1):
        p = OUT / f"scene_{i:02d}.png"
        frame(i, len(SCENES), path, section, title, caption).save(p)
        listing += [f"file '{p}'", f"duration {secs}"]
    listing.append(f"file '{OUT / f'scene_{len(SCENES):02d}.png'}'")
    lst = OUT / "list.txt"
    lst.write_text("\n".join(listing) + "\n")
    mp4 = DOCS / "demo.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "20", "-movflags", "+faststart", str(mp4)], check=True)
    total = sum(s[1] for s in SCENES)
    print(f"{mp4.relative_to(DOCS.parent)}: {len(SCENES)} scenes, {total} s, {mp4.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
