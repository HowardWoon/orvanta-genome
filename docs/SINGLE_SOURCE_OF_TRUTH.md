# Single source of truth

Every number on the website, in the Streamlit lab, in the dashboard PDF and in the slide PDF is produced by code from the same artefacts. Nothing is copied by hand between documents.

```
raw CSV (immutable) ─► src.ingestion ─► data/processed/*.parquet
   ─► src.rules + src.validation ─► outputs/evidence/validation.json      ← rule metrics on 5 splits (the numeric source of every rule figure)
   ─► src.graph / stats / discovery / forensics / evidence ─► outputs/evidence/*.json, outputs/tables/cube_*.parquet
   ─► src.register (narrative + confidence) ─► outputs/evidence/register.json · findings/*.md · reports/<id>.md
   ─► src.levels (six-level scale, one function) ─────────────┐
   ─► src.charts + src.reporting ─► submission/dashboard.pdf, presentation.pdf   (reads register.json, validation.json, stats.json, levels)
   ─► dashboard/app.py (Streamlit)                                               (reads the same JSON + cubes, levels)
   ─► src.webdata ─► web/build_data/registry.json, meta.json, sim.json, explorer.json …
   ─► src.replay ─► replay.json (exact counts from the Parquet) ─► src.ledger ─► ledger.json, genome.json
   ─► src.web ─► web/dist (the website reads only web/build_data copies)
```

## Stable identifiers
| Object | ID | Defined in | Carried to |
|---|---|---|---|
| Rule | `R1`, `C2`, … (34) | `src/rules.py` `@rule(...)` | validation.json → register.json → registry.json → PDFs, Streamlit, web, ledger |
| Hypothesis | `H1`–`H38` | `findings/hypotheses.md` | registry.json `hypotheses` → genealogy, hypothesis register |
| Evidence | `EV-DATA/RULE/VAL/CX/STAT/DISC-###` | `src/ledger.py` (deterministic order) | Evidence Ledger, rule cards, overview, genealogy |
| Confidence level | `VALIDATED` … `REJECTED` | `src/levels.py` | PDFs, Streamlit, web |
| Data version | SHA-256 of each artefact | `src/lineage.py` | ledger `sha`, Data lineage page |

## Headline findings — where each number comes from
| Finding | Number | Source field | Shown in |
|---|---|---|---|
| C2 exact | 9,999,998 / 10,000,000; 2 exceptions | `validation.json → C2.metrics.full.{n,exceptions}`; replay `C2.contradicting` (independently recomputed, must match — tested) | tour 1, overview, rule card, replay, dashboard p.4, slide 2, slide 9 |
| C2 alternative | 91.7% | `C2.metrics.full.alt_distinct` | tour 1, dashboard p.4, slide 17, Q&A |
| R1 law | q = 0.3677, w = 0.0006, P(Direct) = 63.23% | `R1.metrics.full.{q_mle,cohen_w,p_direct}` | tour 2, overview, slide 2, slide 10, dashboard p.5 |
| R2 revised | 61.4% vs 6.7% out of sample; pooled 11.3% | `R2.metrics.full.{oos_cover_banks_share,oos_other_banks_share,pooled_covered_share}` | tour 3, overview, slide 2, slide 7 |
| C3 / H38 | 98.7% in route; outside 1.27%; EUR 1.41% / USD 0.75% | `C3.metrics.full`; `outputs/evidence/h38_vehicle.json` | rule card, dashboard p.4, slide 17 |
| Manual step | median 1,456 s (≈ 24 min) | `stats.json → manual_step.median` | dashboard p.7, slide 12, slide 17 |

## Rule of change
If any calculation changes: run `python run_all.py --skip-ingest`. It regenerates validation → register → PDFs → web data → replay → ledger → site and then runs the 90+ tests, which include cross-checks (registry = validation, replay C2 = validator exceptions, cube = 10M). Never edit a PDF or a page number by hand.

## Known exceptions to automation
- `findings/hypotheses.md` and the narrative tuples in `src/register.py` are hand-written research notes; their numbers were re-checked against the validators on 14 Nov 2026 (90.6% → 91.7% corrected, C3 statement corrected).
- Two quoted figures come from the hypothesis log rather than a validator: H5 "payment currency + borders 93.5%" and H37 "≈2% vs 1.2%". They are labelled with their H-number wherever shown.
