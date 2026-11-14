# Official competition compliance (checked 14 Nov 2026)

Requirements extracted from the official case study (CS), submission format (SF), rules (RR), judging criteria (JC), handbook (HB) and briefing (BR); full extraction in `competition_requirements.md`.

| Requirement | Source | Status | Evidence |
|---|---|---|---|
| Reverse-engineer the generation rules from the raw data only | CS p1, RR 2.3 | ✅ | 34 rules, all from the supplied file; no external data (`source_register.md`) |
| Dashboard PDF, 5–15 dashboards | CS p2, RR 4.4 | ✅ 15 pages | `submission/dashboard.pdf`; asserted in `src/reporting.py` and `tests/test_submission.py` |
| Dashboards grouped by feature type, ≥ 1 chart per feature group, rules stated | CS p2, SF | ✅ | pages 3–8, 11–14 are feature-group pages; page 15 is the synthesis (blueprint, integrity, open questions, conclusion) (time, currency & FX, routing, institutions, processing time, network, value, parties, fraud anomalies, operational anomalies); each has rule cards + ≥ 1 chart; pages 1–2, 9–10 are method/discovery/forensics/robustness |
| Presentation PDF, 10–20 slides incl. introduction and methodology | CS p2, RR 4.4 | ✅ 20 slides | title, headline, the challenge & dataset, 3 methodology slides, blueprint, discovery, 8 feature-group slides (time, currency & FX, routing, institutions, processing time, value, parties, anomaly labels), statistical robustness (methodology), limits, conclusion, references |
| At most one summary slide per dataset feature group | CS p2 | ✅ (fixed) | anomaly labels were on two slides (15 + 16) — merged into one on 14 Nov 2026 |
| Slides restate rules, include/reference charts, explain economic behaviour, describe methodology | CS p2, SF | ✅ | each feature slide: rule card + "Reading" (interpretation) + chart; slides 3–5 methodology |
| Slides focus on insights, not code | BR | ✅ | no code, architecture diagrams or website screenshots in either PDF |
| Both deliverables as PDF | RR 4.3, SF | ✅ | `submission/*.pdf` |
| Horizontal dashboard preferred | BR | ✅ | landscape 16:9 |
| External statistics only with APA citations + URLs | RR 2.4–2.5, HB 3.3–3.4 | ✅ | 5 verified references on slide 20 (references); UK Finance removed (unverifiable) |
| No redistribution of the dataset | RR 2.1–2.2 | ✅ | ZIP excludes CSV and row-level Parquet; website ships aggregates + ≤ 75 de-identified records per rule; site team-only |
| No sharing of solutions outside the team before the deadline | RR 3.3 | ✅ | Vercel Authentication on previews; production alias = private placeholder |
| No data augmentation | BR | ✅ | raw CSV read-only; derived files separate |
| Methodology documented | RR 3.4, HB 2.5.1 | ✅ | README, `docs/`, code comments, slides 3–5 |
| AI use: team must be able to explain | RR 3.6 | ⚠️ team action | `judge_qa.md` must be rehearsed |
| Submit before 19 Nov 2026, 12:00 PM | RR 4.1/4.6 | ⚠️ team action | not automatable |

## Dashboard sub-weights (SF): visual clarity 35 · charts & evidence 50 · correctness/clarity 15
Every chart carries its source line and n; rule cards show formula, level and split status; no page overflows (checked by rendering each page in Edge).

## Slide sub-weights (SF): quality 15 · methodology 65 · economic explanation 20
Three methodology slides plus the blueprint and discovery slides; an interpretation line on every feature slide; limits and rejected hypotheses slide.
