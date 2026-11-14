"""Layer 3/5 · Statistical & actuarial depth: confidence intervals, tails, step-time fits, sensitivity, detector evaluation.

Run: python -m src.stats -> outputs/evidence/stats.json
Principles: effect sizes and intervals over p-values; distribution claims checked against tails; every detector evaluated with
per-class precision / recall / F1 and a confusion table (no accuracy); sensitivity of every analyst-chosen threshold reported.
"""
from __future__ import annotations
import json, math
import numpy as np
import pandas as pd
from scipy import stats
from .config import connect, EVIDENCE

con = connect()
S = {}
df = lambda s: con.execute(s).df()
one = lambda s: con.execute(s).fetchone()
rec = lambda d: json.loads(d.to_json(orient="records"))
N = 10_000_000


def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return dict(k=int(k), n=int(n), p=p, lo=c - h, hi=c + h)


def poisson_ci(k, z=.05):
    return (stats.chi2.ppf(z / 2, 2 * k) / 2 if k else 0.0, stats.chi2.ppf(1 - z / 2, 2 * k + 2) / 2)


# ---------------------------------------------------------------- 1. confidence intervals for headline parameters
r = one("""SELECT sum((ttype='Direct')::INT), sum((ttype='Covered')::INT), sum((ttype<>'Direct')::INT),
  sum((list_filter(string_split(path,';'),x->x<>'...')[1]<>obic)::INT), sum((list_filter(string_split(path,';'),x->x<>'...')[-1]<>bbic)::INT),
  sum((cont='N')::INT), sum(pc-1), sum((otype='B')::INT), sum((btype='B')::INT) FROM t""")
S["ci"] = {"P(Direct) [1-1/e = 0.6321]": wilson(r[0], N), "P(Covered | non-direct)": wilson(r[1], r[2]), "P(path[1] ≠ ORDERING_BIC8)": wilson(r[3], N),
           "P(path[-1] ≠ BENEFICIARY_BIC8)": wilson(r[4], N), "P(ordering = B)": wilson(r[7], N), "P(beneficiary = B)": wilson(r[8], N)}
hs = one("SELECT sum((cur=hcur)::INT), count(*) FROM t JOIN ccy ON ccy.cc=substr(list_filter(string_split(path,';'),x->x<>'...')[1],5,2)")
S["ci"]["P(currency = home of instructing bank)"] = wilson(hs[0], hs[1])
an = df("SELECT anom, count(*) n FROM t WHERE anom IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
S["anomaly_rates"] = [dict(anom=a, n=int(n), per_10k=n / N * 1e4, lo=poisson_ci(n)[0] / N * 1e4, hi=poisson_ci(n)[1] / N * 1e4) for a, n in an.values]
# geometric q: SE from Fisher information of geometric(1-q): Var(q_hat) = q(1-q)^2 / n  (parametrisation P(K=k)=(1-q)q^k)
kbar = one("SELECT avg(pc-2) FROM t")[0]; q = kbar / (1 + kbar); se = math.sqrt(q * (1 - q) ** 2 / N)
S["ci"]["geometric continuation q [1/e = 0.3679]"] = dict(p=q, lo=q - 1.96 * se, hi=q + 1.96 * se, n=N)

# ---------------------------------------------------------------- 2. amounts: shape and tails (actuarial)
res = df("""SELECT ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT) - avg(ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)) OVER (PARTITION BY o_bank_cc) r
            FROM t WHERE anom IS NULL USING SAMPLE 400000 (reservoir, 11)""").r.values
sd = res.std()
qs = [.001, .01, .05, .25, .5, .75, .95, .99, .999]
S["amount_residual"] = dict(sd=float(sd), skew=float(stats.skew(res)), excess_kurtosis=float(stats.kurtosis(res)),
                            ks_D_vs_normal=float(stats.kstest(res / sd, "norm").statistic),
                            qq=[dict(q=x, empirical=float(np.quantile(res, x) / sd), normal=float(stats.norm.ppf(x))) for x in qs])
# tail: Hill estimator at several k — a power law gives a flat alpha(k); a lognormal gives alpha rising with k.
top = df("SELECT amt FROM t WHERE anom IS NULL ORDER BY amt DESC LIMIT 100001").amt.values
S["hill"] = [dict(k=k, alpha=float(1 / np.mean(np.log(top[:k] / top[k])))) for k in (100, 300, 1000, 3000, 10000, 30000, 100000)]
# model-implied exceedance vs observed (segment-and-country lognormal model with the fitted residual sd)
m = df("""WITH c AS (SELECT o_bank_cc, avg(ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)) ce FROM t WHERE anom IS NULL GROUP BY 1)
          SELECT 6+2*(otype='B')::INT+2*(btype='B')::INT + ce mu, count(*) n FROM t JOIN c USING(o_bank_cc) WHERE anom IS NULL GROUP BY 1""")
exc = []
for thr in (1e5, 1e6, 1e7, 1e8, 1e9):
    pred = float((m.n * stats.norm.sf((math.log(thr) - m.mu) / sd)).sum()); obs = one(f"SELECT count(*) FROM t WHERE anom IS NULL AND amt > {thr}")[0]
    exc.append(dict(threshold=thr, observed=int(obs), predicted=pred, ratio=obs / pred if pred else None))
S["exceedance"] = exc
S["top_amounts"] = rec(df("SELECT coalesce(anom,'NORMAL') a, count(*) n FROM (SELECT anom FROM t ORDER BY amt DESC LIMIT 1000) GROUP BY 1 ORDER BY 2 DESC"))

# ---------------------------------------------------------------- 3. duration step distributions
fast = df("""WITH ob AS (SELECT obic b, avg((dur>120)::INT) s FROM t WHERE pc=2 GROUP BY 1 HAVING count(*)>=30),
  bb AS (SELECT bbic b, avg((dur>120)::INT) s FROM t WHERE pc=2 GROUP BY 1 HAVING count(*)>=30)
  SELECT dur, CASE WHEN ob.s>.95 AND bb.s>.95 THEN 'ss' WHEN ob.s>.95 OR bb.s>.95 THEN 'one' ELSE 'ff' END cls FROM t JOIN ob ON ob.b=obic JOIN bb ON bb.b=bbic WHERE pc=2 USING SAMPLE 600000 (reservoir, 5)""")
ff = fast[(fast.cls == "ff") & (fast.dur <= 120)].dur.values.astype(float)
a, loc, sc = stats.gamma.fit(ff, floc=0)
S["fast_step"] = dict(n=int(len(ff)), mean=float(ff.mean()), median=float(np.median(ff)), gamma_shape=float(a), gamma_scale=float(sc),
                      ks_D=float(stats.kstest(ff, "gamma", args=(a, 0, sc)).statistic), note="sum of two fast steps (pc=2, both banks STP)")
sl = fast[(fast.cls == "one") & (fast.dur > 120)].dur.values.astype(float)
ln_mu, ln_sd = np.log(sl).mean(), np.log(sl).std()
ga, _, gs = stats.gamma.fit(sl, floc=0)
S["manual_step"] = dict(n=int(len(sl)), median=float(np.median(sl)), p95=float(np.quantile(sl, .95)), max=float(sl.max()),
                        lognormal_mu=float(ln_mu), lognormal_sd=float(ln_sd), ks_lognormal=float(stats.kstest(np.log(sl), "norm", args=(ln_mu, ln_sd)).statistic),
                        gamma_shape=float(ga), gamma_scale=float(gs), ks_gamma=float(stats.kstest(sl, "gamma", args=(ga, 0, gs)).statistic))
per_hop = df("SELECT pc, quantile_cont(dur, .1) q10, quantile_cont(dur,.25) q25 FROM t WHERE pc<=9 GROUP BY 1 ORDER BY 1")
S["fast_per_participant_slope_q10"] = float(np.polyfit(per_hop.pc, per_hop.q10, 1)[0])

# ---------------------------------------------------------------- 4. sensitivity of analyst-chosen thresholds
sens = []
for slow_thr in (60, 120, 240):
    for cls_thr in (.9, .95, .99):
        d = df(f"""WITH tr AS (SELECT * FROM tt WHERE h=0 AND pc=2), te AS (SELECT * FROM tt WHERE h=1 AND pc=2),
          ob AS (SELECT obic b, avg((dur>{slow_thr})::INT) s FROM tr GROUP BY 1 HAVING count(*)>=30), bb AS (SELECT bbic b, avg((dur>{slow_thr})::INT) s FROM tr GROUP BY 1 HAVING count(*)>=30)
          SELECT (ob.s>{cls_thr})::INT + (bb.s>{cls_thr})::INT nslow, median(dur) med, count(*) n FROM te JOIN ob ON ob.b=te.obic JOIN bb ON bb.b=te.bbic GROUP BY 1 ORDER BY 1""")
        mm = dict(zip(d.nslow, d.med))
        sens.append(dict(slow_threshold_s=slow_thr, class_threshold=cls_thr, med_0=mm.get(0), med_1=mm.get(1), med_2=mm.get(2),
                         additivity=(mm.get(2) / mm.get(1)) if mm.get(1) else None))
S["sensitivity_D1"] = sens
# R1 stratified: q by sending country (top 20) and by party segment -> robustness of the 'global draw' claim
S["R1_by_country"] = rec(df("""SELECT o_bank_cc cc, count(*) n, avg(pc-2)/(1+avg(pc-2)) q FROM t GROUP BY 1 ORDER BY n DESC LIMIT 20"""))
S["R1_by_segment"] = rec(df("""SELECT otype||btype seg, coalesce(anom,'NORMAL')='NORMAL' normal, count(*) n, avg(pc-2)/(1+avg(pc-2)) q FROM t GROUP BY 1,2 ORDER BY 1,2"""))
S["R4_by_ttype"] = rec(df("SELECT ttype, pc, avg((cont='N')::INT) p, count(*) n FROM t WHERE pc BETWEEN 3 AND 5 GROUP BY 1,2 ORDER BY 1,2"))

# ---------------------------------------------------------------- 5. rule-based detectors: per-class evaluation (no ML)
def evaluate(name, flag_sql, label):
    tp, fp, fn = one(f"""WITH f AS ({flag_sql}) SELECT count(*) FILTER (WHERE flag AND anom='{label}'), count(*) FILTER (WHERE flag AND coalesce(anom,'')<>'{label}'),
                       count(*) FILTER (WHERE NOT flag AND anom='{label}') FROM f""")
    p = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
    return dict(detector=name, label=label, tp=int(tp), fp=int(fp), fn=int(fn), tn=int(N - tp - fp - fn), precision=p, recall=rc, f1=2 * p * rc / (p + rc) if p + rc else 0.0)


det = []
det.append(evaluate("exact key (sender, beneficiary, amount, path, duration) repeated within 2 h",
                    """SELECT anom, (count(*) OVER (PARTITION BY oacc,bacc,amt,path,dur) > 1 AND max(epoch) OVER (PARTITION BY oacc,bacc,amt,path,dur)
                         - min(epoch) OVER (PARTITION BY oacc,bacc,amt,path,dur) <= 7200) flag FROM t""", "DUPLICATE_PAYMENT"))
det.append(evaluate("consumer burst: ≥3 payments to same payee within 70 min, rising amounts",
                    """WITH s AS (SELECT oacc,bacc FROM t WHERE otype='C' GROUP BY 1,2 HAVING count(*)>=3 AND max(epoch)-min(epoch)<=4200 AND corr(epoch, ln(amt))>0.5)
                       SELECT anom, (oacc,bacc) IN (SELECT (oacc,bacc) FROM s) flag FROM t""", "ROMANCE_SCAM"))
# fat finger: amount alone vs expectation — precision/recall over thresholds (PR curve, AUC by trapezoid)
fr = df("""WITH c AS (SELECT o_bank_cc, avg(ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)) ce FROM t WHERE anom IS NULL GROUP BY 1)
  SELECT round(abs((ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)-ce)/ln(10)),1) z, count(*) FILTER (WHERE anom='FAT_FINGER_MISTAKE') pos, count(*) neg
  FROM t JOIN c USING(o_bank_cc) GROUP BY 1 ORDER BY 1 DESC""")
fr["neg"] = fr.neg - fr.pos; fr["tp"] = fr.pos.cumsum(); fr["fp"] = fr.neg.cumsum(); P_ = fr.pos.sum()
fr["precision"] = fr.tp / (fr.tp + fr.fp); fr["recall"] = fr.tp / P_
S["fat_finger_pr_curve"] = rec(fr[fr.z.between(0.5, 5)][["z", "precision", "recall", "tp", "fp"]])
rr = np.r_[0, fr.recall.values]; pp = np.r_[fr.precision.values[0], fr.precision.values]
S["fat_finger_pr_auc"] = float(np.trapezoid(pp, rr)); S["fat_finger_base_rate"] = float(P_ / N)
best = fr.assign(f1=2 * fr.precision * fr.recall / (fr.precision + fr.recall)).sort_values("f1", ascending=False).iloc[0]
det.append(dict(detector=f"|log10(amount/expected)| ≥ {best.z:.1f} (amount-only, best F1)", label="FAT_FINGER_MISTAKE", tp=int(best.tp), fp=int(best.fp),
                fn=int(P_ - best.tp), tn=int(N - best.tp - best.fp - (P_ - best.tp)), precision=float(best.precision), recall=float(best.recall), f1=float(best.f1)))
det.append(evaluate("business sender → beneficiary account with no prior payment, cross-border, amount above segment norm",
                    """WITH c AS (SELECT o_bank_cc, avg(ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)) ce FROM t WHERE anom IS NULL GROUP BY 1)
                       SELECT anom, (otype='B' AND o_bank_cc<>b_bank_cc AND ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)-ce > 1
                              AND row_number() OVER (PARTITION BY bacc ORDER BY epoch)=1) flag FROM t JOIN c USING(o_bank_cc)""", "CEO_SCAM"))
S["detectors"] = det

(EVIDENCE / "stats.json").write_text(json.dumps(S, default=float, indent=1))
print(json.dumps({k: S[k] for k in ["ci", "amount_residual", "hill", "exceedance", "fast_step", "manual_step", "detectors", "fat_finger_pr_auc"]}, default=float, indent=1)[:6000])
