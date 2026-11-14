# Competition requirements and traceability

Sources (all in project root): **CS** = *Universiti Malaya UMDAC Datathon 2026 - Swift Case Study Preliminary Round.pdf* · **SF** = *Datathon 2026 Submission Format.pdf* · **RR** = *Datathon 2026 Rules and Regulations.pdf* · **JC** = *Datathon 2026 Judging Criteria Preliminary Round .pdf* · **HB** = *Datathon 2026 Handbook.pdf* · **BR** = *UMDAC 2026 Nai Long .pdf* (team briefing notes).

## Traceability

| # | Requirement | Source | Exact requirement (paraphrased closely) | Deliverable location | Verification |
|---|---|---|---|---|---|
| 1 | Reverse-engineer generation rules | CS p1 | "reverse-engineer the rules used to generate the data set … based exclusively on the raw data" | findings/, dashboard, slides | 26 validators in `src/rules.py`; `findings/validation_report.md` |
| 2 | Dashboard PDF, 5–15 dashboards, one feature group each | CS p2, RR 4.4, SF | grouped by feature type; each insight states the rule and ≥1 chart per feature group | `submission/dashboard.pdf` | page count check in `src/reporting.py` (assert 5 ≤ pages ≤ 15) |
| 3 | Slide deck PDF, 10–20 slides incl. intro & methodology | CS p2, RR 4.4, SF | restate rule, copy/reference chart, explain real-world economic behaviour, describe methodology; ≤1 slide per feature group | `submission/presentation.pdf` | page count assert 10–20; one slide per group |
| 4 | Both in PDF | RR 4.3, SF | dashboards and slides submitted as PDF | `submission/` | files exist, open with pypdf |
| 5 | Deadline | RR 4.1/4.6 | submission link closes 19 Nov 2026 12:00 PM | — | team submits (not automated) |
| 6 | Only provided dataset as primary data | RR 2.3, HB 3.2 | no external primary datasets | all analysis | no external data used; see source_register.md |
| 7 | External reference statistics allowed with APA citations + URLs | RR 2.4–2.5, HB 3.3–3.4 | APA format, URL embedded | slides references | source_register.md (contextual only) |
| 8 | No redistribution of dataset | RR 2.1–2.2 | dataset IP of organiser | ZIP excludes data/ and CSV | `scripts/make_zip.py` exclusion list |
| 9 | Document methodology/code | RR 3.4, HB 2.5.1 | sufficient documentation via code comments / docs / slides | README, docs/, src/ | reviewer walkthrough |
| 10 | AI use permitted, team accountable | RR 3.6 | no declaration required; must explain and justify | — | team defence pack (docs/judge_qa.md) |
| 11 | Scoring weights | JC, CS p2 | Insight 45 · Interpretation 12 · Evidence/Method 23 · Communication 20 | docs/judging_strategy.md | self-audit in findings/audit.md |
| 12 | Dashboard sub-weights | SF | visual clarity 35 · charts & evidence 50 · correctness/clarity 15 | dashboard.pdf | audit |
| 13 | Slide sub-weights | SF | quality 15 · methodology 65 · economic explanation 20 | presentation.pdf | audit |
| 14 | Slides focus on insights, not code | BR | "not coding/technical details" | presentation.pdf | methodology explained conceptually |
| 15 | Horizontal dashboard preferred | BR | "Make it horizontal is better" | dashboard.pdf landscape 16:9 | render check |
| 16 | No data augmentation | BR | cannot modify the original dataset | raw CSV untouched; derived files separate | `src/ingestion.py` reads only |
| 17 | Partial/negative results valued | CS p2, JC 1.3 | "well-described … partial or negative result … more valuable" | X5, T3, R3, A-R rejections | register "Counterexamples" column |

## Conflicts and gaps found in the official materials

| Item | Documents | Detail | Handling |
|---|---|---|---|
| Start time | HB says 11:40 AM; RR 4.1 says 11:50 AM | 13 Nov 11:50 → 19 Nov 12:00 is 144 h **10 min**, not 144 h | Deadline (12:00 PM, 19 Nov) is consistent across RR 4.1 and 4.6 → treat 12:00 PM as binding; recommend confirming with mentor |
| Sixth anomaly label | CS appendix lists 5 labels; data has 6 | `CUSTOMER_RECALL` (317 rows) is undocumented | Kept as-is, analysed as rule X5; ask mentor whether it is intended |
| Broken cross-reference | CS p1 | "appendix Error! Reference source not found." | Appendix A.1 used |
| Dashboard tool | SF mentions Looker Studio "or equivalent – link/PDF"; CS/RR require PDF | Equivalent tool allowed | Streamlit prototype + PDF export |
| Romance scam definition | CS says Consumer → Consumer | Data: sender always C, receiver follows base mix (27% B) | Reported as a discrepancy in X1 |
