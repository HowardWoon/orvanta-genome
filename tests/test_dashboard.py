"""Headless functional tests of the Synthetic Rule Intelligence Lab (every page renders; every control does what it claims)."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "dashboard" / "app.py")
pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

need = pytest.mark.skipif(not (ROOT / "outputs" / "evidence" / "atlas.json").exists(), reason="run the pipeline first")
PAGES = ["Lab Overview", "Dataset Observatory", "Transaction Workbench", "Discovery Engine", "Forensics Lab", "Rule Explorer", "Dependency Atlas",
         "Route Observatory", "Validation Centre", "Anomaly Intelligence", "Methodology & Lineage"]
FILTER_PAGES = {"Transaction Workbench", "Anomaly Intelligence"}


def go(page):
    at = AppTest.from_file(APP, default_timeout=180).run()
    at.sidebar.radio(key="nav").set_value(page).run()
    return at


def kpi(at, label):
    return [m.value for m in at.markdown if f"<span>{label}</span>" in m.value][0]


@need
@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders(page):
    at = go(page)
    assert not at.exception, at.exception
    assert len(at.title) >= 1


@need
@pytest.mark.parametrize("page", PAGES)
def test_filters_only_where_they_act(page):
    at = go(page)
    assert ("f_tt" in {w.key for w in at.sidebar.multiselect}) == (page in FILTER_PAGES)


@need
def test_filter_changes_figures_and_reset_restores():
    at = go("Transaction Workbench")
    assert "10,000,000" in kpi(at, "payments in filter")
    at.multiselect(key="f_an").set_value(["ROMANCE_SCAM"]).run()
    assert "2,476" in kpi(at, "payments in filter")
    at.sidebar.button[0].click().run()
    assert "10,000,000" in kpi(at, "payments in filter")


@need
def test_filters_survive_page_navigation():
    at = go("Transaction Workbench")
    at.multiselect(key="f_an").set_value(["CEO_SCAM"]).run()
    at.sidebar.radio(key="nav").set_value("Rule Explorer").run()
    at.sidebar.radio(key="nav").set_value("Transaction Workbench").run()
    assert at.multiselect(key="f_an").value == ["CEO_SCAM"]
    assert "945" in kpi(at, "payments in filter")


@need
def test_empty_filter_shows_empty_state():
    at = go("Anomaly Intelligence")
    at.multiselect(key="f_tt").set_value([]).run()
    assert not at.exception and any("selects no payments" in w.value for w in at.warning)


@need
def test_rule_explorer_search_filter_and_report():
    at = go("Rule Explorer")
    at.text_input(key="rx_q").set_value("currency").run()
    ids = {o.split(" · ")[0] for o in at.selectbox(key="rx_pick").options}
    assert {"C1", "C2", "C3"} <= ids
    at.selectbox(key="rx_pick").set_value("C3").run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    for field in ("Explicit rule", "Mathematical / computational logic", "Sample size", "Effect size", "Validation", "Counterexamples", "Limitations", "Economic interpretation"):
        assert field in md, field
    assert any(b.label.startswith("Download evidence report") for b in at.get("download_button"))


@need
def test_rule_explorer_empty_state():
    at = go("Rule Explorer")
    at.text_input(key="rx_q").set_value("zzzz-no-such-rule").run()
    assert not at.exception and any("No rule matches" in m.value for m in at.markdown)


@need
def test_overview_button_opens_rule_in_explorer():
    at = AppTest.from_file(APP, default_timeout=180).run()
    next(b for b in at.button if b.label == "Open C3 in Rule Explorer").click().run()
    assert at.sidebar.radio(key="nav").value == "Rule Explorer"
    assert at.selectbox(key="rx_pick").value == "C3"


@need
def test_atlas_focus_filters_edges_and_links_to_rules():
    at = go("Dependency Atlas")
    at.selectbox(key="at_focus").set_value("CURRENCY_CODE").run()
    assert not at.exception
    rules = {o.split(" · ")[0] for o in at.selectbox(key="at_rule").options}
    assert {"C1", "C3"} <= rules
    at.selectbox(key="at_rule").set_value("C3").run()
    at.button(key="at_go").click().run()
    assert at.sidebar.radio(key="nav").value == "Rule Explorer" and at.selectbox(key="rx_pick").value == "C3"


@need
def test_discovery_target_selector():
    at = go("Discovery Engine")
    at.selectbox(key="de_target").set_value("fx_conversions").run()
    assert not at.exception


@need
def test_route_explorer_filters_patterns():
    at = go("Route Observatory")
    before = kpi(at, "patterns")
    at.selectbox(key="rx_cc").set_value("US").run()
    assert not at.exception and kpi(at, "patterns") != before
