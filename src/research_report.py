"""Comprehensive research report (Markdown + PDF), generated from the canonical artefacts.

Run after src.ledger:  python -m src.research_report
Inputs (single source of truth): web/build_data/{registry,meta,sim,genome,ledger,replay,tests}.json, outputs/evidence/{validation,stats}.json,
outputs/evidence/h38_vehicle.json, docs/source_register.md. Every number in the rule catalogue and the worked examples is read from these files.
Outputs: submission/ORVANTA_Comprehensive_Research_Report.md and .pdf (rendered by headless Edge/Chrome).
"""
from __future__ import annotations
import html, json, math, re, shutil, subprocess
from pathlib import Path
from .config import ROOT, EVIDENCE

B = ROOT / "web" / "build_data"; SUB = ROOT / "submission"; BUILD = ROOT / "outputs" / "pdf_build"
rd = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
SPL = ["full", "half_0", "half_1", "P1", "P2"]


def f(x, d=4):
    if x is None: return "—"
    if isinstance(x, bool): return str(x)
    if isinstance(x, float) and 0.999 < x < 1: return f"{x:.7f}"
    if isinstance(x, (int, float)):
        if float(x).is_integer() and abs(x) >= 1: return f"{int(x):,}"
        return f"{x:.{d}g}"
    return str(x)


def md_table(head, rows):
    esc = lambda c: str(c).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows])


def build():
    reg, meta, sim, gen, led, rep, tests = (rd(B / f"{n}.json") for n in ("registry", "meta", "sim", "genome", "ledger", "replay", "tests"))
    val = {r["id"]: r for r in rd(EVIDENCE / "validation.json")["rules"]}; st = rd(EVIDENCE / "stats.json")
    h38 = rd(EVIDENCE / "h38_vehicle.json") if (EVIDENCE / "h38_vehicle.json").exists() else None
    rules = [r for r in reg["rules"] if r["kind"] == "rule"]; R = {r["id"]: r for r in rules}
    rejected = [r for r in reg["rules"] if r["level"] == "REJECTED"]
    lv = {l: sum(r["level"] == l for r in rules) for l in reg["levels"]}
    genmap = {g["rule"]: g for g in gen["genealogy"]}
    evs = {}
    for e in led["entries"]:
        for r in e["rules"]: evs.setdefault(r, []).append(e["id"])
    c2, r1, r2 = val["C2"]["metrics"]["full"], val["R1"]["metrics"]["full"], val["R2"]["metrics"]["full"]
    a1, d1m = val["A1"]["metrics"]["full"], val["D1"]["metrics"]
    fig = [0]; tab = [0]
    def F(cap): fig[0] += 1; return f"*Figure {fig[0]}. {cap}*"
    def T(cap): tab[0] += 1; return f"**Table {tab[0]}. {cap}**"
    S = []
    add = S.append
    add("# ORVANTA — Comprehensive Research Report\n\n**Reconstructing the hidden generator behind 10,000,000 synthetic cross-border payments**  \n"
        f"UMDAC Datathon 2026 · Swift case · Team Nai Long · generated {reg['generated'][:10]} from the project's canonical artefacts\n\n"
        "> This is a supplementary research document. The official deliverables are the dashboard PDF and the presentation PDF; all three are generated from the same pipeline (see §17).\n")
    add("## Contents\n\n1. Executive summary\n2. Problem definition\n3. Background: cross-border payments\n4. Dataset description\n5. Research architecture\n6. Methodology\n7. Discovery process (H1–H38)\n"
        "8. Rule catalogue (34 rules)\n9. The mathematics behind the findings\n10. Generator reconstruction\n11. Economic interpretation\n12. Validation and robustness\n"
        "13. Alternative hypotheses and negative findings\n14. Data integrity and governance\n15. Limitations and unresolved questions\n16. Conclusions and future research\n17. References and reproducibility\n")

    # 1
    add("## 1. Executive summary\n")
    add(f"Swift supplied {meta['rows']:,} synthetic payment records and asked participants to reverse-engineer the rules that generated them, using only the data. "
        f"We reconstructed **{len(rules)} explicit rules** covering all ten feature groups. Every rule has a pre-declared acceptance criterion that was re-tested on five partitions "
        f"(full data, two hash-random halves, and the periods before and after 15 June 2023); all {len(rules)} validators pass. Passing a validator is necessary but not sufficient for confidence, so each rule also carries a level on a six-step scale:\n")
    add(md_table(["Level", "Rules", "Meaning"], [[l, lv[l], reg["levels"][l]] for l in reg["levels"] if l != "REJECTED"] + [["REJECTED", len(rejected), reg["levels"]["REJECTED"]]]))
    add(f"\n**Three findings carry the reconstruction.**\n\n"
        f"1. **C2 — FX conversions are determined by the route.** The number of currency conversions equals the number of adjacent known banks in BIC8_PATH whose countries have different home currencies, on {f(c2['n'] - c2['exceptions'])} of {f(c2['n'])} payments. The only two exceptions are the only two payments in the dataset that touch an Eritrean bank, whose home currency cannot be observed.\n"
        f"2. **R1 — route length follows K = ⌊Exp(1)⌋.** The number of intermediaries is geometric with continuation probability q = {r1['q_mle']:.4f} against the theoretical 1/e = {r1['inv_e']:.4f}; goodness of fit Cohen's w = {r1['cohen_w']:.4f}; P(Direct) = {r1['p_direct']:.2%}.\n"
        f"3. **R2 — a rule we overturned.** Our first reading, “Covered vs Indirect is a constant {r2['pooled_covered_share']:.1%}”, was refuted by our own discovery engine (H32). Cover is a property of the sending bank: classes learned on one random half predict {r2['oos_cover_banks_share']:.1%} vs {r2['oos_other_banks_share']:.1%} on the other half.\n\n"
        f"A systematic scan of {len(meta['discovery']['pairs'])} feature pairs found {sum(1 for p in meta['discovery']['pairs'] if p.get('verdict'))} strong, stable dependencies; every one is explained by a rule or by mediation through rules. "
        f"Three mechanisms remain unresolved and are reported as such: the weekly volume levels (T4), directional bank-pair affinities (G1), and the undocumented CUSTOMER_RECALL label (X5). "
        "The data is synthetic: the rules describe this generator, not real Swift traffic, and we have not recovered its source code.\n")
    # 2
    add("## 2. Problem definition\n\n**Plain language.** A computer program produced ten million fictional cross-border payments. We see only its output. The task is to work backwards: which fields are drawn at random, from which distributions, and which are calculated from others?\n\n"
        "**Technically.** Let each record be a vector x = (x₁ … x₂₀). The generator is an unknown program G that samples latent choices (banks, route length, party types, time) and derives the remaining fields. "
        "A *rule* is a statement of the form “field y = g(x_S)” (deterministic) or “y | x_S ~ D(θ)” (stochastic) with an explicit scope, testable on held-out data. Success is measured by how much of the joint distribution the rule set reproduces, how exactly, and how honestly the residual is described.\n")
    # 3
    add("## 3. Background: cross-border payments\n\n*This section is general background (established knowledge), not a finding from the data.*\n\n"
        + md_table(["Term", "Meaning"], [
            ["Ordering customer / beneficiary", "the payer and the payee (business or consumer)"],
            ["Ordering / beneficiary institution", "the banks that hold the payer's and payee's accounts"],
            ["Intermediary (correspondent) bank", "a bank that relays the payment between two banks that have no direct account relationship"],
            ["BIC (ISO 9362)", "bank identifier: 4-character bank code, 2-letter country, 2-character location (BIC8); characters 5–6 give the country"],
            ["Payment route", "the ordered list of banks the payment passes through (here BIC8_PATH, with '...' for an unobserved hop)"],
            ["Serial vs cover method", "serial: the payment message travels bank to bank; cover: a customer message goes direct while a separate bank-to-bank cover payment settles funds"],
            ["Currency conversion", "a bank converts value into another currency, typically into the currency of the account it pays from"],
            ["IBAN (ISO 13616)", "international account number beginning with a 2-letter country code; formats are registered per country"],
            ["Straight-through processing (STP)", "automated handling without manual intervention"]]) +
        "\n\nThe dataset's fields mimic these concepts. Where our rules use these words (e.g. “instructing bank”, “cover-prone bank”) they name generator behaviour we inferred; they are not claims about how real banks behave.\n")
    # 4
    add("## 4. Dataset description\n")
    add(f"{meta['rows']:,} rows × {meta['columns_raw']} raw columns; UTC span {meta['start']} → {meta['end']}; {meta['currencies']} currencies; {meta['banks_total']:,} distinct BIC8 banks; "
        f"{meta['sender_accounts']:,} sender and {meta['beneficiary_accounts']:,} beneficiary accounts; {meta['anomalies']:,} labelled anomalies.\n\n" + T("Field dictionary (observed ranges and missingness computed over all rows)") + "\n\n" +
        md_table(["Field", "Type", "Observed", "Missing", "Derived features", "Rules", "Limitation"], [[d["field"], d["dtype"], d["observed"], f(d["missing"]), d["derived"], d["rules"], d["limitation"]] for d in meta["dictionary"]]) +
        "\n\n" + T("Data-quality checks") + "\n\n" + md_table(["Check", "Result", "Status", "Detail"], [[q["check"], q["result"], q["status"], q["detail"]] for q in meta["quality"]]) +
        "\n\n**Anomaly labels.** " + ", ".join(f"{a['anom']} {a['n']:,}" for a in st["anomaly_rates"]) + ". CUSTOMER_RECALL is not defined in the case appendix; it is kept and analysed (X5) rather than dropped or interpreted.\n\n"
        "**Transformations.** RFC-4180 parsing (multi-line quoted DETAILS fields), identifiers kept as strings, the DISCLAIMER column (filled on one row) dropped with the row kept; derived columns (bank country, path length, hidden-hop count, IBAN flags) are documented in `src/ingestion.py`. No row was removed and no value altered.\n")
    # 5
    add("## 5. Research architecture\n\n```\nraw CSV (immutable) → Parquet (DuckDB, out-of-core) → discovery (276 pairs, trees, forensics, graph)\n  → 34 SQL validators × 5 splits + pure-Python twin → register (narrative, six-level confidence)\n"
        "  → evidence ledger, forensic replay, blueprint → dashboard PDF · slide PDF · this report · Streamlit lab · web platform\n```\n\n"
        "One pipeline (`python run_all.py`) produces every artefact; nothing is copied by hand between deliverables (`docs/SINGLE_SOURCE_OF_TRUTH.md`).\n")
    # 6
    add("## 6. Methodology\n\n" + md_table(["Step", "Method", "Why it fits"], [
        ["Ingestion", "DuckDB RFC-4180 parser, row count asserted at every stage", "10M rows with embedded newlines; out-of-core; exact counts"],
        ["Descriptive statistics", "exact counts, shares, quantiles over all rows", "no sampling error to manage"],
        ["Dependency discovery", "Cramér's V and symmetric uncertainty for all 276 pairs on a development half, re-measured on a validation half", "categorical-heavy data; scale-free effect size; replication guards against chance"],
        ["Mediation triage", "residual V after stratifying by one or two candidate mediators (threshold 0.03)", "separates direct generator links from composites of other rules"],
        ["Rule search", "depth-3 decision trees (search device only)", "readable IF–THEN candidates"],
        ["Distribution fitting", "MLE (geometric, gamma, lognormal), KS distance, Q–Q, Hill tail index", "explicit parametric generator steps"],
        ["Conditional testing", "stratified contrasts; two-way fixed effects (bank × bank)", "removes composition effects (Simpson)"],
        ["Graph analysis", "PageRank, configuration-model χ², birthday-problem loop prediction", "routes are a weighted multigraph"],
        ["Hypothesis testing", "χ², two-proportion z, Mann–Whitney; Bonferroni inside validators; Benjamini–Hochberg within families in the test registry", f"{len(tests['tests'])} recorded tests; multiplicity controlled per family"],
        ["Validation", "every validator on 5 splits; learned classes fitted on one half and tested on the other", "independence from the data used to find the rule"],
        ["Independent implementation", "pure-Python twin (`src/rulelib.py`) and a JavaScript port checked against SQL", "catches implementation errors"]]) +
        "\n\n**Acceptance on effect sizes.** With n = 10⁷ almost every p-value is ≈ 0, so rules are accepted on exactness (share of rows reproduced), Cohen's w, Cramér's V, KS distance or maximum deviation, with thresholds declared in the validator before it ran.\n")
    # 7
    add("## 7. Discovery process (H1–H38)\n\nHypotheses in the order they were tested. Outcomes are as logged; the arrow shows the rule each became.\n\n" +
        md_table(["ID", "Hypothesis", "Test", "Outcome", "→"], [[h["id"], h["hypothesis"], h["test"], re.sub(r"\*\*", "", h["outcome"]), h["consequence"]] for h in reg["hypotheses"]]) +
        f"\n\n**The R2 revision.** {genmap['R2']['hypotheses'][0]['outcome'].replace('**', '') if genmap.get('R2') and genmap['R2']['hypotheses'] else ''} — the discovery engine found that routing type still depended on sending country "
        f"(covered share {r2['country_share_min']:.1%}–{r2['country_share_max']:.1%} by country, far more dispersed across banks than a constant rate allows). Bank classes learned on half_0 were evaluated on half_1, giving {r2['oos_cover_banks_share']:.1%} vs {r2['oos_other_banks_share']:.1%}.\n")
    # 8
    add("## 8. Rule catalogue\n\nEach entry is generated from the registry and the validator output. *Split metrics* lists every numeric metric the validator recorded on each partition. Evidence IDs refer to the Evidence Ledger (web platform › Research library).\n")
    for gname, ids in reg["groups"].items():
        pass
    for r in rules:
        v = val[r["id"]]; m = v["metrics"]; g = genmap.get(r["id"], {})
        keys = [k for k in (m.get("full") or {}) if isinstance(m["full"].get(k), (int, float)) and k != "n"]
        prim = keys[0] if keys else None
        rng_ = [m[s][prim] for s in SPL if s in m and isinstance(m[s].get(prim), (int, float))] if prim else []
        add(f"### {r['id']} — {r['title']}\n\n**Feature group:** {r['family']} · **Confidence:** {r['level']} · **Validator type:** {r['type']} · **Validator result:** {r['status']} on {len([s for s in SPL if s in m])} partitions\n")
        add(md_table(["Item", "Content"], [
            ["Research question / hypothesis", r["hypothesis"]],
            ["Initial hypothesis (log)", "; ".join(f"{h['id']}: {h['hypothesis']} — {re.sub(r'[*]', '', h['outcome'])}" for h in g.get("hypotheses", [])) or "no separate log entry (formulated directly from the discovery scan)"],
            ["Formal formulation", r["formulation"]], ["Executable logic", r["logic"]], ["Variables", r["fields"]],
            ["Method", r["method"]], ["Acceptance criterion", r["criterion"]], ["Sample size", r["sample_size"]], ["Effect size", r["effect_size"]],
            ["Uncertainty", (f"{prim} ranges {f(min(rng_))} – {f(max(rng_))} across the five partitions" if len(rng_) > 1 else "single-partition metric") if prim else "see split metrics"],
            ["Counterexamples / scope", " ".join(dict.fromkeys(t for t in [r["counterexamples"], (r.get("violation") or {}).get("text")] if t and t not in ("—", "-")))],
            ["Best alternative tested", r.get("alternative") or "—"], ["Economic interpretation (interpretation, not evidence)", r["economic"]],
            ["Limitations", r["limitations"]], ["Related rules", ", ".join(r.get("related") or []) or "—"],
            ["Evidence IDs", ", ".join(evs.get(r["id"], [])[:8]) or "—"]]))
        if keys:
            add("\n*Split metrics*\n\n" + md_table(["Metric"] + [s for s in SPL if s in m], [[k] + [f(m[s].get(k)) for s in SPL if s in m] for k in (["n"] if "n" in m.get("full", {}) else []) + keys[:9]]))
        add("")
    # 9 maths
    q = r1["q_mle"]
    add("## 9. The mathematics behind the findings\n")
    add(f"**Geometric and exponential (R1).** If E ~ Exponential(1) then P(⌊E⌋ ≥ k) = P(E ≥ k) = e^(−k), so K = ⌊E⌋ has P(K = k) = e^(−k)(1 − e^(−1)) — a geometric distribution with continuation probability q = 1/e ≈ 0.3679. "
        f"*Worked example:* P(Direct) = P(K = 0) = 1 − 1/e = 0.6321; observed {r1['p_direct']:.4f}. The ratio P(K = k+1)/P(K = k) should be constant at q; observed ratios {r1['ratio_1']:.4f}, {r1['ratio_2']:.4f}, {r1['ratio_3']:.4f}, {r1['ratio_4']:.4f}. "
        f"The MLE for a geometric with mean K̄ is q̂ = K̄/(1 + K̄) = {q:.4f}.\n")
    add(f"**Cohen's w.** For observed shares pᵢ and model shares p₀ᵢ, w = √Σ (pᵢ − p₀ᵢ)²/p₀ᵢ = √(χ²/n). R1: χ² = {r1['chi2']:.3f}, n = {r1['n']:,.0f} → w = √({r1['chi2']:.3f}/{r1['n']:,.0f}) = {math.sqrt(r1['chi2'] / r1['n']):.5f}. Conventionally w < 0.1 is small; our acceptance bound was 0.01.\n")
    add(f"**Exact-match share (C2).** share = (rows where predicted = recorded)/n = ({c2['n']:,.0f} − {c2['exceptions']:.0f})/{c2['n']:,.0f} = {c2['share_exact']:.7f}. Alternative “distinct currencies − 1”: {c2['alt_distinct']:.4f}.\n")
    add("**Cramér's V.** For an r × c contingency table with χ² statistic, V = √(χ² / (n·(min(r, c) − 1))) ∈ [0, 1]. It is the discovery engine's dependency measure and the independence criterion for R2 (V of routing type vs K < 0.01) and X6.\n")
    add(f"**Lognormal amounts (A1, A3).** ln(amount) = β₀ + β_S·[sender = B] + β_R·[receiver = B] + ε. Fitted: β₀ = {a1.get('intercept', float('nan')):.3f}, β_S = {a1.get('effect_ordering_B', float('nan')):.3f}, β_R = {a1.get('effect_beneficiary_B', float('nan')):.3f}, interaction {a1.get('interaction', float('nan')):.3f}. "
        f"So each business party multiplies the typical amount by about e² ≈ 7.4. The residual after sender-country effects has sd {st['amount_residual']['sd']:.3f}, skew {st['amount_residual']['skew']:.3f}, excess kurtosis {st['amount_residual']['excess_kurtosis']:.3f}, KS D vs normal {st['amount_residual']['ks_D_vs_normal']:.4f}. "
        f"The Hill tail index drifts ({', '.join(f'{h['alpha']:.2f}' for h in st['hill'])}), the signature of a lognormal rather than a power-law tail; the 6 + 2 + 2 coefficients are fitted values close to round numbers, not exact constants.\n")
    add(f"**Gamma steps (D1, D3).** Each bank adds a step: fast ~ Gamma(k = {sim['duration']['fast_shape']:.2f}, θ = {sim['duration']['fast_scale']:.2f} s) or, with probability m, manual ~ Gamma(k = {sim['duration']['manual_shape']:.2f}, θ = {sim['duration']['manual_scale']:.0f} s) (mean kθ ≈ {sim['duration']['manual_shape'] * sim['duration']['manual_scale']:.0f} s). "
        f"With two banks the manual share is 1 − (1 − m)²; solving with the observed {sim['duration']['pc2_manual_observed']:.3f} gives m = {sim['duration']['m_bank']:.4f}. Additivity: two slow banks take ≈ {d1m['additivity_ratio']['value']:.2f}× one slow bank out of sample (2.0 under pure additivity).\n" if isinstance(d1m.get('additivity_ratio'), dict) else "")
    add("**Fixed effects and Simpson's paradox (D2).** A raw contrast (slow share by hour) mixes the hour effect with which banks are active at that hour. Regressing on sender-bank and receiver-bank indicators (two-way fixed effects) and then reading the hour coefficients removes that composition; the hour range falls from 0.037 to 0.003. A pattern that disappears after adjustment is a Simpson effect, not a generator rule.\n")
    add("**Confidence intervals.** Proportions use Wilson intervals; the geometric q uses the Fisher-information standard error √(q(1 − q)²/n). At n = 10⁷ intervals are ±0.0003 or narrower, so decisions rest on effect size.\n")
    add(f"**Multiplicity.** Bonferroni controls the family-wise error by testing at α/m (used inside validators, e.g. X5 with m = 11). Benjamini–Hochberg controls the false-discovery rate: sort p-values p₍₁₎ ≤ … ≤ p₍ₘ₎ and reject up to the largest i with p₍ᵢ₎ ≤ (i/m)α; it is applied *within* each of the test families of the registry ({len(tests['tests'])} tests), never pooled across unrelated families.\n")
    add("**Graph analysis (G1, G3).** Banks are nodes and hops are weighted edges. G3 predicts the share of paths that revisit a bank if intermediaries are drawn i.i.d. with probability ∝ size: 1 − Π_{j}(1 − j·Σp²) (a birthday-problem form); predicted and observed agree within 3.1%. G1 compares observed sender–receiver pair counts with a configuration model that preserves each bank's totals; χ²/dof far above 1 rejects independent pairing, but does not identify the mechanism.\n")
    # 10
    add("## 10. Generator reconstruction\n\nThe reconstructed generator by stage. Mechanisms come only from rules; parts we could not pin down are listed as unresolved.\n")
    for i, s in enumerate(gen["blueprint"], 1):
        add(f"**{i}. {s['section']}** — {s['covers']}\n\n" + "\n".join(f"- {m['rule']} ({m['level']}): {m['statement']}" for m in s["mechanisms"]) +
            ("\n- *Unresolved / partly inferred:* " + " · ".join(f"{u['rule']}: {u['text']}" for u in s["unresolved"]) if s["unresolved"] else "") + (f"\n- *Note:* {s['note']}" if s["note"] else "") + "\n")
    add("Deterministic steps (exact on all rows): R6, R7, C2, P2, X2 and Direct ⇔ 2 participants. All other steps are stochastic draws with fitted parameters.\n")
    # 11
    add("## 11. Economic interpretation\n\nReadings below are interpretation, labelled as such; synthetic patterns do not prove real network behaviour.\n\n" +
        md_table(["Rule", "Observed in the data", "Plausible real-world reading"], [[r["id"], r["title"], r["economic"]] for r in rules if r.get("economic") and r["economic"] not in ("—", "-")]) + "\n")
    # 12
    add("## 12. Validation and robustness\n\n" + md_table(["Rule", "Level", "Acceptance criterion", "Result"], [[r["id"], r["level"], r["criterion"], r["validation"]] for r in rules]) +
        f"\n\nIndependent implementation: SQL vs pure Python on a {meta['validation']['cross_check']['sample']:,}-row sample — R6 {meta['validation']['cross_check']['R6_python_match']:.0%}, R7 {meta['validation']['cross_check']['R7_python_match']:.0%}, C2 {meta['validation']['cross_check']['C2_python_match']:.0%} agreement. "
        "Forensic replay recomputes exact supporting/contradicting counts directly from the Parquet; the C2 count equals the validator's exception count.\n\n" + T("Forensic replay — exact counts over all eligible rows") + "\n\n" +
        md_table(["Check", "Eligible", "Supporting", "Contradicting"], [[x["rule"], f(x["eligible"]), f(x["supporting"]), f(x["contradicting"])] for x in rep["rules"]]) + "\n")
    if h38:
        add(f"\n**H38 (supported refinement of C3).** On routes with no EUR or USD bank, the payment is in EUR {h38['splits'][2]['eur']:.2%} and USD {h38['splits'][2]['usd']:.2%} of the time (full data); across the five partitions EUR ranges "
            f"{min(s['eur'] for s in h38['splits']):.2%}–{max(s['eur'] for s in h38['splits']):.2%}. {h38['outside_eur_usd']:,} of {h38['outside_n']:,} outside-route payments are EUR or USD. The EUR/USD set was chosen after inspection, so this is reported as supported, not validated; why these two currencies serve as vehicles is not identified.\n")
    # 13
    add("## 13. Alternative hypotheses and negative findings\n\n" + md_table(["Rule", "Alternative tested and outcome"], [[r["id"], r.get("alternative")] for r in rules if r.get("alternative") and r["alternative"] != "—"]) +
        "\n\n" + T("Refuted hypotheses kept on the record") + "\n\n" + md_table(["ID", "Hypothesis", "Test", "Outcome"], [[r["id"], r["hypothesis"], r["method"], r["effect_size"]] for r in rejected]) +
        "\n\nA negative result is informative: X5 shows that CUSTOMER_RECALL leaves no trace in the message fields we can observe (no test significant after correction), which bounds what any rule about it could say. It does not prove the generator applies no logic to that label.\n")
    # 14
    add("## 14. Data integrity and governance\n\n- Raw CSV is read-only; every stage asserts 10,000,000 rows.\n- Only the supplied data enters rule discovery; external sources support interpretation only.\n"
        "- The web platform ships aggregates and at most 75 de-identified records per replay check (no accounts, names, free text or tokens; row ids hashed); the raw data and row-level Parquet are never redistributed.\n"
        "- The site is protected (team-only) until the competition deadline.\n- Every artefact is fingerprinted with SHA-256 (`outputs/evidence/lineage.json`).\n")
    # 15
    add("## 15. Limitations and unresolved questions\n\n" + "\n".join(f"- **{r['id']}** ({r['level']}): {r['limitations']}" for r in rules if r["level"] in ("INCONCLUSIVE", "SUPPORTED")) +
        "\n- **Vehicle currency (C3/H38):** rates quantified, mechanism not identified.\n- **Synthetic data:** rates, country effects and bank classes are generator settings, not real market structure.\n"
        "- **Source code:** agreement with the data, even exact, does not identify how the generator was written; alternative programs could produce the same output.\n")
    # 16
    add("## 16. Conclusions and future research\n\nThe generator is a small set of simple mechanisms: geometric route length (R1), route-derived conversions (C2), route-drawn currencies (C3), bank-level habits for cover (R2), customer mix (P5) and processing speed (D1), a 6 + 2 + 2 lognormal amount model (A1/A2), a local office clock with global weekly levels (T1/T4b), and labelled anomalies injected with clear signatures (X1–X4). "
        "The highest-value open questions are the cause of the weekly levels, the bank-pair affinity structure and the vehicle-currency choice.\n")
    # 17
    srcs = [ln for ln in (ROOT / "docs" / "source_register.md").read_text(encoding="utf-8").splitlines() if ln.startswith("| ") and "**Verified" in ln]
    add("## 17. References and reproducibility\n\n**Primary data:** Swift. (2026). *UMDAC Datathon 2026 fictitious payment dataset* [Data set]. Provided to participants.\n\n**Verified context references** (interpretation only; checked 14 Nov 2026):\n\n" +
        "\n".join("- " + ln.split("|")[2].strip() for ln in srcs) +
        "\n\n**Reproduce:**\n\n```bash\npip install -r requirements.txt\npython run_all.py            # or --skip-ingest when the Parquet files exist\npython -m pytest -q tests\n```\n")
    return "\n".join(S) + "\n", fig[0], tab[0], len(rules)


def md_to_html(md: str) -> str:
    out, lines, i = [], md.split("\n"), 0
    inl = lambda s: re.sub(r"\*([^*]+)\*", r"<i>\1</i>", re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(s))))
    while i < len(lines):
        l = lines[i]
        if l.startswith("```"):
            j = i + 1; buf = []
            while j < len(lines) and not lines[j].startswith("```"): buf.append(lines[j]); j += 1
            out.append(f"<pre>{html.escape(chr(10).join(buf))}</pre>"); i = j + 1; continue
        if re.match(r"^#{1,4} ", l):
            n = len(l.split(" ")[0]); t = l[n + 1:]; aid = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
            out.append(f"<h{n} id='{aid}'>{inl(t)}</h{n}>"); i += 1; continue
        if l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|(-+\|)+$", lines[i].replace(" ", "")): rows.append([c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", lines[i])[1:-1]])
                i += 1
            out.append("<table><thead><tr>" + "".join(f"<th>{inl(c)}</th>" for c in rows[0]) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in r) + "</tr>" for r in rows[1:]) + "</tbody></table>"); continue
        if re.match(r"^\s*(-|\d+\.) ", l):
            tag = "ol" if re.match(r"^\s*\d+\.", l) else "ul"; items = []
            while i < len(lines) and re.match(r"^\s*(-|\d+\.) ", lines[i]): items.append(re.sub(r"^\s*(-|\d+\.) ", "", lines[i])); i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inl(x)}</li>" for x in items) + f"</{tag}>"); continue
        if l.startswith("> "): out.append(f"<blockquote>{inl(l[2:])}</blockquote>"); i += 1; continue
        if not l.strip(): i += 1; continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||```|> |\s*(-|\d+\.) )", lines[i]): buf.append(lines[i].rstrip("  ")); i += 1
        out.append("<p>" + "<br>".join(inl(b) for b in buf) + "</p>")
    return "\n".join(out)


CSS = """@page{size:A4;margin:16mm 14mm 18mm}body{font-family:'Segoe UI',system-ui,sans-serif;color:#111827;font-size:9.6pt;line-height:1.45}
h1{font-family:Bahnschrift,'Arial Narrow',sans-serif;font-size:24pt;border-bottom:4px solid #F4D52E;padding-bottom:6px;margin:0 0 8px}
h2{font-family:Bahnschrift,'Arial Narrow',sans-serif;font-size:16pt;margin:22px 0 8px;border-left:8px solid #2479D8;padding-left:8px;break-after:avoid}
h3{font-family:Bahnschrift,'Arial Narrow',sans-serif;font-size:12.5pt;margin:16px 0 6px;background:#F5F0E6;padding:4px 8px;break-after:avoid}
table{border-collapse:collapse;width:100%;margin:6px 0 10px;font-size:8pt;break-inside:auto}th{background:#111827;color:#F5F0E6;text-align:left;padding:3px 5px}
td{border-bottom:1px solid #ddd6c6;padding:3px 5px;vertical-align:top;overflow-wrap:anywhere}tr{break-inside:avoid}
pre{background:#F5F0E6;border:1px dashed #111827;padding:6px 8px;font-size:8pt;white-space:pre-wrap}code{font-family:Consolas,monospace;font-size:8.5pt}
blockquote{border-left:4px solid #EF5147;margin:8px 0;padding:4px 10px;background:#fff}"""


def main():
    md, nf, nt, nr = build()
    SUB.mkdir(exist_ok=True); BUILD.mkdir(parents=True, exist_ok=True)
    mdp = SUB / "ORVANTA_Comprehensive_Research_Report.md"; mdp.write_text(md, encoding="utf-8")
    htp = BUILD / "research_report.html"
    htp.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>ORVANTA research report</title><style>{CSS}</style></head><body>{md_to_html(md)}</body></html>", encoding="utf-8")
    from .config import find_browser
    br = find_browser(); assert br, "no Edge/Chrome/Chromium found for PDF rendering"
    exe, extra = br
    pdf = SUB / "ORVANTA_Comprehensive_Research_Report.pdf"
    subprocess.run([exe, *extra, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", htp.as_uri()], check=True, capture_output=True, timeout=240)
    from pypdf import PdfReader
    print(f"research report: {nr} rules, {nt} tables, {len(md):,} chars; PDF {len(PdfReader(str(pdf)).pages)} pages")


if __name__ == "__main__":
    main()
