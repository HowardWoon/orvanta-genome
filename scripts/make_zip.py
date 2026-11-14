"""Build the review ZIP. Excludes the raw CSV and all row-level derived data (dataset is organiser IP, RR 2.1–2.2)."""
import zipfile, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ["README.md", "requirements.txt", "run_all.py", ".streamlit", "web", "src", "tests", "dashboard", "docs", "findings", "submission", "scripts", "notebooks",
           "outputs/evidence", "outputs/tables", "outputs/charts", "outputs/pdf_build", "outputs/logs", "analysis",
           "data/metadata/cc_currency_map.csv", "data/metadata/country_offsets.csv", "data/metadata/country_effects.csv"]
SKIP_SUFFIX = {".parquet_raw", ".csv.gz", ".pyc"}
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".vercel"}


def main():
    out = ROOT / f"UMDAC2026_NaiLong_review_{dt.date.today():%Y%m%d}.zip"
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in INCLUDE:
            p = ROOT / item
            files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
            for f in files:
                if "responsive-screenshots" in f.parts and "before" in f.parts:   # keep the final screenshot set only
                    continue
                if SKIP_PARTS & set(f.parts) or f.suffix in SKIP_SUFFIX or f.name.endswith(".duckdb") or f.name.startswith(".env"):
                    continue
                assert "swift_umdac_datathon_2026" not in f.name, "raw dataset must not be zipped"
                z.write(f, f.relative_to(ROOT)); n += 1
    print(f"{out.name}: {n} files, {out.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
