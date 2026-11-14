"""Central configuration: paths, DuckDB connection, split definitions.

The raw CSV is never modified. Every derived artefact lives under data/processed or outputs/.
"""
from __future__ import annotations
import os
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = Path(os.environ.get("SWIFT_RAW_CSV", ROOT / "swift_umdac_datathon_2026_fictitious_payment_data.csv"))
PROCESSED = ROOT / "data" / "processed"
METADATA = ROOT / "data" / "metadata"
FULL_PQ = PROCESSED / "payments.parquet"      # all 20 analytic columns, text included (DISCLAIMER dropped)
SLIM_PQ = PROCESSED / "slim.parquet"          # typed + derived columns, no free text
OUT = ROOT / "outputs"
EVIDENCE = OUT / "evidence"
TABLES = OUT / "tables"
CHARTS = OUT / "charts"
FINDINGS = ROOT / "findings"
EXPECTED_ROWS = 10_000_000
SPLIT_DATE = "2023-06-15"   # temporal holdout boundary (roughly half of the 93-day window)

for p in (PROCESSED, METADATA, EVIDENCE, TABLES, CHARTS, FINDINGS):
    p.mkdir(parents=True, exist_ok=True)


def _p(path: Path) -> str:
    return str(path).replace("\\", "/")


# Resource limits: defaults suit the 10-thread development PC; override on smaller machines (Colab: ORVANTA_THREADS=2, ORVANTA_MEMORY=6GB)
THREADS = int(os.environ.get("ORVANTA_THREADS", 10))
MEMORY = os.environ.get("ORVANTA_MEMORY", "9GB")
TEMP_DIR = os.environ.get("ORVANTA_TEMP", "")          # DuckDB spill directory (empty = DuckDB default)


def duck(memory: str | None = None, preserve_order: bool = False) -> duckdb.DuckDBPyConnection:
    """Plain DuckDB connection with the configured limits (used by the ingestion stage)."""
    con = duckdb.connect()
    con.execute(f"SET threads={THREADS}; SET memory_limit='{memory or MEMORY}'; SET preserve_insertion_order={str(preserve_order).lower()}; SET enable_progress_bar=false")
    if TEMP_DIR:
        con.execute(f"SET temp_directory='{TEMP_DIR}'")
    return con


def find_browser() -> tuple[str, list[str]] | None:
    """Headless Chromium-family browser for HTML -> PDF: Edge/Chrome on Windows, google-chrome/chromium on Linux (e.g. Colab)."""
    import shutil, sys
    cands = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
    cands += [shutil.which(n) or "" for n in ("msedge", "chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser")]
    exe = next((p for p in cands if p and Path(p).exists()), None)
    if not exe:
        return None
    extra = ["--no-sandbox"] if sys.platform != "win32" and hasattr(os, "geteuid") and os.geteuid() == 0 else []   # Colab runs as root
    return exe, extra


def connect(threads: int | None = None, memory: str | None = None, slim: Path | None = None) -> duckdb.DuckDBPyConnection:
    """DuckDB connection with view `t` (slim table) and `tt` (t + split keys).

    Split keys
      h   : pseudo-random half, hash(rid) % 2  -> independent-subset validation
      per : 'P1' before SPLIT_DATE, 'P2' after -> temporal validation
    """
    con = duckdb.connect()
    con.execute(f"SET threads={threads or THREADS}; SET memory_limit='{memory or MEMORY}'; SET preserve_insertion_order=false; SET enable_progress_bar=false")
    if TEMP_DIR:
        con.execute(f"SET temp_directory='{TEMP_DIR}'")
    src = _p(slim or SLIM_PQ)
    con.execute(f"CREATE OR REPLACE VIEW t AS SELECT * FROM read_parquet('{src}')")
    con.execute(f"""CREATE OR REPLACE VIEW tt AS SELECT *, (hash(rid) % 2)::INT AS h,
                    CASE WHEN d < DATE '{SPLIT_DATE}' THEN 'P1' ELSE 'P2' END AS per FROM t""")
    if (METADATA / "cc_currency_map.csv").exists():
        con.execute(f"CREATE OR REPLACE TABLE ccy AS SELECT cc, cur AS hcur FROM read_csv('{_p(METADATA / 'cc_currency_map.csv')}')")
    if (METADATA / "country_offsets.csv").exists():
        con.execute(f"CREATE OR REPLACE TABLE off AS SELECT column0 AS cc, \"offset\" AS o FROM read_csv('{_p(METADATA / 'country_offsets.csv')}')")
    return con


# GROUPING SETS clause producing one row per split: full, h=0, h=1, P1, P2
SPLITS = "GROUPING SETS ((), (h), (per))"
SPLIT_LABEL = "CASE WHEN h IS NOT NULL THEN 'half_' || h WHEN per IS NOT NULL THEN per ELSE 'full' END"
