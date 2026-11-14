"""ORVANTA · Generator Genome (formerly the Synthetic Rule Intelligence Lab) — research workbench (DISCOVER → RECONSTRUCT → VALIDATE → EXPLAIN).

Run:  streamlit run dashboard/app.py
Reads only outputs/: evidence/{validation,register,evidence,graph,stats,discovery,forensics,atlas,lineage}.json and tables/cube_*.parquet.
No raw records, no hard-coded statistics: every figure is computed from those artefacts at render time.
Filters are shown only on pages whose charts they drive (no inert controls).
"""
from __future__ import annotations
import json, math
from pathlib import Path
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from src.levels import level as _lvl  # noqa: E402  six-level scale shared with the PDFs and the web platform
TAB, EVD = ROOT / "outputs" / "tables", ROOT / "outputs" / "evidence"
st.set_page_config(page_title="ORVANTA — Generator Genome", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------------ design tokens (neo-brutalist financial intelligence)
INK, PAPER, WHITE, YELLOW, CORAL, BLUE, GREY = "#111827", "#F5F0E6", "#FFFFFF", "#F4D52E", "#EF5147", "#2479D8", "#747474"
TEAL = "#1F8A70"
DISPLAY = "Bahnschrift, 'Arial Narrow', 'Segoe UI', sans-serif"; BODY = "'Segoe UI', system-ui, sans-serif"; MONO = "Consolas, 'Courier New', monospace"
CONF_COL = {"High": BLUE, "Medium": YELLOW, "Low": GREY}

st.markdown(f"""<style>
html, body, [data-testid="stAppViewContainer"], .main {{ background:{PAPER} !important; }}
[data-testid="stHeader"] {{ background:{PAPER}; border-bottom:3px solid {INK}; }}
.block-container {{ padding-top:1.6rem; max-width:1440px; }}
/* ---------- sidebar: ink control panel with numbered nav blocks ---------- */
[data-testid="stSidebar"] {{ background:{INK}; border-right:4px solid {YELLOW}; }}
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{ padding-bottom:0; }}
[data-testid="stSidebarCollapseButton"] span, [data-testid="stSidebarCollapseButton"] svg {{ color:{PAPER} !important; fill:{PAPER} !important; }}
[data-testid="stSidebar"] .brand {{ color:{PAPER}; }}
[data-testid="stSidebar"] .brand span {{ color:{INK}; border-color:{PAPER}; }}
[data-testid="stSidebar"] .mono {{ color:#b9b3a5; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p, [data-testid="stSidebar"] label p {{ color:{PAPER}; font-family:{MONO}; font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; }}
.navhead {{ font-family:{MONO}; font-size:.68rem; letter-spacing:.14em; color:{YELLOW}; text-transform:uppercase; border-top:2px solid #2c3546; padding-top:.7rem; margin:.4rem 0 .4rem; }}
[data-testid="stSidebar"] [role="radiogroup"] {{ counter-reset:nav; gap:6px; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ counter-increment:nav; display:flex; align-items:center; width:100%; margin:0;
  padding:9px 12px; border:2px solid #2c3546; background:#18202f; cursor:pointer; transition:transform .08s ease, background .08s ease; }}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{ display:none; }}
[data-testid="stSidebar"] [role="radiogroup"] label::before {{ content:counter(nav, decimal-leading-zero); font-family:{MONO}; font-size:.72rem; color:#8c96a8;
  margin-right:.75rem; min-width:1.4rem; }}
[data-testid="stSidebar"] [role="radiogroup"] label p {{ font-family:{DISPLAY} !important; font-size:.98rem !important; text-transform:none !important; letter-spacing:0 !important; color:{PAPER} !important; font-weight:600; }}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ border-color:{YELLOW}; transform:translateX(2px); }}
[data-testid="stSidebar"] [role="radiogroup"] label:focus-within {{ outline:2px solid {BLUE}; outline-offset:2px; }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background:{YELLOW}; border-color:{YELLOW}; box-shadow:4px 4px 0 {PAPER}; transform:none; }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p, [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::before {{ color:{INK} !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ position:relative; }}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(1), [data-testid="stSidebar"] [role="radiogroup"] label:nth-child(6),
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(9), [data-testid="stSidebar"] [role="radiogroup"] label:nth-child(11) {{ margin-top:26px !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(1)::after, [data-testid="stSidebar"] [role="radiogroup"] label:nth-child(6)::after,
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(9)::after, [data-testid="stSidebar"] [role="radiogroup"] label:nth-child(11)::after {{
  position:absolute; left:0; top:-21px; font-family:{MONO}; font-size:.66rem; letter-spacing:.16em; color:{YELLOW}; }}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(1)::after {{ content:"▸ 01 DISCOVER"; }}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(6)::after {{ content:"▸ 02 RECONSTRUCT"; }}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(9)::after {{ content:"▸ 03 VALIDATE"; }}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(11)::after {{ content:"▸ 04 EXPLAIN"; }}
.lablog {{ background:{INK}; color:{YELLOW}; font-family:{MONO}; font-size:.8rem; line-height:1.65; border:2.5px solid {INK}; box-shadow:5px 5px 0 {YELLOW};
  padding:12px 16px; margin-bottom:14px; background-image:repeating-linear-gradient(0deg, rgba(255,255,255,.035) 0 1px, transparent 1px 3px); }}
.lablog b {{ color:{PAPER}; }} .lablog .dim {{ color:#9aa3b5; }}
.flow4 {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:0; border:2.5px solid {INK}; box-shadow:5px 5px 0 {INK}; margin-bottom:16px; }}
.flow4 div {{ padding:12px 14px; background:{WHITE}; border-right:2.5px solid {INK}; }} .flow4 div:last-child {{ border-right:0; }}
.flow4 div.on {{ background:{YELLOW}; }} .flow4 b {{ font-family:{DISPLAY}; font-size:1.25rem; display:block; }}
.flow4 span {{ font-family:{MONO}; font-size:.7rem; text-transform:uppercase; letter-spacing:.05em; }}
@media (max-width:900px) {{ .flow4 {{ grid-template-columns:1fr 1fr; }} }}
.atlas {{ background:{WHITE}; border:2.5px solid {INK}; box-shadow:5px 5px 0 {INK}; padding:6px; overflow-x:auto; }}
.sidefoot {{ border:2px solid #2c3546; padding:10px 12px; margin-top:1.2rem; font-family:{MONO}; font-size:.7rem; color:#b9b3a5; letter-spacing:.04em; line-height:1.6; }}
.sidefoot b {{ color:{PAPER}; }} .sidefoot .ok {{ background:{BLUE}; color:{WHITE}; padding:0 5px; font-weight:700; }}
@media (prefers-reduced-motion:reduce) {{ [data-testid="stSidebar"] [role="radiogroup"] label {{ transition:none; }} }}
h1,h2,h3 {{ font-family:{DISPLAY} !important; color:{INK} !important; letter-spacing:-.01em; }}
h1 {{ font-weight:700 !important; }}
p, li, label, .stMarkdown {{ font-family:{BODY}; color:{INK}; }}
.brand {{ font-family:{DISPLAY}; font-weight:700; font-size:1.55rem; line-height:1; color:{INK}; }}
.brand span {{ background:{YELLOW}; padding:0 .25rem; border:2px solid {INK}; }}
.mono {{ font-family:{MONO}; font-size:.78rem; letter-spacing:.06em; text-transform:uppercase; color:#4a4a4a; }}
.card {{ background:{WHITE}; border:2.5px solid {INK}; box-shadow:5px 5px 0 {INK}; padding:14px 16px; margin-bottom:14px; }}
.card.y {{ background:{YELLOW}; }} .card.ink {{ background:{INK}; }} .card.ink, .card.ink * {{ color:{PAPER} !important; }}
.kpi b {{ display:block; font-family:{DISPLAY}; font-size:clamp(1.2rem,1.9vw,1.95rem); line-height:1.05; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; color:{INK}; }}
.kpi span {{ font-family:{MONO}; font-size:.7rem; letter-spacing:.05em; text-transform:uppercase; color:#3a3a3a; }}
.tag {{ display:inline-block; font-family:{MONO}; font-size:.68rem; font-weight:700; letter-spacing:.08em; padding:1px 7px; border:2px solid {INK}; margin-right:6px; }}
.tag.PASS {{ background:{BLUE}; color:{WHITE}; }} .tag.FAIL, .tag.ERROR {{ background:{CORAL}; color:{WHITE}; }}
.tag.lv-validated {{ background:{BLUE}; color:{WHITE}; }} .tag.lv-strongly {{ background:#9cc3ef; color:{INK}; }} .tag.lv-supported {{ background:{YELLOW}; color:{INK}; }} .tag.lv-inconclusive {{ background:#d6d1c4; color:{INK}; }}
.tag.High {{ background:{BLUE}; color:{WHITE}; }} .tag.Medium {{ background:{YELLOW}; color:{INK}; }} .tag.Low {{ background:{WHITE}; color:{INK}; }}
.formula {{ font-family:{MONO}; font-size:.86rem; background:{PAPER}; border:2px dashed {INK}; padding:8px 10px; margin:8px 0; white-space:pre-wrap; }}
.scope {{ font-family:{MONO}; font-size:.7rem; letter-spacing:.06em; text-transform:uppercase; color:#4a4a4a; margin:-4px 0 8px; }}
.sect {{ font-family:{MONO}; font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; background:{INK}; color:{YELLOW}; display:inline-block; padding:3px 9px; margin-bottom:6px; }}
div[data-testid="stDataFrame"] {{ border:2.5px solid {INK}; box-shadow:5px 5px 0 {INK}; }}
.stButton>button {{ border:2.5px solid {INK}; border-radius:0; box-shadow:3px 3px 0 {INK}; background:{YELLOW}; color:{INK}; font-family:{DISPLAY}; font-weight:700; }}
.stButton>button:hover {{ transform:translate(1px,1px); box-shadow:2px 2px 0 {INK}; }}
.stButton>button:focus-visible {{ outline:3px solid {BLUE}; }}
@media (prefers-reduced-motion:reduce) {{ .stButton>button:hover {{ transform:none; }} }}
</style>""", unsafe_allow_html=True)


def _theme():
    return {"config": {"background": WHITE, "view": {"stroke": None}, "font": BODY,
                       "axis": {"labelColor": INK, "titleColor": INK, "domainColor": INK, "domainWidth": 1.5, "tickColor": INK, "gridColor": "#ece7dc",
                                "labelFont": BODY, "titleFont": MONO, "titleFontSize": 10, "labelFontSize": 11, "titleFontWeight": "normal"},
                       "legend": {"labelColor": INK, "titleColor": INK, "orient": "top", "labelFont": BODY, "titleFont": MONO, "titleFontSize": 10},
                       "title": {"color": INK, "font": DISPLAY, "fontSize": 15, "anchor": "start", "fontWeight": 700},
                       "range": {"category": [BLUE, YELLOW, TEAL, CORAL, GREY, INK]}}}


try:
    alt.theme.register("rulebook", enable=True)(_theme)
except AttributeError:
    alt.themes.register("rulebook", _theme); alt.themes.enable("rulebook")


@st.cache_data
def load():
    cubes = {n: pd.read_parquet(TAB / f"cube_{n}.parquet") for n in ["main", "amount", "duration", "route", "hour"]}
    for c in cubes.values():
        c["d"] = pd.to_datetime(c["d"])
    rd = lambda f: json.loads((EVD / f).read_text(encoding="utf-8"))
    return (cubes, rd("evidence.json"), rd("validation.json"), rd("register.json"), rd("graph.json"), rd("stats.json"),
            rd("discovery.json"), rd("forensics.json"), rd("atlas.json"), rd("lineage.json"))


CUBES, EV, VA, REG, GR, ST, DI, FO, AT, LI = load()
for _r in REG:
    _r["level"] = _lvl(_r["id"], _r["confidence"]); _r["lvcls"] = "lv-" + _r["level"].split()[0].lower()
RULES = {r["id"]: r for r in REG}
fmt = lambda x, d=0: f"{x:,.{d}f}"


def card(html, cls=""):
    st.markdown(f"<div class='card {cls}'>{html}</div>", unsafe_allow_html=True)


def kpis(items, cls=""):
    cols = st.columns(len(items))
    for c, (v, lab) in zip(cols, items):
        c.markdown(f"<div class='card kpi {cls}'><b>{v}</b><span>{lab}</span></div>", unsafe_allow_html=True)


def section(tag, title, sub=None):
    st.markdown(f"<div class='sect'>{tag}</div>", unsafe_allow_html=True)
    st.title(title)
    if sub:
        st.caption(sub)


def scope(txt):
    st.markdown(f"<div class='scope'>{txt}</div>", unsafe_allow_html=True)


def chart(c, h=280):
    st.altair_chart(c.properties(height=h), width="stretch")


def rule_card(rid, extra=""):
    r = RULES[rid]
    card(f"<span class='tag {r['status']}'>{r['status']}</span><span class='tag {r['lvcls']}'>{r['level']}</span>"
         f"<span class='mono'>{rid} · TYPE {r['type']} · {r['layer']}</span><h3 style='margin:.35rem 0 .1rem'>{r['title']}</h3>"
         f"<div style='font-size:.9rem'><b>Reading:</b> {r['economic']}</div>{extra}"
         f"<div class='mono' style='margin-top:6px'>Acceptance · {r['criterion']}</div>")


# ------------------------------------------------------------------ navigation & filters
st.sidebar.markdown("<div class='brand'>ORVANTA<br><span>GENOME</span></div><div class='mono' style='margin:.55rem 0 .4rem'>Synthetic Financial Intelligence<br>UMDAC Datathon 2026 · Swift case</div>",
                    unsafe_allow_html=True)
PAGES = ["Lab Overview", "Dataset Observatory", "Transaction Workbench", "Discovery Engine", "Forensics Lab",      # DISCOVER
         "Rule Explorer", "Dependency Atlas", "Route Observatory",                                                   # RECONSTRUCT
         "Validation Centre", "Anomaly Intelligence",                                                                # VALIDATE
         "Methodology & Lineage"]                                                                                    # EXPLAIN
NUMBERED = {p_: f"{i + 1:02d}  {p_}" for i, p_ in enumerate(PAGES)}
page = st.sidebar.radio("Section", PAGES, label_visibility="collapsed", key="nav", format_func=lambda x: x)
FILTER_PAGES = {"Transaction Workbench", "Anomaly Intelligence"}


def goto(target_page, rule=None):
    """on_click callback: jump to another page (and optionally open a rule) before the next run."""
    st.session_state["nav"] = target_page
    if rule:
        st.session_state["rx_pick"] = rule

m0 = CUBES["main"]; dmin, dmax = m0.d.min().date(), m0.d.max().date()
DEFAULTS = {"f_dr": (dmin, dmax), "f_tt": sorted(m0.ttype.unique()), "f_an": sorted(m0.anom.unique(), key=lambda a: (a != "NORMAL", a)),
            "f_cu": sorted(m0.curg.unique()), "f_ot": ["B", "C"], "f_bt": ["B", "C"]}
for k, v in DEFAULTS.items():
    # Streamlit drops a keyed widget's state on any run where the widget is not drawn (non-filter pages).
    # Re-assigning the key every run keeps filter choices alive across page changes (documented workaround).
    st.session_state[k] = st.session_state[k] if k in st.session_state else v
if page in FILTER_PAGES:
    st.sidebar.markdown("<div class='navhead' style='margin-top:1rem'>Filters · drive every chart on this page</div>", unsafe_allow_html=True)
    if st.sidebar.button("Reset filters"):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
    st.sidebar.date_input("Date range (UTC)", min_value=dmin, max_value=dmax, key="f_dr")
    st.sidebar.multiselect("Routing type", DEFAULTS["f_tt"], key="f_tt")
    st.sidebar.multiselect("Anomaly label", DEFAULTS["f_an"], key="f_an")
    st.sidebar.multiselect("Currency (top 12 + Other)", DEFAULTS["f_cu"], key="f_cu")
    a_, b_ = st.sidebar.columns(2)
    a_.multiselect("Sender", ["B", "C"], key="f_ot"); b_.multiselect("Receiver", ["B", "C"], key="f_bt")


def filt(df):
    s = st.session_state; dr = s["f_dr"]
    d0, d1 = (dr if isinstance(dr, (list, tuple)) and len(dr) == 2 else (dmin, dmax))
    return df[(df.d >= pd.Timestamp(d0)) & (df.d <= pd.Timestamp(d1)) & df.ttype.isin(s.f_tt) & df.anom.isin(s.f_an)
              & df.curg.isin(s.f_cu) & df.otype.isin(s.f_ot) & df.btype.isin(s.f_bt)]


F = {k: filt(v) for k, v in CUBES.items()}
N = int(F["main"].n.sum())


def need_data():
    if N == 0:
        card("<b>No payments match the current filters.</b><br>Widen the date range or add categories in the sidebar, or press <b>Reset filters</b>.", "y")
        st.warning("The current filter selects no payments.")
        st.stop()


n_pass = sum(r["status"] == "PASS" for r in REG)
st.sidebar.markdown(f"<div class='sidefoot'><span class='ok'>{n_pass}/{len(REG)} PASS</span> validators · 5 splits<br>"
                    f"<b>10,000,000</b> payments · 0 dropped<br>validated {VA['generated'].replace('T', ' ')}<br>independent prototype · not affiliated with Swift</div>",
                    unsafe_allow_html=True)

# ================================================================== PAGES
if page == "Dataset Observatory":
    section("DISCOVER · data foundation", "Dataset observatory", "What the raw file is, how it was parsed, and what had to be decided before any rule was tested.")
    xc = VA["cross_check"]
    kpis([("4.61 GiB", "raw CSV, read-only"), ("21 → 20", "columns (DISCLAIMER: 1 non-empty row)"), ("93 days", "30 Apr – 31 Jul 2023 UTC"),
          ("0", "missing or invalid numeric values"), (f"{xc['C2_python_match']:.0%}", "SQL vs Python agreement")])
    dd = pd.DataFrame(EV["daily"]); dd["weekend"] = dd.dow.isin([0, 6])
    chart(alt.Chart(dd, title="Timestamp coverage: payments per UTC day").mark_bar(stroke=INK, strokeWidth=.5).encode(
        x=alt.X("d:T", title=None), y=alt.Y("n:Q", title="PAYMENTS"), color=alt.Color("weekend:N", scale=alt.Scale(domain=[False, True], range=[BLUE, YELLOW]), title="Weekend"),
        tooltip=["d:T", alt.Tooltip("n:Q", format=",")]), 230)
    st.subheader("Field dictionary")
    st.dataframe(pd.DataFrame([
        ["EPOCH_SECONDS", "Unix time UTC", "2023-04-30 11:22 → 2023-07-31 09:56", "T1, T3, T4"], ["CURRENCY_CODE", "ISO 4217", "85 codes; EUR 32%, USD 17%", "C1"],
        ["USD_AMOUNT", "USD-normalised amount", "0.01 – 15.66bn; lognormal", "A1–A3, X3"], ["ORDERING_BIC8 / BENEFICIARY_BIC8", "BIC8 NNNN·CC·LL", "8.4k / 8.3k banks", "R5, R5b, G1"],
        ["BIC8_PATH", "';'-separated route", "'...' = hidden segment", "R1–R7, C2, G3"], ["TOTAL_DURATION", "elapsed seconds", "2 – 21,649; bimodal", "D1–D3"],
        ["CONTINUITY_QFLAG", "Y/N observability", "N ⇔ '...' in path", "R7"], ["CURRENCY_CONVERSION_COUNT", "FX steps", "0–17; = currency borders", "C2"],
        ["PARTICIPANT_COUNT", "institutions", "2–22; = known BICs", "R6, R1"], ["TRANSACTION_TYPE_CODE", "Direct/Indirect/Covered", "63.2 / 32.6 / 4.2%", "R1, R2"],
        ["ORDERING/BENEFICIARY_ACCOUNT", "_FAKE_ id", "IBAN or local format", "P2"], ["*_DETAILS / *_TOKENS", "party text / token patterns", "MT 4×35 layout", "P1b, P2, P4"],
        ["ORDERING_TYPE / BENEFICIARY_TYPE", "B / C", "78.7% / 28.8% business", "A1, P1b"], ["ANOMALY_TYPE", "label", "7,006 labelled; 6 values (1 undocumented)", "X1–X6"],
    ], columns=["Field", "Meaning", "Observed", "Rules"]), hide_index=True, width="stretch")
    st.subheader("Issues log")
    st.dataframe(pd.DataFrame([
        ["Multi-line quoted text", "all rows", "RFC-4180 parser; count asserted at every stage"], ["DISCLAIMER column", "1 row", "dropped; row kept"],
        ["CUSTOMER_RECALL absent from case appendix", "317 rows", "kept; tested (X5, negative)"], ["Path endpoint ≠ header BIC", "≈9.7% rows", "explained by R5/R5b"],
        ["Country token missing in details", "≈39%", "BIC country primary"], ["Amount tail to $15.7bn", "tail", "ln modelling; tail tested (A3)"],
        ["Start time 11:40 (Handbook) vs 11:50 (Rules)", "documents", "deadline 12:00 PM 19 Nov treated as binding"],
    ], columns=["Issue", "Scale", "Decision"]), hide_index=True, width="stretch")

elif page == "Transaction Workbench":
    section("DISCOVER · filter-aware", "Transaction workbench", "Explore the raw distributions behind the rules: every chart re-aggregates the additive cubes (exact, 10,000,000 rows).")
    need_data(); mm = F["main"]
    kpis([(fmt(N), "payments in filter"), (f"${math.exp(mm.s_lnamt.sum() / N):,.0f}", "geometric-mean amount"), (f"{mm.n_slow.sum() / N:.1%}", "with a manual step"),
          (f"{mm.s_fx.sum() / N:.2f}", "mean FX conversions"), (f"{mm.n_gap.sum() / N:.1%}", "paths with hidden hops")])
    scope(f"Filter-aware · {N:,} payments")
    c1, c2 = st.columns(2)
    with c1:
        seg = mm.assign(seg=lambda x: x.otype + "→" + x.btype).groupby("seg").agg(n=("n", "sum"), s=("s_lnamt", "sum")).reset_index()
        seg["observed"] = seg.s / seg.n; seg["rule A1"] = 6 + 2 * seg.seg.str[0].eq("B") + 2 * seg.seg.str[-1].eq("B")
        chart(alt.Chart(seg.melt("seg", ["observed", "rule A1"]), title="Mean ln(amount): observed vs rule A1").mark_bar(stroke=INK, strokeWidth=1.5).encode(
            x=alt.X("seg:N", title="SENDER→RECEIVER", sort=["C→C", "B→C", "C→B", "B→B"]), xOffset="variable:N", y=alt.Y("value:Q", title="MEAN LN(USD)"),
            color=alt.Color("variable:N", scale=alt.Scale(domain=["observed", "rule A1"], range=[BLUE, YELLOW]), title=None),
            tooltip=["seg", "variable", alt.Tooltip("value:Q", format=".3f")]))
    with c2:
        du = F["duration"].groupby("dur_bin", as_index=False).n.sum(); du["mode"] = np.where(du.dur_bin >= 7, "manual", "straight-through")
        chart(alt.Chart(du, title="Duration: seconds vs ~20-minute mode").mark_bar(stroke=INK, strokeWidth=1).encode(
            x=alt.X("dur_bin:O", title="LOG2 SECONDS (4=16s · 7=128s · 10=17min)"), y=alt.Y("n:Q", title="PAYMENTS"),
            color=alt.Color("mode:N", scale=alt.Scale(domain=["straight-through", "manual"], range=[BLUE, YELLOW]), title=None), tooltip=["dur_bin", alt.Tooltip("n:Q", format=",")]))
    c3, c4 = st.columns(2)
    with c3:
        h = F["hour"].groupby(["otype", "lh"], as_index=False).n.sum(); h["share"] = h.n / h.groupby("otype").n.transform("sum")
        chart(alt.Chart(h, title="Local clock of the instructing bank (rule T1)").mark_line(strokeWidth=2.5).encode(
            x=alt.X("lh:O", title="LOCAL HOUR"), y=alt.Y("share:Q", axis=alt.Axis(format="%"), title="SHARE"),
            color=alt.Color("otype:N", scale=alt.Scale(domain=["B", "C"], range=[BLUE, CORAL]), title="Sender"), tooltip=["otype", "lh", alt.Tooltip("share:Q", format=".2%")]))
    with c4:
        cm = mm.groupby("curg", as_index=False).n.sum()
        chart(alt.Chart(cm, title="Currency mix").mark_bar(stroke=INK, strokeWidth=1.5, color=BLUE).encode(
            y=alt.Y("curg:N", sort="-x", title=None), x=alt.X("n:Q", title="PAYMENTS"), tooltip=["curg", alt.Tooltip("n:Q", format=",")]))
    r = F["route"].groupby(["pc", "fx"], as_index=False).n.sum(); r = r[r.pc <= 7]; r["share"] = r.n / r.groupby("pc").n.transform("sum")
    chart(alt.Chart(r, title="FX conversions never exceed hops (rule C2)").mark_rect(stroke=INK, strokeWidth=.5).encode(
        x=alt.X("pc:O", title="PARTICIPANT COUNT"), y=alt.Y("fx:O", sort="descending", title="FX"), color=alt.Color("share:Q", scale=alt.Scale(range=[WHITE, BLUE]), legend=alt.Legend(format="%")),
        tooltip=["pc", "fx", alt.Tooltip("n:Q", format=","), alt.Tooltip("share:Q", format=".1%")]), 230)

elif page == "Route Observatory":
    section("RECONSTRUCT · graph", "Payment route observatory", "The payment set as a directed pseudograph: banks are nodes, observed hops are edges ('...' removed, parallel edges and loops kept).")
    nw, cn = GR["network"], GR["concentration"]
    kpis([(fmt(nw["nodes"]), "banks (nodes)"), (fmt(nw["edges"]), "distinct directed edges"), (fmt(nw["hops"]), "observed hops"),
          (f"{cn['gini_strength']:.2f}", "Gini of bank volume"), (f"{cn['top1pct_share']:.0%}", "volume through top 1% banks")])
    rule_card("G3", f"<div class='formula'>P(intermediary = b) ∝ size(b)^β, β = {RULES['G3']['metrics']['full']['beta']:.3f} · drawn with replacement → loop rate = 1 − Π(1 − j·Σp²)</div>")
    lp = pd.DataFrame(GR["G3_loops"]).melt("pc", ["obs_inter_repeat", "pred_iid"]).replace({"obs_inter_repeat": "observed", "pred_iid": "predicted (i.i.d. draws)"})
    c1, c2 = st.columns(2)
    with c1:
        chart(alt.Chart(lp, title="Path loops predicted from the size distribution").mark_line(point=alt.OverlayMarkDef(size=60, filled=True), strokeWidth=2.5).encode(
            x=alt.X("pc:O", title="PARTICIPANT COUNT"), y=alt.Y("value:Q", axis=alt.Axis(format="%"), title="PATHS REVISITING AN INTERMEDIARY"),
            color=alt.Color("variable:N", scale=alt.Scale(range=[BLUE, CORAL]), title=None), tooltip=["pc", "variable", alt.Tooltip("value:Q", format=".4f")]))
    with c2:
        cc = pd.DataFrame(GR["strength_ccdf"])
        chart(alt.Chart(cc, title="Bank volume is heavy-tailed (CCDF, log–log)").mark_line(point=True, color=INK, strokeWidth=2).encode(
            x=alt.X("s:Q", scale=alt.Scale(type="log"), title="BANK HOP VOLUME"), y=alt.Y("p:Q", scale=alt.Scale(type="log"), title="P(VOLUME ≥ X)"),
            tooltip=[alt.Tooltip("s:Q", format=","), alt.Tooltip("p:Q", format=".4f")]))
    gp = GR["G1_pairing"]
    rule_card("G1", f"<div class='formula'>χ²/dof vs independent pairing: raw {gp['chi2_per_dof']:.0f} · unique relationships {gp['chi2_per_dof_unique_relationships']:.0f} · within country pair {gp['chi2_per_dof_given_country_pair']:.0f} — independence rejected</div>")
    c3, c4 = st.columns(2)
    with c3:
        sc = pd.DataFrame(GR["G1_scatter"]); line = pd.DataFrame({"E": [sc.E.min(), sc.E.max()]}); line["n"] = line.E
        chart(alt.Chart(sc, title="Bank-pair counts vs independence expectation").mark_circle(size=14, opacity=.45, color=BLUE).encode(
            x=alt.X("E:Q", scale=alt.Scale(type="log"), title="EXPECTED IF INDEPENDENT"), y=alt.Y("n:Q", scale=alt.Scale(type="symlog"), title="OBSERVED PAYMENTS")) +
            alt.Chart(line).mark_line(color=CORAL, strokeWidth=2, strokeDash=[6, 4]).encode(x="E:Q", y="n:Q"))
    with c4:
        hs = pd.DataFrame(GR["hub_stp"])
        chart(alt.Chart(hs, title="Hubs are automated: manual-bank share by PageRank decile").mark_bar(stroke=INK, strokeWidth=1.5, color=YELLOW).encode(
            x=alt.X("pr_decile:O", title="PAGERANK DECILE (10 = TOP HUBS)"), y=alt.Y("slow_bank_share:Q", axis=alt.Axis(format="%"), title="MANUAL (NON-STP) BANKS"),
            tooltip=["pr_decile", alt.Tooltip("slow_bank_share:Q", format=".1%"), "banks"]))
    st.subheader("Route explorer")
    scope("Aggregated country-level route patterns (≥200 payments each) · full dataset")
    rp = pd.DataFrame(GR["route_patterns"]); rp["len"] = rp.route.str.count("›") + 1; mx = int(rp.len.max())
    e1, e2, e3 = st.columns([1, 1, 2])
    tsel = e1.selectbox("Routing type", ["All"] + sorted(rp.ttype.unique()), key="rx_type")
    ccs = sorted({c for r_ in rp.route for c in r_.split(" › ")})
    csel = e2.selectbox("Route passes through", ["Any"] + ccs, key="rx_cc")
    hops = e3.slider("Countries on route", 2, mx, (2, mx), key="rx_len")
    v = rp[rp.len.between(*hops)]
    if tsel != "All":
        v = v[v.ttype == tsel]
    if csel != "Any":
        v = v[v.route.str.split(" › ").apply(lambda x: csel in x)]
    if v.empty:
        card("No aggregated route pattern matches. Try another country or widen the route length.", "y")
    else:
        kpis([(fmt(v.n.sum()), "payments on matching patterns"), (fmt(len(v)), "patterns"), (f"{(v.med_dur * v.n).sum() / v.n.sum():,.0f}s", "volume-weighted median duration"),
              (f"{(v.fx * v.n).sum() / v.n.sum():.2f}", "mean FX conversions"), (f"{(v.gap * v.n).sum() / v.n.sum():.1%}", "with hidden hops")])
        st.dataframe(v.rename(columns={"ttype": "Type", "route": "Route (bank countries)", "n": "Payments", "med_dur": "Median s", "fx": "Mean FX", "gap": "Hidden-hop share", "len": "Countries"}).round(3),
                     hide_index=True, width="stretch", height=320)
    fm = pd.DataFrame(GR["flow_matrix_top"])
    chart(alt.Chart(fm, title="Flow matrix, top 12 bank countries").mark_rect(stroke=INK, strokeWidth=.5).encode(
        x=alt.X("b:N", title="RECEIVING BANK COUNTRY"), y=alt.Y("o:N", title="SENDING BANK COUNTRY"), color=alt.Color("n:Q", scale=alt.Scale(type="log", range=[WHITE, BLUE]), title="Payments"),
        tooltip=["o", "b", alt.Tooltip("n:Q", format=",")]), 340)

elif page == "Anomaly Intelligence":
    section("VALIDATE · filter-aware comparison", "Anomaly intelligence", "Six observed labels: three frauds, two operational errors, one undocumented (CUSTOMER_RECALL is not in the official case appendix).")
    need_data()
    mm = F["main"].groupby("anom").agg(n=("n", "sum"), slow=("n_slow", "sum"), lam=("s_lnamt", "sum"), fx=("s_fx", "sum"), dom=("n_dom", "sum"), gap=("n_gap", "sum")).reset_index()
    mm["per 10k in filter"] = mm.n / N * 1e4; mm["geo-mean USD"] = np.exp(mm.lam / mm.n); mm["manual-step share"] = mm.slow / mm.n
    mm["domestic share"] = mm.dom / mm.n; mm["hidden-hop share"] = mm.gap / mm.n; mm["mean FX"] = mm.fx / mm.n
    cls = {"ROMANCE_SCAM": "fraud", "CEO_SCAM": "fraud", "ACCOUNT_REPLACEMENT_SCAM": "fraud", "FAT_FINGER_MISTAKE": "error", "DUPLICATE_PAYMENT": "error", "CUSTOMER_RECALL": "undocumented", "NORMAL": "baseline"}
    mm["class"] = mm.anom.map(cls)
    scope(f"Filter-aware · {N:,} payments · normalised per class so rare labels compare with the baseline")
    st.dataframe(mm[["anom", "class", "n", "per 10k in filter", "geo-mean USD", "manual-step share", "domestic share", "hidden-hop share", "mean FX"]].sort_values("n").round(3),
                 hide_index=True, width="stretch")
    metric = st.selectbox("Compare classes on", ["geo-mean USD", "manual-step share", "domestic share", "hidden-hop share", "mean FX"], key="an_metric")
    chart(alt.Chart(mm, title=f"{metric} by label").mark_bar(stroke=INK, strokeWidth=1.5).encode(
        y=alt.Y("anom:N", sort="-x", title=None), x=alt.X(f"{metric}:Q", title=metric.upper()),
        color=alt.Color("class:N", scale=alt.Scale(domain=["baseline", "fraud", "error", "undocumented"], range=[INK, CORAL, YELLOW, GREY]), title=None),
        tooltip=["anom", alt.Tooltip(f"{metric}:Q", format=".3f"), alt.Tooltip("n:Q", format=",")]), 260)
    st.subheader("Rule-based detectors, evaluated per class")
    scope("Full dataset · precision / recall / F1 and confusion counts · no accuracy reported (classes are 0.003–0.025% of rows)")
    st.dataframe(pd.DataFrame(ST["detectors"])[["label", "detector", "precision", "recall", "f1", "tp", "fp", "fn"]].round(4), hide_index=True, width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        pr = pd.DataFrame(ST["fat_finger_pr_curve"])
        chart(alt.Chart(pr, title=f"Fat finger from amount alone: PR-AUC {ST['fat_finger_pr_auc']:.2f}").mark_line(point=True, color=CORAL, strokeWidth=2).encode(
            x=alt.X("recall:Q", title="RECALL"), y=alt.Y("precision:Q", title="PRECISION"), tooltip=["z", alt.Tooltip("precision:Q", format=".3f"), alt.Tooltip("recall:Q", format=".3f")]))
    with c2:
        ro = pd.DataFrame(EV["romance_steps"]); ro["rule +0.40/step"] = ro.mlog.iloc[0] + .4 * (ro.k - 1)
        chart(alt.Chart(ro.rename(columns={"mlog": "observed"}).melt("k", ["observed", "rule +0.40/step"]), title="Romance scams escalate ×1.5 per payment").mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("k:O", title="PAYMENT # IN SERIES"), y=alt.Y("value:Q", scale=alt.Scale(zero=False), title="MEAN LN(USD)"),
            color=alt.Color("variable:N", scale=alt.Scale(range=[BLUE, CORAL]), title=None)))
    for rid in ["X1", "X2", "X3", "X4", "X5"]:
        rule_card(rid)


# ================================================================== LAB PAGES (appended into app.py by the build patch; not imported)
elif page == "Lab Overview":
    st.markdown("<div class='mono'>ORVANTA · Generator Genome · local research workbench</div>", unsafe_allow_html=True)
    st.title("Decode the rules behind 10 million synthetic payments")
    tri = pd.DataFrame(DI["triage"]); pr = pd.DataFrame(DI["pairs"]); strong = pr[pr.v_dev >= .05]
    n_expl = int(strong.explained_by.notna().sum()); n_med = int((tri.verdict.str.startswith("mediated")).sum()) if len(tri) else 0
    st.markdown(f"""<div class='flow4'>
      <div class='on'><span>01 · Discover</span><b>{len(pr)} feature pairs scanned</b><span>{len(strong)} strong · {len(DI['trees'])} decision-tree searches</span></div>
      <div><span>02 · Reconstruct</span><b>{len(REG)} explicit rules</b><span>typed A–E · formula + logic each</span></div>
      <div><span>03 · Validate</span><b>{n_pass}/{len(REG)} pass 5 splits</b><span>random halves · periods · out-of-sample</span></div>
      <div><span>04 · Explain</span><b>{len(AT['edges'])} atlas edges</b><span>economic reading · limits · lineage</span></div></div>""", unsafe_allow_html=True)
    c2 = RULES["C2"]["metrics"]["full"]; conf = pd.Series([r["level"] for r in REG]).value_counts()
    kpis([("10,000,000", "payments · 0 dropped"), (f"{n_expl}+{n_med}/{len(strong)}", "strong dependencies explained (rule + mediated)"),
          (f"{conf.get('VALIDATED', 0)}·{conf.get('STRONGLY SUPPORTED', 0)}·{conf.get('SUPPORTED', 0)}·{conf.get('INCONCLUSIVE', 0)}", "validated · strong · supported · inconclusive"),
          (f"{(c2['n'] - c2['exceptions']) / c2['n']:.5%}", "FX rule exact match"), ("100%", "SQL vs independent Python")])
    st.markdown(f"""<div class='lablog'><b>LAB LOG</b> <span class='dim'>— what changed our mind</span><br>
      &gt; discovery engine flagged <b>routing_type × sender_country</b> (V = .095, no rule) → <b>R2 revised</b>: Covered is a per-bank propensity, not a constant 11.3%<br>
      &gt; flagged <b>routing_type × home_currency</b> → <b>C3 discovered</b>: currency is drawn from the route ({RULES['C3']['metrics']['full']['in_route_share']:.1%} in a route currency)<br>
      &gt; flagged <b>receiver_type × receiver_bank_country</b> → <b>P5 discovered</b>: customer mix is a bank attribute (split-half r = {RULES['P5']['metrics']['full']['receiver_split_half_r']:.3f})<br>
      &gt; change-point search on weekly levels → <b>T4b</b>: {RULES['T4b']['metrics']['full']['change_points']} change points, <b>all on Mondays</b><br>
      &gt; cents forensics → <b>F1</b>: USD amounts {RULES['F1']['metrics']['full']['usd_whole_share']:.0%} whole-dollar vs {RULES['F1']['metrics']['full']['non_usd_whole_share']:.1%} for converted currencies<br>
      &gt; open: bank-pair affinity mechanism (G1) · weekly level values (T4) · CUSTOMER_RECALL has no signature (X5)</div>""", unsafe_allow_html=True)
    st.subheader("Headline rules")
    cols = st.columns(3)
    for i, rid in enumerate(["C2", "C3", "R1", "G3", "D2", "A1"]):
        r = RULES[rid]
        with cols[i % 3]:
            card(f"<span class='tag {r['lvcls']}'>{rid}</span><span class='mono'>{r['group']}</span><h4 style='font-family:{DISPLAY};margin:.4rem 0'>{r['title']}</h4>"
                 f"<div class='formula'>{r['formulation']}</div><div class='mono'>{r['effect_size']}</div>")
            st.button(f"Open {rid} in Rule Explorer", key=f"ov_{rid}", on_click=goto, args=("Rule Explorer", rid))

elif page == "Discovery Engine":
    section("DISCOVER · automated", "Rule discovery engine",
            f"Every pair of {len(DI['features'])} discretised features scored on a development half and re-scored on an independent validation half "
            f"({DI['dev_rows']:,} + {DI['val_rows']:,} rows); strong pairs are mapped to the rule that explains them or tested for mediation.")
    pr = pd.DataFrame(DI["pairs"]); strong = pr[pr.v_dev >= .05].copy()
    strong["status"] = np.where(strong.explained_by.notna(), "explained by rule", strong.verdict.fillna("open"))
    kpis([(fmt(len(pr)), "feature pairs scanned"), (fmt(len(strong)), "strong (Cramér's V ≥ 0.05)"), (fmt((strong.status == "explained by rule").sum()), "explained by a reconstructed rule"),
          (fmt(strong.status.str.startswith("mediated").sum()), "mediated (composite of rules)"), (fmt(strong.status.str.startswith("open").sum()), "open candidates")])
    hm = pd.concat([pr[["a", "b", "v_dev"]], pr[["b", "a", "v_dev"]].rename(columns={"b": "a", "a": "b"})])
    chart(alt.Chart(hm, title="Dependency map: Cramér's V between features (development half)").mark_rect(stroke=WHITE, strokeWidth=.5).encode(
        x=alt.X("a:N", title=None, axis=alt.Axis(labelAngle=-50, labelFontSize=9)), y=alt.Y("b:N", title=None, axis=alt.Axis(labelFontSize=9)),
        color=alt.Color("v_dev:Q", scale=alt.Scale(range=[WHITE, YELLOW, BLUE, INK], domain=[0, .05, .3, 1]), title="V"),
        tooltip=["a", "b", alt.Tooltip("v_dev:Q", format=".3f")]), 520)
    st.subheader("Strong dependencies and how each is explained")
    st.dataframe(strong[["a", "b", "v_dev", "v_val", "status", "explained_by", "best_mediator", "residual_v"]].rename(columns={
        "a": "Feature A", "b": "Feature B", "v_dev": "V (dev)", "v_val": "V (validation)", "status": "Verdict", "explained_by": "Rule",
        "best_mediator": "Best mediator", "residual_v": "Residual V | mediator"}).round(4), hide_index=True, width="stretch", height=360)
    st.subheader("Decision-tree rule search (depth 3, holdout-scored)")
    tsel = st.selectbox("Target field", [t_["target"] for t_ in DI["trees"]], key="de_target")
    tr = next(t_ for t_ in DI["trees"] if t_["target"] == tsel)
    if "holdout_accuracy" in tr:
        kpis([(f"{tr['holdout_accuracy']:.3f}", "holdout accuracy"), (f"{tr['majority_baseline']:.3f}", "majority baseline"),
              (f"{tr['holdout_accuracy'] - tr['majority_baseline']:+.3f}", "gain over baseline"), (str(len(tr["leaves"])), "candidate rules (leaves)"),
              (tr["top_splits"][0]["feature"] if tr["top_splits"] else "—", "strongest split")])
    else:
        kpis([(f"{tr['holdout_r2']:.3f}", "holdout R²"), (str(len(tr["leaves"])), "candidate rules"), (tr["top_splits"][0]["feature"], "strongest split"), ("A1 / A2", "rules rediscovered"), ("σ ≈ 2.08", "irreducible noise")])
    st.dataframe(pd.DataFrame(tr["leaves"]).round(4), hide_index=True, width="stretch")
    card("Trees are used as a <b>search device</b>, not a predictive model: a candidate counts only if its holdout purity confirms it, and every confirmed leaf is compared with the hand-reconstructed rules "
         "(e.g. <i>participants = 2 ⇒ Direct</i> = R1; the routing ceiling of 0.958 = R1 + R2's coin flip between Covered and Indirect).", "y")

elif page == "Forensics Lab":
    section("DISCOVER · VALIDATE", "Statistical forensics lab", "How were values drawn? Fingerprints, change points, conditional independence, intervals and tails.")
    bf = FO["benford"]; usd = {r["usd_denominated"]: r for r in FO["usd_roundness"]}
    kpis([(f"{bf['nigrini_mad']:.4f}", f"Benford MAD ({bf['conformity']})"), (f"{usd[True]['whole_units']:.1%}", "USD amounts ending .00"),
          (f"{usd[False]['whole_units']:.1%}", "converted currencies ending .00"), (f"w = {FO['second_uniform']['cohen_w']:.4f}", "seconds-of-minute uniform"),
          (f"{FO['bic']['grammar_match']:.0%}", "BIC grammar NNNN·CC·LL")])
    c1, c2 = st.columns(2)
    with c1:
        b = pd.DataFrame(FO["benford"]["digits"]).melt("d", ["observed", "benford"])
        chart(alt.Chart(b, title="First digit of USD_AMOUNT vs Benford").mark_bar(stroke=INK, strokeWidth=1).encode(
            x=alt.X("d:O", title="FIRST DIGIT"), xOffset="variable:N", y=alt.Y("value:Q", axis=alt.Axis(format="%"), title="SHARE"),
            color=alt.Color("variable:N", scale=alt.Scale(domain=["observed", "benford"], range=[BLUE, YELLOW]), title=None)), 260)
    with c2:
        cc = pd.DataFrame(FO["cents00_by_currency"])
        chart(alt.Chart(cc, title="Rule F1: whole-unit share by payment currency").mark_bar(stroke=INK, strokeWidth=1.5).encode(
            y=alt.Y("cur:N", sort="-x", title=None), x=alt.X("cents00:Q", axis=alt.Axis(format="%"), title="AMOUNTS ENDING .00"),
            color=alt.condition("datum.cur == 'USD'", alt.value(YELLOW), alt.value(BLUE)), tooltip=["cur", alt.Tooltip("cents00:Q", format=".2%"), alt.Tooltip("n:Q", format=",")]), 260)
    cp = FO["change_points"]; dly = pd.DataFrame(cp["daily"]); dly["d"] = pd.to_datetime(dly.d)
    segs = pd.DataFrame(cp["segments"]); segs["start"] = pd.to_datetime(segs.start); segs["end"] = pd.to_datetime(segs.end) + pd.Timedelta(days=1); segs["lvl"] = np.log(segs.level)
    chart((alt.Chart(dly, title=f"Rule T4b: {len(cp['change_points'])} change points in weekly volume, all on Mondays (weekday shape removed)").mark_line(color=GREY, point=alt.OverlayMarkDef(size=18, color=INK)).encode(
        x=alt.X("d:T", title=None), y=alt.Y("y:Q", title="LOG DAILY VOLUME (WEEKDAY-ADJUSTED)", scale=alt.Scale(zero=False))) +
           alt.Chart(segs).mark_rule(color=BLUE, strokeWidth=4).encode(x="start:T", x2="end:T", y="lvl:Q", tooltip=["start_weekday", "days", alt.Tooltip("level:Q", format=",.0f")])), 280)
    st.subheader("Conditional-independence tests (feed the Dependency Atlas)")
    st.dataframe(pd.DataFrame(FO["ci_tests"]).round(4), hide_index=True, width="stretch")
    st.subheader("Identifier grammar")
    a, b = st.columns(2)
    with a:
        card(f"<b>BIC8</b>: {FO['bic']['banks']:,} banks in {FO['bic']['countries']} countries; grammar NNNN·CC·LL matches {FO['bic']['grammar_match']:.0%}; "
             f"countries with more than one location code: <b>{FO['bic']['countries_with_multiple_location_codes']}</b>; bank numbers 0–{FO['bic']['max_bank_number']} (sparse).<br>"
             f"<b>IBAN</b>: one length per country in {FO['iban_single_length_share']:.0%} of IBAN countries.")
    with b:
        lt = FO["local_account_templates"]
        card(f"<b>Local account formats</b>: {lt['distinct']:,} character templates; top 10 cover {lt['top10_share']:.0%} → formats are generated per bank/country, not one template.<br>"
             f"<b>Negative result</b>: no fixed FX rate restores round originals for EUR/GBP/CHF (best near-integer share ≈ {max(r['best_near_integer_share'] for r in FO['fixed_rate_search']):.1%} vs ≈1.2% baseline).")
    st.subheader("Intervals, tails and step-time distributions")
    ci = pd.DataFrame([dict(parameter=k, estimate=v["p"], lo95=v["lo"], hi95=v["hi"]) for k, v in ST["ci"].items()])
    st.dataframe(ci.round(5), hide_index=True, width="stretch")
    c3, c4 = st.columns(2)
    with c3:
        qq = pd.DataFrame(ST["amount_residual"]["qq"]); diag = pd.DataFrame({"normal": [-3.2, 3.2], "empirical": [-3.2, 3.2]})
        chart(alt.Chart(qq, title=f"Log-amount residual vs Normal (KS D = {ST['amount_residual']['ks_D_vs_normal']:.4f})").mark_point(size=80, filled=True, color=BLUE, stroke=INK).encode(
            x=alt.X("normal:Q", title="NORMAL QUANTILE"), y=alt.Y("empirical:Q", title="EMPIRICAL (σ)")) + alt.Chart(diag).mark_line(color=INK, strokeDash=[6, 4]).encode(x="normal:Q", y="empirical:Q"), 260)
    with c4:
        hl = pd.DataFrame(ST["hill"])
        chart(alt.Chart(hl, title="Hill tail index drifts → lognormal, not power law").mark_line(point=True, color=INK, strokeWidth=2.5).encode(
            x=alt.X("k:Q", scale=alt.Scale(type="log"), title="TOP-K"), y=alt.Y("alpha:Q", title="HILL α", scale=alt.Scale(zero=False))), 260)
    st.dataframe(pd.DataFrame(ST["sensitivity_D1"]).round(2), hide_index=True, width="stretch")

elif page == "Rule Explorer":
    section("RECONSTRUCT · signature", "Rule explorer", "Search the registry, open a rule, and inspect every piece of evidence behind it.")
    reg = pd.DataFrame(REG)
    q = st.text_input("Search rules (id, title, field, keyword)", key="rx_q", placeholder="e.g. currency, Gamma, C3, mule")
    f1, f2, f3, f4 = st.columns(4)
    lay = f1.multiselect("Feature group", sorted(reg.group.unique()), key="rx_group")
    con_ = f2.multiselect("Confidence level", ["VALIDATED", "STRONGLY SUPPORTED", "SUPPORTED", "INCONCLUSIVE"], key="rx_conf")
    typ = f3.multiselect("Rule type", sorted(reg.type.unique()), key="rx_type", help="A deterministic · B probabilistic · C conditional · D template · E composite")
    stt = f4.multiselect("Status", sorted(reg.status.unique()), key="rx_status")
    v = reg.copy()
    if q:
        ql = q.lower(); v = v[v.apply(lambda r: ql in " ".join(str(r[c]) for c in ("id", "title", "fields", "hypothesis", "formulation", "group")).lower(), axis=1)]
    for col, sel in (("group", lay), ("level", con_), ("type", typ), ("status", stt)):
        if sel:
            v = v[v[col].isin(sel)]
    if v.empty:
        card("No rule matches. Clear the search or filters.", "y")
        st.stop()
    st.dataframe(v[["id", "group", "type", "level", "status", "title"]], hide_index=True, width="stretch", height=250)
    opts = v.id.tolist()
    if st.session_state.get("rx_pick") not in opts:
        st.session_state["rx_pick"] = opts[0]
    rid = st.selectbox("Open rule", opts, format_func=lambda i: f"{i} · {RULES[i]['title']}", key="rx_pick")
    r = RULES[rid]
    a, b = st.columns([3, 2])
    with a:
        card(f"<span class='tag {r['status']}'>{r['status']}</span><span class='tag {r['lvcls']}'>{r['level']}</span>"
             f"<span class='mono'>{rid} · TYPE {r['type']} · {r['group']}</span><h2 style='margin:.4rem 0'>{r['title']}</h2>"
             f"<p><b>Hypothesis.</b> {r['hypothesis']}</p><div class='mono'>Explicit rule</div><div class='formula'>{r['formulation']}</div>"
             f"<div class='mono'>Mathematical / computational logic</div><div class='formula'>{r['logic']}</div>"
             f"<p><b>Fields.</b> {r['fields']}</p><p><b>Method.</b> {r['method']}</p><div class='formula'>ACCEPT IF · {r['criterion']}</div>")
        card(f"<p><b>Counterexamples / exceptions.</b> {r['counterexamples']}</p><p><b>Limitations.</b> {r['limitations']}</p>"
             f"<p><b>Economic interpretation</b> <span class='mono'>(interpretation, not proven by data)</span>. {r['economic']}</p>")
    with b:
        kp = [("Sample size", r["sample_size"]), ("Effect size", r["effect_size"]), ("Validation", r["validation"]), ("Confidence level", r["level"])]
        card("".join(f"<div class='mono'>{k}</div><div style='font-weight:600;margin-bottom:8px'>{v_}</div>" for k, v_ in kp))
        mtr = r["metrics"]
        if isinstance(mtr, dict) and mtr and all(isinstance(v_, dict) for v_ in mtr.values()):
            md = pd.DataFrame(mtr).T
            st.markdown("<div class='mono'>Statistical results by split</div>", unsafe_allow_html=True)
            st.dataframe(md, width="stretch")
            num = [c for c in md.columns if pd.api.types.is_numeric_dtype(md[c]) and md[c].notna().sum() >= 3 and c not in ("n", "n_sample")]
            if num:
                col = st.selectbox("Plot metric across splits", num, key=f"rx_metric_{rid}")
                pdf = md[[col]].dropna().reset_index().rename(columns={"index": "split"})
                chart(alt.Chart(pdf, title=f"{col}: stability across independent splits").mark_bar(stroke=INK, strokeWidth=1.5, color=CONF_COL[r["confidence"]]).encode(
                    x=alt.X("split:N", title=None), y=alt.Y(f"{col}:Q", title=col.upper(), scale=alt.Scale(zero=False)), tooltip=["split", alt.Tooltip(f"{col}:Q", format=".5g")]), 220)
        rep = EVD / "reports" / f"{rid}.md"
        if rep.exists():
            st.download_button("Download evidence report (.md)", rep.read_text(encoding="utf-8"), file_name=f"{rid}_evidence_report.md", mime="text/markdown", key=f"dl_{rid}")
        rel = [e for e in AT["edges"] if rid in e["rules"]]
        if rel:
            nm = {n_["id"]: n_["label"] for n_ in AT["nodes"]}
            card("<div class='mono'>Atlas edges supported by this rule</div>" + "".join(f"<div>{nm[e['source']]} → {nm[e['target']]} <span class='tag'>{e['kind']}</span></div>" for e in rel))
        card(f"<div class='mono' style='color:{YELLOW}'>Trace</div>validator <b>src/rules.py · {rid}</b><br>report findings/validation_report.md<br>run {VA['generated']}", "ink")

elif page == "Dependency Atlas":
    section("RECONSTRUCT · EXPLAIN · signature", "Rule dependency atlas",
            "The reconstructed generator as a dependency map. Edges are generation dependencies consistent with the data — never causal claims. Select a field to trace its rules.")
    nodes = {n_["id"]: n_ for n_ in AT["nodes"]}
    k1, k2 = st.columns([2, 3])
    focus = k1.selectbox("Focus on field", ["(all)"] + [n_["label"] for n_ in AT["nodes"]], key="at_focus")
    kinds = k2.multiselect("Edge kinds", list(AT["legend"]), default=list(AT["legend"]), key="at_kinds")
    fid = next((i for i, n_ in nodes.items() if n_["label"] == focus), None)
    STY = {"deterministic": (INK, 3.2, "none"), "stochastic": (BLUE, 2.2, "none"), "unresolved": (BLUE, 2.2, "8 5"),
           "independent": (GREY, 1.6, "4 4"), "confounded": ("#9a7b00", 1.8, "1 4")}
    OX, OY, W_, H_ = 95, 34, 178, 36
    svg = [f"<svg viewBox='0 0 1380 590' width='100%' style='min-width:900px;font-family:Segoe UI, sans-serif'><defs>"]
    for k_, (c_, w_, _) in STY.items():
        svg.append(f"<marker id='ar_{k_}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='{c_}'/></marker>")
    svg.append("</defs>")
    for e in AT["edges"]:
        if e["kind"] not in kinds:
            continue
        a_, b_ = nodes[e["source"]], nodes[e["target"]]
        x1, y1, x2, y2 = a_["x"] + OX, a_["y"] + OY, b_["x"] + OX, b_["y"] + OY
        dx, dy = x2 - x1, y2 - y1; L = max((dx * dx + dy * dy) ** .5, 1)
        x2s, y2s = x2 - dx / L * 24, y2 - dy / L * 22
        c_, w_, da = STY[e["kind"]]; on = fid is None or fid in (e["source"], e["target"])
        mk = "" if e["kind"] in ("independent", "confounded") else f"marker-end='url(#ar_{e['kind']})'"
        svg.append(f"<line x1='{x1}' y1='{y1}' x2='{x2s:.0f}' y2='{y2s:.0f}' stroke='{c_}' stroke-width='{w_}' stroke-dasharray='{da}' {mk} opacity='{1 if on else .1}'>"
                   f"<title>{a_['label']} → {b_['label']} · {e['kind']} · {', '.join(e['rules'])}: {e['evidence']}</title></line>")
        if e["kind"] in ("independent", "confounded", "unresolved") and on:
            sym = {"independent": "⟂", "confounded": "≈", "unresolved": "?"}[e["kind"]]
            svg.append(f"<text x='{(x1 + x2) / 2:.0f}' y='{(y1 + y2) / 2 - 4:.0f}' font-size='15' font-weight='700' fill='{c_}' text-anchor='middle'>{sym}</text>")
    for i, n_ in nodes.items():
        x, y = n_["x"] + OX, n_["y"] + OY; on = fid is None or fid == i or any(fid in (e["source"], e["target"]) and i in (e["source"], e["target"]) for e in AT["edges"] if e["kind"] in kinds)
        fill = YELLOW if i == fid else (WHITE if n_["kind"] == "field" else PAPER)
        svg.append(f"<g opacity='{1 if on else .25}'><rect x='{x - W_ / 2}' y='{y - H_ / 2}' width='{W_}' height='{H_}' fill='{fill}' stroke='{INK}' stroke-width='2.2' "
                   f"stroke-dasharray='{'5 3' if n_['kind'] == 'latent' else 'none'}'/><text x='{x}' y='{y + 4}' font-size='11' font-weight='600' text-anchor='middle' fill='{INK}'>{n_['label']}</text></g>")
    svg.append("</svg>")
    st.markdown(f"<div class='atlas'>{''.join(svg)}</div>", unsafe_allow_html=True)
    st.markdown(" · ".join(f"<span class='tag' style='border-color:{STY[k_][0]}'>{k_}</span> {AT['legend'][k_]}" for k_ in AT["legend"]) +
                "<br><span class='mono'>Solid box = dataset field · dashed box = latent generator entity · ⟂ tested independent · ≈ confounded · ? mechanism open</span>", unsafe_allow_html=True)
    ed = pd.DataFrame(AT["edges"]); ed = ed[ed.kind.isin(kinds)]
    if fid:
        ed = ed[(ed.source == fid) | (ed.target == fid)]
    nm = {i: n_["label"] for i, n_ in nodes.items()}
    ed = ed.assign(source=ed.source.map(nm), target=ed.target.map(nm), rules=ed.rules.map(", ".join))
    st.dataframe(ed[["source", "target", "kind", "rules", "status", "evidence"]], hide_index=True, width="stretch")
    if len(ed):
        rr = sorted({x.strip() for s_ in ed.rules for x in s_.split(",") if x.strip() in RULES})
        c1, c2 = st.columns([3, 1])
        pick = c1.selectbox("Open a supporting rule", rr, format_func=lambda i: f"{i} · {RULES[i]['title']}", key="at_rule")
        c2.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        c2.button("Open in Rule Explorer", key="at_go", on_click=goto, args=("Rule Explorer", pick))
    card(AT["note"], "y")

elif page == "Validation Centre":
    section("VALIDATE", "Validation centre", "Every rule's acceptance test on five independent splits, the two-implementation check, detector evaluation and data lineage.")
    xc = VA["cross_check"]
    kpis([(f"{n_pass}/{len(REG)}", "validators pass"), ("5", "splits: full · 2 halves · 2 periods"), (f"{xc['C2_python_match']:.0%}", "SQL vs Python (C2)"),
          (f"{VA['runtime_s']:.0f}s", "validation runtime"), ("OK" if LI["contract_ok"] else "FAIL", "schema contract")])
    rows = []
    for r in REG:
        m_ = r["metrics"]; key = r["effect_size"].split(" = ")[0]
        row = dict(id=r["id"], group=r["group"], confidence=r["confidence"], status=r["status"], metric=key)
        if isinstance(m_, dict):
            for sp in ("full", "half_0", "half_1", "P1", "P2"):
                vv = m_.get(sp, {}).get(key) if isinstance(m_.get(sp), dict) else None
                row[sp] = vv
        rows.append(row)
    st.subheader("Validation matrix: headline metric on each split")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=420,
                 column_config={sp: st.column_config.NumberColumn(sp, format="%.4g") for sp in ("full", "half_0", "half_1", "P1", "P2")})
    st.subheader("Signature detectors, per class (no accuracy reported)")
    st.dataframe(pd.DataFrame(ST["detectors"])[["label", "detector", "precision", "recall", "f1", "tp", "fp", "fn"]].round(4), hide_index=True, width="stretch")
    st.subheader("Data lineage: dashboard number → artefact → producer → input")
    la = pd.DataFrame(LI["artefacts"]); la["sha256"] = la.sha256.str[:16] + "…"
    st.dataframe(la[["path", "producer", "inputs", "rows", "bytes", "sha256", "modified"]], hide_index=True, width="stretch")
    st.dataframe(pd.DataFrame(LI["schema_contract"]), hide_index=True, width="stretch")

elif page == "Methodology & Lineage":
    section("EXPLAIN", "Methodology & lineage", "How every rule was found, tested, challenged and replicated — and what we could not explain.")
    steps = [("01 DISCOVER", "Automated scan of all feature pairs + decision-tree search + forensics (fingerprints, change points); development half only."),
             ("02 RECONSTRUCT", "Each discovery written as an explicit rule with formula and computational logic; typed A deterministic … E composite."),
             ("03 VALIDATE", "Acceptance criteria on effect size; five splits; out-of-sample classes; Simpson checks; Bonferroni; SQL vs Python."),
             ("04 EXPLAIN", "Dependency atlas; economic reading labelled as interpretation; limitations and negative results kept.")]
    cols = st.columns(4)
    for c_, (k_, t_) in zip(cols, steps):
        c_.markdown(f"<div class='card'><div class='mono'>{k_}</div><div style='font-size:.9rem'>{t_}</div></div>", unsafe_allow_html=True)
    st.subheader("Pipeline (each step regenerates its artefact; hashes in the Validation Centre)")
    card("<div class='formula'>" + " → ".join(LI["pipeline"]) + "</div>" + f"Environment: Python {LI['environment']['python']} · " +
         " · ".join(f"{k} {v_}" for k, v_ in LI["environment"]["packages"].items() if v_))
    st.subheader("Known limitations and negative results")
    for lim in ["G1: bank-pair affinities exist, mechanism not identified.", "T4: weekly level values are not explained (their timing is: Mondays, T4b).",
                "F1: no fixed exchange rate restores round originals for EUR/GBP/CHF.", "X5: CUSTOMER_RECALL (undocumented label) shows no signature.",
                "Offsets estimated in whole hours; home-currency map inferred from data (validated indirectly by C2)."]:
        st.markdown(f"- {lim}")
    st.subheader("Disclosure")
    card("Primary data: Swift UMDAC Datathon 2026 fictitious payment dataset (provided); only aggregates are shown. External references are context only and must be verified by the team. "
         "AI assistance was used for coding and drafting (permitted, RR 3.6). Independent student prototype — not affiliated with or endorsed by Swift.")
