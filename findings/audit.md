# Strict audit (judge simulation) and GO / NO-GO

Scale: rubric 0–20 per sub-criterion (17–20 = Exceptional). The estimates are conservative and supported by evidence; they are not inflated.

| Sub-criterion (weight) | Score | Evidence | Remaining weakness |
|---|---|---|---|
| 1.1 Hypotheses (5) | 17 | 37-entry hypothesis log (H1–H37) plus 29 rejected candidates in the evidence registry, many rejected; shows course changes (sample → R5 → R5b; G1 independence → rejected) | the slides show the loop only briefly |
| 1.2 Rule reconstruction (12) | 17 | 34 typed rules with formulas; a runnable Monte-Carlo version of the reconstructed generator compared against observation (web simulator); `rulelib.py` as a generator spec; distributions named with parameters (geometric 1/e, Gamma(2, 817 s), lognormal σ ≈ 2.08) | weekly levels, vehicle currency and pair affinities not specified |
| 1.3 Explanatory depth (14) | 18 | alternatives rejected per rule; Simpson FE check; out-of-sample D1; loop prediction G3; Bonferroni within validators and per-family BH on the 297-test registry; sensitivity tables | economic readings rely on general knowledge (labelled) |
| 1.4 Specificity (5) | 17 | quantified titles (99.99998%, 1/e, ×7.4, 3.1%, χ²/dof 358) | — |
| 1.5 Correctness (9) | 15–18 | exact rules cannot be wrong on this data; stochastic parameters sit inside 95% CIs of theoretical values | the organisers' reference rules are unknown (e.g. T1 DST, C1 vehicle choice) |
| 2.1 Economic explanation (5) | 15 | mechanism per rule; alternatives considered (R5b, P4, G1) | external references not yet verified by the team |
| 2.2 Consistency (4) | 18 | observation vs interpretation separated; departures from reality listed (findings/economic_interpretation.md) | — |
| 2.3 Coverage (3) | 18 | all 20 fields and 6 labels; open questions prioritised | — |
| 3.1 Data preparation (5) | 18 | issues log; reconciliation asserts at every stage; document conflicts logged | — |
| 3.2 Claim–evidence (7) | 18 | every KPI and chart reads outputs/evidence; registers generated from validation.json | slide body text has a few rounded constants (×1.5, ~20 min) |
| 3.3 Method (8) | 18 | simplest adequate methods, decision register (27 entries), per-class detector metrics, no decorative ML | analyst thresholds (disclosed and sensitivity-tested) |
| 3.4 Responsible use (3) | 18 | provided data only; no raw rows shipped; product not branded as Swift; AI disclosed | — |
| 4.1 Narrative (6) | 15 | headline → method → groups → limits → conclusion | slide design polish belongs to the pitch team |
| 4.2 Dashboard (8) | 17–18 | 14-page PDF, each page with rules + charts + reading; a 39-route interactive platform (explorer, simulator, playground, zoomable atlas) with output-kind labels; consistent design system | dense rule cards in the PDF |
| 4.3 Visual clarity (6) | 16 | takeaway titles; semantic colour (coral only for anomaly/risk); log scales labelled | some charts are small inside their grids |

**Weighted estimate:** about 17.4 / 20 ≈ **87%**. The automated discovery engine corrected one rule (R2) and found two more (C3, P5). Forensics added F1 and T4b, the dependency atlas and lineage manifest make every claim traceable, and all 55 strong feature dependencies are now explained.

## Readiness gates (Part XII §34)
| Gate | Status | Evidence |
|---|---|---|
| No unresolved critical data-integrity issue | ✅ | issues log; reconciliation tests |
| Every major numerical claim reproducible | ✅ | `python run_all.py`; registers generated from validators |
| No important rule unsupported | ✅ | 34/34 validators PASS on 5 splits; G1 and X5 stated as negative/partial results; R2 corrected after discovery scan |
| No model incorrectly evaluated | ✅ | detectors: per-class P/R/F1 + confusion; no accuracy; GMM used for density only |
| Dashboard shows correct statistics | ✅ | cubes reconcile to 10M; KPI and filter tests |
| Controls work | ✅ | AppTest functional tests (Streamlit) + Playwright end-to-end tests on Edge (web: all 39 routes, URL state, explorer numbers vs Python, simulator, atlas, phone layout) |
| Presentation consistent with outputs | ✅ | slides generated from the same JSON |
| Official requirements met | ✅ | 15 dashboard pages (5–15), 20 slides (10–20), PDF, ≤1 slide per group |
| Critical implementation defects | ✅ none known | see docs/FINAL_QA_REPORT.md and docs/FINAL_INDEPENDENT_JUDGE_AUDIT.md; web defect register D-W01…D-W21 closed (`docs/defect_register.md`) |

## Verdict: **GO (technical)** — conditional **GO for submission** once the team closes three non-technical items
1. Verify each external reference (title, date, URL) in `docs/source_register.md`, or remove it from the references slide.
2. Rehearse `docs/judge_qa.md`; every member should be able to explain C2, R1, D2 (Simpson) and G3.
3. Rename files as the submission link requires and submit before **19 Nov 2026, 12:00 PM**.
