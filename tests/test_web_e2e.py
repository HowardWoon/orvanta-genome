"""Browser end-to-end tests of the static web edition (Playwright + the system's Microsoft Edge; no browser download).

Covers: every route renders without errors, URL state survives refresh/back/forward, explorer numbers equal an independent Python
re-aggregation of the cube, empty states, reset, simulator calibration and scenario labelling, atlas tracing/zoom, live rule search,
JS ↔ Python rule-library parity, the 404 route, and phone-width layout without horizontal scrolling.
"""
from __future__ import annotations
import json, socket, subprocess, sys, time
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
pw = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.skipif(not (DIST / "index.html").exists(), reason="run python -m src.web first")
sys.path.insert(0, str(ROOT))
from src import rulelib  # noqa: E402


@pytest.fixture(scope="module")
def base():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(DIST)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close(); break
        except OSError:
            time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    proc.terminate()


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            try:
                b = p.chromium.launch(headless=True)
            except Exception as e:  # pragma: no cover
                pytest.skip(f"no browser available: {e}")
        yield b
        b.close()


@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport={"width": 1366, "height": 900})
    pg = ctx.new_page()
    pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
    yield pg
    ctx.close()


def go(pg, base, route):
    pg.goto(f"{base}/#/{route}")
    wait(pg, route.split("?")[0])


def wait(pg, path):
    pg.wait_for_function("p => document.querySelector('main').dataset.path === p && !document.querySelector('main .loading') && document.querySelector('main .crumbs')", arg=path, timeout=30000)
    pg.wait_for_timeout(150)


def routes():
    js = (DIST / "js" / "main.js").read_text(encoding="utf-8")
    import re
    return re.findall(r"\['([a-z/]+)', '[^']+', '[a-z]+', '[A-Z]+'\]", js)


def test_every_route_renders(page, base):
    rs = routes()
    assert len(rs) >= 45
    for r in rs:
        go(page, base, r)
        main = page.locator("main")
        assert main.locator(".err").count() == 0, r
        txt = main.inner_text()
        assert "NaN" not in txt and "undefined" not in txt and "[object" not in txt, r
        assert len(txt) > 300, r
    assert not page.errors, page.errors


def test_404_route(page, base):
    page.goto(f"{base}/#/no/such/page")
    page.wait_for_selector("text=Page not found")


def _cube_n(filters):
    ex = json.loads((DIST / "data" / "explorer.json").read_text(encoding="utf-8"))
    ix = {c: i for i, c in enumerate(ex["cols"])}
    return sum(r[ix["n"]] for r in ex["rows"] if all(str(r[ix[d]]) in v for d, v in filters.items()))


def _kpi(pg, label_part):
    return pg.locator(".kpi", has_text=label_part).first.locator("b").inner_text()


def test_explorer_matches_python_and_state_survives_reload(page, base):
    go(page, base, "lab/explorer")
    page.click("button.chip[data-d='otype'][data-v='C']")
    page.click("button.chip[data-d='btype'][data-v='B']")
    expect = _cube_n({"otype": {"C"}, "btype": {"B"}})
    assert _kpi(page, "payments") == f"{expect:,}"
    assert "otype=C" in page.url and "btype=B" in page.url
    page.reload(); wait(page, "lab/explorer")
    assert page.locator("button.chip[data-d='otype'][data-v='C']").get_attribute("aria-pressed") == "true"
    assert _kpi(page, "payments") == f"{expect:,}"
    # comparison statistics are present and finite
    assert page.locator("text=Amount ratio A/B").count() == 1
    # empty state: Direct payments never have 3 participants (R1/R6)
    page.click("button.chip[data-d='ttype'][data-v='Direct']")
    page.click("button.chip[data-d='pc'][data-v='3']")
    page.wait_for_selector(".empty")
    page.click("#ereset")
    assert _kpi(page, "payments") == "10,000,000"
    assert not page.errors, page.errors


def test_back_forward_restore_routes(page, base):
    go(page, base, "overview")
    page.click("a.ni[data-r='rules/registry']"); wait(page, "rules/registry")
    page.click("a.ni[data-r='forensics/tests']"); wait(page, "forensics/tests")
    page.go_back(); wait(page, "rules/registry")
    page.go_back(); wait(page, "overview")
    page.go_forward(); wait(page, "rules/registry")


def test_simulator_calibrated_and_scenarios_labelled(page, base):
    go(page, base, "lab/simulator")
    meta = json.loads((DIST / "data" / "meta.json").read_text(encoding="utf-8"))
    rt = {x["k"]: x["n"] for x in meta["distributions"]["Routing type"]}
    obs_direct = rt["Direct"] / 1e7
    sim_direct = float(_kpi(page, "Direct (sim)").rstrip("%")) / 100
    assert abs(sim_direct - obs_direct) < 0.01
    assert page.locator("text=Parameters at their estimates").count() == 1
    page.locator("#rq").fill("0.6"); page.locator("#rq").dispatch_event("input")
    page.wait_for_selector("text=Parameters moved away from the estimates")
    assert float(_kpi(page, "Direct (sim)").rstrip("%")) / 100 < 0.45
    for tab in ("amount", "duration"):
        page.click(f"#stabs .chip[data-t='{tab}']")
        page.wait_for_selector(".kpi", timeout=10000)
        assert page.locator("text=KS").count() >= 1
    assert not page.errors, page.errors


def test_atlas_trace_focus_zoom(page, base):
    go(page, base, "rules/atlas")
    vb0 = page.locator("#asvg").get_attribute("viewBox")
    page.click("#zi")
    assert page.locator("#asvg").get_attribute("viewBox") != vb0
    page.click("g.node[data-id='path']")
    page.wait_for_selector("#ap .card.y")
    assert "BIC8_PATH" in page.locator("#ap .card.y").inner_text()
    assert "node=path" in page.url
    page.fill("#ar", "R6")
    page.wait_for_selector("text=Rule R6")
    assert page.locator("#ap tbody tr").count() >= 1
    page.click("#ax")
    assert page.locator("g.node.dim").count() == 0


def test_rule_search_is_live(page, base):
    go(page, base, "rules/explorer")
    page.locator("#rq").press_sequentially("IBAN")
    page.wait_for_function("() => /of 63 entries/i.test(document.querySelector('#rt').innerText) && !/^34 of/i.test(document.querySelector('#rt').innerText)")
    ids = page.locator("#rt tbody tr td:first-child").all_inner_texts()
    assert "P2" in ids and len(ids) < 34


def test_x5_not_significant_after_bh(page, base):
    go(page, base, "forensics/tests?fam=X5")
    page.wait_for_selector("#to .kpi")
    assert _kpi(page, "significant after BH") == "0"


def test_js_rulelib_matches_python(page, base):
    go(page, base, "lab/playground")
    cases = ["0309CHZ0;1022DEA1;...;0004IMD0", "0450USA1;0812USB3", "0001GBA1;...;...;0002FRB2;0003DEC3", "0001GBA1"]
    homes = {"CH": "CHF", "DE": "EUR", "IM": "GBP", "US": "USD", "GB": "GBP", "FR": "EUR"}
    js = page.evaluate("""async ([cases, homes]) => { const R = await import('./js/rulelib.js');
        return cases.map(c => [R.participantCount(c), R.continuityFlag(c), R.fxCount(c, homes), R.pGap(Math.max(R.participantCount(c), 1)), R.hopPmf(2)]); }""", [cases, homes])
    for c, (pc, cont, fx, pg_, hp) in zip(cases, js):
        assert pc == rulelib.participant_count(c)
        assert cont == rulelib.continuity_flag(c)
        assert fx == rulelib.fx_count(c, homes)
        assert abs(pg_ - rulelib.p_gap(max(pc, 1))) < 1e-12 and abs(hp - rulelib.hop_pmf(2)) < 1e-12
    det = "/ACCT\nLINE ONE\nLINE TWO"
    assert page.evaluate("async d => (await import('./js/rulelib.js')).mt4x35ok(d)", det) == rulelib.mt_4x35_ok(det)
    ser = [[0, 120.0], [900, 450.0], [2100, 1800.0], [3600, 5200.0]]
    assert page.evaluate("async s => (await import('./js/rulelib.js')).romanceLike(s)", ser) == rulelib.romance_like([tuple(x) for x in ser])
    page.click("#pbad")
    assert "violates P2" in page.locator("#pout").inner_text()


def test_phone_layout_has_no_horizontal_scroll(browser, base):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
    pg = ctx.new_page()
    for r in ("overview", "lab/explorer", "lab/simulator", "rules/atlas", "rules/explorer", "forensics/tests", "feature/route", "forensics/replay", "foundry/builder", "library/ledger", "tour"):
        go(pg, base, r)
        over = pg.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
        assert over <= 1, (r, over)
    assert not pg.locator("#navwrap").is_visible()
    pg.click("#menu")
    assert pg.locator("#navwrap").is_visible()
    pg.click("a.ni[data-r='deliverables']"); wait(pg, "deliverables")
    assert not pg.locator("#navwrap").is_visible()
    ctx.close()


def test_forensic_replay_shows_exact_counterexamples(page, base):
    go(page, base, "forensics/replay?rule=C2")
    assert _kpi(page, "contradicting") == "2"
    assert page.locator("#ro tbody tr").count() == 2
    page.select_option("#rr", "R6")
    page.wait_for_selector("text=holds without exception")
    page.select_option("#rs", "support")
    assert page.locator("#ro tbody tr").count() >= 10
    assert "rule=R6" in page.url and "side=support" in page.url


def test_rule_builder_runs_and_replicates(page, base):
    go(page, base, "foundry/builder")
    page.wait_for_selector("text=SUPPORTED IN THIS DATA")            # default: pc = 2 has a lower manual share (D1)
    assert page.locator("text=replicates on the independent later period").count() == 1
    page.select_option("#bdir", "higher")
    page.wait_for_selector("text=REVERSED / NOT SUPPORTED")
    page.select_option("#bt", "ttype")
    page.wait_for_selector("text=Cramér's V =")
    assert not page.errors, page.errors


def test_ledger_genealogy_blueprint(page, base):
    go(page, base, "library/ledger?q=C2")
    assert page.locator("#lt2 tbody tr").count() >= 3
    page.fill("#lq", "EV-RULE-001"); page.wait_for_timeout(200)
    assert "EV-RULE-001" in page.locator("#ld").inner_text()
    go(page, base, "genome/genealogy?id=R2")
    assert "H32" in page.locator("#go").inner_text()
    go(page, base, "genome/blueprint")
    assert page.locator("details.fold").count() == 10
    page.select_option("#bl", "VALIDATED")
    assert page.locator("#bo .tag.lv-val").count() >= 6


def test_scenario_pin_compare_and_sensitivity(page, base):
    go(page, base, "lab/simulator")
    page.click("#spin")
    page.locator("#rq").fill("0.5"); page.locator("#rq").dispatch_event("input"); page.wait_for_timeout(400)
    page.click("#spin")
    assert page.locator("#scmp tbody tr").count() == 2
    assert page.locator("#scmp .b-structural-scenario").count() >= 1
    with page.expect_download() as d:
        page.click("#sexp")
    assert d.value.suggested_filename == "scenario_report.md"
    go(page, base, "lab/sensitivity")
    for p_ in ("p", "m", "th"):
        page.select_option("#sp", p_); page.wait_for_timeout(300)
        assert page.locator("#so").inner_text().strip()
    assert not page.errors, page.errors


def test_judge_guided_tour(page, base):
    go(page, base, "overview")
    page.click("a.go[href='#/tour']"); wait(page, "tour")
    body = page.locator("#tbody")
    assert body.locator("tbody tr").count() == 2 and "0000ERA0" in body.inner_text()      # the two C2 exceptions
    assert "9,999,998" in body.inner_text()
    page.click("#tnext"); page.wait_for_timeout(200)
    assert "Cohen's w" in body.inner_text() and "s=2" in page.url
    page.click("#tnext"); page.wait_for_timeout(200)
    assert "H32" in body.inner_text()
    page.click("#tnext"); page.wait_for_selector("#tbody .b-model-simulation")
    assert body.locator("tbody tr").count() == 2                                            # 2 vs 4 participants
    page.reload(); wait(page, "tour")
    assert "From reconstructed rule to scenario" in page.locator("#tbody").inner_text()     # stage survives refresh
    page.go_back()
    assert page.locator("a.ni.jp").count() == 7                                              # judge-facing journey marked in the menu
    assert not page.errors, page.errors


MEASURE = """() => ({over: document.documentElement.scrollWidth - innerWidth,
  giant: [...document.querySelectorAll('main .badge')].filter(b => b.getBoundingClientRect().height > 60).length,
  esc: [...document.querySelectorAll('main *')].filter(el => { const r = el.getBoundingClientRect(); if (!r.width || r.right <= innerWidth + 1) return false;
        for (let p = el.parentElement; p; p = p.parentElement) if (/(auto|scroll|hidden)/.test(getComputedStyle(p).overflowX)) return false; return true; }).length})"""


@pytest.mark.parametrize("vw", [(320, 568), (390, 844), (844, 390), (768, 1024), (1024, 768)])
def test_every_route_fits_viewport(browser, base, vw):
    ctx = browser.new_context(viewport={"width": vw[0], "height": vw[1]}, is_mobile=vw[0] < 768, has_touch=True)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    bad = []
    for r in routes():
        go(pg, base, r)
        m = pg.evaluate(MEASURE)
        if m["over"] > 1 or m["giant"] or m["esc"]:
            bad.append((r, m))
    ctx.close()
    assert not bad, bad
    assert not errs, errs


def test_touch_targets_and_drawer_on_phone(browser, base):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    for r in ("overview", "lab/explorer", "lab/simulator", "forensics/replay", "foundry/builder", "tour"):
        go(pg, base, r)
        small = pg.evaluate("""() => [...document.querySelectorAll('main button, main select, main input:not([type=checkbox]), main .chip, #menu')]
            .filter(c => { const b = c.getBoundingClientRect(); return b.width && b.height && b.height < 40; }).map(c => c.id || c.className || c.tagName)""")
        assert not small, (r, small[:5])
    pg.click("#menu")
    assert pg.evaluate("document.body.classList.contains('navlock')")
    box = pg.locator("#navwrap").bounding_box()
    assert box and box["x"] >= 0 and box["x"] + box["width"] <= 391                       # drawer fits the viewport
    pg.keyboard.press("Escape")
    assert not pg.locator("#navwrap").is_visible() and not pg.evaluate("document.body.classList.contains('navlock')")
    assert pg.evaluate("document.activeElement.id") == "menu"
    ctx.close()


def test_sensitivity_recomputes_and_exposes_values(page, base):
    go(page, base, "lab/sensitivity")
    page.locator("#sv").fill("0.5"); page.locator("#sv").dispatch_event("input")
    assert _kpi(page, "model output at selected value") == "50.00%"                          # Share Direct = 1 − q
    assert page.locator("text=STRUCTURAL SCENARIO").count() >= 1 and "v=0.5000" in page.url
    page.click("#sreset")
    assert page.locator("text=At the estimate the model reproduces").count() == 1
    assert _kpi(page, "selected q") == "0.3677" and _kpi(page, "model output at selected value") == _kpi(page, "model at estimate")
    assert page.locator("details.cdata").count() >= 1                                        # plotted values as a table
    page.select_option("#sp", "p"); page.wait_for_timeout(200)
    assert "%" in _kpi(page, "model output at selected value")
    assert not page.errors, page.errors


def test_feature_evidence_has_no_stretched_label_panels(browser, base):
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}); pg = ctx.new_page()
    for g in ("temporal", "institution", "party", "token", "anomaly", "currency"):
        go(pg, base, f"feature/{g}")
        assert pg.locator("#ev > .badge").count() == 0 and pg.locator("#evhead .badge").count() >= 1
        assert pg.evaluate("[...document.querySelectorAll('main .badge')].every(b => b.getBoundingClientRect().height < 40)")
    ctx.close()
