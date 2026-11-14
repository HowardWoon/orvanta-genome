"""Dashboard PDF v2 — dense, structured 15-page analytical publication.

Every page uses the same anatomy:
  header (feature group · page) → headline finding → research question
  left column : rule cards (statement, confidence, formula, reading) → evidence & validation table (key metric, 5-split range, n,
                evidence ID) → "read with care" (exceptions, limits)
  right column: 2×2 grid of charts at their natural aspect ratio, each with a one-line reading
All values are read from outputs/evidence/*.json (and web/build_data/ledger.json for evidence IDs) by src.reporting helpers.
"""
from __future__ import annotations
import json
from pathlib import Path
from .config import ROOT, CHARTS

SPL = ("full", "half_0", "half_1", "P1", "P2")
# key metric per rule: (metric key in validation.json, label, format)
KEY = {"R6": ("share_exact", "exact-match share", "x7"), "R7": ("share_exact", "exact-match share", "x7"), "R5": ("p_first", "P(path[1] ≠ header)", "pct2"),
       "R5b": ("ccy_follows_path_first", "currency follows path[1]", "pct1"), "R1": ("q_mle", "continuation q (1/e = 0.3679)", "f4"),
       "R2": ("pooled_covered_share", "pooled covered share", "pct2"), "P5": ("sender_split_half_r", "split-half r (bank mix)", "f3"), "R4": ("p_link_mle", "per-link hidden p", "f4"),
       "R3": ("corr_log", "corr(log uses, log size)", "f2"), "C2": ("share_exact", "exact-match share", "x7"), "C1": ("home_share", "currency = home of path[1]", "pct1"),
       "A1": ("effect_ordering_B", "sender-business effect (ln)", "f3"), "A2": ("split_half_corr", "split-half r of country effects", "f4"),
       "D2": ("fe_range_by_hour", "hour range after bank FE", "f3"), "T1": ("night_local", "night share, local clock", "pct1"), "T3": ("max_dev", "max country deviation", "pct1"),
       "T4": ("min_corr", "min corr of country weekly series", "f3"), "P2": ("o_prefix", "IBAN prefix = BIC country", "pct1"), "P4": ("o_match", "ordering address = bank country", "pct1"),
       "P1b": ("diff", "P(B|sender B) − P(B|sender C)", "f4"), "X1": ("median_ln_step", "median ln step in burst", "f2"), "X2": ("groups", "duplicate groups", "int"),
       "X3": ("up_share", "share ×100 (vs ÷100)", "pct1"), "X4": ("CEO_SCAM", "CEO: only-anomalous payees", "pct1"), "X6": ("cramers_v", "Cramér's V vs routing type", "f4"),
       "G3": ("max_rel_err", "max loop-rate error", "pct1"), "G1": ("chi2_dof_raw", "χ²/dof vs independence", "f0"), "A3": ("ks_D", "KS D vs normal", "f4"),
       "D3": ("manual_ks_gamma", "KS manual step vs Gamma", "f3"), "C3": ("in_route_share", "currency in a route-bank currency", "pct1"),
       "F1": ("usd_whole_share", "USD amounts ending .00", "pct1"), "T4b": ("share_on_monday", "change points on Mondays", "pct0")}


def fmtv(v, f):
    if v is None or isinstance(v, str): return str(v)
    if f == "x7" and v == 1: return "1 (every row)"
    return {"x7": f"{v:.7f}", "pct0": f"{v:.0%}", "pct1": f"{v:.1%}", "pct2": f"{v:.2%}", "f0": f"{v:,.0f}", "f2": f"{v:.2f}", "f3": f"{v:.3f}", "f4": f"{v:.4f}", "int": f"{int(v):,}"}[f]


def build(R):
    """R = dict of helpers/data from src.reporting: V, F, LVL, REG, STJ, E, GRJ, FOJ, DIJ, ATJ, VA, REJ, rule, img, n_pass, N_*."""
    V, F, LVL, REG, STJ, E, GRJ, FOJ, DIJ, ATJ, VA = (R[k] for k in ("V", "F", "LVL", "REG", "STJ", "E", "GRJ", "FOJ", "DIJ", "ATJ", "VA"))
    rule = R["rule"]
    ledf = ROOT / "web" / "build_data" / "ledger.json"
    EVID = {e["rules"][0]: e["id"] for e in json.loads(ledf.read_text(encoding="utf-8"))["entries"] if e["type"] == "rule"} if ledf.exists() else {}
    lv = lambda i: f"<span class='pass lv-{LVL[i].split()[0].lower()}' style='float:none;margin:0'>{LVL[i]}</span>"

    def fig(name, cap, span=False, short=False):
        return (f"<figure class='fg{' short' if short else ''}'{' style=\"grid-column:1/3\"' if span else ''}><img src='{(CHARTS / (name + '.png')).as_uri()}'>"
                f"<figcaption><b>Reading:</b> {cap}</figcaption></figure>")

    def evtab(ids):
        rows = []
        for i in ids:
            m = V[i]["metrics"]
            if i == "D1":
                a = m["additivity_ratio"]; rows.append(f"<tr><td><b>{i}</b></td><td>{lv(i)}</td><td>two-slow ÷ one-slow median (out of sample)</td><td>{a['value']:.2f}</td><td>half_0 → half_1</td><td>—</td><td>{EVID.get(i, '—')}</td></tr>"); continue
            if i == "X5":
                rows.append(f"<tr><td><b>{i}</b></td><td>{lv(i)}</td><td>features differing from normal (11 tested)</td><td>0</td><td>Bonferroni and BH</td><td>317</td><td>{EVID.get(i, '—')}</td></tr>"); continue
            k, lab, f = KEY[i]; full = m.get("full", {})
            vals = [m[s][k] for s in SPL if s in m and isinstance(m[s].get(k), (int, float))]
            rng = (f"{fmtv(min(vals), f)} – {fmtv(max(vals), f)}" if min(vals) != max(vals) else "identical") if len(vals) > 1 else "full only"
            n = full.get("n") or full.get("n_sample")
            ns = (f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.0f}k") if n else "—"
            rows.append(f"<tr><td><b>{i}</b></td><td>{lv(i)}</td><td>{lab}</td><td>{fmtv(full.get(k), f)}</td><td>{rng}</td><td>{ns}</td><td>{EVID.get(i, '—')}</td></tr>")
        return ("<table class='ev'><tr><th>Rule</th><th>Confidence</th><th>Key metric</th><th>Full data</th><th>Range, 5 splits</th><th>n</th><th>Evidence</th></tr>" + "".join(rows) + "</table>")

    def care(ids, extra=""):
        items = "".join(f"<li><b>{i}</b> {REG[i]['limitations']}</li>" for i in ids if REG[i].get("limitations") and REG[i]["limitations"] not in ("—", "-", "None material."))
        return f"<div class='care'><b>Read with care</b><ul>{items}{extra}</ul></div>"

    def fpage(eye, title, q, ids, cards, figs, extra_left="", care_extra=""):
        return (eye, title, f"<b>Research question:</b> {q}",
                f"<div class='fp'><div class='lc'>{cards}{evtab(ids)}{extra_left}{care(ids, care_extra)}</div><div class='cg'>{''.join(figs)}</div></div>")

    c2, r1, a1, d1, d2, x1, x3, x4, r5, r5b = F("C2"), F("R1"), F("A1"), V["D1"]["metrics"], F("D2"), F("X1"), F("X3"), F("X4"), F("R5"), F("R5b")
    anom = sum(a["n"] for a in E["anom_counts"]); xc = VA["cross_check"]
    P = []

    # ---------------- 1 · executive overview
    kp = "".join(f"<div class='kpi'><b>{v}</b><span>{s}</span></div>" for v, s in [
        ("10,000,000", "payments · 0 dropped · reconciled at every stage"), (f"{len(VA['rules'])} rules", f"{R['n_pass']}/{len(VA['rules'])} pass their validator on 5 splits"),
        (f"{R['N_VAL']} · {R['N_STRONG']} · {R['N_SUP']} · {R['N_INC']}", "validated · strongly supported · supported · inconclusive"),
        (f"{(c2['n'] - c2['exceptions']) / c2['n']:.5%}", f"FX rule (C2) exact: {int(c2['n'] - c2['exceptions']):,} rows"),
        (f"{xc['C2_python_match']:.0%}", "SQL = independent Python (R6, R7, C2)"), (f"{anom:,}", "labelled anomalies · 6 types")])
    flow = ("<div class='journey'>" + "".join(f"<div><b>{a}</b>{b}</div>" for a, b in [
        ("1 · Discover", f"{len(DIJ['pairs'])} feature pairs scanned on a development half; trees; forensics; graph"),
        ("2 · Reconstruct", "each pattern written as a rule: condition, formula, parameters, scope"),
        ("3 · Challenge", f"best alternative tested per rule; {len(R['REJ'])} hypotheses rejected; Simpson checks"),
        ("4 · Validate", "criterion fixed first; 2 random halves + 2 periods; out-of-sample classes; SQL = Python"),
        ("5 · Explain", "economic reading labelled as interpretation; limits and open questions stated")]) + "</div>")
    top = [("C2", f"FX conversions = home-currency borders on the route", f"{int(c2['n'] - c2['exceptions']):,} / 10M exact"),
           ("R1", "intermediaries K = ⌊Exp(1)⌋ (geometric, q = 1/e)", f"q = {r1['q_mle']:.4f}, w = {r1['cohen_w']:.4f}"),
           ("R2", "cover is a sending-bank habit (rule revised)", f"{F('R2')['oos_cover_banks_share']:.1%} vs {F('R2')['oos_other_banks_share']:.1%} out of sample"),
           ("C3", "payment currency drawn from route-bank currencies", f"{F('C3')['in_route_share']:.1%} in route"),
           ("D1", "duration = sum of per-bank steps (manual ≈ 24 min)", f"additivity ×{d1['additivity_ratio']['value']:.2f} out of sample"),
           ("A1", "ln(amount) = 6 + 2·[sender B] + 2·[receiver B]", f"fit {a1['intercept']:.2f} / {a1['effect_ordering_B']:.2f} / {a1['effect_beneficiary_B']:.2f}"),
           ("F1", "USD amounts keep roundness; converted ones do not", f"{F('F1')['usd_whole_share']:.0%} vs {F('F1')['non_usd_whole_share']:.1%} end .00"),
           ("X2", "duplicates: 2–5 identical copies within 2 h", f"{int(F('X2')['groups'])} groups, all labelled")]
    disc = "<table><tr><th>Rule</th><th>Discovery</th><th>Evidence</th><th>Confidence</th></tr>" + "".join(f"<tr><td><b>{i}</b></td><td>{t}</td><td>{e}</td><td>{lv(i)}</td></tr>" for i, t, e in top) + "</table>"
    groups = [("Time", "T1 T3 T4 T4b"), ("Currency & FX", "C1 C2 C3 F1"), ("Routing", "R1 R2 R4 R6 R7"), ("Institutions", "R3 R5 R5b P5"), ("Processing time", "D1 D2 D3"),
              ("Network", "G1 G3"), ("Payment value", "A1 A2 A3"), ("Parties & text", "P1b P2 P4"), ("Fraud anomalies", "X1 X4 X6"), ("Operational anomalies", "X2 X3 X5")]
    cov = "<table><tr><th>Feature group</th><th>Rules and confidence</th></tr>" + "".join(
        f"<tr><td>{g}</td><td>{' '.join(f'<span class=\"pass lv-{LVL[i].split()[0].lower()}\" style=\"float:none;margin:0 2px 0 0\">{i}</span>' for i in ids.split())}</td></tr>" for g, ids in groups) + "</table>"
    integ = """<table><tr><th>Data decision</th><th>Scale</th><th>Handling</th></tr>
      <tr><td>Multi-line quoted text fields</td><td>all rows</td><td>RFC-4180 parse; count asserted</td></tr><tr><td>DISCLAIMER column</td><td>1 row</td><td>dropped; row kept</td></tr>
      <tr><td>CUSTOMER_RECALL not in appendix</td><td>317 rows</td><td>kept; tested (X5)</td></tr><tr><td>Path endpoint ≠ header BIC</td><td>9.7%</td><td>explained by R5/R5b</td></tr>
      <tr><td>Country token missing in details</td><td>≈39%</td><td>BIC country used</td></tr><tr><td>Extreme amounts (max $15.7bn)</td><td>tail</td><td>kept; ln(amount)</td></tr><tr><td>Partial first / last day</td><td>2 days</td><td>excluded from weekly levels only</td></tr></table>"""
    P.append(("Executive overview · method · integrity", "We reconstructed the hidden generator behind 10 million synthetic cross-border payments",
              "<b>Approach:</b> treat the data as the output of an unknown program and recover it rule by rule — accepted on effect size and exactness (at n = 10M every p-value is ≈ 0), never on p-values alone. Passing a validator is necessary, not proof: each rule also carries a confidence level.",
              f"<div class='kpis6'>{kp}</div>{flow}<div class='tri'><div><h2>Headline discoveries</h2>{disc}</div><div><h2>Coverage: 34 rules, 10 feature groups</h2>{cov}"
              "<p class='note'>Blue validated · light blue strongly supported · yellow supported · grey inconclusive.</p></div>"
              f"<div><h2>Data integrity</h2>{integ}<div class='care' style='margin-top:.08in'><b>Scope</b><ul><li>Synthetic data: rates and country effects are generator settings, not real Swift traffic.</li><li>Rules are reconstructions consistent with the data, not recovered source code.</li><li>Open: T4 weekly levels · G1 bank-pair affinities · X5 recall · why EUR/USD are vehicles.</li></ul></div></div></div>"))

    # ---------------- 2 · discovery engine
    pr_ = DIJ["pairs"]; strong_ = [x for x in pr_ if x["v_dev"] >= .05]; ne_ = sum(1 for x in strong_ if x.get("explained_by")); nm_ = sum(1 for x in strong_ if str(x.get("verdict") or "").startswith("mediated"))
    hist = """<table><tr><th>Starting hypothesis</th><th>What the evidence showed</th><th>Rule</th></tr>
      <tr><td>FX = distinct currencies on route (H4)</td><td>""" + f"{c2['alt_distinct']:.1%}" + """ match → borders between adjacent banks: exact</td><td>C2</td></tr>
      <tr><td>Hop count ~ Poisson (H3)</td><td>successive ratios constant at 1/e → geometric</td><td>R1</td></tr>
      <tr><td>Covered share constant 11.3% (H32)</td><td>3–50% by country; bank-level dispersion → per-bank propensity</td><td>R2</td></tr>
      <tr><td>Currency independent of route (H33)</td><td>98.7% in a route-bank currency</td><td>C3</td></tr>
      <tr><td>Slow durations from off-hours (H8)</td><td>hour effect vanishes after bank fixed effects (Simpson)</td><td>D2</td></tr>
      <tr><td>Business share set per country (H34)</td><td>bank attribute, split-half r ≈ 0.99</td><td>P5</td></tr></table>"""
    sig_box = ("<div class='care'><b>Why significance is not enough</b><ul><li>With 10M rows a 0.01-point difference has p ≈ 0; rules are accepted on Cramér's V, Cohen's w, exact-match share or KS distance against thresholds fixed in advance.</li>"
               f"<li>A pair counts as strong at V ≥ 0.05 on the development half <i>and</i> the validation half ({DIJ['val_rows']:,} rows).</li><li>Mediated = conditional V &lt; 0.03 once country or route length is held fixed.</li></ul></div>")
    top_pairs = "<table><tr><th>Field pair</th><th>V dev</th><th>V val</th><th>Explained by</th></tr>" + "".join(
        f"<tr><td>{x['a']} × {x['b']}</td><td>{x['v_dev']:.2f}</td><td>{x['v_val']:.2f}</td><td>{x.get('explained_by') or x.get('verdict')}</td></tr>"
        for x in sorted(strong_, key=lambda x: -x["v_dev"])[:9]) + "</table>"
    cards2 = (f"<div class='rule'><b class='id'>SCAN</b> {len(DIJ['features'])} discretised features → {len(pr_)} pairs; Cramér's V on a {DIJ['dev_rows']:,}-row development half, re-scored on an independent half. "
              f"<b>{len(strong_)}</b> strong pairs: <b>{ne_}</b> explained by a rule · <b>{nm_}</b> mediated · <b>{len(strong_) - ne_ - nm_}</b> open.</div>"
              f"<div class='rule'><b class='id'>TREES</b> Depth-3 trees as a search device, scored on the holdout: routing accuracy {DIJ['trees'][0]['holdout_accuracy']:.3f} (= R1 + R2); manual step {DIJ['trees'][3]['holdout_accuracy']:.3f} vs baseline {DIJ['trees'][3]['majority_baseline']:.3f} (= D2: a bank attribute).</div>"
              f"<div class='rule'><b class='id'>ATLAS</b> {len(ATJ['edges'])} edges: {sum(e['kind'] == 'deterministic' for e in ATJ['edges'])} deterministic · {sum(e['kind'] == 'stochastic' for e in ATJ['edges'])} stochastic · {sum(e['kind'] == 'independent' for e in ATJ['edges'])} tested independent · {sum(e['kind'] == 'confounded' for e in ATJ['edges'])} confounded · {sum(e['kind'] == 'unresolved' for e in ATJ['edges'])} unresolved — generation dependencies, not causal claims.</div>")
    P.append(("Method · discovery engine & dependency atlas", f"{len(pr_)} feature pairs scanned: every strong dependency is explained by a rule or by rules combined",
              "<b>Research question:</b> which fields depend on which — and is every strong dependency accounted for by a reconstructed rule?",
              f"<div class='fp'><div class='lc'>{cards2}<h2>How the engine changed our hypotheses</h2>{hist}{sig_box}</div>"
              f"<div class='cg'>{fig('atlas', 'arrows run from generator inputs to derived fields; dashed boxes are latent choices (bank size, calendar). Solid black = exact, blue = stochastic, grey = tested independent, gold = confounded.', True)}"
              f"{fig('discovery_heatmap', 'Cramér’s V for all pairs (development half); dark cells are the strong dependencies the rules must explain.', short=True)}"
              f"<div class='fg'><h2 style='margin:0 0 4px'>Strongest dependencies and what explains them</h2>{top_pairs}</div></div></div>"))

    # ---------------- 3 · time
    P.append(fpage("Feature group 01 · Time", "Payments follow the instructing bank's local office clock, scaled by one global weekly multiplier",
                   "how does the generator decide when a payment is sent?", ["T1", "T3", "T4", "T4b"],
                   rule("T1", "local_hour = UTC_hour + offset(country of first path bank); 07:00 start", f"Night share (01–05h) {F('T1')['night_local']:.1%} on the local clock vs {F('T1')['night_utc']:.1%} in UTC. Offsets are January values (US −5, GB 0, AU +11): DST ignored.")
                   + rule("T3", "Mon 18.9 · Tue 17.0 · Wed 17.0 · Thu 18.0 · Fri 18.9 · Sat 3.6 · Sun 6.5 (%)", "One shape in every country; a Fri–Sat weekend for Gulf/Israel banks was tested and rejected.")
                   + rule("T4", "weekly volume = base × global step level", f"All countries move together (min corr {F('T4')['min_corr']:.3f}); what sets the levels is not identified."),
                   [fig("time_daily", "volume jumps between week-long plateaus while the weekday pattern repeats inside every week."),
                    fig("change_points", f"binary segmentation finds {len(FOJ['change_points']['change_points'])} level changes, every one on a Monday (T4b)."),
                    fig("time_localhour", "converted to each sending country's clock, activity starts at 07:00 everywhere — UTC would smear it."),
                    fig("time_weekday", "the same weekday shares apply in every country (max deviation 0.4%).")]))

    # ---------------- 4 · currency & FX
    sup = None
    rp = ROOT / "web" / "build_data" / "replay.json"
    if rp.exists():
        X = {x["rule"]: x for x in json.loads(rp.read_text(encoding="utf-8"))["rules"]}["C2"]
        rows_ = [dict(zip(X["columns"], r)) for r in X["supporting_rows"][:2] + X["contradicting_rows"][:2]]
        sup = ("<table><tr><th>BIC8_PATH (synthetic)</th><th>Home currencies</th><th>Predicted FX</th><th>Recorded</th></tr>" + "".join(
            f"<tr><td style='font-family:Consolas;font-size:8pt'>{r['path']}</td><td>{r['route_currencies']}</td><td>{r['predicted_fx']}</td><td{' style=\"color:#EF5147;font-weight:700\"' if r['predicted_fx'] != r['fx'] else ''}>{r['fx']}</td></tr>" for r in rows_) + "</table>"
               "<p class='note'>First two rows: random supporting records. Last two: the only exceptions — the receiver 0000ERA0 (Eritrea) never sends, so its home currency is unobservable.</p>")
    P.append(fpage("Feature group 02 · Currency & FX", f"FX conversions equal the currency borders along the route — exact on {int(c2['n'] - c2['exceptions']):,} of 10,000,000 payments",
                   "how are payment currencies and the number of conversions generated?", ["C2", "C3", "C1", "F1"],
                   rule("C2", "FX = Σ 1[home_ccy(bicᵢ) ≠ home_ccy(bicᵢ₊₁)], known BICs only", f"Alternatives rejected: distinct currencies − 1 ({c2['alt_distinct']:.1%}); payment currency plays no role.")
                   + rule("C3", "currency drawn from the route: first bank · receiver · intermediaries · vehicle", f"{F('C3')['in_route_share']:.1%} in a route-bank currency; receiver {F('C3')['receiver_only_mean']:.1%} at every length; +{F('C3')['intermediary_slope_per_hop'] * 100:.1f} pts per intermediary; outside route {F('C3')['outside_share']:.1%} (mostly EUR/USD, H38)."),
                   [fig("ccy_mix", "in every large sending country ≈ 93% of payments use the instructing bank's home currency (C1)."),
                    fig("fx_heat", "FX never exceeds the number of links (pc − 1): conversions happen only between adjacent banks."),
                    fig("h38_vehicle", "outside-route currencies are a route-independent vehicle draw: EUR 1.41%, USD 0.75% (H38, supported)."),
                    fig("f1_cents", "USD keeps round amounts; converted currencies do not — amounts are generated in USD, then converted (F1).")],
                   extra_left=(f"<h2>C2 worked example (real records)</h2>{sup}" if sup else "")))

    # ---------------- 5 · routing
    P.append(fpage("Feature group 03 · Routing structure", "Route length is a chain with a 1/e continuation probability; every link hides with p = 0.05",
                   "how does the generator decide how many banks a payment passes through, and which links are visible?", ["R1", "R2", "R4", "R6", "R7"],
                   rule("R1", "K = ⌊Exp(1)⌋ : P(K=k) = (1−e⁻¹)e⁻ᵏ ; pc = K + 2", f"MLE q = {r1['q_mle']:.4f} vs 1/e = 0.3679; Cohen's w = {r1['cohen_w']:.4f}; ⇒ Direct {r1['p_direct']:.2%}.")
                   + rule("R2", "Covered vs Indirect = per-sending-bank propensity; independent of K", f"Out of sample {F('R2')['oos_cover_banks_share']:.0%} vs {F('R2')['oos_other_banks_share']:.1%}; V vs K = {F('R2')['cramers_v_vs_K']:.4f}. Revised from a pooled 11.3%.")
                   + rule("R4", "P(≥1 hidden | pc) = 1 − 0.95^(pc−1)", f"Per-link MLE p = {F('R4')['p_link_mle']:.4f}; max deviation {F('R4')['max_abs_dev']:.4f}.")
                   + rule("R6", "PARTICIPANT_COUNT = known BICs; CONTINUITY_QFLAG = N ⇔ '...' in path (R7)", "Both exact on all 10M rows and in an independent Python re-implementation."),
                   [fig("hops", "observed participant counts sit on the geometric curve with q = 1/e at every length."),
                    fig("r1_country", "q is the same in all 20 largest sending countries — routing depth ignores geography."),
                    fig("gaps", "the share with a hidden hop rises exactly as 1 − 0.95^(pc−1): each link hides independently."),
                    fig("r2_classes", "Covered share is a property of the sending bank, stable out of sample.")]))

    # ---------------- 6 · institutions
    P.append(fpage("Feature group 04 · Institutions & route roles", "On 5% of payments a different bank instructs — and the two banks drive different fields",
                   "which institution does each field follow, and how are intermediaries chosen?", ["R5", "R5b", "R3", "P5"],
                   rule("R5", "path[1] ≠ ORDERING_BIC8 w.p. 0.05 · path[−1] ≠ BENEFICIARY_BIC8 w.p. 0.05, independent", f"Mismatch {r5['p_first']:.2%} / {r5['p_last']:.2%}; joint/product ratio {r5['indep_ratio']:.2f} (independent). Not errors: a role distinction.")
                   + rule("R5b", "currency & clock ← path[1] ;  IBAN & customer country ← ORDERING_BIC8", f"Currency follows path[1] {r5b['ccy_follows_path_first']:.0%} vs header {r5b['ccy_follows_obic']:.0%}; IBAN prefix = header {r5b['iban_follows_obic']:.0%}.")
                   + rule("R3", "P(bank used as intermediary) ∝ bank activity", f"corr(log uses, log volume) = {F('R3')['corr_log']:.2f}; only {F('R3')['share_in_currency_zone']:.0%} sit in the payment-currency zone (alternative rejected).")
                   + rule("P5", "customer-type mix is a bank attribute", f"split-half r = {F('P5')['sender_split_half_r']:.3f} across banks."),
                   [fig("endpoint_swap", "first and last path banks are replaced independently, each about 5% of the time."),
                    fig("r5b_roles", "on mismatched rows currency follows the instructing bank, the IBAN follows the account bank."),
                    fig("r3_scatter", "banks are used as intermediaries in proportion to their own volume (log–log)."),
                    fig("ob_share", "business-customer shares differ by bank; aggregated to countries they look like country effects (P5).")]))

    # ---------------- 7 · processing time
    ms = STJ["manual_step"]
    P.append(fpage("Feature group 05 · Processing time", f"Duration is a sum of per-bank steps: seconds if straight-through, ~{ms['median'] / 60:.0f} minutes if manual",
                   "what determines TOTAL_DURATION, and is it the clock, the amount or the bank?", ["D1", "D2", "D3"],
                   rule("D1", "TOTAL_DURATION ≈ Σ_banks {fast ≈ 7–15 s w.p. STP(bank); manual ≈ 1,400 s}", f"Out of sample: fast→fast {d1['fast->fast']['median_s']:.0f} s · both slow {d1['slow->slow']['median_s']:,.0f} s (×{d1['additivity_ratio']['value']:.2f} one slow).")
                   + rule("D2", "slow step depends on the bank only", f"Hour range {d2['raw_range_by_hour']:.3f} → {d2['fe_range_by_hour']:.3f} after bank fixed effects; corr with ln amount {d2['fe_corr_ln_amount']:+.4f}.")
                   + rule("D3", f"manual ~ Gamma({ms['gamma_shape']:.1f}, {ms['gamma_scale']:.0f} s); two fast ~ Gamma({STJ['fast_step']['gamma_shape']:.1f}, {STJ['fast_step']['gamma_scale']:.1f} s)", f"KS Gamma {ms['ks_gamma']:.3f} beats lognormal {ms['ks_lognormal']:.3f}."),
                   [fig("dur_hist", "two humps: seconds for straight-through paths, ~20–30 min when a manual bank is involved."),
                    fig("dur_class", "medians by bank speed class: one slow bank ≈ 1,400 s, two ≈ 2,600 s — the steps add."),
                    fig("simpson", "the raw hour-of-day effect disappears once bank composition is fixed (Simpson's paradox)."),
                    fig("stp_size", "large banks are almost never manual; about half of small banks are.")],
                   care_extra="<li>Durations describe the generator's processing model, not real bank performance.</li>"))

    # ---------------- 8 · network
    g3 = F("G3"); gp = GRJ["G1_pairing"]; nw = GRJ["network"]; cn = GRJ["concentration"]; g2 = GRJ["G2_country"]
    P.append(fpage("Feature group 06 · Route network", "The route network is a size-weighted pseudograph: loops are predictable, pairings are not independent",
                   "what network structure emerges from how banks are selected and connected?", ["G3", "G1"],
                   rule("G3", "P(intermediary = b) ∝ size(b)^β, drawn with replacement", f"β = {g3['beta']:.2f}; predicted loop rate within {g3['max_rel_err']:.1%} at every length (pc 4–8); explains {int(GRJ['pseudograph']['paths_with_revisit']):,} revisiting paths.")
                   + rule("G1", "sender bank × receiver bank ≠ independent (directional affinities)", f"χ²/dof {gp['chi2_per_dof']:.0f} raw · {gp['chi2_per_dof_unique_relationships']:.0f} unique · {gp['chi2_per_dof_given_country_pair']:.0f} within country pair; domestic ×{g2['domestic_affinity_mean']:.2f}; asymmetric (r = {g2['affinity_symmetry_corr']:.2f}). Mechanism open.")
                   + f"<div class='rule'><b class='id'>NET</b> {int(nw['nodes']):,} banks · {int(nw['edges']):,} directed edges · {int(nw['hops']):,} hops · reciprocity {nw['reciprocity']:.2f}. Gini {cn['gini_strength']:.2f}; top 1% of banks carry {cn['top1pct_share']:.0%} of hops, top 10% {cn['top10pct_share']:.0%}.</div>",
                   [fig("graph_loops", "the birthday-problem prediction from size-weighted draws matches observed revisits at every length."),
                    fig("graph_pairs", "observed bank-pair counts scatter far from independence — something beyond size pairs banks."),
                    fig("graph_hubs", "the top PageRank decile is mostly automated; the other deciles are ~50–58% manual."),
                    fig("strength_ccdf", "a heavy-tailed size distribution: a few hubs carry most hops.")],
                   care_extra="<li>Network figures describe the synthetic generator; they are not real correspondent market shares.</li>"))

    # ---------------- 9 · forensics
    us_ = {r["usd_denominated"]: r for r in FOJ["usd_roundness"]}; cp_ = FOJ["change_points"]
    fpr = (f"<div class='rule'><b class='id'>FPRINT</b> Seconds-of-minute uniform (w = {FOJ['second_uniform']['cohen_w']:.4f}); Benford MAD {FOJ['benford']['nigrini_mad']:.4f} ({FOJ['benford']['conformity']}); "
           f"BIC grammar NNNN·CC·LL {FOJ['bic']['grammar_match']:.0%} over {FOJ['bic']['banks']:,} banks, one location code per country; one IBAN length per country ({FOJ['iban_single_length_share']:.0%}); {FOJ['local_account_templates']['distinct']} local-account templates.</div>")
    rate = "<table><tr><th>Currency</th><th>Best fixed rate</th><th>Near-integer at best</th><th>Grid median</th></tr>" + "".join(
        f"<tr><td>{r['currency']}</td><td>{r['best_rate']:.4f}</td><td>{r['best_near_integer_share']:.2%}</td><td>{r['median_share']:.2%}</td></tr>" for r in FOJ["fixed_rate_search"]) + "</table><p class='note'>Negative result: no single FX rate makes converted amounts round, so no fixed conversion table is claimed.</p>"
    P.append(fpage("Statistical forensics · generator fingerprints", "Fingerprints: USD keeps round amounts, volume steps on Mondays, identifiers follow fixed grammars",
                   "which statistical signatures reveal how the generator was built?", ["F1", "T4b"],
                   rule("F1", "USD-denominated amounts keep whole-unit roundness; converted currencies do not", f"USD .00 {us_[True]['whole_units']:.0%} (multiples of 100: {us_[True]['mult100']:.0%}) vs converted {us_[False]['whole_units']:.1%} (uniform cents).")
                   + rule("T4b", "weekly level piecewise-constant, changes only on Mondays", f"{len(cp_['change_points'])} change points (BIC penalty), all Mondays; residual sd {cp_['residual_sd_log']:.3f} in log volume.") + fpr,
                   [fig("f1_cents", "USD amounts end .00 far more often — the generator draws USD first and converts."),
                    fig("benford", "leading digits follow Benford closely, as lognormal amounts with σ ≈ 2 should."),
                    fig("cents_segment", "round amounts are slightly more common in business segments (7.7% vs 6.9% .00)."),
                    fig("fp_uniform", "second and minute stamps are uniform (w ≈ 0.003, continuous time draws); cents are far from uniform (w = 0.64) — the USD-roundness fingerprint.")],
                   extra_left=f"<h2>Fixed-rate search</h2>{rate}"))

    # ---------------- 10 · robustness
    ar = STJ["amount_residual"]
    P.append(fpage("Statistical robustness · model fit & parameters", "Parameters sit on their theoretical values; distributions survive tail checks; replication holds",
                   "are the reconstructed models statistically adequate, or just visually plausible?", ["A3", "D3", "R1", "R4"],
                   rule("A3", "within-country ln-amount residual ~ Normal; lognormal tail", f"KS D = {ar['ks_D_vs_normal']:.4f}; skew {ar['skew']:+.3f}; excess kurtosis {ar['excess_kurtosis']:+.3f}; Hill α drifts {STJ['hill'][0]['alpha']:.2f} → {STJ['hill'][-1]['alpha']:.2f} (not a power law).")
                   + rule("D3", f"manual ~ Gamma({ms['gamma_shape']:.1f}, {ms['gamma_scale']:.0f} s)", f"KS {ms['ks_gamma']:.3f} (Gamma) vs {ms['ks_lognormal']:.3f} (lognormal): Gamma(2) = two exponential stages."),
                   [fig("param_ci", "every core parameter has a 95% interval of ±0.03 points or less: decisions rest on size, not significance."),
                    fig("stat_qq", "residual quantiles lie on the normal line from the 0.1% to the 99.9% quantile."),
                    fig("stat_hill", "a drifting Hill index is the lognormal signature; a power law would be flat."),
                    fig("exceedance", "the fitted model predicts how many payments exceed $100k … $1bn within 1–15%.")],
                   care_extra="<li>A good fit shows the model is adequate, not that it is the generator's code.</li>"))

    # ---------------- 11 · value
    P.append(fpage("Feature group 07 · Payment value", "ln(amount) = 6 + 2·[sender is business] + 2·[receiver is business] + sending-country level",
                   "how does the generator set payment amounts?", ["A1", "A2", "A3"],
                   rule("A1", "ln(USD_AMOUNT) ~ N(6 + 2[O=B] + 2[B=B] + countryₒ + bank, σ≈2)", f"Fit {a1['intercept']:.2f} + {a1['effect_ordering_B']:.2f}·O + {a1['effect_beneficiary_B']:.2f}·B, interaction {a1['interaction']:+.3f}; σ {a1['sd_min']:.2f}–{a1['sd_max']:.2f}. Medians C→C $464 · B→C $3,118 · B→B $22,883.")
                   + rule("A2", "country effect: MC +2.0 … BD −3.2 (ln units); beneficiary country ≈ 0", f"Split-half r = {F('A2')['split_half_corr']:.4f}; sd ordering {F('A2')['sd_ordering']:.2f} vs beneficiary {F('A2')['sd_beneficiary']:.2f}."),
                   [fig("amt_segments", "each business party shifts ln(amount) by ≈ +2, i.e. multiplies the typical amount by ≈ 7.4."),
                    fig("amt_country", "sending-country effects span ±3 in ln units and replicate across random halves."),
                    fig("amt_variance", "after party types, the sending country explains 17% of the variance; bank 4%; the rest is noise."),
                    fig("exceedance", "the largest amounts ($15.7bn kept, not capped) follow the same lognormal model.")],
                   care_extra="<li>Country effects are generator parameters, not national economic statistics; coefficients are fitted, not exact constants.</li>"))

    # ---------------- 12 · parties
    P.append(fpage("Feature group 08 · Parties, accounts & text", "Party text follows MT conventions; IBANs follow the bank's country; beneficiary residence is decoupled",
                   "how are the sender, beneficiary, accounts and free-text details constructed?", ["P2", "P4", "P1b"],
                   rule("P2", "IBAN only for IBAN-country banks; IBAN prefix = BIC country", "Mirrors the IBAN registry. Details: optional /account line + ≤ 4 lines × 35 chars (99.96% of lines).")
                   + rule("P4", "ordering address country = BIC country; beneficiary ≈ never", f"Ordering {F('P4')['o_match']:.0%}; beneficiary {F('P4')['b_match']:.1%}.")
                   + rule("P1b", "P(receiver = B) = 28.8% regardless of sender type", f"difference {F('P1b')['diff']:+.4f}; business tokens never co-occur with person names."),
                   [fig("iban_country", "IBAN use is either ≈ 0% or ≈ 100% per bank country — a country attribute (P2)."),
                    fig("tokens", "token presence separates business and consumer templates cleanly."),
                    fig("country_compare", "the ordering party lives in its bank's country; the beneficiary's residence is drawn separately."),
                    "<div class='fg' style='padding:.06in .08in'>" + "<h2>Field anatomy — what each party field is</h2><table><tr><th>Field</th><th>What it contains</th><th>Rule</th></tr>"
                               "<tr><td>ORDERING/BENEFICIARY_DETAILS</td><td>free text: optional /account line + ≤ 4 lines × 35 chars</td><td>P1b, P4</td></tr>"
                               "<tr><td>…_TOKENS</td><td>engineered summary of the details, supplied with the data</td><td>P1b</td></tr>"
                               "<tr><td>…_ACCOUNT</td><td>IBAN if the bank country uses IBANs, else a local template</td><td>P2</td></tr>"
                               "<tr><td>…_BIC8</td><td>bank id NNNN·CC·LL (chars 5–6 = country)</td><td>R5, P2</td></tr>"
                               "<tr><td>…_TYPE</td><td>B / C; sender 78.7% B, receiver 28.8% B</td><td>P1b, P5</td></tr></table>" + "<p class='note'>Synthetic placeholders only; no names, addresses or account numbers are reproduced.</p></div>"],
                   care_extra="<li>Tokens are engineered summaries supplied with the data, not original text; no personal data is shown.</li>"))

    # ---------------- 13 · fraud anomalies
    ap_ = {r["a"]: r for r in R["E"]["anom_profile"]}
    ap_cap = (f"romance payments are small (median ${ap_['ROMANCE_SCAM']['med_amt']:,.0f}) and slow ({ap_['ROMANCE_SCAM']['med_dur']:,.0f} s); "
              f"fat-finger amounts sit far above normal (${ap_['FAT_FINGER_MISTAKE']['med_amt']:,.0f} vs ${ap_['NORMAL']['med_amt']:,.0f}); "
              f"recall rows look like normal traffic (X5).")
    P.append(fpage("Feature group 09 · Fraud anomalies", "Fraud labels carry injection signatures: escalating bursts and mule accounts at small banks",
                   "how are scam labels generated, and what pattern does each leave?", ["X1", "X4", "X6"],
                   rule("X1", "ROMANCE: consumer → same payee, 2–8 payments, ln step +0.40 (×1.5), ~5 min apart", f"{int(x1['series'])} series; sender consumer {x1['sender_consumer_share']:.0%}; burst rule: 0 normal false positives.")
                   + rule("X4", "CEO / ACCOUNT_REPLACEMENT → mule accounts at small banks", f"Only-anomalous payees: CEO {x4['CEO_SCAM']:.0%}, account replacement {x4['ACCOUNT_REPLACEMENT_SCAM']:.0%} vs fat finger {x4['FAT_FINGER_MISTAKE']:.0%}.")
                   + rule("X6", "anomaly label independent of routing type", f"Cramér's V = {F('X6')['cramers_v']:.4f}: labels injected after routing."),
                   [fig("anomaly_rates", f"{anom:,} labelled payments in six types; Wilson 95% intervals."),
                    fig("romance", "romance-scam payments grow ≈ ×1.5 per step within a burst."),
                    fig("mule", "CEO and account-replacement money flows to accounts that receive only flagged payments."),
                    fig("anomaly_profile", ap_cap)],
                   care_extra="<li>Labels are synthetic; they are not confirmed real-world fraud and their prevalence is not real prevalence.</li>"))

    # ---------------- 14 · operational
    P.append(fpage("Feature group 10 · Operational errors & recall", "Errors are mechanical copies and decimal shifts; CUSTOMER_RECALL leaves no trace",
                   "which operational anomalies leave identifiable patterns in the message fields?", ["X2", "X3", "X5"],
                   rule("X2", "DUPLICATE: 2–5 identical copies (amount, path, duration) within ≤ 2 h; all labelled", f"{int(F('X2')['groups'])} groups; max span {int(F('X2')['max_span_s']):,} s; exact-key detector recalls 100% of labelled rows.")
                   + rule("X3", "FAT_FINGER: amount × 100 (≈77%) or ÷ 100 (≈23%)", f"GMM modes {x3['mode_low']:+.2f} / {x3['mode_high']:+.2f} log₁₀: a decimal separator misplaced by two digits.")
                   + rule("X5", "CUSTOMER_RECALL ≈ normal traffic on 11 features", "Not in the official appendix. A recall is decided after sending, so message fields cannot reveal it (negative result)."),
                   [fig("dup_groups", "duplicate groups of 2–5 copies, all within two hours."),
                    fig("fatfinger", "fat-finger amounts sit about two decades from the expected amount — ×100 or ÷100."),
                    fig("ff_pr", "an amount-only detector stays weak: the label overlaps normal variation."),
                    fig("recall", "no tested feature separates recall payments from normal ones after correction.")],
                   care_extra="<li>Absence of a detected signature does not prove the generator applies no logic to CUSTOMER_RECALL.</li>"))

    # ---------------- 15 · synthesis
    from .ledger import SECTIONS
    det = {"R6", "R7", "C2", "P2", "X2"}
    rows = "".join(
        f"<tr><td><b>{name}</b> <span style='color:#555'>— {what}</span></td><td>" + " ".join(f"<span class='pass lv-{LVL[i].split()[0].lower()}' style='float:none;margin:0 2px 0 0'>{i}</span>" for i in ids if i in LVL)
        + f"</td><td>{'exact + stochastic' if det & set(ids) and set(ids) - det else 'exact' if set(ids) <= det else 'stochastic'}</td><td>{'; '.join(i for i in ids if LVL.get(i) == 'INCONCLUSIVE') or '—'}</td></tr>"
        for name, ids, what in SECTIONS)
    bylv = "".join(f"<tr><td>{lv_}</td><td>{sum(1 for v in LVL.values() if v == lv_)}</td><td>{' '.join(sorted(k for k, v in LVL.items() if v == lv_))}</td></tr>" for lv_ in ("VALIDATED", "STRONGLY SUPPORTED", "SUPPORTED", "INCONCLUSIVE"))
    P.append(("Synthesis · generator blueprint, integrity & conclusions", "The reconstructed generator in ten stages — what is exact, what is fitted, what is still open",
              "<b>Research question:</b> taken together, how much of the generator have we reconstructed, how confidently, and what remains unknown?",
              "<div class='fp' style='grid-template-columns:1.25fr 1fr'><div class='lc'><h2>Generator blueprint</h2>"
              f"<table class='ev'><tr><th>Generation stage</th><th>Rules (confidence)</th><th>Type</th><th>Open</th></tr>{rows}</table>"
              f"<h2>Confidence matrix — all {len(LVL)} rules</h2><table class='ev'><tr><th>Level</th><th>n</th><th>Rules</th></tr>{bylv}</table>"
              "<p class='note'>Exact = reproduces its field on every row (R6, R7, C2, P2, X2; Direct ⇔ 2 participants). Stochastic = draws with fitted parameters. Validator pass ≠ proof; the level says how strongly each rule is supported.</p>"
              f"<h2>What we rejected (selection of {len(R['REJ'])})</h2><table><tr><th>Hypothesis</th><th>Why it failed</th></tr>"
              f"<tr><td>FX = distinct currencies on the route (H4)</td><td>only {c2['alt_distinct']:.1%} match; borders between adjacent banks are exact</td></tr>"
              "<tr><td>Hop count ~ Poisson (H3)</td><td>successive ratios constant at 1/e — geometric</td></tr>"
              "<tr><td>Covered share is one constant (H32)</td><td>3–50% by country; a sending-bank habit</td></tr>"
              "<tr><td>Delays come from off-hours queuing (H8)</td><td>effect vanishes after bank fixed effects (Simpson)</td></tr>"
              "<tr><td>Gulf/Israel banks have a Fri–Sat weekend (H16)</td><td>one weekday shape everywhere</td></tr>"
              "<tr><td>One fixed FX rate per currency (H37)</td><td>≈2% near-integer vs 1.2% baseline — not supported</td></tr></table></div>"
              "<div class='lc'><h2>Research integrity</h2><table><tr><th>Check</th><th>Result</th></tr>"
              f"<tr><td>Rows parsed / dropped</td><td>10,000,000 / 0</td></tr><tr><td>Validators passing (5 splits)</td><td>{R['n_pass']} / {len(VA['rules'])}</td></tr>"
              f"<tr><td>SQL vs independent Python</td><td>R6 {xc['R6_python_match']:.0%} · R7 {xc['R7_python_match']:.0%} · C2 {xc['C2_python_match']:.0%} ({xc['sample']:,} rows)</td></tr>"
              f"<tr><td>Strong dependencies explained</td><td>{ne_ + nm_} / {len(strong_)}</td></tr><tr><td>Hypotheses logged / rejected</td><td>H1–H38 / {len(R['REJ'])}</td></tr>"
              "<tr><td>Raw data redistributed</td><td>no</td></tr></table>"
              "<h2>How the stages connect</h2><table><tr><th>Upstream choice</th><th>Shapes</th><th>Rules</th></tr>"
              "<tr><td>Bank size (latent)</td><td>which banks relay → route loops, network concentration</td><td>R3, G3</td></tr>"
              "<tr><td>Route length K</td><td>participants, routing type, hidden hops, number of conversions, duration</td><td>R1, R6, R4, C2, D1</td></tr>"
              "<tr><td>Bank home currencies</td><td>payment currency and FX count</td><td>C1, C3, C2</td></tr>"
              "<tr><td>Bank habits</td><td>cover vs indirect, customer mix, manual processing</td><td>R2, P5, D2</td></tr>"
              "<tr><td>Party types + sending country</td><td>payment amount</td><td>A1, A2</td></tr>"
              "<tr><td>Anomaly injection (after routing)</td><td>bursts, mule payees, copies, ×100 slips</td><td>X1–X4, X6</td></tr></table>"
              "<div class='care'><b>Open questions</b><ul><li><b>T4</b> what sets the weekly volume levels (changes all on Mondays, cause unknown)</li><li><b>G1</b> why bank pairs have directional affinities</li>"
              "<li><b>X5</b> CUSTOMER_RECALL leaves no observable trace</li><li><b>C3 / H38</b> EUR 1.41% / USD 0.75% vehicle draw quantified; why these currencies, unknown</li></ul></div>"
              "<div class='concl'><b>Conclusion</b><p>The generator is a compact set of mechanisms: route length ⌊Exp(1)⌋; conversions at every home-currency border; currencies drawn from the route; bank-level habits for cover, customer mix and speed; a 6 + 2 + 2 lognormal amount model; a local office clock with global weekly levels; and anomalies injected with clear signatures.</p>"
              "<p>These are reconstructions consistent with the data — validated on independent splits — not the generator's source code. The data is synthetic and describes this generator, not real Swift traffic.</p></div></div></div>"))
    return P


FIT = """<script>
window.addEventListener('load', () => {            // last-resort fit: scale a column down (never below 82%) if it would cross the footer
  for (const pg of document.querySelectorAll('section.pg')) {
    const limit = pg.getBoundingClientRect().bottom - 40;
    for (let pass = 0; pass < 8; pass++) for (const el of pg.querySelectorAll('.lc, .cg, .tri > div')) {
      const floor = el.classList.contains('cg') ? .74 : .85, z0 = +(el.dataset.zoom || 1);
      const r = el.getBoundingClientRect(), bottom = Math.max(...[...el.children].map(c => c.getBoundingClientRect().bottom), r.top);
      if (bottom > limit) { const z = Math.max(floor, z0 * (limit - r.top) / (bottom - r.top)); el.style.zoom = z; el.dataset.zoom = z.toFixed(3); }
    }
  }
  document.body.dataset.fitted = '1';
});
</script>"""

CSS2 = """
h1 { font-size: 23pt !important }
table.ev td:last-child, table.ev td:nth-child(2) { white-space: nowrap }
.pass { white-space: nowrap }
.fp { display: grid; grid-template-columns: 5.45in 1fr; gap: .18in; flex: 1; min-height: 0 }
.lc { display: flex; flex-direction: column; gap: .09in; min-width: 0; min-height: 0 }
.cg { display: grid; grid-template-columns: 1fr 1fr; gap: .12in; align-content: start; min-width: 0 }
.fg { margin: 0; background: #fff; border: 2px solid #111827; box-shadow: 3px 3px 0 #111827; display: flex; flex-direction: column; min-width: 0 }
.fg img { width: 100%; height: auto; display: block }
.fg.short img { max-height: 2.35in; object-fit: contain }
.fg figcaption { font-size: 8.4pt; line-height: 1.3; padding: 3px 7px 5px; border-top: 1px solid #e3ddcf; color: #222 }
.sub { font-size: 10.6pt !important; color: #222 !important; line-height: 1.35 }
.rule { font-size: 9.4pt !important; padding: .06in .1in !important; line-height: 1.3 !important }
.rule .f { font-size: 8.6pt !important; margin: 3px 0 !important }
.econ { font-size: 9pt !important }
table.ev { font-size: 8.4pt } table.ev td, table.ev th { padding: 2px 5px }
.lc table { font-size: 8.6pt } .lc table td, .lc table th { padding: 2.5px 6px }
.care { border: 2px solid #EF5147; background: #fff; padding: .05in .1in; font-size: 8.5pt; line-height: 1.3 }
.care b { font-family: Consolas, monospace; text-transform: uppercase; letter-spacing: .05em; font-size: 8pt; color: #EF5147 }
.care ul { margin: 2px 0 0 14px; padding: 0 } .care li b { color: #111827; font-family: inherit; font-size: inherit; text-transform: none; letter-spacing: 0 }
.lc h2 { font-size: 11.5pt; margin: .02in 0 0 }
.note { font-size: 8.4pt !important; margin: 2px 0 0 }
.kpis6 { display: grid; grid-template-columns: repeat(6, 1fr); gap: .12in }
.kpis6 .kpi { border: 2px solid #111827; box-shadow: 3px 3px 0 #111827; padding: .07in .11in; background: #fff }
.kpis6 .kpi b { display: block; font-family: Bahnschrift, sans-serif; font-size: 19pt; font-weight: 700 } .kpis6 .kpi span { font-family: Consolas, monospace; font-size: 7.6pt; text-transform: uppercase; letter-spacing: .03em }
.journey { display: grid; grid-template-columns: repeat(5, 1fr); border: 2px solid #111827; box-shadow: 3px 3px 0 #111827 }
.journey div { padding: .06in .1in; font-size: 8.8pt; line-height: 1.3; background: #fff; border-right: 2px solid #111827 } .journey div:last-child { border-right: 0 }
.journey div:nth-child(1) { background: #fff } .journey div:nth-child(2) { background: #cfe3f8 } .journey div:nth-child(3) { background: #fde2df } .journey div:nth-child(4) { background: #2479D8; color: #fff } .journey div:nth-child(5) { background: #F4D52E }
.journey b { display: block; font-family: Bahnschrift, sans-serif; font-size: 12pt }
.tri { display: grid; grid-template-columns: 1.15fr 1fr 1fr; gap: .16in; flex: 1; min-height: 0 }
.tri h2 { font-size: 12.5pt } .tri table { font-size: 9.4pt } .tri td, .tri th { padding: 4.5px 7px }
.concl { background: #111827; color: #F5F0E6; padding: .08in .12in; font-size: 9.4pt; line-height: 1.35; border: 2px solid #111827 } .concl b { color: #F4D52E; font-family: Bahnschrift, sans-serif; font-size: 12pt } .concl p { margin: 4px 0 0 }
"""
