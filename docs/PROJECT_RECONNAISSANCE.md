# Project reconnaissance — ORVANTA upgrade (14 Nov 2026)

## 1. Deployment access (tested logged out)
| URL | Logged-out result | Cause |
|---|---|---|
| `synthetic-rule-j3073i00i-…vercel.app` (URL in the brief; old 11-route lab) | HTTP 302 → `vercel.com/sso-api` | Vercel Authentication (Standard Protection) on preview deployments — the team-only setting chosen by the owner |
| `synthetic-rule-ez1ikg8vs-…vercel.app` (39-route platform, earlier today) | HTTP 302 → SSO | same |
| `synthetic-rule-lab.vercel.app` (production alias) | 200, "This project is private" placeholder | deliberate: no dataset-derived content public before the deadline (rules 2.2 / 3.3) |

Public access is intentionally off until judging; `web/DEPLOY.md` documents the one command that makes the real site public afterwards. All functional testing was done against the identical local build (`web/dist`) with Playwright on Edge.

## 2. Existing architecture (preserved)
- **Analysis**: Python 3.12, DuckDB over Parquet (out-of-core), SciPy, scikit-learn; 15 pipeline modules in `src/` (ingestion → graph/stats/discovery/forensics → 34 validators × 5 splits → evidence/cubes/register/atlas/lineage → charts/PDFs → web).
- **Evidence**: JSON artefacts in `outputs/evidence`, SHA-256 lineage, schema contract.
- **Surfaces**: dashboard PDF (14 pp), slides PDF (18), Streamlit lab (`dashboard/app.py`), static web platform (`web/app` → `web/dist`).
- **No backend / API, no environment secrets** in the app. The only secret-like file is the Vercel CLI's `.env.local` OIDC token, excluded by `.vercelignore` and the ZIP builder.
- **Framework**: vanilla ES modules (no Next.js/React) — kept: no build step, CSP `script-src 'self'`, 9.5 MB total, fully testable (decision D-22).

## 3. Functional before this upgrade
39 routes in 9 groups: observed-data explorer, scenario simulator, rule playground, zoomable atlas, BH-controlled test registry, validation centre, 10 feature pages; 75 automated tests passing.

## 4. Gaps against the ORVANTA brief (now closed unless noted)
| Gap | Severity | Resolution |
|---|---|---|
| No identity / six-stage journey | P2 | ORVANTA · Generator Genome branding on web, PDFs and Streamlit; stage chip on every page; journey strip on the overview |
| Navigation not organised as the 10-group product architecture | P2 | 48 routes in 10 groups; old URLs unchanged so links keep working |
| No Generator Blueprint | P1 | `genome/blueprint` — 10 generation stages, mechanisms only from rules, unresolved parts listed |
| No Rule Genealogy | P1 | `genome/genealogy` — built only from the logged hypothesis order (28/34 rules have a recorded history; 6 say so) |
| No Rule Builder | P1 | `foundry/builder` — IF/THEN/COMPARED/WHILE spec, test chosen by target type, stratification + Simpson flag, P1→P2 replication, export |
| No record-level evidence (Forensic Replay) | P1 | `forensics/replay` — 10 rule checks, exact counts on all rows, ≤ 75 de-identified records each |
| No evidence IDs / claim-to-evidence links | P1 | `library/ledger` — 459 EV records (DATA, RULE, VAL, CX, STAT, DISC); rules, genealogy and overview link to them |
| Scenarios could not be compared or exported | P2 | pin / compare / export report in the Scenario Studio |
| No sensitivity page | P2 | `lab/sensitivity` — q, p, m sweeps + D1 threshold table |
| No coverage matrix | P2 | `command/coverage` |
| No alternative-hypotheses view | P2 | `forensics/alternatives` |
| Server-side queries over raw rows | — (not done) | deliberately replaced by exact aggregates + bounded replay samples (see `DATA_PIPELINE.md`) |
| Past-winner benchmark | — | searched; champions' solutions not publicly verifiable (`COMPETITIVE_BENCHMARK.md`) |

## 5. Worth preserving (kept unchanged)
Validators and five-split design; the SQL ↔ Python twin; per-family BH; out-of-sample bank classes; lineage hashes; PDFs' structure and page limits; Streamlit lab; explorer cube engine; neo-brutalist tokens.

## 6. Documents requested by the brief
| Requested | File |
|---|---|
| PROJECT_RECONNAISSANCE | this file |
| DEFECT_REGISTER | `docs/defect_register.md` (route inventory before/after + D-W01…) |
| COMPETITION_REQUIREMENTS | `docs/competition_requirements.md` |
| DATA_DICTIONARY | `docs/dataset_dictionary.md` (+ live Feature dictionary page) |
| DATA_QUALITY_REPORT | `docs/DATA_QUALITY_REPORT.md` (generated) |
| DATA_PIPELINE | `docs/DATA_PIPELINE.md` |
| COMPETITIVE_BENCHMARK | `docs/COMPETITIVE_BENCHMARK.md` |
| QA_REPORT | `docs/QA_REPORT.md` |
| FINAL_JUDGE_AUDIT | `docs/FINAL_JUDGE_AUDIT.md` |
