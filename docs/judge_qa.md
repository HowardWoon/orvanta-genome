# Judge Q&A defence pack

**Q: With 10M rows everything is significant. How do you avoid false discoveries?**
A: We accept rules on effect size and exactness, not p-values: exact match rates (C2 99.99998%), Cohen's w < 0.01 (R1), Cramér's V < 0.01 (R2, X6), and max deviation < 0.006 (R4). Each criterion must hold on 5 splits: full, two random halves and two time periods. Where we did use p-values (CUSTOMER_RECALL) we applied Bonferroni correction.

**Q: Isn't FX = currency borders circular, since you built the currency map from the data?**
A: The map is built from `CURRENCY_CODE` by sending country (the modal currency). The rule predicts `CURRENCY_CONVERSION_COUNT`, a different field, from the path only. It reproduces 9,999,998 rows, and two natural alternatives score 91.7% and 93.5%. A pure-Python re-implementation agrees 100% on a 200k sample.

**Q: How do you know duration additivity isn't an artefact of how you defined "slow banks"?**
A: Classes are learned on one random half and evaluated on the other. Out-of-sample, both-slow is 2,641 s and one-slow about 1,400 s, a ratio of 1.89, close to the 2.0 that pure additivity predicts.

**Q: Durations vary by hour — doesn't that contradict "bank attribute only"?**
A: Raw slow share ranges 3.7 points across hours. Once sender-bank and receiver-bank fixed effects are removed, the range is 0.3 points. Banks in different time zones have different STP rates (Simpson's paradox).

**Q: Why should we believe ORDERING_BIC8 is not the sending bank on 5% of rows?**
A: On those rows the currency matches the first path bank's home currency 93% of the time (14% for ORDERING_BIC8). The local-night share is 4.6% using the path bank's clock vs 17% using ORDERING_BIC8's. Meanwhile the IBAN prefix and customer country match ORDERING_BIC8 100%. Two different roles explain this: the account-servicing institution vs the instructing agent.

**Q: What is CUSTOMER_RECALL?**
A: It is not in the official case appendix. We tested 11 features against normal traffic and none differs after Bonferroni correction (and none is significant under per-family Benjamini–Hochberg either). We report it as a negative result. A recall happens after the payment is sent, so message fields would not reveal it.

**Q: Is the romance scam really Consumer → Consumer as the case says?**
A: The sender is a consumer in 100% of rows, but 27% of receivers are businesses, which is the base rate. The generator constrains only the sender.

**Q: Why no machine-learning model?**
A: The task is to reconstruct rules, and every rule is an explicit formula a reader can check. ML is used once, a 2-component Gaussian mixture to locate the two fat-finger modes, because that is a density-estimation question. A black-box classifier would add score-free complexity (rubric 3.3).

**Q: How would someone reproduce your work?**
A: Run `python run_all.py`: ingestion → graph → stats → validation → evidence → cube → register → charts → reporting → tests. `src/rulelib.py` doubles as a generator specification. The tests cover rule logic, artefact reconciliation and every dashboard page.

**Q: What can't you explain?**
A: The cause of the weekly volume levels (T4), the directional bank-pair affinities (G1), the exact step-time tail, and why EUR and USD are the vehicle currencies (their rates we did quantify: EUR 1.41%, USD 0.75% on routes without either, flat across route length and splits — H38). Business-sender shares by country are explained by P5 (a bank attribute). Listed in `findings/limitations.md`.

**Q: Your network claims — isn't any graph of 10M payments "heavy-tailed"?**
A: We go further than describing heavy tails. G3 makes a quantitative prediction: if correspondents are drawn i.i.d. in proportion to size, with replacement, the share of paths that revisit a bank should be 1 − Π(1 − j·Σp²). That matches observed values within 3.1% at every route length. G1 is the opposite case: independence of bank pairing is *rejected* (χ²/dof 125–358), and we say we have not identified the mechanism.

**Q: Did you check the lognormal assumption in the tails, where it matters for risk?**
A: Yes. Within-country residuals have skew −0.02, excess kurtosis 0.02 and KS D 0.003. Model-implied exceedances above $100k, $1M, $10M, $100M and $1B are within 1–15% of observed. The Hill index drifts from 2.21 to 1.21, which rules out a power law. 26.5% of the top 1,000 amounts are fat-finger errors, so extreme tickets come from errors, not from a fat natural tail.

**Q: How good are your anomaly detectors, and why no ML model?**
A: We report per-class precision, recall and F1 with confusion counts:
- Duplicates (exact key within 2 h): F1 0.977.
- Romance (burst rule): F1 0.951.
- Fat finger from the amount alone: F1 0.22 (PR-AUC 0.10). That is 500× better than chance, but the amount by itself cannot reliably separate errors.
- The CEO heuristic fails (precision 0.03%).

These evaluate the reconstructed signatures. We do not claim that fitting the labels would prove how they were generated.


**Q: C2 has two exceptions. Doesn't that break the rule?**
A: They are the only two payments in the dataset that touch an Eritrean bank (receiver 0000ERA0). Eritrea never sends, so its home currency cannot be inferred and our predictor treats the route as single-currency (0 borders); the generator recorded 1. That is exactly C2's prediction if Eritrea's currency differs from the sender's. The exceptions mark the rule's observable scope, not a second mechanism. Both records are in Forensic Replay.
