# Mobile & responsive QA report (14 Nov 2026)

**Scope:** all 49 routes (the guided tour + 48 research pages in 10 groups) × 17 viewports — 320×568, 360×800, 375×812, 390×844, 393×852, 412×915, 430×932, 844×390 (phone landscape), 600×960, 768×1024, 820×1180, 1024×768, 1280×800, 1366×768, 1440×900, 1600×900, 1920×1080 — rendered in headless Microsoft Edge with mobile/touch emulation below 768/1024 px. These are browser emulations, not physical devices.

**Tools:** `scripts/responsive_audit.py` (measures every render), `scripts/responsive_report.py` (writes `MOBILE_RESPONSIVE_AUDIT.md`), Playwright tests in `tests/test_web_e2e.py`.

## Results (833 renders per phase)
| Check | Before | Final |
|---|---|---|
| Document-level horizontal overflow | 0 | 0 |
| Element extending past the viewport outside a scroll container | 0 | 0 |
| Label stretched into an empty panel (the reported Evidence defect) | 10 | 0 |
| Chart labels rendered < 7 px (atlas excluded: zoomable) | 201 | 0 |
| Touch targets < 40 px on touch-size screens | 539 | 0 |
| Console / page errors | 0 | 0 |

Per-route, per-viewport detail: `MOBILE_RESPONSIVE_AUDIT.md`. Root causes and fixes: `COMPLETE_UI_AUDIT.md`.

## Screenshots
- `docs/responsive-screenshots/before/<route>/<w>x<h>.jpg` and `final/…` — every route at 320, 390, 768, 1024, 1440 and 1920 px (294 images per phase; first viewport only). The review ZIP carries the `final` set; `before` stays local.
- `docs/visual-regression/{before,after}_*.jpg` — crops of the specific defects (Evidence grid at 1920/1600 px, currency page and sensitivity at 390 px, discovery matrix at 390 px, sensitivity at 1440 px).
- Inspected by eye: overview 320, atlas 390, sensitivity 768, Evidence grid 1920 (before/after), currency page 390. The sensitivity screenshot exposed a slider-rounding bug (selected value 0.3680 instead of the 0.3677 estimate), fixed and now covered by a test.

## Automated responsive tests (all pass)
| Test | Covers |
|---|---|
| `test_every_route_fits_viewport[320x568, 390x844, 844x390, 768x1024, 1024x768]` | all 49 routes: no page overflow, no escaping element, no stretched label, no page errors — portrait and landscape |
| `test_touch_targets_and_drawer_on_phone` | ≥ 40-px controls on six key pages; drawer opens inside the viewport, locks background scroll, closes on Escape and returns focus |
| `test_phone_layout_has_no_horizontal_scroll` | 10 key pages at 390 px; menu opens, navigation closes it |
| `test_feature_evidence_has_no_stretched_label_panels` | the reported Evidence defect on six feature pages at 1920 px |
| `test_sensitivity_recomputes_and_exposes_values` | slider recomputes 1 − q; data table present; estimate restored |
| plus existing route, refresh, back/forward, direct-URL and interaction tests | |

## Remaining limitations
- Not tested on physical iOS/Android devices or Safari/Firefox engines (Edge/Chromium only).
- The dependency atlas starts zoomed on phones; reading the whole graph needs pan or zoom (by design).
- Very wide research tables (route patterns, ledger) scroll horizontally inside their own region with a sticky first column rather than switching to card layout.
- There are no modal dialogs in the product; the only overlay is the mobile navigation drawer.
