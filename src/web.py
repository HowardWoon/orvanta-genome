"""Build the static web edition of the Synthetic Rule Intelligence Lab for Vercel (web/dist/).

Run: python -m src.webdata && python -m src.web
Layout of web/dist:
  index.html, app.css, js/            the modular front end (web/app, vanilla ES modules, hash router)
  data/*.json                         browser aggregates from src.webdata (no row-level records)
  data/docs/*.md                      limitations and economic interpretation (rendered in Methodology)
  charts/*.png, downloads/, reports/  pipeline figures, submission PDFs, per-rule evidence reports
  vercel.json, robots.txt, .vercelignore
"""
from __future__ import annotations
import json, shutil
from .config import ROOT, EVIDENCE, CHARTS, FINDINGS

WEB = ROOT / "web"; DIST = WEB / "dist"; APP = WEB / "app"; BUILD = WEB / "build_data"
DATA_FILES = ["explorer", "institutions", "meta", "registry", "routes", "sim", "temporal", "tests", "tokens", "replay", "ledger", "genome"]


def main():
    link = (DIST / ".vercel" / "project.json").read_text() if (DIST / ".vercel" / "project.json").exists() else None
    missing = [f for f in DATA_FILES if not (BUILD / f"{f}.json").exists()]
    if missing:
        raise SystemExit(f"web/build_data is missing {missing}: run python -m src.webdata first")
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(APP, DIST)
    (DIST / "data" / "docs").mkdir(parents=True)
    for f in DATA_FILES:
        shutil.copy(BUILD / f"{f}.json", DIST / "data" / f"{f}.json")
    for f in ("limitations.md", "economic_interpretation.md"):
        shutil.copy(FINDINGS / f, DIST / "data" / "docs" / f)
    (DIST / "charts").mkdir(); (DIST / "downloads").mkdir(); (DIST / "reports").mkdir()
    for p in CHARTS.glob("*.png"):
        shutil.copy(p, DIST / "charts" / p.name)
    for f in ("dashboard.pdf", "presentation.pdf", "ORVANTA_Comprehensive_Research_Report.pdf", "ORVANTA_Comprehensive_Research_Report.md"):
        if (ROOT / "submission" / f).exists():
            shutil.copy(ROOT / "submission" / f, DIST / "downloads" / f)
    shutil.copy(FINDINGS / "validation_report.md", DIST / "downloads" / "validation_report.md")
    for f in (EVIDENCE / "reports").glob("*.md"):
        shutil.copy(f, DIST / "reports" / f.name)
    (DIST / "vercel.json").write_text(json.dumps({
        "headers": [
            {"source": "/(.*)", "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow"},
                                            {"key": "X-Content-Type-Options", "value": "nosniff"},
                                            {"key": "Referrer-Policy", "value": "no-referrer"},
                                            {"key": "X-Frame-Options", "value": "DENY"},
                                            {"key": "Content-Security-Policy", "value": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'"}]},
            {"source": "/reports/(.*)", "headers": [{"key": "Content-Type", "value": "text/markdown; charset=utf-8"}]},
            {"source": "/data/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=300"}]}]}, indent=1))
    (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    (DIST / ".vercelignore").write_text(".env*\n.gitignore\n.vercel\n")      # never upload CLI tokens or link metadata
    if link:                                                                  # keep the Vercel project link across rebuilds
        (DIST / ".vercel").mkdir(); (DIST / ".vercel" / "project.json").write_text(link)
    files = [p for p in DIST.rglob("*") if p.is_file() and ".vercel" not in p.parts]
    print(f"web/dist built: {len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
