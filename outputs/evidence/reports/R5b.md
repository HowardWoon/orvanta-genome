# R5b — On endpoint mismatch, currency follows the path's first bank; account/IBAN follows ORDERING_BIC8

Status **PASS** · confidence **Medium** · type E · feature group Routing / Currency · validated 2026-11-14T17:00:29

**Hypothesis.** On swapped rows, which BIC drives currency, timing and account format?

**Explicit rule.** On replaced rows, CURRENCY_CODE and the local clock follow path[1] (instructing bank); account IBAN and ordering address follow ORDERING_BIC8 (account-servicing bank)

**Logic.** `compare P(cur = home(path[1])) vs P(cur = home(ORDERING_BIC8)) on rows with path[1] ≠ ORDERING_BIC8`

**Fields.** CURRENCY_CODE, EPOCH_SECONDS, ORDERING_ACCOUNT, BIC8_PATH

**Method.** Compare home-currency match, local-night share and IBAN prefix against path[1] vs ORDERING_BIC8.

**Acceptance criterion.** home-ccy share via path[1] > 0.85 and via ORDERING_BIC8 < 0.25; IBAN prefix = ORDERING_BIC8 country == 1

**Sample size.** 498,399 (n) · **Effect size.** see metrics · **Validation.** PASS on 5 splits (P1, P2, full, half_0, half_1)

**Counterexamples / exceptions.** Small share of non-home currency on both sides (vehicle currencies).

**Limitations.** Relies on our data-derived country→currency map.

**Economic interpretation (interpretation, not proven by data).** The instructing bank books and times the payment; the customer's account stays at the servicing bank.

## Metrics by split
```json
{
 "P1": {
  "ccy_follows_path_first": 0.9347258373123265,
  "ccy_follows_obic": 0.13814145105407408,
  "iban_follows_obic": 1.0,
  "n": 232052.0
 },
 "P2": {
  "ccy_follows_path_first": 0.9347843227068449,
  "ccy_follows_obic": 0.13907046071478185,
  "iban_follows_obic": 1.0,
  "n": 266347.0
 },
 "full": {
  "ccy_follows_path_first": 0.9347570922092541,
  "ccy_follows_obic": 0.13863791861540653,
  "iban_follows_obic": 1.0,
  "n": 498399.0
 },
 "half_0": {
  "ccy_follows_path_first": 0.9350372950376157,
  "ccy_follows_obic": 0.13834234479773305,
  "iban_follows_obic": 1.0,
  "n": 249497.0
 },
 "half_1": {
  "ccy_follows_path_first": 0.9344762195562912,
  "ccy_follows_obic": 0.13893419900201687,
  "iban_follows_obic": 1.0,
  "n": 248902.0
 }
}
```

Validator: `src/rules.py` · `R5b` · reproduce with `python -m src.validation`