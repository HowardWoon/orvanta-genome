# Methodology

1. **Frame.** Treat the 10M rows as the output of an unknown program built from hard-coded rules, NumPy draws and Faker. The goal is to recover that program as a set of rules, each with a condition, effect, size and scope.
2. **Hypothesise.** Each hypothesis is phrased so it can fail. There are 37 logged in `findings/hypotheses.md` (H1–H37), including the rejected ones.
3. **Test, choosing the test by rule type.**
   - A, deterministic: exact match rate on all rows.
   - B, probabilistic: MLE fit, goodness of fit as an effect size (Cohen's w, KS D), confidence intervals (Wilson or Fisher information).
   - C, conditional: stratified contrasts and fixed-effect adjustment; Cramér's V for independence.
   - D, template: token-presence and format checks.
   - E, composite: joint predictions such as the loop rate from the size distribution.
4. **Challenge.**
   - State the best alternative and show that it fits worse.
   - Look for counterexamples and list them.
   - Check for Simpson effects with fixed effects.
   - Run out-of-sample checks for any rule that uses learned classes.
   - Correct for multiplicity: validators that run a batch of tests use Bonferroni (e.g. X5); the hypothesis-test registry shown on the site applies Benjamini–Hochberg within each test family, never pooled across unrelated families.
   - Report sensitivity to every analyst-chosen threshold (`stats.json → sensitivity_D1`).
5. **Replicate.** Every validator runs on 5 splits. Three deterministic rules are re-implemented in pure Python and must agree 100%.
6. **Explain.** Each rule gets an economic reading labelled as interpretation, plus a note where the dataset departs from reality.
7. **Classify confidence** on a six-level scale (criteria in `web/build_data/registry.json → levels`, shown on the site's Approach page):
   - **VALIDATED:** deterministic and exact (≥ 99.999% of rows) on every split, or a parameter whose CI contains the theoretical value and which passes all 5 splits with an independent second implementation / out-of-sample test.
   - **STRONGLY SUPPORTED:** passes all splits with a wide margin; mechanism explicit; best alternative tested and rejected.
   - **SUPPORTED:** passes, but part of the mechanism is inferred or thresholds are analyst-chosen.
   - **CANDIDATE:** proposed but not yet validated (empty by design — every candidate was either validated or rejected).
   - **INCONCLUSIVE:** a real pattern or a negative result whose mechanism we could not pin down (G1, T4, X5).
   - **REJECTED:** tested and refuted; kept on the record (29 entries).
   The older High/Medium/Low labels in the register map onto these levels.

**Statistical cautions applied.** No normality or independence was assumed without testing (A3 tests normality; G1 tests independence and rejects it). Rare anomaly classes are evaluated with precision, recall and F1, never accuracy. Detector results are framed as evidence of a signature, not proof of generation.
