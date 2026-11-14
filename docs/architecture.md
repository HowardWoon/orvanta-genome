# Architecture — six layers, one evidence system

Product: **The Synthetic Rule Intelligence Lab** (workflow DISCOVER → RECONSTRUCT → VALIDATE → EXPLAIN). Tagline: *Decode the rules behind 10 million transactions.*
(Original name; "Swift" appears only as the case-study reference, never as product branding. See decision D-14.)

```
 L1 DATA FOUNDATION        raw CSV (immutable) ─► src/ingestion.py ─► payments.parquet ─► slim.parquet      [row counts asserted = 10,000,000]
 L2 FEATURE INTELLIGENCE   slim.parquet derived columns: time (ts, d, hr, dow, local hour via offsets), value (ln amt), route (known BICs,
                           gaps, path_n), party (bank/customer country, IBAN/struct flags), split keys (hash half, period)       src/ingestion.py, src/config.py
 L3 DISCOVERY              src/evidence.py (distributions & conditionals) · src/graph.py (pseudograph, PageRank, pairing, loops)
                           · src/stats.py (CIs, tails, step fits, sensitivity, detector evaluation)
 L4 RULE RECONSTRUCTION    src/rules.py (34 SQL validators, typed A–E) · src/rulelib.py (pure-Python rule spec = generator blueprint)
 L5 VALIDATION & EXPLAIN.  src/validation.py (5 splits, SQL-vs-Python cross-check) · src/register.py (register.json/.md) · src/levels.py (six-level confidence scale)
                           · findings/*.md · tests/
 L6 INTELLIGENCE INTERFACE dashboard/app.py (Streamlit; reads only outputs/) · src/charts.py + src/reporting.py (PDFs)
                           · src/webdata.py (browser aggregates) + src/web.py → web/dist: 39-route research platform (web/app ES modules)
```

**One evidence system.** Every number shown anywhere comes from one of five JSON/Parquet artefacts in `outputs/`:
`validation.json` (rule metrics per split) · `register.json` (narrative + confidence + metrics) · `evidence.json` (chart aggregates) ·
`graph.json` · `stats.json` · `tables/cube_*.parquet` (filter-aware additive aggregates). The dashboard, PDFs, markdown registers and the web platform all read these files; the web platform reads them through `web/build_data/*.json`, which `src/webdata.py` derives from the same artefacts (plus one additive explorer cube computed from the slim Parquet).
None of them hold their own statistics.

**Dependency order** (`run_all.py`): ingestion → graph → stats → validation → evidence → cube → register → charts → reporting → pytest.
`graph` and `stats` run before `validation` because validators G1 and D3 read their outputs; this keeps the heavy pair cross-join out of the validator loop.

**Separation of concerns**
| Concern | Lives in | Never in |
|---|---|---|
| Parsing & typing | ingestion.py | app, charts |
| Rule logic | rules.py (SQL), rulelib.py (Python) | app, reporting |
| Acceptance thresholds | rules.py decorators (`criterion`) | docs (docs quote them) |
| Narrative | register.py | app (app reads register.json) |
| Presentation | app.py, charts.py, reporting.py | analysis modules |

**Performance** (Ryzen 5, 12 threads, 15 GB RAM, ≈3 GB free disk). CSV→Parquet takes about 80 s and slim about 90 s. The full validation takes about 4 min; the exact FX validator dominates at about 200 s because it unnests every path. Graph runs in about 3 min and stats in about 2 min. The app starts on about 4 MB of cubes in under 2 s. Peak DuckDB memory is capped at 9 GB.

**Security & governance.** The raw CSV is read-only. No row-level data ships in the ZIP or the app, and there are no network calls at runtime (fonts are local system fonts). The ZIP builder asserts the dataset filename is absent.


## Research layer added (discovery, forensics, atlas, lineage)
| Module | Stage | Output |
|---|---|---|
| src/discovery.py | DISCOVER | discovery.json: 276 pair scores (dev/validation), mediation triage, depth-3 tree candidates |
| src/forensics.py | DISCOVER/VALIDATE | forensics.json: Benford, cents, timestamp grain, identifier grammar, change points, CI tests, fixed-rate search |
| src/atlas.py | RECONSTRUCT/EXPLAIN | atlas.json: 21 nodes, 37 typed edges linked to rules |
| src/lineage.py | VALIDATE/EXPLAIN | lineage.json: SHA-256 per artefact, schema contract, environment, pipeline |
| src/formulations.py | RECONSTRUCT | explicit rule + logic per rule (merged into register.json and per-rule reports) |
