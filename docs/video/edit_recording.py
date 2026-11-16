"""Edit the raw screen recordings into docs/demo.mp4 (about 1:50).

Raw clips come from macOS screencapture of the live Snowflake and Strategy
sessions (account identifiers blurred in-page before recording). This script
trims, speeds up, crops the browser chrome, centres each clip on a dark canvas
and adds a caption strip, then concatenates everything with ffmpeg.

    python docs/video/edit_recording.py RAW_DIR FFMPEG
"""
import subprocess, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RAW, FF = Path(sys.argv[1]), sys.argv[2]
ROOT = Path(__file__).resolve().parents[2]
WORK = RAW.parent / "edit"; WORK.mkdir(exist_ok=True)
W, H, STRIP = 1920, 1080, 190
BG, STRIP_BG = (15, 23, 42), (20, 26, 43)
FONT = "/System/Library/Fonts/Helvetica.ttc"
CROP_A = "crop=2164:1882:16:0"      # clips recorded below the toolbar
CROP_C = "crop=2164:2010:16:116"    # full-window clips: drop debug banner
CROP_D = "crop=3388:1590:16:4"      # full-width dashboard clips

# (clip, start, end, speed, crop, section, title, caption)
SEGMENTS = [
    (None, 0, 7, 1, None, "OVERVIEW", "Architecture",
     "Synthetic CSVs load into Snowflake. Reporting views fix the grain. Strategy reads only those views "
     "through a read-only service login, and SQL tests reconcile every total."),
    ("A_schema", 1.5, 8.7, 1, CROP_A, "SNOWFLAKE", "The warehouse: WHOLESALE_DEMO.DW",
     "Staging tables, three facts (orders, returns, weekly inventory), three dimensions, and three reporting views "
     "that aggregate each fact to date x customer x SKU before joining."),
    ("B_recon_chart", 2, 16, 1.3, CROP_A, "SNOWFLAKE", "Reconciliation, live: difference 0.00",
     "The total the dashboard reads ($1,045,629.04) is checked against an independent total built from the raw fact "
     "tables. If the reporting layer ever adds or drops money, this catches it."),
    ("B2_chart", 1, 9.7, 1, CROP_A, "SNOWFLAKE", "Net sales by category",
     "The same reporting view, charted. Bottoms leads, then Dresses, Tops, Fleece and Accessories."),
    ("C2_dashboard", 1, 30, 1.5, CROP_D, "STRATEGY", "Executive dashboard, live on Snowflake",
     "Weekly net sales, KPI tiles comparing this week with last week, top styles, discount exposure, customers and "
     "category mix. Every number is queried live from the Snowflake reporting view."),
    ("C3_filtered", 0, 7, 1, CROP_D, "STRATEGY", "One filter, every visual recalculates",
     "Filtered to a single style (Baggy Denim): KPIs, trend, customers and category all re-query Snowflake. "
     "Nothing is extracted, so the dashboard cannot drift from the warehouse."),
    ("D_defect", 1, 13, 1.3, CROP_C, "INCIDENT", "A realistic defect",
     "A product-master reload inserts a second row for one SKU instead of updating it. "
     "Nothing fails; the numbers are simply wrong."),
    ("E2_inflated", 0.5, 9.5, 1, CROP_D, "INCIDENT", "What an executive sees",
     "Totals jump everywhere: Atlantic Value Stores moves from $139,964 to $145,878 and Bottoms from $397,439 to "
     "$414,095. Net sales are overstated by $16,656."),
    ("F_rootcause", 1, 12, 1.5, CROP_C, "ROOT CAUSE", "Step 1: compare line counts, view vs fact",
     "Order lines per SKU in the reporting view vs the fact table. One SKU, ST120-BLK-M, carries 40 lines "
     "instead of 20: the view is double counting it."),
    ("F_rootcause", 12, 26, 1.6, CROP_C, "ROOT CAUSE", "Step 2: check keys on the joined dimension",
     "DIM_PRODUCT has two rows for that SKU (seasons SS26 and FW26), so the join multiplies every sale "
     "and return for it."),
    ("F_rootcause", 26, 35, 1.5, CROP_C, "FIX", "Rebuild the dimension, one row per SKU",
     "Rebuild DIM_PRODUCT from the source master with exactly one row per SKU, and restore ownership to the "
     "loader role so the reporting views keep working."),
    ("F_rootcause", 35, 47, 1.5, CROP_C, "VALIDATE", "Reconciliation back to 0.00",
     "View total and independent total match again. In the pipeline, the unique-key and no-fan-out tests now "
     "block a dashboard refresh before anyone sees a wrong number."),
    ("G_history", 0.5, 9.7, 1, CROP_C, "SECURITY", "Least privilege, proven",
     "Snowflake query history: every dashboard query runs as STRATEGY_REPORTING, a service login that can read the "
     "three reporting views and nothing else."),
]


def font(size, bold=False):
    return ImageFont.truetype(FONT, size, index=1 if bold else 0)


def strip(i, n, section, title, caption):
    img = Image.new("RGB", (W, STRIP), STRIP_BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 3], fill=(124, 92, 214))
    d.text((60, 22), f"{section}  ·  {i}/{n}", font=font(22, True), fill=(167, 139, 250))
    d.text((60, 54), title, font=font(38, True), fill="white")
    y = 108
    for line in textwrap.wrap(caption, 128)[:2]:
        d.text((60, y), line, font=font(25), fill=(214, 219, 230))
        y += 34
    p = WORK / f"strip_{i:02d}.png"; img.save(p); return p


def run(*args):
    subprocess.run([FF, "-loglevel", "error", "-y", *args], check=True)


def main():
    n = len(SEGMENTS); parts = []
    vh = H - STRIP
    for i, (clip, s, e, spd, crop, section, title, cap) in enumerate(SEGMENTS, 1):
        st = strip(i, n, section, title, cap)
        out = WORK / f"seg_{i:02d}.mp4"
        fit = (f"scale={W-60}:{vh-30}:force_original_aspect_ratio=decrease,"
               f"pad={W}:{vh}:(ow-iw)/2:(oh-ih)/2:color=0x0f172a")
        if clip is None:
            run("-loop", "1", "-t", str(e), "-i", str(ROOT / "docs" / "architecture.png"), "-loop", "1", "-t", str(e), "-i", str(st),
                "-filter_complex", f"[0]format=rgb24,{fit},fps=30[v];[1]fps=30[s];[v][s]vstack,format=yuv420p",
                "-c:v", "libx264", "-crf", "20", "-r", "30", str(out))
        else:
            dur = (e - s) / spd
            run("-ss", str(s), "-t", str(e - s), "-i", str(RAW / f"{clip}.mov"), "-loop", "1", "-t", f"{dur:.2f}", "-i", str(st),
                "-filter_complex", f"[0]{crop},setpts=PTS/{spd},{fit},fps=30[v];[1]fps=30[s];[v][s]vstack=shortest=1,format=yuv420p",
                "-an", "-c:v", "libx264", "-crf", "20", "-r", "30", str(out))
        parts.append(out)
    lst = WORK / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    mp4 = ROOT / "docs" / "demo.mp4"
    run("-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "libx264", "-preset", "slow", "-crf", "21",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4))
    probe = subprocess.run([FF, "-i", str(mp4)], capture_output=True, text=True).stderr
    print(mp4, [l.strip() for l in probe.splitlines() if "Duration" in l][0], f"{mp4.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
