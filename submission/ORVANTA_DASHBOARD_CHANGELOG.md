# ORVANTA dashboard changelog

## v2: reconstruction (14 Nov 2026)

### Structure
- Rebuilt all 15 pages on one template. On each feature-group page:
  - the left column holds the research question, rule cards (formula, test status, confidence level, "Reading:"), an evidence table and a "Read with care" box;
  - the right side holds a 2 × 2 chart grid, and every chart has a source line and a "Reading:" caption.
- Page plan:

| Page | Content |
|---|---|
| 1 | Executive overview |
| 2 | Discovery engine and dependency atlas |
| 3 | Time |
| 4 | Currency and FX |
| 5 | Routing |
| 6 | Institutions |
| 7 | Processing time |
| 8 | Network |
| 9 | Statistical forensics |
| 10 | Statistical robustness |
| 11 | Payment value |
| 12 | Parties and text |
| 13 | Fraud anomalies |
| 14 | Operational anomalies |
| 15 | Synthesis |

- Every one of the 34 rules now appears in an evidence table. Each row gives the key metric, the full-data value, the range over 5 splits, n and the evidence ID, all read from `validation.json` and the evidence ledger.

### Pages that changed most
- **Page 1 (executive overview):** six KPI tiles, a five-stage method strip, a headline-discoveries table, a 34-rule coverage grid by feature group, a data-integrity table and a scope box. Blank share fell from 0.43 to 0.26.
- **Page 2:** added a "How the engine changed our hypotheses" table and a "Strongest dependencies and what explains them" table (top 9 strong pairs, V on the development and validation halves, explaining rule). Moved "Why significance is not enough" into the left column.
- **Page 4:** added a worked C2 example from real records, including the only two exceptions.
- **Page 9:** added the fixed-rate search table (a negative result) and a new uniformity-fingerprint chart (Cohen's w for seconds, minutes, duration digit, Benford and cents).
- **Page 12:** added a field-anatomy table explaining what each party field contains.
- **Page 13:** the anomaly-profile chart now shows median amount and median duration per label against normal traffic. The old chart showed counts, which did not match its caption.
- **Page 15:**
  - generator blueprint (10 stages) and a confidence matrix of all 34 rules;
  - "What we rejected (selection of 29)" and a research-integrity table;
  - "How the stages connect", open questions and the conclusion.
  - Blank share fell from 0.62 to 0.25.

### Charts
- Added 17 charts, among them:
  - change points, local hour, R1 by country, R2 classes, R5b roles, R3 scatter;
  - STP by size, strength CCDF, parameter CIs, exceedance, amount variance;
  - IBAN by country, ordering/beneficiary share, anomaly rates, duplicate groups, fat-finger PR, uniformity fingerprints.
- Widened the tall charts (time weekday, amount by country, tokens, country compare, QQ) to fit the grid.
- Chart titles now wrap automatically, so none is clipped at the right edge (previously clipped on pages 7, 9 and 13).

### Layout QA
- Added `scripts/dashboard_audit.py`. On every page it measures overflow, footer clearance, column zoom and blank share. Result: 0 overflow on all 15 pages, footer clearance ≥ 9 px, blank share 0.16–0.26.
- Added `scripts/dashboard_registers.py`, which writes the rule crosswalk and the claim-evidence register from the rendered HTML.

### Integrity (unchanged rules, stated more visibly)
- Inconclusive rules (T4, G1, X5) and negative results (fixed FX rate, CUSTOMER_RECALL) stay on the pages with their status.
- Every page states that the data is synthetic and that the rules are reconstructions consistent with the data, not recovered source code.
- Atlas edges are labelled as generation dependencies, not causal claims.
