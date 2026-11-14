# ORVANTA — Generator Genome
*Synthetic Financial Intelligence · Decode the structure. Reconstruct the logic.* (formerly the Synthetic Rule Intelligence Lab)
UMDAC Datathon 2026 · Swift case · Team Nai Long · *Decode the rules behind 10 million transactions.*

Workflow: **DISCOVER → RECONSTRUCT → VALIDATE → EXPLAIN**.

We reverse-engineered the rules that generated Swift's 10,000,000-row synthetic cross-border payment dataset. We found **34 rules** (each with explicit formula, logic, sample size, effect size, validation, counterexamples, confidence, interpretation and limitations), each with an acceptance criterion validated on five splits (full data, two random halves, two time periods); 5 are deterministic and reproduce their field exactly. The work is organised in six layers (see `docs/architecture.md`).

## Deliverables
| File | What |
|---|---|
| `submission/dashboard.pdf` | 15-page landscape dashboard: discovery engine & atlas, forensics, one page per feature group, statistical robustness |
| `submission/presentation.pdf` | 20-slide deck: headline, the challenge & dataset, 3 methodology slides, blueprint, 'what the discovery engine changed', 1 slide per feature group (the two anomaly slides merged into one), statistical robustness, limits, conclusion, references |
| `dashboard/app.py` | Lab workbench, 11 sections grouped by workflow: Rule Explorer (searchable, evidence report download), Dependency Atlas, Discovery Engine, Forensics Lab, Route Observatory, Validation Centre (incl. lineage) … |
| `web/dist/` | **research platform** for Vercel: 49 routes (a 2-minute judge's guided tour + 48 research pages in 10 groups) — generator blueprint, rule genealogy, rule builder, forensic replay of real records, evidence ledger (459 EV records), — observed-data explorer (10-dimension additive cube), scenario simulator (Monte Carlo of the reconstructed generator), rule playground, zoomable dependency atlas, BH-controlled hypothesis tests, validation centre. Source in `web/app/`, data from `src/webdata.py`. Deploy guide: `web/DEPLOY.md`; audit: `docs/defect_register.md` |
| `submission/ORVANTA_Comprehensive_Research_Report.{md,pdf}` | supplementary research report generated from the registry: all 34 rules with formulas, split metrics, evidence IDs, the mathematics, H1–H38, limitations |
| `findings/validation_report.md` | every validator, every split, every metric |
| `findings/rule_evidence_register.md` | rule register (hypothesis, method, evidence, counterexamples, limitations, economic reading) |
| `findings/hypotheses.md` | the 37-step hypothesis log (H1–H37), including rejected hypotheses |
| `docs/` | architecture (6 layers), decision register, methodology, project status (tasks, tests, submission checklist), requirements traceability, dataset dictionary, sources, judge Q&A |

## For teammates: start here
| You want to … | Open |
|---|---|
| **Read and run all the analysis code in Google Colab** | `notebooks/ORVANTA_prototype_analysis.ipynb`. In Colab use File → Upload notebook. Put the dataset CSV in your Google Drive (`MyDrive/swift_umdac_datathon_2026_fictitious_payment_data.csv`), then Runtime → Run all. **Part A** is a readable prototype of every analysis on a sample (a few minutes). **Part B** contains every source file of this repository and runs the full pipeline on all 10M rows (about 1.5–3 h on free Colab), producing the same validation results, charts and PDFs. The notebook is saved with its outputs, so you can read it without running it. |
| **Edit the dashboard** | `submission/ORVANTA_GENOME_DASHBOARD_EDITABLE.pptx` has 15 slides at 16 × 9 in, with native text boxes and tables (charts are images). It opens in PowerPoint, Keynote and Google Slides, and imports into Canva. |
| See the final dashboard | `submission/ORVANTA_GENOME_FINAL_DASHBOARD.pdf` |

The dataset is **not** in this repository: it is 5 GB, and the competition rules do not allow redistributing it.

Regenerate the notebook and the editable deck after changing code or results:
```bash
python scripts/make_notebook.py
```
```bash
python scripts/make_pptx.py
```

## Reproduce (Windows, Python 3.12)
```bash
pip install duckdb pandas numpy scipy scikit-learn matplotlib streamlit pypdf pytest
```
Put the raw CSV in the project root (or set `SWIFT_RAW_CSV`), then:
```bash
python run_all.py
```
`run_all.py` runs, in order: `src.ingestion` (CSV → Parquet → slim, ~3 min), `src.metadata` (home currencies, UTC offsets, country effects derived from the data), `src.graph`, `src.stats`, `src.discovery`, `src.forensics`, `src.h38` (vehicle-currency test), `src.validation` (34 rules × 5 splits, ~5 min), `src.evidence`, `src.cube`, `src.register`, `src.atlas`, `src.lineage`, `src.charts`, `src.webdata` (browser aggregates), `src.replay` (forensic replay counts and samples), `src.ledger` (evidence ledger, blueprint, genealogy), `src.reporting` (dashboard + presentation PDFs), `src.research_report` (research report MD + PDF), `src.web` (static site), then `pytest`. On a smaller machine set `ORVANTA_THREADS` and `ORVANTA_MEMORY` (e.g. `2` and `6GB`). Each step can also be run on its own with `python -m src.<step>`.

Start the dashboard (it reads only the precomputed tables in `outputs/`, about 4 MB, never the CSV):
```bash
streamlit run dashboard/app.py
```

## Architecture
```
raw CSV (read-only, 4.6 GB)
  └─ src/ingestion.py ── payments.parquet (1.27 GB, text kept) ── slim.parquet (0.48 GB, typed + derived)
        ├─ src/rules.py + src/validation.py ─ validation.json, validation_report.md   (34 validators × 5 splits, SQL vs Python cross-check)
        ├─ src/evidence.py ─ evidence.json  (chart-ready aggregates)
        ├─ src/cube.py ─ cube_*.parquet     (additive, filter-aware; each reconciles to 10,000,000)
        ├─ src/register.py ─ rule_evidence_register.md, confirmed_rules.md (numbers pulled from validation.json)
        └─ src/charts.py + src/reporting.py ─ PNG charts → HTML → Edge headless → PDFs (page limits asserted)
dashboard/app.py ← cubes + evidence.json + validation.json
src/webdata.py → web/build_data/*.json (aggregates only) → src/web.py → web/dist (web/app ES modules + data + charts + PDFs)
src/rulelib.py  = pure-Python reference implementation of the rules (used for tests and as a generator specification)
```
Engine: DuckDB, chosen because it parses multi-line quoted CSV correctly and gives out-of-core SQL on 10M rows within 15 GB RAM. Peak working set is under 10 GB; the slowest validator (the exact FX check, which unnests every path) takes about 3.5 minutes.

## Tests
`pytest -q` runs 90 tests:
- rule-logic unit tests;
- artefact contracts: cubes reconcile to 10M, anomaly counts match an independent pandas profile, all validators pass;
- PDF page limits;
- headless functional tests of every dashboard page, the filters, the empty-filter state and Reset;
- static-site contracts (cube reconciles to 10M, BH is per family, no account identifiers or IBAN-shaped strings in shipped data);
- browser end-to-end tests with Playwright on the system's Microsoft Edge (`pip install playwright`, no browser download): all 49 routes, URL state across refresh/back/forward, explorer counts vs an independent Python re-aggregation, simulator calibration, atlas tracing, JS ↔ Python rule parity, phone-width layout, and every route at 320, 390, 844 (landscape), 768 and 1024 px. A separate audit (`scripts/responsive_audit.py`) measures all 49 routes at 17 viewports; see `docs/MOBILE_QA_REPORT.md`.

## Data governance
The raw dataset and all derived row-level data (`data/`) are excluded from the ZIP (RR 2.1–2.2). Only aggregates ship. No external datasets were used. AI assistance was used for coding and drafting (RR 3.6), and every figure is produced by the code in `src/`.
