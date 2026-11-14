# Final independent judge audit (14 Nov 2026)

Written as a sceptical judge with the dashboard, deck, research report and the protected site. No score is manufactured and no outcome is promised; the assessments below state evidence and risk.

## Criterion by criterion
| Criterion (weight) | Assessment | Evidence | Weaknesses | Likely judge objection | Recommended response |
|---|---|---|---|---|---|
| Insight (45%) | Strong. The reconstruction is specific and quantified, and the strongest rules are non-obvious. | C2 exact on 9,999,998 / 10M with both exceptions explained (only two payments touching an Eritrean bank); R1 = ⌊Exp(1)⌋ with q̂ 0.3677 vs 1/e and w 0.0006; R2 overturned and re-validated out of sample; C3 + H38 vehicle rates; D1 additivity out of sample; 34 rules with scope and counterexamples | T4, G1, X5 open; H38 post-hoc; R6/R7 are derivations of field definitions | "R6 and R7 are obvious" | agree — they are foundations; lead with C2, R1, R2 |
| Evidence & method (23%) | Very strong. | criteria fixed before testing; 5 partitions; SQL/Python/JS parity; per-family BH; Simpson check; exact replay counts; 459 evidence IDs; consistency checker | browser Rule Builder replicates by period only | "with 10M rows everything is significant" | acceptance is on effect size (w, V, exact share), shown on slide "Statistical robustness" |
| Communication (20%) | Good to strong. | 2-minute tour; overview opens on three findings; 15-page dashboard with a synthesis page; 20-slide deck with one summary slide per group; research report for scrutiny; responsive site | dashboard rule cards dense; deck design polish belongs to the pitch team | "too much material" | use the tour and the synthesis page; the report is optional reading |
| Economic reasoning (12%) | Adequate to good. | every reading labelled interpretation; synthetic caveats everywhere; 5 verified references | scam readings uncited; some readings general | "is this real Swift behaviour?" | no — it is the generator's behaviour; readings are plausibility, not evidence |

## The questions a sceptical judge asks
- **Genuinely novel / non-obvious:** C2 (borders, not distinct currencies — 91.7% for the alternative), R1 (one constant explains the whole route-length distribution), R2 (a passed rule that was wrong), D1 (additive bank steps out of sample), F1 (USD roundness fingerprint).
- **Merely descriptive:** some network statistics and token presence shares — kept in supporting pages, not headlines.
- **Exact:** R6, R7, C2, P2, X2, Direct ⇔ 2 participants. **Fitted:** R1 q, R4 p, A1 coefficients (≈ 6, 2, 2 but estimated), D3 gamma parameters, C3 shares.
- **Uncertain:** T4 levels, G1 affinities, X5, the reason EUR/USD act as vehicles.
- **Effect sizes meaningful?** Yes — reported alongside every test; p-values are secondary.
- **Alternatives considered?** Each rule names its best alternative; 29 refuted hypotheses are kept.
- **Reproducible?** `python run_all.py` regenerates every artefact; the checker and 91 tests guard consistency.
- **Can the dashboard stand alone?** Yes, with page 15 summarising; dense in places.
- **Does the deck tell a story?** Task → method → blueprint → what the engine changed → eight feature groups → robustness → limits → conclusion.
- **Does the report allow scrutiny?** Yes: split metrics and evidence IDs per rule, worked mathematics.
- **Does the website add value?** Yes: replay of real records, interactive simulation and evidence tracing — not reproducible in a PDF.

## Remaining risks
1. Density of the dashboard rule cards (communication).
2. Judges may not open the site (it is protected until the deadline); the PDFs must carry the story alone — they do.
3. Signed-in preview testing and on-time submission are team actions.

**No unresolved P0 issues.** The one P0 found in this pass (C2's 0.9999998 displayed as "1") is fixed and guarded by the consistency checker.
