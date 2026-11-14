# Data quality report

Generated from `web/build_data/meta.json` (pipeline output) — do not edit numbers by hand; rerun `python -m src.webdata`.

- Rows: 10,000,000 · raw columns: 21 · span (UTC): 2023-04-30 11:22:26 → 2023-07-31 09:56:01
- Currencies: 155 · banks (BIC8): 8,727 · sender accounts: 391,132 · beneficiary accounts: 2,590,877 · labelled anomalies: 7,006

## Checks

| Check | Result | Status | Detail |
|---|---|---|---|
| Rows parsed (RFC-4180, multi-line fields) | 10,000,000 | pass | row count asserted after every stage |
| Exact duplicate rows (time, accounts, amount, currency, path, duration) | 1 | info | the one exact duplicate is a labelled DUPLICATE_PAYMENT pair sent in the same second (0-s gap), consistent with rule X2; kept |
| Currency codes not 3 upper-case letters | 0 | pass | regex [A-Z]{3} |
| ORDERING_BIC8 failing NNNN·CC·LL grammar | 0 | pass | regex |
| BENEFICIARY_BIC8 failing grammar | 0 | pass | regex |
| Non-positive amounts / durations | 0 / 0 | pass | domain check |
| PARTICIPANT_COUNT ≠ known BICs in path | 0 | pass | rule R6 |
| CONTINUITY_QFLAG inconsistent with '...' | 0 | pass | rule R7 |
| Unexpected categorical values (flag / type / party) | 0 | pass | domain sets |
| Malformed path separators (';;', leading/trailing ';') | 0 | pass | route structure |
| Header BIC ≠ path endpoint | ≈9.7% of rows | info | explained by rule R5 (5% swap per end), not an error |
| Country token absent from party details | ≈39% per side | info | analysis uses BIC country as primary |
| Detail text beyond MT 4×35 | 0.17% of rows | info | generator quirk, kept |
| DISCLAIMER column | 1 non-empty row | info | legal notice; dropped from analytic tables |

## Field profile (type, observed range, missingness)

| Field | Type | Observed | Missing | Origin | Limitation |
|---|---|---|---|---|---|
| `EPOCH_SECONDS` | integer (Unix s, UTC) | 1,682,853,746 – 1,690,797,361 | 0 | raw | UTC only; local clock reconstructed (T1) |
| `CURRENCY_CODE` | string, ISO 4217 | 85 codes | 0 | raw | home-currency map inferred from data |
| `USD_AMOUNT` | decimal (USD) | 0.01 – 15,664,132,213.09 | 0 | raw | normalised; original-currency amount absent |
| `ORDERING_BIC8` | string NNNN·CC·LL | 8,392 banks | 0 | raw | account-servicing bank; 5% differ from path[1] |
| `BENEFICIARY_BIC8` | string NNNN·CC·LL | 8,266 banks | 0 | raw | 5% differ from last path BIC |
| `BIC8_PATH` | string, ';'-separated | 2–22 known BICs; '...' = hidden | 0 | raw | hidden hops unobservable |
| `TOTAL_DURATION` | integer seconds | 2 – 21,649 | 0 | raw | elapsed time to completion or observation end; not proven settlement time |
| `CONTINUITY_QFLAG` | Y / N | N on 7.7% | 0 | derived in generator | observability marker, not success/failure |
| `CURRENCY_CONVERSION_COUNT` | integer | 0–17 | 0 | derived in generator | = currency borders on known path |
| `PARTICIPANT_COUNT` | integer | 2–22 | 0 | derived in generator | counts known BICs only |
| `TRANSACTION_TYPE_CODE` | Direct/Indirect/Covered | 63.2 / 32.6 / 4.2% | 0 | raw | — |
| `ORDERING_ACCOUNT` | string _FAKE_… | 391,132 accounts | 0 | raw | synthetic identifiers |
| `BENEFICIARY_ACCOUNT` | string _FAKE_… | 2,590,877 accounts | 0 | raw | synthetic identifiers |
| `ORDERING_DETAILS` | free text, multi-line | ≤ 4×35 MT layout | 0 | raw | synthetic Faker-style text |
| `ORDERING_TOKENS` | engineered token string | <type:len> tokens | 0 | derived (engineered) | pattern summaries, not original content |
| `BENEFICIARY_DETAILS` | free text, multi-line | ≤ 4×35 MT layout | 0 | raw | synthetic |
| `BENEFICIARY_TOKENS` | engineered token string | <type:len> tokens | 0 | derived (engineered) | pattern summaries |
| `ORDERING_TYPE` | B / C | 78.7% B | 0 | raw | — |
| `BENEFICIARY_TYPE` | B / C | 28.8% B | 0 | raw | — |
| `ANOMALY_TYPE` | label or empty | 6 labels, 7,006 rows | 9,992,994 | raw | CUSTOMER_RECALL undocumented by organiser |

## Interpretation safeguards

- `TOTAL_DURATION` may run to an observation endpoint; it is treated as observed elapsed time, not proof of completion.
- `CONTINUITY_QFLAG` = route observability (`N` ⇔ a `...` hidden hop, rule R7), not payment success.
- `ORDERING_TOKENS` / `BENEFICIARY_TOKENS` are engineered summaries supplied with the data, not original text.
- `ANOMALY_TYPE` blank = normal payment. `CUSTOMER_RECALL` (317 rows) is outside the case appendix; kept and analysed (X5), meaning not invented.
- Parsing is RFC-4180 (quoted multi-line DETAILS fields); identifiers and codes are kept as strings; the row count is asserted after every stage.
