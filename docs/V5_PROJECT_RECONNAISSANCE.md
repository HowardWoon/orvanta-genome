# V5 project reconnaissance

> Superseded by `FINAL_QA_REPORT.md` / `FINAL_INDEPENDENT_JUDGE_AUDIT.md` (final upgrade: 15-page dashboard, 20 slides, research report).

Baseline at the start of V5: 82 passing tests; 49 routes (tour + 48 in 10 groups); vanilla ES-module front end with an in-house SVG chart kit (`web/app/js/core.js`); static Vercel preview behind Vercel Authentication; Streamlit lab sharing the same evidence; PDFs 14 pages / 19 slides.

Shared components: router + drawer (`main.js`), chart kit (`core.js`), cube engine, simulator, rule port. No external chart library, no modals.

Risks found: (1) label badges inside CSS grids (the Evidence defect); (2) fixed-width SVG coordinates → unreadable phone charts; (3) values only in hover tooltips; (4) 28–34 px touch targets; (5) in-flow mobile menu; (6) two anomaly slides vs the one-slide-per-group rule; (7) sensitivity slider rounding. All addressed — see `COMPLETE_UI_AUDIT.md`. Earlier reconnaissance: `PROJECT_RECONNAISSANCE.md`.
