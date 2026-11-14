"""One-command pipeline. Usage: python run_all.py [--skip-ingest]"""
import os, subprocess, sys, time

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
steps = ([] if "--skip-ingest" in sys.argv else ["src.ingestion", "src.metadata"]) + ["src.graph", "src.stats", "src.discovery", "src.forensics", "src.h38", "src.validation", "src.evidence", "src.cube", "src.register", "src.atlas", "src.lineage", "src.charts", "src.webdata", "src.replay", "src.ledger", "src.reporting", "src.research_report", "src.web"]  # reporting reads ledger + replay, so it runs after them
for s in steps:
    t = time.time(); print(f"==> {s}", flush=True)
    subprocess.run([sys.executable, "-m", s], check=True)
    print(f"    done in {time.time()-t:.0f}s", flush=True)
subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], check=True)
