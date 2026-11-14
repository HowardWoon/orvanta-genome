# Final release QA (14 Nov 2026)

> Superseded by `FINAL_QA_REPORT.md` / `FINAL_INDEPENDENT_JUDGE_AUDIT.md` (final upgrade: 15-page dashboard, 20 slides, research report).

## Commands executed
```bash
python run_all.py --skip-ingest            # validation → register → PDFs → web data → replay → ledger → site → pytest
python -m src.reporting && python -m src.web
python -m pytest -q tests                   # final run
python scripts/responsive_audit.py final --shots && python scripts/responsive_report.py
```

## Results
| Item | Result |
|---|---|
| Test baseline before this round | 81 passed |
| After guided tour (V4) | 82 passed (`run_all.py`, exit 0) |
| **Final** | **90 passed, 0 failed** (141 s): rulelib 16 · outputs 8 · research 5 · submission 1 · Streamlit AppTest 31 · site contracts 6 · Playwright e2e 23 |
| Validators | 34 / 34 PASS on 5 splits (full run) |
| Routes | 49 (tour + 48), every one renders with no console error and no NaN/undefined text at 17 viewports |
| Responsive audit | 833 renders: 0 overflow, 0 escaping elements, 0 stretched panels, 0 unreadable chart labels (atlas excluded), 0 small touch targets |
| Dashboard PDF | 14 pages (limit 5–15); every page rendered in Edge with zero overflow |
| Presentation PDF | **18 slides** (limit 10–20; was 19 — the two anomaly slides merged to respect "≤ 1 slide per feature group"); zero overflow |
| Headline values | C2 9,999,998 / 10,000,000 (2 exceptions) in validator and replay (test asserts equality); R1 q = 0.3677, w = 0.0006; R2 61.4% vs 6.7%; ledger 459 records; registry 34 rules + 29 rejected |
| Data files shipped | explorer 1.71 MB, routes 0.43, temporal 0.23, ledger 0.21, meta 0.14, registry 0.10, tests 0.08, replay 0.07, institutions 0.05, genome 0.03, tokens 0.02, sim < 0.01 MB; site 9.5 MB |
| Privacy | tests assert no account identifiers or IBAN-shaped strings in any shipped JSON; replay columns exclude accounts, names, details, tokens, row ids |
| Secrets | no `.env*` in `web/dist`; `.vercelignore` excludes them; ZIP excludes them |
| Raw data | CSV and row-level Parquet excluded from the ZIP (asserted in `scripts/make_zip.py`) |

## Manual checks
- Screenshots reviewed: overview (320), atlas (390), sensitivity (768, 1440), Evidence grid (1920/1600 before & after), currency page (390), presentation slides 2, 15, 17, 18 and dashboard page 4.
- PDF text extracted with pypdf: ORVANTA branding present, "to be verified" removed, no "34 validated rules" claim, 91.7% used consistently.

## Deployment
| Check | How | Result |
|---|---|---|
| Logged-out access to the preview (gdqjr66o8) | `curl` of `/`, `/data/replay.json`, `/js/pages/tour.js` | 302 → Vercel SSO (protected) |
| Production alias | `curl https://synthetic-rule-lab.vercel.app/` | private placeholder only |
| Signed-in click-through of the preview | needs a team member's Vercel login | **not done — team action** |
| Public deployment | intentionally not made | gated on deadline + team agreement (`web/DEPLOY.md`) |

All functional testing ran against the identical local build (`web/dist`); the preview serves the same files.

## Outstanding
1. Team: signed-in click-through of the preview on a phone and a laptop.
2. Team: rehearse the tour and `judge_qa.md`; submit both PDFs before 19 Nov 2026, 12:00 PM.
3. Known limitation: Chromium-only browser testing; no physical-device testing.
