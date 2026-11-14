# V5 final judge audit (strict, 14 Nov 2026)

> Superseded by `FINAL_QA_REPORT.md` / `FINAL_INDEPENDENT_JUDGE_AUDIT.md` (final upgrade: 15-page dashboard, 20 slides, research report).

Internal estimate after the V4 narrative work and the V5 visual/responsive/traceability work. Not a prediction of the official score.

| Criterion | Weight | Estimate (0–20) | Evidence | Weakness | Possible deduction | Remaining improvement |
|---|---|---|---|---|---|---|
| Insight quality | 45% | 17 | C2 exact (9,999,998/10M) with both exceptions explained; R1 = ⌊Exp(1)⌋ (q 0.3677, w 0.0006); R2 overturned and re-validated out of sample; C3 refined by H38 on all splits; 34 rules with scope and counterexamples | G1, T4 mechanisms open; H38 post-hoc; R6/R7 are derivations | "some rules obvious" | none without new research |
| Evidence & method | 23% | 18 | 5-split validators; SQL/Python/JS parity; per-family BH; exact replay counts with records; 459 evidence IDs; single-source pipeline; 90 tests | Rule Builder replicates by period only | minimal | — |
| Communication | 20% | 17.5 | 2-minute tour; three-finding overview; ★ judge path; every route usable from 320 px to 1920 px (833 renders, 0 defects); a data table under every chart; 18-slide deck now strictly one slide per feature group | PDF rule cards dense; slide visual polish belongs to the pitch team | small | rehearse the tour live |
| Economic reasoning | 12% | 15.5 | labelled readings; 5 verified references, unverifiable one removed | scam readings uncited | small | — |

**Weighted ≈ 17.1 / 20 (≈ 85–86%).** Up slightly from ≈ 85% (V4) because mobile/tablet usability and chart readability no longer risk a poor first impression and the slide deck no longer risks the one-slide-per-group rule.

## Strict findings
- *Weak discoveries:* none presented as headlines; R6/R7 are framed as foundations.
- *Unsupported explanations:* economic readings are labelled interpretation; the cover-method reading of R2 is explicitly not attributed to the BIS source.
- *Confusing diagrams:* the atlas needs pan/zoom on phones (by design, with Fit). Everything else reads at native size.
- *Unclear formulas:* each rule card shows formulation and executable logic; the tour restates the three headline formulas in plain words.
- *Inconsistent values:* fixed this round (91.7%, C3 statement, manual-step minutes, "34 validated rules", slider rounding). All now derive from `validation.json`/`stats.json`.
- *Missing evidence:* none for headline claims; H5/H37 figures come from the hypothesis log and are labelled as such.
- *Unnecessary pages:* none empty; the extended environment is secondary to the ★ path.
- *Visual/mobile problems:* none detected by the audit; physical devices and non-Chromium browsers untested.
- *Broken interactions:* none found by the 23 browser tests.
- *Compliance gaps:* none in the artefacts; team actions remain (signed-in preview check, rehearsal, on-time submission).

## Release recommendation
**Ready for submission**, subject to the team's signed-in preview check, rehearsal and submission before 19 Nov 2026, 12:00 PM. Keep the site protected until the deadline has passed and the team agrees to publish.
