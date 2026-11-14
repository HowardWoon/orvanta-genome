"""DISCOVER/VALIDATE · Statistical forensics: synthetic fingerprints, change points, conditional-independence tests.

Run: python -m src.forensics -> outputs/evidence/forensics.json
Fingerprints test HOW values were drawn (continuous random draws vs templates vs hard-coded grids), which is direct evidence
about the generator (the case names NumPy + Faker). Effect sizes (Cohen's w, Nigrini MAD) are reported, not just p-values.
"""
from __future__ import annotations
import json, math
import numpy as np
import pandas as pd
from scipy import stats
from .config import connect, EVIDENCE

con = connect()
df = lambda s: con.execute(s).df()
rec = lambda d: json.loads(d.to_json(orient="records"))
F = {}


def gof(obs, exp_p, label):
    obs = np.asarray(obs, float); n = obs.sum(); e = n * np.asarray(exp_p, float)
    chi2 = float(((obs - e) ** 2 / e).sum()); w = math.sqrt(chi2 / n)
    return dict(test=label, n=int(n), chi2=chi2, dof=len(obs) - 1, p=float(stats.chi2.sf(chi2, len(obs) - 1)), cohen_w=w)


# 1. Benford first digit (normal rows) — lognormal with σ≈2.1 is expected to be close to Benford
bd = df("SELECT CAST(substr(regexp_replace(CAST(amt AS VARCHAR),'[^1-9]','','g'),1,1) AS INT) d, count(*) n FROM t WHERE anom IS NULL GROUP BY 1 ORDER BY 1")
bd = bd[bd.d.between(1, 9)]
ben = np.log10(1 + 1 / np.arange(1, 10)); obs_p = bd.n.values / bd.n.sum()
mad = float(np.abs(obs_p - ben).mean())
F["benford"] = dict(**gof(bd.n.values, ben, "first digit vs Benford"), nigrini_mad=mad,
                    conformity="close" if mad < .006 else "acceptable" if mad < .012 else "marginal" if mad < .015 else "nonconformity",
                    digits=[dict(d=int(a), observed=float(b), benford=float(c)) for a, b, c in zip(bd.d, obs_p, ben)])

# 2. Cents and round numbers (2-decimal rounding of a continuous draw ⇒ uniform cents)
cd = df("SELECT CAST(round(amt*100) AS BIGINT) % 100 c, count(*) n FROM t WHERE anom IS NULL GROUP BY 1 ORDER BY 1")
F["cents_uniform"] = gof(cd.n.values, np.full(len(cd), 1 / len(cd)), "cents (00–99) uniform")
F["cents_00_share"] = float(cd[cd.c == 0].n.sum() / cd.n.sum())
F["cents_by_segment"] = rec(df("""SELECT otype||btype seg, avg((CAST(round(amt*100) AS BIGINT) % 100 = 0)::INT) cents00, avg((amt % 100 = 0)::INT) mult100,
                                  avg((amt % 1000 = 0)::INT) mult1000, count(*) n FROM t WHERE anom IS NULL GROUP BY 1 ORDER BY 1"""))
F["cents00_by_decade"] = rec(df("""SELECT floor(log10(amt))::INT AS amt_decade, avg((CAST(round(amt*100) AS BIGINT) % 100 = 0)::INT) cents00, count(*) n
                                   FROM t WHERE anom IS NULL AND amt >= 1 GROUP BY 1 HAVING count(*)>=1000 ORDER BY 1"""))
F["cents00_by_currency"] = rec(df("""SELECT cur, avg((CAST(round(amt*100) AS BIGINT) % 100 = 0)::INT) cents00, count(*) n FROM t WHERE anom IS NULL
                                     GROUP BY 1 ORDER BY n DESC LIMIT 12"""))

# 3. Timestamp grain: second-of-minute and minute-of-hour uniform ⇒ continuous time draw (no batch grid)
sec = df("SELECT epoch % 60 AS sec, count(*) n FROM t GROUP BY 1 ORDER BY 1"); mi = df("SELECT (epoch // 60) % 60 AS mnt, count(*) n FROM t GROUP BY 1 ORDER BY 1")
F["second_uniform"] = gof(sec.n.values, np.full(60, 1 / 60), "second of minute uniform")
F["minute_uniform"] = gof(mi.n.values, np.full(60, 1 / 60), "minute of hour uniform")
dd = df("SELECT dur % 10 AS last_digit, count(*) n FROM t GROUP BY 1 ORDER BY 1")
F["duration_last_digit"] = gof(dd.n.values, np.full(10, .1), "duration last digit uniform")

# 4. Identifier grammar
F["bic"] = rec(df("""WITH b AS (SELECT DISTINCT obic b FROM t UNION SELECT DISTINCT bbic FROM t)
  SELECT count(*) banks, count(DISTINCT substr(b,5,2)) countries, max(CAST(substr(b,1,4) AS INT)) max_bank_number,
         (SELECT count(*) FROM (SELECT substr(b,5,2) cc, count(DISTINCT substr(b,7,2)) k FROM b GROUP BY 1) WHERE k>1) countries_with_multiple_location_codes,
         avg(regexp_full_match(b, '[0-9]{4}[A-Z]{2}[0-9A-Z]{2}')::INT) grammar_match FROM b"""))[0]
F["bic_numbering"] = rec(df("""WITH b AS (SELECT DISTINCT obic b FROM t UNION SELECT DISTINCT bbic FROM t), c AS (SELECT substr(b,5,2) cc, count(*) banks,
  max(CAST(substr(b,1,4) AS INT)) mx FROM b GROUP BY 1) SELECT cc, banks, mx, banks/(mx+1.0) density FROM c ORDER BY banks DESC LIMIT 12"""))
F["iban_length_by_country"] = rec(df("""SELECT substr(oacc,7,2) cc, count(DISTINCT length(oacc)-6) lengths, min(length(oacc)-6) len, count(*) n
  FROM t WHERE o_iban GROUP BY 1 ORDER BY n DESC LIMIT 15"""))
F["iban_single_length_share"] = float(con.execute("""SELECT avg((k=1)::INT) FROM (SELECT substr(oacc,7,2) cc, count(DISTINCT length(oacc)) k FROM t WHERE o_iban GROUP BY 1)""").fetchone()[0])
tpl = df("""SELECT regexp_replace(regexp_replace(replace(oacc,'_FAKE_',''),'[0-9]','9','g'),'[A-Z]','A','g') tpl, count(*) n FROM t WHERE NOT o_iban
            GROUP BY 1 ORDER BY 2 DESC""")
F["local_account_templates"] = dict(distinct=int(len(tpl)), top=rec(tpl.head(12)), top10_share=float(tpl.n.head(10).sum() / tpl.n.sum()),
                                    lengths=rec(df("""SELECT length(replace(oacc,'_FAKE_','')) len, count(*) n FROM t WHERE NOT o_iban GROUP BY 1 ORDER BY 1""")))

# 5. Change-point detection on weekday-normalised daily volume (binary segmentation, BIC penalty, log scale)
d = df("SELECT d, dayofweek(d) dow, count(*) n FROM t WHERE d BETWEEN DATE '2023-05-01' AND DATE '2023-07-30' GROUP BY 1,2 ORDER BY 1")
d["y"] = np.log(d.n); d["y"] -= d.groupby("dow").y.transform("mean") - d.y.mean()       # remove weekday shape
y = d.y.values; n = len(y)


def cost(a, b):
    s = y[a:b]; return float(((s - s.mean()) ** 2).sum())


cps, segs = [], [(0, n)]
sig2 = None
while True:
    best = None
    for (a, b) in segs:
        for k in range(a + 3, b - 2):
            gain = cost(a, b) - cost(a, k) - cost(k, b)
            if best is None or gain > best[0]:
                best = (gain, a, b, k)
    if best is None:
        break
    rss = sum(cost(a, b) for a, b in segs); sig2 = rss / n
    if best[0] < 2 * math.log(n) * sig2 + 1e-12:   # BIC-type penalty per extra change point
        break
    _, a, b, k = best; cps.append(k); segs.remove((a, b)); segs += [(a, k), (k, b)]
cps.sort()
dates = d.d.dt.strftime("%Y-%m-%d").tolist()
bounds = [0] + cps + [n]
seg_rows = [dict(start=dates[a], end=dates[b - 1], days=b - a, level=float(np.exp(y[a:b].mean())), start_weekday=pd.Timestamp(dates[a]).day_name()) for a, b in zip(bounds, bounds[1:])]
resid = np.concatenate([y[a:b] - y[a:b].mean() for a, b in zip(bounds, bounds[1:])])
F["change_points"] = dict(n_days=n, change_points=[dates[k] for k in cps], weekdays=[pd.Timestamp(dates[k]).day_name() for k in cps],
                          segments=seg_rows, residual_sd_log=float(resid.std()), shapiro_p=float(stats.shapiro(resid).pvalue),
                          share_on_monday=float(np.mean([pd.Timestamp(dates[k]).day_of_week == 0 for k in cps])) if cps else None,
                          daily=[dict(d=a, y=float(b)) for a, b in zip(dates, y)])

# 6. Conditional-independence tests feeding the Dependency Atlas (tested non-edges and edges)
smp = df("""SELECT otype, btype, ttype, least(pc,6) pc, (dur>120) slow, hr // 6 qday, floor(log10(amt))::INT AS "dec", coalesce(anom,'N') AS an, (o_bank_cc=b_bank_cc) AS dom
            FROM t USING SAMPLE 2000000 ROWS (reservoir, 77)""")


def cv(a, b):
    tab = pd.crosstab(a, b).values.astype(float); n_ = tab.sum(); e = np.outer(tab.sum(1), tab.sum(0)) / n_
    return float(math.sqrt(((tab - e) ** 2 / e).sum() / (n_ * (min(tab.shape) - 1))))


def ci(x, y_, z=None):
    if z is None:
        return cv(smp[x], smp[y_])
    acc = tot = 0
    for _, g in smp.groupby(z):
        if len(g) > 500 and g[x].nunique() > 1 and g[y_].nunique() > 1:
            acc += len(g) * cv(g[x], g[y_]); tot += len(g)
    return acc / tot


tests = [("amount decade", "routing type", "dec", "ttype", ["otype", "btype"]), ("amount decade", "UTC quarter-day", "dec", "qday", ["otype", "btype"]),
         ("amount decade", "manual step", "dec", "slow", ["otype", "btype"]), ("routing type", "sender type", "ttype", "otype", None),
         ("routing type", "receiver type", "ttype", "btype", None), ("receiver type", "sender type", "btype", "otype", None),
         ("anomaly label", "routing type", "an", "ttype", None), ("manual step", "UTC quarter-day", "slow", "qday", ["pc"]),
         ("participants", "domestic", "pc", "dom", None), ("manual step", "participants", "slow", "pc", None)]
F["ci_tests"] = [dict(x=a, y=b, given=" × ".join(z) if z else "—", cramers_v=ci(xc, yc, z), verdict="independent (V<0.01)" if ci(xc, yc, z) < .01 else "dependent")
                 for a, b, xc, yc, z in tests]

(EVIDENCE / "forensics.json").write_text(json.dumps(F, indent=1, default=float), encoding="utf-8")
print(json.dumps({k: F[k] for k in ["cents_uniform", "cents_00_share", "second_uniform", "minute_uniform", "duration_last_digit", "bic", "iban_single_length_share"]}, indent=1, default=float))
print("benford", {k: F["benford"][k] for k in ("cohen_w", "nigrini_mad", "conformity")})
print("cps", F["change_points"]["change_points"], F["change_points"]["weekdays"], "resid sd", round(F["change_points"]["residual_sd_log"], 4))
print("templates", F["local_account_templates"]["distinct"], F["local_account_templates"]["top10_share"])
for t_ in F["ci_tests"]: print(t_)

# 7. USD-roundness fingerprint and fixed-rate search (negative result kept)
F["usd_roundness"] = rec(df("""SELECT (cur='USD') usd_denominated, avg((CAST(round(amt*100) AS BIGINT) % 100 = 0)::INT) whole_units,
   avg((CAST(round(amt*100) AS BIGINT) % 10 = 0)::INT) cents_end_0, avg((amt % 100 = 0)::INT) mult100, count(*) n FROM t WHERE anom IS NULL GROUP BY 1"""))
rate_search = []
for cur_, lo, hi in [("EUR", .7, 1.6), ("GBP", .9, 1.8), ("CHF", .7, 1.6)]:
    a = df(f"SELECT amt FROM t WHERE anom IS NULL AND cur='{cur_}' AND amt BETWEEN 2000 AND 200000 USING SAMPLE 150000 ROWS (reservoir, 1)").amt.values
    grid = np.geomspace(lo, hi, 40000); share = np.array([np.mean(np.abs(a / r - np.round(a / r)) < .006) for r in grid])
    rate_search.append(dict(currency=cur_, best_rate=float(grid[share.argmax()]), best_near_integer_share=float(share.max()), median_share=float(np.median(share))))
F["fixed_rate_search"] = rate_search
(EVIDENCE / "forensics.json").write_text(json.dumps(F, indent=1, default=float), encoding="utf-8")
print("usd", F["usd_roundness"]); print("rate search", rate_search)
