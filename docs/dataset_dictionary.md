# Dataset dictionary

Raw file: `swift_umdac_datathon_2026_fictitious_payment_data.csv` · 4,952,194,328 bytes (4.612 GiB) · 10,000,000 records · 21 columns · RFC-4180 CSV with multi-line quoted fields. The raw file is never modified.

| Column | Official meaning (CS A.1) | Observed format / facts (full data) | Derived fields |
|---|---|---|---|
| DISCLAIMER | — (not in appendix) | Empty on 9,999,999 rows; row 1 holds the legal notice ("purely fictitious … SWIFT © 2026") | dropped from analytic tables |
| EPOCH_SECONDS | Unix time, UTC | 1,682,853,746 – 1,690,797,361 (2023-04-30 11:22 → 2023-07-31 09:56 UTC); 93 calendar days | ts, d, hr, dow, local hour (via offset of first path bank) |
| CURRENCY_CODE | ISO 4217 | 85 codes; EUR 32.0%, USD 17.0%, GBP 8.7%, CHF 8.0% | curg (top 12 + Other) |
| USD_AMOUNT | amount in USD | 0.01 – 15,664,132,213.09; log-normal (σ≈2.28 in ln) | ln(amt) |
| ORDERING_BIC8 | sending institution | `NNNNCCLL`: 4-digit bank id, ISO country, location code (one per country, e.g. US=30, DE=F0) | o_bank_cc |
| BENEFICIARY_BIC8 | receiving institution | same format | b_bank_cc |
| BIC8_PATH | `;`-separated route | first element ≠ ORDERING_BIC8 in 5.0%, last ≠ BENEFICIARY_BIC8 in 5.0% (rule R5); `...` placeholders | known list, path_n, gaps |
| TOTAL_DURATION | elapsed seconds | 2 – 21,649; bimodal (seconds vs ~20 min) | slow flag (>120 s) |
| CONTINUITY_QFLAG | Y/N observability | N ⇔ path contains `...` (exact) | — |
| CURRENCY_CONVERSION_COUNT | FX steps | 0–17; equals currency borders along known BICs (exact) | — |
| PARTICIPANT_COUNT | institutions in route | 2–22; = number of known BICs (exact) | K = pc − 2 intermediaries |
| TRANSACTION_TYPE_CODE | Direct/Indirect/Covered | 63.2% / 32.6% / 4.2% | — |
| ORDERING_ACCOUNT / BENEFICIARY_ACCOUNT | anonymised `_FAKE_…` | IBAN (prefix = BIC country) or local free format | o_iban, b_iban |
| ORDERING_DETAILS / BENEFICIARY_DETAILS | party text | optional `/account` line + ≤4×35 lines; free (wrapped) or structured `1/ 2/ 3/` (MT 50F/59F style) | o_struct, b_struct |
| ORDERING_TOKENS / BENEFICIARY_TOKENS | engineered token patterns | `<type:len>` tokens: business, company_keyword, first_name, last_name, street, city, post_code:CC, country_code:CC, country_name, iban:len, line_break:35, chr:pattern … | o_cust_cc, b_cust_cc (last country_code token) |
| ORDERING_TYPE / BENEFICIARY_TYPE | B business / C consumer | ordering B 78.7%; beneficiary B 28.8% (independent) | — |
| ANOMALY_TYPE | anomaly label | empty (normal) 9,992,994; ROMANCE_SCAM 2,476; FAT_FINGER_MISTAKE 1,940; CEO_SCAM 945; DUPLICATE_PAYMENT 679; ACCOUNT_REPLACEMENT_SCAM 649; **CUSTOMER_RECALL 317 (undocumented)** | NORMAL label |

Fraud vs error: ROMANCE_SCAM, CEO_SCAM, ACCOUNT_REPLACEMENT_SCAM are frauds; FAT_FINGER_MISTAKE and DUPLICATE_PAYMENT are operational/user errors; CUSTOMER_RECALL is an after-the-fact customer action (classification not given officially).

Cautions: TOTAL_DURATION is elapsed observation time, not proven settlement time. CONTINUITY_QFLAG is observability, not success/failure. USD_AMOUNT is normalised — the original-currency amount is not provided.
