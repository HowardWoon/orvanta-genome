# Feature justification & technology evaluation (written before implementation)

Product identity: **The Synthetic Rule Intelligence Lab**. Workflow: **DISCOVER → RECONSTRUCT → VALIDATE → EXPLAIN**.
Each feature below is accepted only if it serves the official task (reverse-engineer the generator's rules, logic, causal relationships and business knowledge) and a rubric line.

## Features evaluated

| Feature | Workflow stage | Competition relevance / rubric | Research value | Data & assumptions | Cost | Validation | Decision |
|---|---|---|---|---|---|---|---|
| **Automated Rule Discovery Engine**: pairwise dependency scan (Cramér's V / normalised mutual information) over all discretised features + shallow decision trees on target fields, candidate rules ranked by purity × coverage | DISCOVER | 1.1 hypotheses, 1.2 rule quality, 3.3 method: shows that rules came from a systematic search, not cherry-picking | finds relationships we have not hand-coded; confirms that "no dependency" findings are complete | 2M-row random sample (dev = hash half 0, validation = half 1); discretisation of continuous fields; trees as a search tool, not a model | ~2 min | every candidate re-scored on the independent half; reported with its holdout purity and lift | **Build** |
| **Statistical Forensics: synthetic fingerprints**: Benford first digit, cents-digit uniformity, round-number shares, timestamp second/minute uniformity, identifier grammar (BIC numbering, account templates) | DISCOVER / VALIDATE | the case says NumPy + Faker generated the data; fingerprints test *how* values were drawn (1.2, 1.5) | separates "drawn from a continuous distribution" from "chosen from templates" | full data via DuckDB; χ² goodness of fit with effect size (Cohen's w, MAD) | ~1 min | stability across splits | **Build** |
| **Change-point detection** on weekday-normalised daily volume | DISCOVER | turns T4 ("weekly steps") from an eyeballed claim into a located, tested rule | locates the step dates and tests whether steps align with week boundaries | 93 daily totals; binary segmentation with a BIC penalty on log-volume (Gaussian errors on the log scale, checked by residuals) | seconds | segment means on both random halves; boundary weekday check | **Build** |
| **Conditional independence tests → Rule Dependency Atlas** | RECONSTRUCT / EXPLAIN | "causal relationships" is in the task text (1.3 depth, 2.2 consistency). The atlas lets judges inspect what depends on what, and what was tested independent | encodes the generator as a dependency graph: validated deterministic edges, probabilistic dependencies, tested non-edges, unresolved | stratified Cramér's V (dependency of X,Y within strata of Z); no causal identification claimed, edges = "generation dependency consistent with data" | ~2 min | each edge links to a rule ID and its validator; non-edges carry their test statistic | **Build** (signature feature) |
| **Data lineage & reproducibility manifest**: SHA-256 of every artefact, row counts, schema contract, tool versions, processing log | VALIDATE / EXPLAIN | 3.1 preparation, 3.2 claim–evidence, 3.4 responsible use: a judge can trace a dashboard number to its file and script | proves outputs come from the current pipeline | file hashes (Parquet hashing ~10 s) | low | contract test in pytest | **Build** |
| **Rule Explorer v2** (every field the brief lists: formulation, logic, n, effect size, validation, counterexamples, confidence, interpretation, limitations) + downloadable per-rule evidence report | EXPLAIN | central product feature; directly serves "inspect the evidence behind a finding" | none new; improves inspectability | register.json + validation.json | low | snapshot test of report generation | **Build** |
| Bayesian inference for proportions | VALIDATE | marginal: with n = 10M, Beta posteriors equal the Wilson intervals already reported | none | — | low | — | **Not built**: no information gain; documented |
| Bootstrap CIs | VALIDATE | useful only for statistics without closed-form SEs | applied to the non-analytic quantities that matter: country-effect split-half r and G3 loop error (via split replication) | — | — | — | **Covered** by 5-split replication + Wilson/Fisher CIs |
| Extreme-value analysis (GPD) | VALIDATE | tail behaviour already established (A3: lognormal, Hill drift); GPD on a lognormal tail gives ξ→0 and adds no rule | low | — | — | — | **Not built**: A3 covers it |
| Association-rule mining (Apriori) | DISCOVER | overlaps with decision-tree leaves + dependency scan on categorical features | low incremental | — | needs mlxtend (not installed) | — | **Not built**: tree leaves give the same if-then rules with holdout scoring |
| Generic fraud classifier / chatbot / risk score | — | outside the case | — | — | — | — | **Rejected** |

## Technology evaluation

| Technology | Needed? | Problem solved | Better than simpler alternative? | Cost | Maintenance | Decision |
|---|---|---|---|---|---|---|
| DuckDB | yes | out-of-core SQL on 10M rows, RFC-4180 CSV, GROUPING SETS for split validation | pandas would need chunking and could not parse the multi-line CSV reliably | in-process, 9 GB cap | one dependency | **Keep** |
| PyArrow / Parquet | yes | columnar storage 4.6 GB → 1.27 GB / 0.48 GB | CSV re-parsing costs about 80 s per pass | none | stable | **Keep** |
| SciPy | yes | distributions, χ², KS, sparse PageRank | — | low | stable | **Keep** |
| scikit-learn | limited | decision trees for discovery; GaussianMixture for X3 | hand-written trees would be error-prone | low | stable | **Keep (scoped)** |
| Polars | no | DuckDB already covers it | duplicate engine | — | — | **Not adopted** |
| NetworkX | no | graph metrics computed with DuckDB + SciPy sparse | adds a dependency and is slow on 2.3M edges | — | — | **Not adopted** (D-11) |
| Plotly | no | Altair (bundled with Streamlit) + matplotlib cover interactive and static charts | not installed; duplicate charting stack | — | — | **Not adopted** |
| Pandera | no | schema contracts implemented as explicit pytest checks + lineage manifest | not installed; a small number of contracts | — | — | **Not adopted** |
| Hypothesis (property tests) | no | rulelib functions are small and are tested with hand-crafted edge cases | not installed | — | — | **Not adopted** |
| SHAP | no | no predictive model whose behaviour needs explaining; rules are explicit | — | — | — | **Not applicable** |
| MLflow | no | no model training loop; experiment record = validation.json + lineage manifest with hashes | heavy for a 1-machine pipeline | — | — | **Not adopted** |
| FastAPI | no | the presentation layer reads static artefacts; no write path or multi-client service | would add a server and failure modes without a benefit | — | — | **Not adopted** |
| Streamlit (+ Altair) | yes | interactive local workbench with headless AppTest testing | custom React would cost days | low | moderate (widget-state quirks handled) | **Keep** |
| Static web edition | yes | hosting on Vercel (Streamlit cannot run there) | — | low | regenerated by src/web.py | **Keep** |
