# P1b — Beneficiary type independent of ordering type

Status **PASS** · confidence **High** · type B · feature group Parties · validated 2026-11-14T17:00:29

**Hypothesis.** Receiver type independent of sender type.

**Explicit rule.** BENEFICIARY_TYPE is drawn independently of ORDERING_TYPE

**Logic.** `|P(bB | oB) − P(bB | oC)|`

**Fields.** ORDERING_TYPE, BENEFICIARY_TYPE

**Method.** Conditional shares by split.

**Acceptance criterion.** |P(bB|oB)-P(bB|oC)| < 0.005

**Sample size.** 10,000,000 (full data) · **Effect size.** diff = 0.001093 · **Validation.** PASS on 5 splits (P1, P2, full, half_0, half_1)

**Counterexamples / exceptions.** -

**Limitations.** -

**Economic interpretation (interpretation, not proven by data).** Independent sampling per side.

## Metrics by split
```json
{
 "P1": {
  "pB_given_oB": 0.288295332679543,
  "pB_given_oC": 0.2875720028011771,
  "diff": 0.0007233298783658748
 },
 "P2": {
  "pB_given_oB": 0.2884672046512103,
  "pB_given_oC": 0.28705328053731644,
  "diff": 0.0014139241138938496
 },
 "full": {
  "pB_given_oB": 0.2883872615334523,
  "pB_given_oC": 0.28729445275936394,
  "diff": 0.0010928087740883496
 },
 "half_0": {
  "pB_given_oB": 0.28839111074118773,
  "pB_given_oC": 0.28703408489198756,
  "diff": 0.0013570258492001663
 },
 "half_1": {
  "pB_given_oB": 0.288383405598695,
  "pB_given_oC": 0.2875551027863509,
  "diff": 0.0008283028123441394
 }
}
```

Validator: `src/rules.py` · `P1b` · reproduce with `python -m src.validation`