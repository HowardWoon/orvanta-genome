"""Render every dashboard page from outputs/pdf_build/dashboard.html and measure layout quality.

Usage: python scripts/dashboard_audit.py <tag>
Writes docs/dashboard-audit/<tag>/page_NN.png and audit.json with, per page:
  blank_share   share of the content area (inside margins, above the footer) that is plain paper background
  largest_gap   tallest fully blank horizontal band (px at 1536-wide render)
  overflow      content taller/wider than the page box (must be 0)
  min_font_px   smallest rendered text size (readability)
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
tag = sys.argv[1] if len(sys.argv) > 1 else "audit"
OUT = ROOT / "docs" / "dashboard-audit" / tag; OUT.mkdir(parents=True, exist_ok=True)
JS = """(sec) => {
  const r = sec.getBoundingClientRect();
  let minf = 99;
  for (const el of sec.querySelectorAll('*')) { if (el.childNodes.length && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) { const f = parseFloat(getComputedStyle(el).fontSize); if (f && f < minf) minf = f; } }
  const zooms = [...sec.querySelectorAll('[data-zoom]')].map(e => +e.dataset.zoom); const foot = sec.querySelector('.foot').getBoundingClientRect().top; const lowest = Math.max(...[...sec.querySelectorAll('.lc > *, .cg > *, .tri > div > *, h1, .sub')].map(e => e.getBoundingClientRect().bottom)); return {overflow: [sec.scrollHeight - sec.clientHeight, sec.scrollWidth - sec.clientWidth], footer_clearance_px: Math.round(foot - lowest), zoom: zooms.length ? Math.min(...zooms) : 1, min_font_px: minf, h: r.height, w: r.width};
}"""
res = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1536, "height": 864}, device_scale_factor=1)
    pg.goto((ROOT / "outputs" / "pdf_build" / "dashboard.html").as_uri()); pg.wait_for_function("document.body.dataset.fitted === '1'"); pg.wait_for_timeout(300)
    secs = pg.locator("section.pg")
    from PIL import Image
    import numpy as np
    for i in range(secs.count()):
        el = secs.nth(i); m = el.evaluate(JS)
        f = OUT / f"page_{i + 1:02d}.png"; el.screenshot(path=str(f))
        a = np.asarray(Image.open(f).convert("RGB")).astype(int)
        H, W, _ = a.shape; y0, y1, x0, x1 = int(H * .14), int(H * .94), int(W * .035), int(W * .965)   # below the header rule, above the footer
        body = a[y0:y1, x0:x1]
        paper = (abs(body[..., 0] - 245) < 6) & (abs(body[..., 1] - 240) < 6) & (abs(body[..., 2] - 230) < 8)
        rows = paper.mean(axis=1) > .985
        gap = run = 0
        for r_ in rows: run = run + 1 if r_ else 0; gap = max(gap, run)
        m.update(page=i + 1, blank_share=round(float(paper.mean()), 3), largest_gap=int(gap))
        res.append(m); print(m)
    b.close()
(OUT / "audit.json").write_text(json.dumps(res, indent=1))
