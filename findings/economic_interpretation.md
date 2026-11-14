# Economic interpretation (summary)

Interpretations are plausible real-world readings of synthetic rules. They are **not** proven by the data. The per-rule detail is in `rule_evidence_register.md`.

| Rule | Observation (data) | Interpretation (real world) | Where the dataset departs from reality |
|---|---|---|---|
| C2 | conversions happen at every currency border on the route | correspondents convert into the currency of their next nostro account, so long multi-zone chains cost more | real chains often route along the payment currency |
| R1/R3 | hops are geometric; hubs are chosen by size | most banks pay directly; large banks (US/CH/GB) act as hubs | real routing follows bilateral relationships, not a fixed probability |
| R2 | Covered vs Indirect is a per-bank propensity (cover-prone banks ≈61%, others ≈7%, out of sample) | some banks habitually settle by cover (MT103 + MT202 COV) | real choice also depends on corridor and currency |
| C3 | currency drawn from route-bank currencies | a payment is denominated in a currency some bank in the chain can book | real invoicing currency is set by the commercial contract |
| F1 | USD amounts keep round units; converted currencies do not | invoices are issued in round units of the invoice currency | — |
| R4 | each link is hidden 5% of the time | legs outside the messaging channel reduce end-to-end traceability (the case for tracking) | — |
| R5/R5b | 5% instructing ≠ account bank | ordering institution vs instructing agent roles | — |
| D1/D2 | manual banks add ~20 min each, independent of time | STP automation is a bank capability; small banks lag | real delays also depend on cut-offs and time zones |
| A1/A2 | ×7.4 per business party; country level | commercial flows exceed personal flows; richer origins send larger tickets | country levels randomised by design |
| T1/T3/T4 | local office clock; universal week | payments are released in working hours | DST and local weekends ignored |
| P4 | beneficiaries reside away from their bank | diaspora / non-resident accounts (literal reading) | most likely a sampling shortcut |
| X1–X5 | bursts, mules, replays, ×100 slips, invisible recall | push-payment fraud mechanics; back-office errors | romance timing compressed to minutes |
