# Data pipeline

One command rebuilds everything from the raw CSV: `python run_all.py` (add `--skip-ingest` when the Parquet files exist).

```
raw CSV (immutable, 4.6 GB, 10,000,000 rows × 21 columns)
 └─ src.ingestion   RFC-4180 parse (multi-line quoted fields) → payments.parquet (all text) → slim.parquet (typed + derived); row count asserted
     ├─ src.graph · src.stats · src.discovery · src.forensics         → outputs/evidence/{graph,stats,discovery,forensics}.json
     ├─ src.validation (34 validators × 5 splits, SQL vs Python twin)  → validation.json, findings/validation_report.md
     ├─ src.evidence · src.cube · src.register · src.atlas · src.lineage → evidence.json, cubes, register.json, atlas.json, lineage.json (SHA-256)
     ├─ src.charts · src.reporting                                      → charts/*.png, submission/dashboard.pdf (15 pp), presentation.pdf (20 slides)
     ├─ src.webdata   browser aggregates (explorer cube, routes n ≥ 150, top-600 banks, tests with per-family BH, simulator parameters, registry)
     ├─ src.replay    exact support/violation counts + hash-sampled de-identified records per rule (Forensic Replay)
     ├─ src.ledger    evidence ledger (EV-*), generator blueprint, rule genealogy, coverage matrix
     ├─ src.research_report  comprehensive research report (MD + PDF) from the registry and validator output
     └─ src.web       web/app + data + charts + PDFs → web/dist (static, deployed to Vercel as a protected preview)
pytest (unit, artefact contracts, PDFs, Streamlit AppTest, static-site contracts, Playwright end-to-end on Edge)
```

| Layer | Location | Notes |
|---|---|---|
| Raw | project root CSV | never modified; fingerprinted by size + verified row count |
| Cleaned | `data/processed/*.parquet` | DuckDB, out-of-core; codes and identifiers kept as strings |
| Features | `slim.parquet` columns (`path_n`, `gaps`, `o_iban`, bank/customer countries …) | every derivation in `src/ingestion.py` |
| Analytical outputs | `outputs/evidence/*.json`, `outputs/tables/*.parquet` | single source of truth for PDFs, Streamlit and web |
| Rule registry | `register.json` → `web/build_data/registry.json` | six-level confidence (`src/levels.py`) |
| Evidence | `web/build_data/ledger.json`, `replay.json` | every rule has EV-RULE and EV-VAL records |
| API layer | static JSON files (no server) | see decision D-28 in `decision_register.md` |
| Presentation | `web/app` (ES modules), `dashboard/app.py`, `src/reporting.py` | |

**Why no server-side API.** A server querying the 0.48 GB slim Parquet would need a long-running host (Vercel functions cap bundle size and run time) and would put row-level data behind a public endpoint. Instead, every interactive query runs on exact additive aggregates in the browser, and Forensic Replay ships only bounded, de-identified record samples with exact counts computed offline. The trade-off is disclosed on the pages: medians and KS are bin-resolution, and replay shows samples, not arbitrary queries.
