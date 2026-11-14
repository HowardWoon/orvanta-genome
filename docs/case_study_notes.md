# Case study notes

**What Swift is (for correct framing):** a member-owned cooperative operating the messaging network that connects ~11,500 institutions. Swift carries payment *instructions*; it does not hold or move the funds. Our language: "payment messages", "instructing / account-servicing institution", "correspondent (intermediary)", never "Swift transferred the money".

**What the data is:** a snapshot of a *directed temporal pseudograph* — nodes are institutions and parties, edges are timestamped payment instructions, and parallel edges and loops are allowed (59,191 paths revisit a bank; 2,387 rows have the same ordering and beneficiary BIC). It is flattened into one row per payment. It was generated with hard-coded rules, NumPy random draws and Faker, with business knowledge distilled from real traffic, while country sizes and populations are deliberately randomised.

**The ask:** reconstruct the generating logic and causal relationships. "Dig deeper than A is correlated with B." Partial or negative results that are well argued earn credit.

**Our framing of the generator (reconstructed, see register):**
1. Pick the ordering party (type, country weighted by banking size) and its account-servicing bank (ORDERING_BIC8). With 5% probability a different instructing bank sends the message (R5).
2. Timestamp = global weekly level × universal weekday shape × office-hours curve on the instructing bank's local clock (T1–T4).
3. Currency = instructing bank's home currency (93%) or a vehicle currency (C1).
4. Route: K = ⌊Exp(1)⌋ intermediaries drawn by size (R1, R3); Covered with p = 0.113 (R2); each link hidden with p = 0.05 (R4); FX = currency borders (C2); PARTICIPANT_COUNT and the continuity flag derived from the path (R6, R7).
5. Amount = exp(6 + 2[O=B] + 2[B=B] + country + bank + N(0, 2²)) (A1, A2).
6. Duration = sum over banks of a fast step or a manual step, decided by the bank's STP rate (D1, D2).
7. Party text from Faker templates in MT 4×35 layout; IBAN by country registry; beneficiary residence sampled by population (P1–P4).
8. Anomalies injected afterwards with specific signatures (X1–X6).
