# ORVANTA Genome dashboard: source

This folder is a copy of the files that produce `ORVANTA_GENOME_FINAL_DASHBOARD.pdf`. The working copies live in the project's `src/` and `scripts/` folders. Rebuild from the project root, not from this folder.

## Rebuild
```bash
python -m src.charts                    # 48 matplotlib charts (200 dpi) from outputs/evidence/*.json
python -m src.reporting                 # HTML -> headless Edge -> submission/dashboard.pdf (15 pages)
python scripts/dashboard_audit.py v2    # renders each page, measures overflow / footer clearance / blank share
python scripts/dashboard_registers.py   # rule crosswalk + claim-evidence register, read back from the rendered HTML
```

## Files
| File | Role |
|---|---|
| `dashboard_v2.py` | Page plan and content for all 15 pages, the page CSS (`CSS2`) and the fit-to-page script (`FIT`). |
| `reporting.py` | Loads the evidence JSON, calls `dashboard_v2.build()`, renders the HTML and prints it to PDF with Edge. |
| `charts.py` | Every chart: reads only `outputs/evidence/*.json`, so no number is typed by hand. |
| `levels.py` | The fixed confidence scale (validated, strongly supported, supported, inconclusive). |
| `dashboard_audit.py` | Layout QA run with Playwright and Edge: overflow, footer clearance, column zoom, blank share, largest empty band. |
| `dashboard_registers.py` | Writes `ORVANTA_RULE_CROSSWALK.csv` and `ORVANTA_CLAIM_EVIDENCE_REGISTER.csv`. It fails if any rule is missing or a printed level disagrees with `levels.py`. |
| `dashboard.html` | The rendered HTML. Chart images are referenced from `outputs/charts/`, so open it inside the project. |
| `audit_before/`, `audit_after/` | Audit results for the previous dashboard and this one. `audit_after/` also has a PNG of every page. |

## Page layout
Pages are 16 in × 9 in. Each feature-group page has the same layout:
- **Left column:** the research question, rule cards (formula, test status and confidence level, a "Reading:" line), an evidence table (key metric, full-data value, range over 5 splits, n, evidence ID) and a "Read with care" box of limitations.
- **Right side:** a 2 × 2 chart grid. Every chart has a source line and a "Reading:" caption.

If a column is still too tall after the fixed layout, the fit script scales just that column down, to no less than 85% for text columns and 74% for chart grids.
