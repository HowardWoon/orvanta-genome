"""Build notebooks/ORVANTA_prototype_analysis.ipynb, a readable, self-contained prototype of the ORVANTA analysis for Google Colab.

Usage:
  python scripts/make_notebook.py            # write the notebook (no outputs)
  python scripts/make_notebook.py --execute  # also run it locally on the parquet copy and save it with outputs

The dashboard's reference values are copied from outputs/evidence/validation.json at build time, so the notebook can print
"notebook vs dashboard" without anyone retyping numbers.
"""
import json, os, sys
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "ORVANTA_prototype_analysis.ipynb"
V = {r["id"]: r for r in json.loads((ROOT / "outputs" / "evidence" / "validation.json").read_text(encoding="utf-8"))["rules"]}
f = lambda rid: V[rid]["metrics"]["full"]
REF = {
    "R6 share exact": f("R6")["share_exact"], "R7 share exact": f("R7")["share_exact"],
    "R1 continuation q": f("R1")["q_mle"], "R1 share direct (K=0)": f("R1")["p_direct"],
    "R4 per-link hidden p": f("R4")["p_link_mle"], "R2 pooled covered share": f("R2")["pooled_covered_share"],
    "R5 first-bank mismatch": f("R5")["p_first"], "R5 last-bank mismatch": f("R5")["p_last"], "R5 independence ratio": f("R5")["indep_ratio"],
    "C1 home-currency share": f("C1")["home_share"], "C2 FX rule exact share": f("C2")["share_exact"],
    "C2 alternative (distinct ccys - 1)": f("C2")["alt_distinct"], "C3 currency in route": f("C3")["in_route_share"],
    "T1 night share, local clock": f("T1")["night_local"], "T1 night share, UTC": f("T1")["night_utc"],
    "A1 intercept": f("A1")["intercept"], "A1 sender-business effect": f("A1")["effect_ordering_B"],
    "A1 receiver-business effect": f("A1")["effect_beneficiary_B"], "A1 interaction": f("A1")["interaction"],
    "A3 residual skew": f("A3")["skew"], "A3 residual excess kurtosis": f("A3")["excess_kurtosis"],
    "P2 IBAN prefix = BIC country": f("P2")["o_prefix"], "P4 ordering address = bank country": f("P4")["o_match"],
    "P4 beneficiary address = bank country": f("P4")["b_match"], "P1b P(B|B) - P(B|C)": f("P1b")["diff"],
    "F1 USD amounts ending .00": f("F1")["usd_whole_share"], "F1 other amounts ending .00": f("F1")["non_usd_whole_share"],
    "X1 romance series": f("X1")["series"], "X1 median ln step": f("X1")["median_ln_step"],
    "X2 duplicate groups": f("X2")["groups"], "X3 share inflated (x100)": f("X3")["up_share"],
    "X6 Cramer's V label x routing": f("X6")["cramers_v"],
}
# absolute tolerance per metric: sampling error at ~500k rows, or exact for deterministic rules
TOL = {"R6 share exact": 0, "R7 share exact": 0, "C2 FX rule exact share": 1e-4, "P2 IBAN prefix = BIC country": 0,
       "P4 ordering address = bank country": 1e-3, "X1 romance series": 0, "X2 duplicate groups": 0,
       "A1 intercept": .03, "A1 sender-business effect": .03, "A1 receiver-business effect": .03, "A1 interaction": .05,
       "A3 residual skew": .02, "A3 residual excess kurtosis": .03, "X1 median ln step": .01, "X3 share inflated (x100)": .02,
       "R5 independence ratio": .1, "X6 Cramer's V label x routing": .01, "P1b P(B|B) - P(B|C)": .006}
DEFAULT_TOL = .005

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md(r"""
# ORVANTA Genome: prototype analysis notebook

**UMDAC Datathon 2026 · Swift case · Team Nai Long**

This notebook is the readable prototype behind the ORVANTA dashboard. It treats the 10-million-row synthetic payment file as the output of an unknown generator and recovers that generator **rule by rule**. For each rule it:

1. **states the rule** and its formula,
2. **tests it** with an effect size or exact-match share (at n = 10M every p-value is ≈ 0, so p-values decide nothing),
3. **draws the evidence**, and
4. **prints the notebook's number next to the dashboard's**. The dashboard was computed on all 10M rows.

**Scope and honesty rules**
- The data is synthetic. Rates and country effects are generator settings, not real Swift traffic.
- The rules are reconstructions consistent with the data, not recovered source code.
- Dependencies are generation dependencies, not causal claims.
- By default the notebook runs on a **~5% deterministic sample** plus **every labelled anomaly row**, so it fits in free Colab. Sample estimates differ from the full-data dashboard by sampling error. Exact rules (R6, R7, C2, P2) must still match exactly.

**The notebook has two parts:**
- **Part A (sections 1–11): a readable prototype.** The core of every analysis is written out in plain cells. It runs on a sample and needs a few minutes.
- **Part B (sections 12–14): the complete production pipeline.** Every source file of the project is written to disk by `%%writefile` cells, so the full code sits inside this notebook. The pipeline then runs end to end on all 10M rows:
  - ingestion and the derived country tables;
  - the discovery scan, network graph, statistics and forensics;
  - all 34 validators on 5 splits, evidence, register, dependency atlas and lineage;
  - 48 charts, the website data and the evidence ledger;
  - the 15-page dashboard PDF, the 20-slide presentation PDF, the 41-page research report and the static website.

**Runtime on free Colab (2 CPUs, ~12 GB RAM):** Part A ≈ 5 min after loading. Part B ≈ 1.5–3 h. Set `RUN_FULL_PIPELINE = False` in section 0 to write the code without running it.
""")

md(r"""
## 0 · Setup

**Getting the data in:** the raw file `swift_umdac_datathon_2026_fictitious_payment_data.csv` (~5 GB) is not stored in this notebook. Use either option:
- **Google Drive (recommended):** put the CSV in your Drive, run the next cell, and set `DATA_PATH` to its path, e.g. `/content/drive/MyDrive/swift_umdac_datathon_2026_fictitious_payment_data.csv`.
- **Parquet copy:** if a teammate shares `payments.parquet` (1.3 GB), point `DATA_PATH` at it. It reads about 10× faster.

The raw CSV is read **once**. Section 1 converts it to a Parquet file in the working folder (about 10–20 min on Colab, because the address fields contain line breaks inside quotes and must be parsed sequentially). Part A and Part B both read that Parquet file.

**Runtime type:** the default CPU runtime is enough. Keep the browser tab open while Part B runs.
""")
code(r"""
import sys, os, math, re, json, time, shutil, subprocess, warnings
from pathlib import Path
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    # the exact library versions the project was built and tested with
    !pip -q install duckdb==1.5.2 pandas==3.1.0 scipy==1.17.1 scikit-learn==1.8.0 matplotlib==3.10.9 pyarrow==24.0.0 pypdf==6.19.0
    # headless Chrome renders the PDF deliverables in Part B (the pipeline uses Edge/Chrome's print-to-PDF)
    !wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt-get -qq install -y /tmp/chrome.deb > /dev/null 2>&1 || echo "Chrome install failed: the PDF steps will be skipped"
    from google.colab import drive
    drive.mount("/content/drive")
warnings.filterwarnings("ignore")
""")
code(r"""
# ---- settings you may change -------------------------------------------------------------
DATA_PATH  = ("/content/drive/MyDrive/swift_umdac_datathon_2026_fictitious_payment_data.csv" if IN_COLAB
              else os.environ.get("ORVANTA_DATA", "../data/processed/payments.parquet"))   # raw CSV or payments.parquet
WORK       = Path("/content/orvanta" if IN_COLAB else os.environ.get("ORVANTA_WORK", "orvanta")).resolve()   # project folder Part B builds
SAMPLE_PCT = 5        # Part A: deterministic hash sample of normal rows (5% ≈ 500k rows)
RUN_FULL_PIPELINE = True if IN_COLAB else os.environ.get("ORVANTA_RUN_FULL", "1") == "1"   # Part B: run the complete pipeline on all 10M rows (≈ 1.5–3 h on free Colab)
THREADS, MEMORY = (2, "6GB") if IN_COLAB else (int(os.environ.get("ORVANTA_THREADS", 2)), os.environ.get("ORVANTA_MEMORY", "6GB"))
SEED_NOTE  = "sample = hash(EPOCH_SECONDS, BIC8_PATH, USD_AMOUNT) — the same rows on every run"
# --------------------------------------------------------------------------------------------
import duckdb, numpy as np, pandas as pd, matplotlib.pyplot as plt
from scipy import stats
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 30)
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": .3, "axes.spines.top": False, "axes.spines.right": False})
BLUE, INK, RED, YELLOW, GREY = "#2479D8", "#111827", "#EF5147", "#F4D52E", "#8a8a8a"
print("duckdb", duckdb.__version__, "| pandas", pd.__version__, "| data file:", Path(DATA_PATH).name, "| found:", os.path.exists(DATA_PATH))
assert os.path.exists(DATA_PATH), "Set DATA_PATH to the dataset CSV (or payments.parquet) — see the instructions above."
""")
code("# Dashboard reference values (full 10M rows), copied from outputs/evidence/validation.json when this notebook was built.\n"
     f"REF = {json.dumps(REF, indent=1)}\nTOL = {json.dumps(TOL)}\nDEFAULT_TOL = {DEFAULT_TOL}\n"
     "RESULTS = {}   # filled as we go; compared with REF in the last section\n"
     "def record(name, value):\n    RESULTS[name] = float(value)\n    ref = REF.get(name)\n"
     "    print(f\"{name:<40} notebook {value:>12.6g}   dashboard {ref if ref is not None else '—':>12}\")")

md(r"""
## 1 · Load: CSV → Parquet once, then a deterministic sample and all labelled anomalies

- **Parsing:** DuckDB reads the CSV as RFC-4180 (`quote='"'`, `escape='"'`), so the multi-line address fields stay inside one row. Counting newlines would overstate the row count. The row count is asserted to be exactly 10,000,000.
- **Column handling:** every column is read as text, so identifiers (leading zeros, IBANs) are kept exactly. The `DISCLAIMER` column holds the legal notice on one row only, so the column is dropped and the row is kept. This is the same step as `src/ingestion.py` in Part B, which reuses the Parquet file.
- **What Part A keeps:**
  - `in_sample` rows: a hash sample used for every rate and distribution;
  - every row with an `ANOMALY_TYPE`, needed for the anomaly rules (bursts and duplicate groups must be complete).
""")
code(r"""
PQ = WORK / "data" / "processed" / "payments.parquet"; PQ.parent.mkdir(parents=True, exist_ok=True)
con = duckdb.connect(); con.execute(f"SET threads={THREADS}; SET memory_limit='{MEMORY}'; SET preserve_insertion_order=false")
if not PQ.exists():
    t0 = time.time()
    if DATA_PATH.endswith(".parquet"):
        try: os.link(DATA_PATH, PQ)              # same disk: a hard link costs no space
        except OSError: shutil.copy(DATA_PATH, PQ)
    else:
        csv = f"read_csv('{DATA_PATH}', header=true, quote='\"', escape='\"', all_varchar=true, max_line_size=10000000, parallel=false)"
        con.execute(f"COPY (SELECT * EXCLUDE (DISCLAIMER) FROM {csv}) TO '{PQ.as_posix()}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)")
    print(f"payments.parquet written in {time.time() - t0:.0f} s")
n_rows = con.execute(f"SELECT count(*) FROM read_parquet('{PQ.as_posix()}')").fetchone()[0]
assert n_rows == 10_000_000, n_rows
print(f"rows: {n_rows:,} (expected 10,000,000)")
src = f"read_parquet('{PQ.as_posix()}')"
con.execute(f'''
CREATE OR REPLACE TABLE base AS
SELECT
  EPOCH_SECONDS::BIGINT                                     AS epoch,
  CURRENCY_CODE                                             AS cur,
  USD_AMOUNT::DOUBLE                                        AS amt,
  TOTAL_DURATION::INT                                       AS dur,
  CURRENCY_CONVERSION_COUNT::INT                            AS fx,
  PARTICIPANT_COUNT::INT                                    AS pc,
  ORDERING_BIC8 AS obic, BENEFICIARY_BIC8 AS bbic, BIC8_PATH AS path,
  CONTINUITY_QFLAG AS cont, TRANSACTION_TYPE_CODE AS ttype,
  ORDERING_ACCOUNT AS oacc, BENEFICIARY_ACCOUNT AS bacc,
  ORDERING_TYPE AS otype, BENEFICIARY_TYPE AS btype,
  coalesce(ANOMALY_TYPE, '')                                AS anom,
  regexp_extract(ORDERING_TOKENS,    '.*<country_code:([A-Z]{{2}})>', 1) AS o_cust_cc,
  regexp_extract(BENEFICIARY_TOKENS, '.*<country_code:([A-Z]{{2}})>', 1) AS b_cust_cc,
  ORDERING_TOKENS LIKE '%<iban:%'                           AS o_iban,
  (hash(EPOCH_SECONDS, BIC8_PATH, USD_AMOUNT) % 10000) < {int(SAMPLE_PCT * 100)} AS in_sample
FROM {src}
WHERE (hash(EPOCH_SECONDS, BIC8_PATH, USD_AMOUNT) % 10000) < {int(SAMPLE_PCT * 100)} OR coalesce(ANOMALY_TYPE, '') <> ''
''')
df = con.execute("SELECT * FROM base").df()
df["ts"] = pd.to_datetime(df.epoch, unit="s", utc=True)
df["kb"] = df.path.str.split(";").apply(lambda p: [b for b in p if b != "..."])   # known BICs in route order
df["path_n"] = df.path.str.count(";") + 1
df["gaps"] = df.path_n - df.kb.str.len()                                          # '...' placeholders = hidden hops
df["cc1"] = df.kb.str[0].str[4:6]                                                 # country of the first (instructing) bank
df["o_bank_cc"], df["b_bank_cc"] = df.obic.str[4:6], df.bbic.str[4:6]
s = df[df.in_sample].copy()                    # the sample: all rates and distributions
a = df[df.anom != ""].copy()                   # every labelled anomaly row (complete groups)
print(f"sample rows: {len(s):,}   labelled anomaly rows: {len(a):,}   ({SEED_NOTE})")
s[["ts", "cur", "amt", "dur", "fx", "pc", "ttype", "cont", "otype", "btype", "anom"]].head()
""")

md(r"""
## 2 · Discovery: which fields depend on which?

Before writing any rule, we scan every pair of discretised fields with **Cramér's V**. V is an effect size from 0 (independent) to 1 (one field determines the other). A pair counts as *strong* at V ≥ 0.05. Every strong pair must end up explained by a rule, or by rules combined.

In the full pipeline the scan runs on a development half and is re-scored on an independent half. Here we scan the sample once.
""")
code(r"""
def top(x, k):                                   # keep the k most frequent categories, pool the rest
    keep = x.value_counts().index[:k]; return x.where(x.isin(keep), "other")
F = pd.DataFrame({
    "currency": top(s.cur, 12), "participants": s.pc.clip(upper=6), "fx_conversions": s.fx.clip(upper=4),
    "routing_type": s.ttype, "continuity": s.cont, "sender_type": s.otype, "receiver_type": s.btype,
    "sender_bank_cc": top(s.o_bank_cc, 15), "receiver_bank_cc": top(s.b_bank_cc, 15),
    "amount_decade": np.floor(np.log10(s.amt.clip(lower=1))).clip(upper=7), "utc_hour": s.ts.dt.hour,
    "weekday": s.ts.dt.dayofweek, "duration_decile": pd.qcut(s.dur.rank(method="first"), 10, labels=False),
    "hidden_hop": (s.gaps > 0), "domestic": (s.o_bank_cc == s.b_bank_cc)})
def cramers_v(x, y):
    t = pd.crosstab(x, y).values; chi2 = stats.chi2_contingency(t, correction=False)[0]
    return math.sqrt(chi2 / t.sum() / max(1, min(t.shape) - 1))
cols = list(F); M = pd.DataFrame(np.eye(len(cols)), cols, cols)
for i, c1 in enumerate(cols):
    for c2 in cols[i + 1:]:
        M.loc[c1, c2] = M.loc[c2, c1] = cramers_v(F[c1], F[c2])
fig, ax = plt.subplots(figsize=(8.5, 7)); im = ax.imshow(M.values, cmap="Blues", vmin=0, vmax=.8)
ax.set_xticks(range(len(cols)), cols, rotation=70, fontsize=8); ax.set_yticks(range(len(cols)), cols, fontsize=8)
plt.colorbar(im, label="Cramér's V"); ax.set_title("Pairwise dependence (sample)"); ax.grid(False); plt.tight_layout(); plt.show()
pairs = [(c1, c2, M.loc[c1, c2]) for i, c1 in enumerate(cols) for c2 in cols[i + 1:]]
strong = sorted([p for p in pairs if p[2] >= .05], key=lambda p: -p[2])
print(f"{len(pairs)} pairs, {len(strong)} strong (V ≥ 0.05). Strongest:")
pd.DataFrame(strong[:12], columns=["field A", "field B", "Cramér's V"]).round(3)
""")
md(r"""
**Reading:** the strongest dependencies all sit in routing and currency (participants × FX, routing type × participants, currency × bank country). These are the families the next sections explain with exact or near-exact rules.
""")

md(r"""
## 3 · Routing structure (rules R6, R7, R1, R4, R2)

| Rule | Statement | Type |
|---|---|---|
| **R6** | `PARTICIPANT_COUNT` = number of known BICs in `BIC8_PATH` | exact |
| **R7** | `CONTINUITY_QFLAG = 'N'` ⇔ the path contains a `...` placeholder | exact |
| **R1** | intermediaries K = ⌊Exp(1)⌋, so P(K = k) = (1 − 1/e)·e^(−k), a geometric chain with continuation q = 1/e | stochastic |
| **R4** | each link is hidden independently with p = 0.05: P(≥ 1 hidden ∣ pc) = 1 − 0.95^(pc − 1) | stochastic |
| **R2** | Covered vs Indirect is a per-sending-bank habit, flat across route length | stochastic |
""")
code(r"""
record("R6 share exact", (s.pc == s.kb.str.len()).mean())
record("R7 share exact", ((s.cont == "N") == (s.gaps > 0)).mean())

k = s.pc - 2; kbar = k.mean(); q = kbar / (1 + kbar)            # geometric MLE of the continuation probability
record("R1 continuation q", q); record("R1 share direct (K=0)", (k == 0).mean())
obs = k.clip(upper=6).value_counts().sort_index()
exp_ = pd.Series([(1 - math.exp(-1)) * math.exp(-i) for i in range(6)] + [math.exp(-6)], index=range(7)) * len(k)
w = math.sqrt((((obs - exp_) ** 2) / exp_).sum() / len(k)); print(f"Cohen's w vs exact 1/e geometric: {w:.4f}  (< 0.01 = negligible)")

g = s.groupby("pc").agg(n=("gaps", "size"), hidden=("gaps", lambda x: (x > 0).mean())); g = g[g.n >= 500]
g["model"] = 1 - .95 ** (g.index - 1)
p_link = np.average(1 - (1 - g.hidden) ** (1 / (g.index - 1)), weights=g.n)
record("R4 per-link hidden p", p_link)
nd = s[s.ttype != "Direct"]; record("R2 pooled covered share", (nd.ttype == "Covered").mean())

fig, ax = plt.subplots(1, 3, figsize=(15, 3.8))
ax[0].bar(obs.index + 2, obs.values, color=BLUE, label="observed"); ax[0].plot(exp_.index + 2, exp_.values, "o--", color=INK, label="(1−1/e)·e^−k")
ax[0].set_yscale("log"); ax[0].set_xlabel("participants (K + 2)"); ax[0].set_title(f"R1: geometric chain, q = {q:.4f} vs 1/e = 0.3679"); ax[0].legend()
ax[1].plot(g.index, g.hidden, "o", color=BLUE, label="observed"); ax[1].plot(g.index, g.model, "--", color=INK, label="1 − 0.95^(pc−1)")
ax[1].set_xlabel("participants"); ax[1].set_title(f"R4: each link hidden with p = {p_link:.4f}"); ax[1].legend()
cov = nd.assign(K=(nd.pc - 2).clip(upper=5)).groupby("K").ttype.apply(lambda x: (x == "Covered").mean())
ax[2].bar(cov.index, cov.values, color=BLUE); ax[2].set_ylim(0, .2); ax[2].set_xlabel("intermediaries K (5 = 5+)")
ax[2].set_title("R2: covered share is flat across route length"); plt.tight_layout(); plt.show()
""")
md(r"""
**Reading:** each extra hop is 1/e as likely as the one before. The hidden-hop share follows 1 − 0.95^(pc−1) at every length, and the covered share does not depend on route length. In the full pipeline R2 is also tested out of sample by bank: banks classed as cover-prone on one half send 61% Covered on the other half, versus 7% for other banks.

*Limitation:* which bank is chosen as correspondent is random in the generator. Real networks depend on bilateral relationships.
""")

md(r"""
## 4 · Currency & FX (rules C1, C2, C3)

We first **infer each country's home currency from the data**: the most common payment currency among payments whose first bank is in that country. That gives:

| Rule | Statement |
|---|---|
| **C1** | the payment currency is usually the instructing (first) bank's home currency |
| **C2** | `CURRENCY_CONVERSION_COUNT` = number of *adjacent* known banks on the route whose home currencies differ (a border rule) |
| **C3** | the currency is drawn from the currencies on the route; outside-route currencies are rare (mostly EUR/USD as vehicles) |

The obvious alternative to C2, "conversions = distinct currencies on the route − 1", is tested and rejected.
""")
code(r"""
home = s.groupby("cc1").cur.agg(lambda x: x.value_counts().index[0])          # inferred home currency per country
HOME = home.to_dict(); print(f"home currency inferred for {len(HOME)} countries, e.g.", {k: HOME[k] for k in list(HOME)[:8]})
def route_ccys(kb): return [HOME.get(b[4:6]) for b in kb]
rc = s.kb.apply(route_ccys)
known = rc.apply(lambda l: None not in l)                                         # every route country has an inferred currency
pred_border = rc.apply(lambda l: sum(x != y for x, y in zip(l, l[1:])))
pred_distinct = rc.apply(lambda l: len(set(l)) - 1)
N1 = s.cc1.value_counts()                                                        # sampled payments per first-bank country
thin = rc.index[s.kb.apply(lambda kb: any(N1.get(b[4:6], 0) < 30 for b in kb))]  # route touches a country seen < 30 times
ok_rows = known & ~s.index.isin(thin)
record("C1 home-currency share", (s.cur == s.cc1.map(HOME)).mean())
record("C2 FX rule exact share", (pred_border[ok_rows] == s.fx[ok_rows]).mean())
print(f"   (on all sampled rows: {(pred_border[known] == s.fx[known]).mean():.6f}; rows touching a country with < 30 sampled "
      f"payments, whose home currency the sample cannot pin down, are set aside: {len(thin):,} rows)")
record("C2 alternative (distinct ccys - 1)", (pred_distinct[known] == s.fx[known]).mean())
record("C3 currency in route", pd.Series([c in set(l) for c, l in zip(s.cur, rc)]).mean())
print(f"rows with every route country mapped: {known.mean():.4%}")
mism = s[known & (pred_border != s.fx)]
thin_cc = sorted({b[4:6] for kb in mism.kb for b in kb if N1.get(b[4:6], 0) < 30})
print(f"C2 mismatches on all sampled rows: {len(mism)}; {mism.index.isin(thin).sum()} of them touch thinly sampled countries {thin_cc} "
      f"(sampled payments: {[int(N1.get(c, 0)) for c in thin_cc]}). Full data: 2 exceptions in 10M, both receivers whose home currency is never observed.")
""")
code(r"""
t = pd.crosstab(s.fx, s.pc.clip(upper=6), normalize="columns")
fig, ax = plt.subplots(1, 2, figsize=(13, 3.8))
im = ax[0].imshow(t.values, origin="lower", cmap="Blues", aspect="auto"); ax[0].grid(False)
ax[0].set_xticks(range(t.shape[1]), t.columns); ax[0].set_yticks(range(t.shape[0]), t.index)
ax[0].set_xlabel("participants"); ax[0].set_ylabel("FX conversions"); ax[0].set_title("FX never exceeds the number of links (pc − 1)")
veh = s[s.cur != s.cc1.map(HOME)].cur.value_counts(normalize=True).head(8)
ax[1].bar(veh.index, veh.values, color=BLUE); ax[1].set_title("When not the home currency: which currency?"); plt.tight_layout(); plt.show()
""")
md(r"""
**Reading:** conversions happen only at borders between adjacent banks. The rule matches on every sampled row, while "distinct currencies − 1" matches only about 92%. When the currency is not the sender's home currency, it is mostly a route currency, or EUR/USD as a vehicle.

*Limitation:* home currencies are inferred from the data (modal currency), not given. How the vehicle currency is chosen is not fully identified.
""")

md(r"""
## 5 · Institutions (R5) and parties (P2, P4, P1b)

- **R5:** the route's first bank differs from `ORDERING_BIC8` with p ≈ 0.05, and its last bank differs from `BENEFICIARY_BIC8` with p ≈ 0.05, independently. These mismatches are a role distinction, not errors.
- **P2:** an IBAN-format account always starts with its bank's country code.
- **P4:** the ordering party lives in its bank's country, while the beneficiary's address country is drawn separately (it almost never matches).
- **P1b:** the receiver's customer type does not depend on the sender's.
""")
code(r"""
p_first = (s.kb.str[0] != s.obic).mean(); p_last = (s.kb.str[-1] != s.bbic).mean()
p_both = ((s.kb.str[0] != s.obic) & (s.kb.str[-1] != s.bbic)).mean()
record("R5 first-bank mismatch", p_first); record("R5 last-bank mismatch", p_last); record("R5 independence ratio", p_both / (p_first * p_last))
ib = s[s.o_iban]; record("P2 IBAN prefix = BIC country", (ib.oacc.str[6:8] == ib.obic.str[4:6]).mean())
oc = s[s.o_cust_cc != ""]; bc = s[s.b_cust_cc != ""]
record("P4 ordering address = bank country", (oc.o_cust_cc == oc.o_bank_cc).mean())
record("P4 beneficiary address = bank country", (bc.b_cust_cc == bc.b_bank_cc).mean())
record("P1b P(B|B) - P(B|C)", (s[s.otype == "B"].btype == "B").mean() - (s[s.otype == "C"].btype == "B").mean())
print(f"customer mix: sender business {(s.otype == 'B').mean():.1%}, receiver business {(s.btype == 'B').mean():.1%}")
""")
md(r"""
**Reading:** the two endpoint swaps are independent (joint ≈ product). Where IBANs are used, the prefix always equals the bank country. The ordering party's address always matches its bank's country, while the beneficiary's matches only about 1% of the time.

*Limitation:* about 39% of details fields carry no country token. Tokens are engineered summaries supplied with the data, not original text.
""")

md(r"""
## 6 · Time (rules T1, T3, T4b)

**T1** says the timestamp follows the *instructing bank's local office clock*: activity starts at 07:00 local time. We **estimate each country's UTC offset from the data**: the hour with the steepest rise in volume is 07:00 local. Then we compare the night share (01–05 h) on the local clock with UTC.
""")
code(r"""
s["utc_hour"] = s.ts.dt.hour
big = s.cc1.value_counts(); big = big[big >= 3000].index
prof = s[s.cc1.isin(big)].groupby(["cc1", "utc_hour"]).size().unstack(fill_value=0)
prof = prof.div(prof.sum(axis=1), axis=0)
rise = prof.values - np.roll(prof.values, 1, axis=1)                       # circular: hour h minus hour h−1
start_utc = pd.Series(rise.argmax(axis=1), index=prof.index)
OFFSET = ((7 - start_utc + 12) % 24 - 12).astype(int)                      # local = UTC + offset, in −12..+11
print("estimated UTC offsets:", OFFSET.sort_values().to_dict())
for f_ in (WORK / "data/metadata/country_offsets.csv", Path("../data/metadata/country_offsets.csv")):   # pipeline table, if already built
    if f_.exists():
        ref_off = pd.read_csv(f_, index_col=0)["offset"]; both = OFFSET.index.intersection(ref_off.index)
        print(f"agreement with the pipeline's offset table (src/metadata.py): {(OFFSET[both] == ref_off[both]).mean():.0%} of {len(both)} countries")
        break
m = s[s.cc1.isin(OFFSET.index)].copy(); m["local_hour"] = (m.utc_hour + m.cc1.map(OFFSET)) % 24
record("T1 night share, local clock", m.local_hour.between(1, 5).mean()); record("T1 night share, UTC", m.utc_hour.between(1, 5).mean())
m["local_dow"] = (m.ts + pd.to_timedelta(m.cc1.map(OFFSET), unit="h")).dt.dayofweek
wk = m.groupby("cc1").local_dow.value_counts(normalize=True).unstack()
print("weekday shape (Mon..Sun, %):", (m.local_dow.value_counts(normalize=True).sort_index() * 100).round(1).tolist(),
      f"| max country deviation {(wk - wk.mean()).abs().max().max():.1%}")
fig, ax = plt.subplots(1, 2, figsize=(13, 3.6))
ax[0].plot(m.local_hour.value_counts(normalize=True).sort_index(), "-o", color=BLUE, label="local clock")
ax[0].plot(m.utc_hour.value_counts(normalize=True).sort_index(), "-", color=GREY, label="UTC"); ax[0].legend()
ax[0].set_xlabel("hour"); ax[0].set_title("T1: on the local clock every country starts at 07:00")
daily = s.groupby(s.ts.dt.date).size() * 100 / SAMPLE_PCT
ax[1].bar(daily.index, daily.values, color=[INK if d.weekday() >= 5 else BLUE for d in daily.index])
ax[1].set_title("T4b: week-long volume plateaus (scaled to 10M)"); plt.tight_layout(); plt.show()
""")
md(r"""
**Reading:** converted to each sending country's clock, activity starts at 07:00 everywhere and the night share drops sharply. One weekday shape fits all countries (Mon–Fri ≈ 17–19%, weekend low). Weekly volume moves in steps that change on Mondays.

*Limitation:* offsets are whole hours and ignore DST (January values). What sets the weekly levels (T4) is still open, so T4 is rated **inconclusive**.
""")

md(r"""
## 7 · Processing time (D1, D3)

`TOTAL_DURATION` looks like a **sum of per-bank steps**: straight-through (STP) banks take seconds, and manual banks take about 20+ minutes. On two-bank payments the histogram has two humps. Manual steps fit a **Gamma(shape ≈ 2)** distribution (two exponential stages) better than a lognormal.
""")
code(r"""
two = s[(s.pc == 2) & (s.anom == "")]
bins = np.logspace(0, np.log10(two.dur.max() + 1), 40)
slow = two.dur[two.dur > 300]
shape, loc_, scale = stats.gamma.fit(slow, floc=0)
ks_g = stats.kstest(slow, "gamma", args=(shape, 0, scale)).statistic
ks_l = stats.kstest(np.log(slow), "norm", args=(np.log(slow).mean(), np.log(slow).std())).statistic
print(f"two-bank payments: median fast part {two.dur[two.dur <= 300].median():.0f} s, median slow part {slow.median():.0f} s, slow share {len(slow) / len(two):.1%}")
print(f"slow part: Gamma shape {shape:.2f}, scale {scale:.0f} s | KS gamma {ks_g:.3f} vs lognormal {ks_l:.3f} (illustrative — the dashboard "
      "fits only rows with exactly one slow bank, classed on an independent half: shape 2.04, KS 0.023 vs 0.066)")
fig, ax = plt.subplots(figsize=(7, 3.4)); ax.hist(two.dur, bins=bins, color=BLUE); ax.set_xscale("log")
ax.set_xlabel("duration (s, log)"); ax.set_title("D1: seconds if straight-through, ~20+ minutes if manual"); plt.tight_layout(); plt.show()
""")
md(r"""
**Reading:** two humps, at seconds and at tens of minutes. In the full pipeline, banks are classed fast or slow on one half and tested on the other: payments where both banks are slow take ≈ 1.89× as long as payments with one slow bank (sum of steps). The hour-of-day effect disappears once bank composition is held fixed (Simpson's paradox).

*Limitation:* exact step distributions are not identified. Durations describe the generator's processing model, not real bank performance.
""")

md(r"""
## 8 · Payment value (A1, A3)

**A1:** ln(amount) = 6 + 2·[sender is business] + 2·[receiver is business] + sending-country level + noise (σ ≈ 2.3). So each business party multiplies the typical amount by e² ≈ 7.4.
**A3:** the residual within a country is **Normal**, which means amounts are lognormal with no power-law tail.
""")
code(r"""
n = s[s.anom == ""]; y = np.log(n.amt); oB = (n.otype == "B").astype(float); bB = (n.btype == "B").astype(float)
X = np.column_stack([np.ones(len(n)), oB, bB, oB * bB]); beta = np.linalg.lstsq(X, y, rcond=None)[0]
for name, b in zip(["A1 intercept", "A1 sender-business effect", "A1 receiver-business effect", "A1 interaction"], beta): record(name, b)
resid = y - y.groupby([n.o_bank_cc, n.otype, n.btype]).transform("mean")          # remove party types and sending country
z = (resid - resid.mean()) / resid.std()
record("A3 residual skew", stats.skew(resid)); record("A3 residual excess kurtosis", stats.kurtosis(resid))
print(f"KS distance of the standardised residual vs Normal: {stats.kstest(z, 'norm').statistic:.4f}")
fig, ax = plt.subplots(1, 2, figsize=(13, 3.6))
for (o, b), c in zip([("C", "C"), ("B", "C"), ("C", "B"), ("B", "B")], [GREY, BLUE, YELLOW, INK]):
    ax[0].hist(np.log10(n.amt[(n.otype == o) & (n.btype == b)]), bins=60, histtype="step", lw=1.6, color=c, density=True, label=f"{o}→{b}")
ax[0].legend(); ax[0].set_xlabel("log10 USD amount"); ax[0].set_title("A1: each business party shifts the curve right")
qq = np.quantile(z, np.linspace(.001, .999, 60)); th = stats.norm.ppf(np.linspace(.001, .999, 60))
ax[1].plot(th, qq, "o", color=BLUE, ms=4); ax[1].plot(th, th, "--", color=INK); ax[1].set_title("A3: residual quantiles on the Normal line")
plt.tight_layout(); plt.show()
""")
md(r"""
**Reading:** the four sender → receiver curves are the same lognormal shifted by about +2 in ln units for each business party, with almost no interaction. The residual lies on the Normal line, so a lognormal model predicts even the largest amounts.

*Limitation:* country and bank effects are generator parameters, not national statistics. Fat-finger rows are excluded from the fit.
""")

md(r"""
## 9 · Statistical forensics (F1 and uniformity fingerprints)

How the generator was built leaves marks in the digits:
- **F1:** USD-denominated amounts are often whole (.00), while amounts originally in other currencies have uniform cents. So the generator draws a round amount in the original currency and converts it to USD.
- Timestamps (second of minute) are uniform, which points to continuous time draws.
- Leading digits are close to **Benford's law**, as wide lognormal amounts should be.
""")
code(r"""
whole = (np.round(s.amt * 100) % 100 == 0)
record("F1 USD amounts ending .00", whole[s.cur == "USD"].mean()); record("F1 other amounts ending .00", whole[s.cur != "USD"].mean())
sec = s.epoch % 60; c = np.bincount(sec, minlength=60); w_sec = math.sqrt(((c - c.mean()) ** 2 / c.mean()).sum() / c.sum())
fd = (s.amt / 10 ** np.floor(np.log10(s.amt.clip(lower=1e-9)))).astype(int).clip(1, 9)
obs_fd = fd.value_counts(normalize=True).sort_index(); ben = np.log10(1 + 1 / np.arange(1, 10))
print(f"second-of-minute Cohen's w {w_sec:.4f} — sampling noise alone gives ≈ {math.sqrt(59 / c.sum()):.4f} at this n, so: uniform")
print(f"Benford MAD {np.abs(obs_fd.values - ben).mean():.4f} (dashboard 0.0060 on 10M; Nigrini: < 0.006 close, 0.006–0.012 acceptable conformity)")
fig, ax = plt.subplots(1, 2, figsize=(13, 3.4))
cw = s.assign(w=whole).groupby("cur").w.mean().sort_values(ascending=False).head(12)
ax[0].barh(cw.index[::-1], cw.values[::-1], color=[YELLOW if x == "USD" else BLUE for x in cw.index[::-1]]); ax[0].set_title("F1: share of amounts ending .00")
ax[1].bar(np.arange(1, 10) - .2, obs_fd.values, .4, color=BLUE, label="observed"); ax[1].bar(np.arange(1, 10) + .2, ben, .4, color=YELLOW, label="Benford")
ax[1].legend(); ax[1].set_title("First digit vs Benford"); plt.tight_layout(); plt.show()
""")
md(r"""
**Negative result kept:** in the full pipeline we searched for one fixed FX rate per currency that would make converted amounts round. None does (about 2% near-integer at best, against a 1.2% baseline), so no fixed conversion table is claimed.
""")

md(r"""
## 10 · Anomalies (X1, X2, X3, X6), using every labelled row

| Label | What we find |
|---|---|
| **ROMANCE_SCAM (X1)** | bursts of 2–8 payments from a consumer to the same payee; each payment is ×1.5 the previous one (ln step +0.40) |
| **DUPLICATE_PAYMENT (X2)** | groups of 2–5 identical copies (same amount, path, duration) within 2 h, every copy labelled |
| **FAT_FINGER_MISTAKE (X3)** | the amount is ×100 or ÷100 of what the party types and country predict; about 77% are inflated |
| **X6** | labels are injected *after* routing: the label is independent of routing type |
| **CUSTOMER_RECALL (X5)** | no observable signature, a documented **negative** result (rated inconclusive) |
""")
code(r"""
print(a.anom.value_counts().to_string())
r = a[a.anom == "ROMANCE_SCAM"].sort_values("epoch"); r["series"] = r.groupby(["oacc", "bacc"]).ngroup()
steps = r.groupby("series").amt.apply(lambda x: np.diff(np.log(x.values))).explode().astype(float)
record("X1 romance series", r.series.nunique()); record("X1 median ln step", steps.median())
d = a[a.anom == "DUPLICATE_PAYMENT"]; grp = d.groupby(["amt", "path", "dur"]).epoch.agg(["size", lambda x: x.max() - x.min()])
grp.columns = ["copies", "span_s"]; record("X2 duplicate groups", len(grp))
print(f"duplicate group sizes {grp.copies.min()}–{grp.copies.max()}, max span {grp.span_s.max():,} s")
mu = np.log(n.amt).groupby([n.o_bank_cc, n.otype, n.btype]).mean()           # expected ln amount from the A1/A2 model
ff = a[a.anom == "FAT_FINGER_MISTAKE"].copy()
ff["exp_ln"] = [mu.get((c, o, b), np.nan) for c, o, b in zip(ff.o_bank_cc, ff.otype, ff.btype)]
ff["log10_ratio"] = (np.log(ff.amt) - ff.exp_ln) / np.log(10); ff = ff.dropna(subset=["log10_ratio"])
record("X3 share inflated (x100)", (ff.log10_ratio > 0).mean())
# normal rows are a SAMPLE_PCT sample but anomalies are complete: scale normal counts back to full size before computing V
ct = pd.concat([pd.crosstab(a.anom, a.ttype), (s[s.anom == ""].ttype.value_counts() * 100 / SAMPLE_PCT).rename("NORMAL").to_frame().T]).fillna(0)
chi2_ = stats.chi2_contingency(ct.values, correction=False)[0]
record("X6 Cramer's V label x routing", math.sqrt(chi2_ / ct.values.sum() / (min(ct.shape) - 1)))
fig, ax = plt.subplots(1, 2, figsize=(13, 3.6))
for i, (_, g_) in enumerate(r.groupby("series")):
    if i < 40: ax[0].plot(range(1, len(g_) + 1), np.log(g_.amt.values) - np.log(g_.amt.values[0]), color=RED, alpha=.35)
ax[0].plot([1, 8], [0, 7 * .4], "--", color=INK, label="+0.40 per payment"); ax[0].legend(); ax[0].set_title("X1: romance bursts escalate ×1.5")
ax[0].set_xlabel("position in series"); ax[0].set_ylabel("ln amount − first")
ax[1].hist(ff.log10_ratio, bins=40, color=RED); ax[1].axvline(2, color=INK, ls="--"); ax[1].axvline(-2, color=INK, ls="--")
ax[1].set_xlabel("log10(amount ÷ expected)"); ax[1].set_title("X3: fat-finger amounts sit ≈100× off"); plt.tight_layout(); plt.show()
""")
md(r"""
**Reading:** each fraud label leaves its own signature: escalating bursts, identical copies, and ×100 decimal slips. The labels are independent of routing (V ≈ 0.003), which is consistent with injection after the route was built. In the full data, CEO and account-replacement scams pay into accounts that receive nothing but flagged payments (mule accounts). Testing that needs every row, so it is not repeated here.

*Limitation:* labels are synthetic; they are not confirmed real-world fraud, and their prevalence is not real prevalence.
""")

md(r"""
## 11 · Notebook vs dashboard

Each number above is compared with the dashboard's full-data value.
- **Exact rules** must match exactly.
- **Rates** must agree within sampling error (about ±0.005 at 5%).
- **Anomaly counts** use every labelled row, so they must match exactly.
""")
code(r"""
rows = []
for k_, ref in REF.items():
    if k_ in RESULTS:
        tol = TOL.get(k_, DEFAULT_TOL); v = RESULTS[k_]
        rows.append((k_, v, ref, v - ref, tol, "match" if abs(v - ref) <= tol + 1e-12 else "CHECK"))
cmp_ = pd.DataFrame(rows, columns=["metric", "notebook (sample)", "dashboard (10M)", "difference", "tolerance", "status"])
print(f"{(cmp_.status == 'match').sum()} of {len(cmp_)} metrics agree with the dashboard within tolerance")
cmp_.style.format({"notebook (sample)": "{:.4f}", "dashboard (10M)": "{:.4f}", "difference": "{:+.4f}", "tolerance": "{:.3f}"}) \
    .apply(lambda r_: ["background:#fde2e1" if r_.status == "CHECK" else "" for _ in r_], axis=1)
""")
# =============================================================================== PART B
GROUPS = [
    ("12.1 · Configuration, confidence scale and the one-command runner",
     "Paths, DuckDB connection with the split keys (`h` = random half, `per` = before/after 15 Jun 2023), resource limits (set from section 0) and the fixed confidence scale.",
     ["src/__init__.py", "src/config.py", "src/levels.py", "run_all.py", "requirements.txt"]),
    ("12.2 · Stage 1–2: ingestion and derived country tables",
     "Raw CSV → `payments.parquet` (all text kept) → `slim.parquet` (typed and derived columns). `metadata.py` derives the home currency per country, the UTC offsets (rule T1) and the country amount effects (rule A2) from the data.",
     ["src/ingestion.py", "src/metadata.py"]),
    ("12.3 · Stage 3: discovery, network, statistics, forensics",
     "Cramér's V scan of 276 field pairs with depth-3 trees (development half → validation half), the bank network (loops, pairings, hubs), parameter CIs and tail checks, digit and timestamp fingerprints, and the H38 vehicle-currency test.",
     ["src/discovery.py", "src/graph.py", "src/stats.py", "src/forensics.py", "src/h38.py"]),
    ("12.4 · Stage 4: the 34 rule validators",
     "`rules.py` holds every validator as DuckDB SQL evaluated on 5 splits; a rule passes only if its pre-set criterion holds on all of them. `rulelib.py` is an independent pure-Python implementation used to cross-check R6, R7 and C2 row by row. `formulations.py` holds the formal statement of each rule.",
     ["src/rules.py", "src/rulelib.py", "src/formulations.py", "src/validation.py"]),
    ("12.5 · Stage 5: evidence, register, atlas, lineage",
     "Evidence tables behind every chart, the rule register (confidence level, limitations, economic reading), the dependency atlas (37 typed edges) and file lineage with hashes.",
     ["src/evidence.py", "src/cube.py", "src/register.py", "src/atlas.py", "src/lineage.py"]),
    ("12.6 · Stage 6: charts, website data, replay, evidence ledger",
     "48 charts read only from the evidence JSON, browser aggregates, row-level replay of the exact rules, and the evidence ledger (EV-RULE-001 …).",
     ["src/charts.py", "src/webdata.py", "src/replay.py", "src/ledger.py"]),
    ("12.7 · Stage 7: deliverables",
     "The 15-page dashboard (page plan in `dashboard_v2.py`), the 20-slide presentation, the research report, and the static website build.",
     ["src/dashboard_v2.py", "src/reporting.py", "src/research_report.py", "src/web.py"]),
    ("12.8 · Hand-written research inputs",
     "The hypothesis log (H1–H38, including the 29 rejected), limitations, economic interpretation and the verified source register. The pipeline reads these; they are research notes, not generated files.",
     ["findings/hypotheses.md", "findings/limitations.md", "findings/economic_interpretation.md", "docs/source_register.md"]),
    ("12.9 · Website front end (static HTML/CSS/JS)",
     "The browser app that `src/web.py` packages with the data into `web/dist/`.",
     sorted(str(f.relative_to(ROOT)).replace("\\", "/") for f in (ROOT / "web" / "app").rglob("*") if f.is_file())),
]
listed = {f for _, _, fs in GROUPS for f in fs}
missing = sorted(str(f.relative_to(ROOT)).replace("\\", "/") for f in (ROOT / "src").glob("*.py") if str(f.relative_to(ROOT)).replace("\\", "/") not in listed)
assert not missing, f"src modules not embedded in the notebook: {missing}"

md(r"""
# Part B: the complete production pipeline

Part B contains **every source file** of the ORVANTA project. Each `%%writefile` cell below writes one file into the working folder `WORK`. Section 13 then runs the whole pipeline on all 10M rows, the same way `python run_all.py` does in the repository.

| Stage | Modules | Output |
|---|---|---|
| 1–2 Ingestion | `ingestion`, `metadata` | `payments.parquet`, `slim.parquet`, country tables |
| 3 Discovery | `discovery`, `graph`, `stats`, `forensics`, `h38` | dependency scan, network, statistics, fingerprints |
| 4 Validation | `rules`, `rulelib`, `formulations`, `validation` | 34 rules × 5 splits → `validation.json` |
| 5 Evidence | `evidence`, `cube`, `register`, `atlas`, `lineage` | evidence, register, atlas, lineage |
| 6 Charts and data | `charts`, `webdata`, `replay`, `ledger` | 48 charts, web data, replay, evidence ledger |
| 7 Deliverables | `dashboard_v2`, `reporting`, `research_report`, `web` | dashboard PDF, presentation PDF, research report, website |
""")
code(r"""
for d in ["src", "findings", "docs", "web/app", "data/processed", "data/metadata", "outputs/evidence", "submission"]:
    (WORK / d).mkdir(parents=True, exist_ok=True)
for f in sorted({str(Path(x).parent) for x in FILES_TO_WRITE}):
    (WORK / f).mkdir(parents=True, exist_ok=True)
print("working folder ready:", WORK.name, "| files to write:", len(FILES_TO_WRITE))
""".replace("FILES_TO_WRITE", json.dumps(sorted(listed))))

for title, blurb, files in GROUPS:
    md(f"## {title}\n\n{blurb}")
    for rel in files:
        body = (ROOT / rel).read_text(encoding="utf-8")
        cells.append(nbf.v4.new_code_cell("%%writefile {WORK.as_posix()}/" + rel + "\n" + body.rstrip("\n") + "\n"))

md(r"""
## 13 · Run the full pipeline (all 10M rows)

The steps run in the same order as `run_all.py`, each as `python -m src.<module>` inside `WORK`, with the thread and memory limits from section 0. Each step prints its own summary line.
- **Core analysis steps** stop the notebook on failure.
- **The three rendering steps** (`reporting`, `research_report`, `web`) need a headless browser. If one fails, it is reported and the analysis still completes.

The Part A sample is cleared from memory first, so the pipeline has the full RAM.
""")
code(r"""
import gc
for _v in ("df", "s", "a", "n", "lab", "F", "M"):
    globals().pop(_v, None)
gc.collect()
try: con.close()
except Exception: pass

STEPS = [["src.ingestion", "--skip-full"], ["src.metadata"], ["src.graph"], ["src.stats"], ["src.discovery"], ["src.forensics"], ["src.h38"],
         ["src.validation"], ["src.evidence"], ["src.cube"], ["src.register"], ["src.atlas"], ["src.lineage"], ["src.charts"],
         ["src.webdata"], ["src.replay"], ["src.ledger"], ["src.reporting"], ["src.research_report"], ["src.web"]]
OPTIONAL = {"src.reporting", "src.research_report", "src.web"}
env = dict(os.environ, PYTHONIOENCODING="utf-8", MPLBACKEND="Agg", PYTHONWARNINGS="ignore",
           ORVANTA_THREADS=str(THREADS), ORVANTA_MEMORY=MEMORY, ORVANTA_TEMP=str(WORK / "duckdb_tmp"))
NOISE = ("warn", "findfont", "font family", "self._get_loop", "UserWarning")
STATUS = {}
if not RUN_FULL_PIPELINE:
    print("RUN_FULL_PIPELINE = False: the code is written to", WORK.name, "but not run.")
else:
    T0 = time.time()
    for step in STEPS:
        t0, name, tail = time.time(), step[0], []
        p = subprocess.Popen([sys.executable, "-m", *step], cwd=WORK, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace")
        print(f"▶ {name}", flush=True)
        for line in p.stdout:
            tail = (tail + [line.rstrip()])[-40:]
            if line.strip() and not any(k.lower() in line.lower() for k in NOISE):
                print("   ", line.rstrip()[:180], flush=True)
        rc = p.wait(); STATUS[name] = "ok" if rc == 0 else "FAILED"
        print(f"  {'✔' if rc == 0 else '✘'} {name} — {time.time() - t0:.0f} s", flush=True)
        if rc != 0:
            print("\n".join(tail[-25:]))
            if name not in OPTIONAL:
                raise RuntimeError(f"pipeline step {name} failed (exit {rc})")
    print(f"\npipeline finished in {(time.time() - T0) / 60:.1f} min · steps ok: {sum(v == 'ok' for v in STATUS.values())}/{len(STEPS)}")
""")

md(r"""
## 14 · Results of the full run

The validators ran on all 10M rows, so these numbers are the dashboard's numbers. The check below compares the full-run `validation.json` with the reference values this notebook was built with. Any difference would mean the pipeline did not reproduce.
""")
code(r"""
from IPython.display import Image, display
VJ = WORK / "outputs/evidence/validation.json"
if VJ.exists():
    val = json.loads(VJ.read_text(encoding="utf-8"))["rules"]
    vt = pd.DataFrame([(r["id"], r["title"], r["status"]) for r in val], columns=["rule", "statement", "status on 5 splits"])
    print(f"validators passing on all 5 splits: {(vt['status on 5 splits'] == 'PASS').sum()} / {len(vt)}")
    display(vt)
    KEY = {"R6 share exact": ("R6", "share_exact"), "R1 continuation q": ("R1", "q_mle"), "C2 FX rule exact share": ("C2", "share_exact"),
           "C1 home-currency share": ("C1", "home_share"), "A1 sender-business effect": ("A1", "effect_ordering_B"),
           "F1 USD amounts ending .00": ("F1", "usd_whole_share"), "X2 duplicate groups": ("X2", "groups")}
    V_ = {r["id"]: r for r in val}
    rep = pd.DataFrame([(k, V_[r]["metrics"]["full"][m], REF[k]) for k, (r, m) in KEY.items()], columns=["metric", "this run (10M)", "dashboard"])
    rep["identical"] = (rep["this run (10M)"] - rep["dashboard"]).abs() < 1e-9
    display(rep)
    outs = [f for f in [WORK / "submission/dashboard.pdf", WORK / "submission/presentation.pdf",
                        WORK / "submission/ORVANTA_Comprehensive_Research_Report.pdf"] if f.exists()]
    print("deliverables:", ", ".join(f"{f.name} ({f.stat().st_size / 1e6:.1f} MB)" for f in outs) or "none rendered")
    print("charts:", len(list((WORK / "outputs/charts").glob("*.png"))), "| website files:", sum(1 for _ in (WORK / "web/dist").rglob("*")) if (WORK / "web/dist").exists() else 0)
    for c in ("atlas", "hops", "f1_cents"):
        if (WORK / f"outputs/charts/{c}.png").exists():
            display(Image(filename=str(WORK / f"outputs/charts/{c}.png"), width=760))
    if IN_COLAB and outs:
        print("To download a PDF: from google.colab import files; files.download(str(WORK / 'submission/dashboard.pdf'))")
else:
    print("Run section 13 first (RUN_FULL_PIPELINE = True).")
""")

md(r"""
## Open questions (from the full research)

- **T4:** what sets the weekly levels.
- **G1:** why bank pairs have directional affinities.
- **X5:** CUSTOMER_RECALL leaves no trace (a documented negative result).
- **C3/H38:** why EUR and USD are the vehicle currencies.

The rules are reconstructions consistent with the data, not recovered source code. The data is synthetic and describes this generator, not real Swift traffic.
""")

nb = nbf.v4.new_notebook(); nb.cells = cells
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
               "language_info": {"name": "python"}, "colab": {"name": "ORVANTA_prototype_analysis.ipynb", "provenance": []}}
OUT.parent.mkdir(exist_ok=True)
if "--execute" in sys.argv:
    from nbconvert.preprocessors import ExecutePreprocessor
    ExecutePreprocessor(timeout=None, kernel_name=os.environ.get("NB_KERNEL", "python3")).preprocess(nb, {"metadata": {"path": os.environ.get("NB_RUN_DIR", str(OUT.parent))}})
nbf.write(nb, OUT)
print("wrote", OUT, "| cells:", len(cells), "| executed:", "--execute" in sys.argv)
