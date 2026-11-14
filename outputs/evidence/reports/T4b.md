# T4b — Weekly volume levels are piecewise-constant with every change point on a Monday (week boundary)

Status **PASS** · confidence **High** · type B · feature group Time · validated 2026-11-14T17:00:29

**Hypothesis.** Do weekly levels change at random times or at week boundaries?

**Explicit rule.** level(week) is piecewise-constant and changes only at week boundaries (Mondays)

**Logic.** `binary segmentation of weekday-normalised log volume with BIC penalty 2·ln(n)·σ̂²`

**Fields.** EPOCH_SECONDS

**Method.** Binary segmentation with BIC penalty on weekday-normalised log daily volume (91 full days); residual normality.

**Acceptance criterion.** binary segmentation (BIC penalty) on weekday-normalised log volume: ≥1 change point, 100% on Mondays, residual sd < 0.03

**Sample size.** 10,000,000 (full data) · **Effect size.** see metrics · **Validation.** PASS · full-data / out-of-sample test

**Counterexamples / exceptions.** Several adjacent weeks share a level (segments of 1–3 weeks).

**Limitations.** 13 weeks only; cause of the levels still open (T4).

**Economic interpretation (interpretation, not proven by data).** Volume plans are set per week (business calendars), not per day.

## Metrics by split
```json
{
 "full": {
  "change_points": 10,
  "share_on_monday": 1.0,
  "residual_sd_log": 0.018307311508139548,
  "segments": 11
 }
}
```

Validator: `src/rules.py` · `T4b` · reproduce with `python -m src.validation`