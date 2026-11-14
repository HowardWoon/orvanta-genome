# Limitations and open questions

**Method limits**
- *Home-currency map is inferred* (modal currency per country). The exact C2 match (9,999,998/10M) validates it indirectly; 2 rows have a BIC country absent from the map.
- *Offsets are whole hours* estimated by profile alignment (India +5 vs true +5:30). This affects local-hour charts slightly, not the rule.
- *Bank speed classes* use a 0.95 threshold on the slow share. D1 is tested out-of-sample to avoid circularity; the class boundary is a modelling choice.
- *D2 fixed effects* use one-step two-way demeaning (linear probability), not a full logit with crossed effects.
- *Fat-finger factor*: we cannot tell ×100 from ×1000 for individual rows, because normal amounts already vary by about 0.9 in log₁₀ around their expectation.
- *Country effects are randomised by design* (case study p2). Rankings describe the generator, not real economies.

**Unexplained (honestly reported)**
- T4 weekly step levels: no cause identified.
- C1 vehicle-currency selection: which non-home currency is picked.
- The exact distributions of the fast and manual step lengths (tail up to 21,649 s).
- Bank-level amount variance (0.22 of 5.22).
- Country-level business-sender share (38–96%).
- CUSTOMER_RECALL: no signature (negative result); the label is not documented by the organiser.

**Data that cannot answer some questions**
- The original-currency amount is absent, so conversion rates cannot be checked.
- Duration is elapsed observation time; the data cannot show settlement success.
- The text tokens are engineered patterns, not the original content.

**Added after the discovery/forensics layer**
- R2 was revised: the original 'constant 11.3%' was wrong across banks; the per-bank propensity itself is not explained further.
- C3's direction (route first, then currency) is consistent with the data, not identified.
- F1: no fixed FX rate restores round non-USD originals; the conversion mechanism is open.
- Mediation triage uses a residual-V threshold of 0.03 (analyst-chosen).
