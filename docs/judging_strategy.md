# Judging strategy

| Rubric item (weight) | What wins it | Our asset |
|---|---|---|
| 1.2 Rule reconstruction (12) + 1.5 Correctness (9) | rules precise enough to regenerate data | formula per rule; `src/rulelib.py` is literally a generator spec; exact rules (C2, R6, R7, X2) |
| 1.3 Explanatory depth (14) | alternatives tested, causal vs correlational, uncertainty | rejected hypotheses (C2 alternatives, R3 currency-zone, T3 Gulf weekend, X4 name-swap, X5 recall), Simpson check D2, out-of-sample D1 |
| 1.1 Hypotheses (5) | hypotheses drive analysis, early results change plan | hypotheses.md shows the loop (e.g. sample 28/30 endpoint match → R5 → R5b re-specifies C1/T1) |
| 1.4 Specificity (5) | one-sentence quantified headline | each slide title is a quantified claim |
| 3.x Evidence & method (23) | issues log, every claim traceable, simple justified methods, tools disclosed | validation_report.md, two-implementation check, splits, README |
| 2.x Economics (12) | mechanism per rule, observation vs interpretation separated | register "Economic interpretation" column labelled as interpretation |
| 4.x Communication (20) | headline-first, dashboard readable alone | 9-page dashboard with rule + chart + reading per page |

**Priorities for the 20 slides:** methodology is 65% of the slide score, so we give 3 slides to the method (hypothesis loop, validation design, data integrity). Each feature-group slide restates the rule, shows one chart, and gives the economic reading.
