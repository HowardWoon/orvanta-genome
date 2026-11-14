# Final championship review (V4, 14 Nov 2026)

> Superseded by `FINAL_QA_REPORT.md` / `FINAL_INDEPENDENT_JUDGE_AUDIT.md` (final upgrade: 15-page dashboard, 20 slides, research report).

> Superseded by `V5_FINAL_JUDGE_AUDIT.md` after the visual, responsive and compliance pass (deck now 18 slides; 90 tests).

A sceptical-judge assessment after the V4 refinement. Internal estimate only — not a prediction of the official score. Executed test results are in `FINAL_RELEASE_QA.md`.

## Rubric assessment
| Criterion | Weight | Estimate (0–20) | Evidence | Remaining weakness | Possible deduction | Highest-impact improvement |
|---|---|---|---|---|---|---|
| Insight quality | 45% | 17 | C2 exact on 9,999,998/10M with both exceptions explained (the only 2 payments touching an Eritrean bank); R1 = ⌊Exp(1)⌋ with q = 0.3677 vs 1/e, Cohen's w 0.0006, constant successive ratios; R2 overturned by our own engine and re-validated out of sample (61% vs 6.7%); C3 refined by H38 (EUR 1.41% / USD 0.75% vehicle draw, flat across route length and splits) | G1 and T4 mechanisms open; H38 is a supported refinement, not a validated rule; R6/R7 are derivations | "a few rules are obvious" | none before submission — the narrative now leads with the non-obvious rules |
| Evidence & method | 23% | 18 | 5-split validators; SQL/Python/JS parity; per-family BH; out-of-sample classes; Simpson checks; 459 evidence records; exact replay counts | browser Rule Builder replicates on periods only (random halves live in the validators) | minimal | — |
| Communication | 20% | 17 (from 16) | 2-minute guided tour; overview cut to headline + three findings + unresolved; ★ judge journey in the menu; slides open on C2/R1/R2 and close with reconstructed / validated / unresolved | PDF rule cards remain dense; slide design polish is the pitch team's | "too much to absorb" (reduced) | rehearse the tour path live |
| Economic reasoning | 12% | 15.5 (from 15) | per-rule readings labelled as interpretation; 5 references verified, outdated title/URL fixed, unverifiable source removed | readings for scams uncited (general knowledge) | small | none needed |

**Weighted estimate ≈ 17.0 / 20 (≈ 85%)**, up from ≈ 84%, driven by communication and reference integrity. The insight score is unchanged: no rule definition was altered to look better.

## The twelve questions
1. *Is the reconstructed generator immediately understandable?* Yes via the tour and the blueprint; the overview states it in one sentence.
2. *Are the strongest findings non-obvious?* C2 (FX = home-currency borders, not distinct currencies 91.7% or payment-currency start 93.5%), R1 (a single constant e), R2 (a passed rule that was wrong) — yes. R6/R7 are kept as foundations only.
3. *Can judges verify every important number?* Evidence ledger IDs on rules; Forensic Replay shows exact counts and records; registry, PDFs and site regenerate from the same artefacts.
4. *Can judges see the exceptions?* Yes — C2's two records in tour stage 1 and in replay; C3's 126,857 outside-route payments sampled.
5. *Can we explain why R2 was overturned?* Yes — H32: country range 3–50%, bank dispersion far above binomial; classes learned on one half, tested on the other.
6. *Are economic interpretations supported?* Labelled as interpretation; external sources only for context and now verified.
7. *Are unresolved mechanisms labelled?* T4, G1, X5 are INCONCLUSIVE on every surface; H38 marked "supported, not validated".
8. *Does the dashboard meet the feature-group requirement?* 14 pages (5–15), grouped by feature, each with a rule and a chart.
9. *Does the presentation explain findings, not technology?* 18 slides; no architecture or website screenshots; methodology limited to 3 slides.
10. *Can a judge understand the product in two minutes?* The tour is built for exactly that.
11. *Can we defend the methodology?* `judge_qa.md` (now including the C2 exceptions question).
12. *Anything that could damage credibility?* The fixed inconsistencies (90.6 vs 91.7, C3 title, "34 validated rules", "~20 minutes") were the main risks; all now come from one source. Residual risk: a slide edited by hand after generation — re-run `run_all.py` instead.

## Limitations to state openly
- Synthetic data: rates and country effects are generator settings, not real-world shares.
- H38's EUR/USD set was chosen after inspecting the data; replicated on all splits but not pre-registered.
- Forensic Replay shows fixed samples (≤ 75 records per rule) with exact counts — not arbitrary queries.
- Signed-in testing of the protected deployment requires a team member's Vercel login.

## Release recommendation
**Ready for submission** once the team (1) clicks through the protected preview while signed in, (2) rehearses the tour and the Q&A, and (3) submits both PDFs before 19 Nov 2026, 12:00 PM. Do not publish the site before the deadline.
