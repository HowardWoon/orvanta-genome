# Final independent judge audit (strict)

> Superseded by `V5_FINAL_JUDGE_AUDIT.md`.

Written as a sceptical judge with access to the PDFs, the protected site and the repository. Scores are 0–20 per criterion, then weighted.

| Criterion (weight) | Score | Evidence | Missing / weak | Possible deduction | Highest-impact fix |
|---|---|---|---|---|---|
| Insight quality (45%) | 17 | 34 explicit rules with formulas; exact rules (C2 9,999,998/10M, R6/R7/P2 zero violations, verifiable in Forensic Replay); fitted distributions (geometric 1/e, Gamma steps, lognormal amounts); discovery engine explains 55/55 strong dependencies; R2 corrected by our own engine | G1 (bank pairing) and T4 (weekly levels) mechanisms open; C3's 1.3% outside-route currency unexplained; several rules are "obvious once seen" (R6, R7) | "some rules are derivations, not discoveries" | lead the slides with the non-obvious rules (C2, R1 = ⌊Exp(1)⌋, R2 revised, C3, F1) |
| Evidence & method (23%) | 18 | 5-split validation; SQL/Python/JS parity; per-family BH; out-of-sample bank classes; Simpson checks; 459-record evidence ledger; lineage hashes; 81 automated tests | random halves not available in the browser builder; replay shows samples not arbitrary queries (disclosed) | minimal | none needed before submission |
| Communication (20%) | 16 | dashboard 14 pp, slides 19, one per group; web opens on the headline finding; labels separate observed/estimated/simulated | PDF rule cards are dense; slides need pitch-team polish; 48 web routes can overwhelm — judges need a guided path | "too much to absorb in the time" | pitch team: rehearse a 2-minute path (Overview → C2 replay → R2 genealogy → Simulator) |
| Economic reasoning (12%) | 15 | per-rule readings labelled as interpretation; synthetic caveats; alternatives listed | external references still to be verified by the team; some readings generic (correspondent banking) | if a cited source is wrong | verify `docs/source_register.md` or drop unverified citations |

**Weighted estimate ≈ 16.8 / 20 (≈ 84%).** Not inflated: the uncertainty is mostly in communication and reference checking, which belong to the pitch team.

## Competitor challenge
- *What would a stronger team find?* The rule behind the 1.3% outside-route "vehicle" currency (C3) and the directional bank-pair affinities (G1). We report both as open rather than guessing.
- *Too obvious?* R6 (pc = known BICs) and R7 (flag ⇔ '...') — keep them as the foundation, not as headlines.
- *Insufficiently supported?* T4 (weekly levels) and X5 (recall) are INCONCLUSIVE and labelled so. D2 rests on fixed-effects adjustment (sound but subtle — explain it well).
- *Correct but economically uninteresting?* Benford conformity, seconds uniformity — kept in Forensics, not in the headline.
- *Impressive but not reconstructive?* The route playground's top-600 bank table and the scatter plots describe, they do not reconstruct; they are secondary pages.
- *Unnecessary pages?* None is empty; for judging, the core path is Overview, Blueprint, Rule Explorer, Replay, Validation, Simulator.
- *What could cost credibility?* Any slide number that differs from the site. All three surfaces read the same artefacts and the R2 figure was corrected everywhere; re-run `run_all.py` after any change.
- **Single biggest weakness:** density. The research is deep; the risk is that judges see breadth before they see the three sharpest findings.

## Fixes applied in this pass
- Overview now opens on the headline finding (C2 exactness) with the six-stage journey and unresolved questions.
- Rule Genealogy shows how R2 was overturned by our own engine (H32) — the strongest "we challenged ourselves" evidence.
- Forensic Replay lets a judge see the 2 C2 exceptions and the zero-violation rules directly.

## Remaining actions for the team (non-technical)
1. Verify references or remove them from the references slide.
2. Rehearse the 2-minute path and `docs/judge_qa.md`.
3. Submit both PDFs before 19 Nov 2026, 12:00 PM.
