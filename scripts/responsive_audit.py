"""Responsive audit: every route × the viewport matrix, measured in headless Microsoft Edge (Playwright).

Usage: python scripts/responsive_audit.py <phase> [--shots]
Writes docs/responsive-screenshots/<phase>/audit.json (+ JPEG screenshots with --shots).

Per route and viewport it measures
  doc_overflow   document scrollWidth − viewport width (must be ≤ 1)
  escapees       elements whose box extends past the viewport and that are NOT inside a scroll container (the cause of overflow)
  tiny_svg_text  chart labels rendered below 7 px tall (unreadable)
  small_targets  visible controls under 40 px tall on touch-size viewports (< 900 px wide)
  giant_badges   label badges stretched taller than 60 px (the "empty OBSERVED DATA panel" defect)
  errors         console / page errors
"""
from __future__ import annotations
import json, re, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
MATRIX = [(320, 568), (360, 800), (375, 812), (390, 844), (393, 852), (412, 915), (430, 932), (844, 390), (600, 960), (768, 1024), (820, 1180),
          (1024, 768), (1280, 800), (1366, 768), (1440, 900), (1600, 900), (1920, 1080)]
SHOT_W = {320, 390, 768, 1024, 1440, 1920}
MEASURE = r"""() => {
  const vw = window.innerWidth, out = {doc_overflow: document.documentElement.scrollWidth - vw, escapees: [], tiny_svg_text: 0, small_targets: [], giant_badges: 0};
  const scrolls = el => { for (let p = el.parentElement; p; p = p.parentElement) { const s = getComputedStyle(p); if (/(auto|scroll|hidden)/.test(s.overflowX)) return true; } return false; };
  const name = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
  for (const el of document.querySelectorAll('main *, aside *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    if (r.right > vw + 1 && !scrolls(el) && out.escapees.length < 5) out.escapees.push(name(el) + ' →' + Math.round(r.right - vw) + 'px');
  }
  for (const t of document.querySelectorAll('main svg text')) { const r = t.getBoundingClientRect(); if (r.height && r.height < 7 && r.width) out.tiny_svg_text++; }
  if (vw < 900) for (const c of document.querySelectorAll('main button, main select, main input:not([type=checkbox]), main .chip, aside .ni, #menu')) {
    const r = c.getBoundingClientRect(); if (r.width && r.height && r.height < 40 && out.small_targets.length < 6) out.small_targets.push(name(c) + ' ' + Math.round(r.height) + 'px');
  }
  for (const b of document.querySelectorAll('main .badge')) if (b.getBoundingClientRect().height > 60) out.giant_badges++;
  return out;
}"""


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "audit"; shots = "--shots" in sys.argv
    out_dir = ROOT / "docs" / "responsive-screenshots" / phase; out_dir.mkdir(parents=True, exist_ok=True)
    js = (DIST / "js" / "main.js").read_text(encoding="utf-8")
    routes = re.findall(r"\['([a-z/]+)', '[^']+', '[a-z]+', '[A-Z]+'\]", js)
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(DIST)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1); res = []; t0 = time.time()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel="msedge", headless=True)
            for w, h in MATRIX:
                ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=w < 768, has_touch=w < 1024)
                pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:160])); pg.on("console", lambda m: errs.append(m.text[:160]) if m.type == "error" else None)
                for r in routes:
                    errs.clear()
                    pg.goto(f"http://127.0.0.1:{port}/#/{r}")
                    try:
                        pg.wait_for_function("p => document.querySelector('main').dataset.path === p && !document.querySelector('main .loading') && document.querySelector('main .crumbs')", arg=r, timeout=30000)
                    except Exception:
                        res.append(dict(route=r, w=w, h=h, error="timeout")); continue
                    pg.wait_for_timeout(120)
                    m = pg.evaluate(MEASURE); m.update(route=r, w=w, h=h, errors=list(errs)); res.append(m)
                    if shots and w in SHOT_W:
                        d = out_dir / r.replace("/", "_"); d.mkdir(exist_ok=True)
                        pg.screenshot(path=str(d / f"{w}x{h}.jpg"), type="jpeg", quality=55)
                ctx.close()
                print(f"{w}x{h} done ({time.time()-t0:.0f}s)", flush=True)
            b.close()
    finally:
        srv.terminate()
    (out_dir / "audit.json").write_text(json.dumps(res, indent=0), encoding="utf-8")
    bad = [x for x in res if x.get("error") or x["doc_overflow"] > 1 or x["escapees"] or x["giant_badges"] or x["errors"]]
    print(f"{len(routes)} routes × {len(MATRIX)} viewports = {len(res)} renders; with layout/console defects: {len(bad)}; "
          f"tiny-chart-text renders: {sum(1 for x in res if x.get('tiny_svg_text'))}; small-target renders: {sum(1 for x in res if x.get('small_targets'))}")


if __name__ == "__main__":
    main()
