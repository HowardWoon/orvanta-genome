"""DISCOVER · Automated rule discovery engine.

Run: python -m src.discovery  -> outputs/evidence/discovery.json
1. Pairwise dependency scan: every pair of discretised features scored by Cramér's V and symmetric uncertainty
   (normalised mutual information) on the DEV half; re-scored on the independent VALIDATION half.
   Each strong pair is mapped to the reconstructed rule that explains it; strong pairs with no rule = new candidates.
2. Candidate rules from shallow decision trees (depth 3) per target field: each leaf becomes
   "IF conditions THEN target" with dev purity/coverage, re-scored on the validation half (holdout purity, lift).
Trees are a search device, not a predictive model: only holdout-confirmed leaves count, and they are compared with the
hand-reconstructed rules.
"""
from __future__ import annotations
import itertools, json, math
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from .config import connect, EVIDENCE

con = connect()
SAMPLE = 2_000_000

df = con.execute(f"""
WITH topo AS (SELECT o_bank_cc c FROM t GROUP BY 1 ORDER BY count(*) DESC LIMIT 15),
     topb AS (SELECT b_bank_cc c FROM t GROUP BY 1 ORDER BY count(*) DESC LIMIT 15),
     topc AS (SELECT cur c FROM t GROUP BY 1 ORDER BY count(*) DESC LIMIT 12),
     x AS (SELECT *, list_filter(string_split(path,';'),x->x<>'...') k FROM tt USING SAMPLE {SAMPLE} ROWS (reservoir, 2026))
SELECT h,
  CASE WHEN cur IN (SELECT c FROM topc) THEN cur ELSE 'Other' END currency,
  ttype AS routing_type, cont AS continuity, otype AS sender_type, btype AS receiver_type,
  CASE WHEN anom IS NULL THEN 'NORMAL' ELSE anom END anomaly,
  CASE WHEN o_bank_cc IN (SELECT c FROM topo) THEN o_bank_cc ELSE 'Other' END sender_bank_country,
  CASE WHEN b_bank_cc IN (SELECT c FROM topb) THEN b_bank_cc ELSE 'Other' END receiver_bank_country,
  least(pc, 6)::VARCHAR participants, least(fx, 4)::VARCHAR fx_conversions,
  (dur > 120)::VARCHAR manual_step, greatest(least(floor(log10(amt))::INT, 7), 0)::VARCHAR amount_decade,
  (hr // 6)::VARCHAR utc_quarter_day, (dow IN (0,6))::VARCHAR weekend_utc,
  o_iban::VARCHAR sender_iban, b_iban::VARCHAR receiver_iban, o_struct::VARCHAR sender_structured, b_struct::VARCHAR receiver_structured,
  (o_cust_cc<>'')::VARCHAR sender_country_token, (b_cust_cc<>'')::VARCHAR receiver_country_token,
  (o_bank_cc=b_bank_cc)::VARCHAR domestic,
  (k[1]<>obic)::VARCHAR first_hop_swapped, (k[-1]<>bbic)::VARCHAR last_hop_swapped,
  (cur = c1.hcur)::VARCHAR home_currency, ln(amt) ln_amount
FROM x LEFT JOIN ccy c1 ON c1.cc = substr(k[1],5,2)""").df()
FEATS = [c for c in df.columns if c not in ("h", "ln_amount")]
dev, val = df[df.h == 0], df[df.h == 1]


def cramers_v(a, b):
    tab = pd.crosstab(a, b).values.astype(float)
    if min(tab.shape) < 2:
        return 0.0
    n = tab.sum(); e = np.outer(tab.sum(1), tab.sum(0)) / n
    chi2 = ((tab - e) ** 2 / e).sum()
    return float(math.sqrt(chi2 / (n * (min(tab.shape) - 1))))


def sym_uncertainty(a, b):
    tab = pd.crosstab(a, b).values.astype(float); p = tab / tab.sum()
    px, py = p.sum(1), p.sum(0)
    H = lambda v: float(-(v[v > 0] * np.log(v[v > 0])).sum())
    mi = H(px) + H(py) - H(p.ravel())
    return float(2 * mi / (H(px) + H(py))) if H(px) + H(py) > 0 else 0.0


# rule that explains a dependency (unordered pair -> rule ids). 'construction' = derived field (definitional).
EXPLAINS = {
    frozenset({"participants", "routing_type"}): "R1/R2 (Direct ⇔ pc=2)", frozenset({"participants", "fx_conversions"}): "C2 (FX ≤ pc−1, borders)",
    frozenset({"participants", "continuity"}): "R4 (gap per link)", frozenset({"routing_type", "fx_conversions"}): "C2 via R1",
    frozenset({"routing_type", "continuity"}): "R4 via R1", frozenset({"fx_conversions", "continuity"}): "R4 & C2 via pc",
    frozenset({"fx_conversions", "domestic"}): "C2 (no border when same currency)", frozenset({"fx_conversions", "home_currency"}): "C2 + C1",
    frozenset({"sender_type", "amount_decade"}): "A1", frozenset({"receiver_type", "amount_decade"}): "A1", frozenset({"sender_bank_country", "amount_decade"}): "A2",
    frozenset({"currency", "sender_bank_country"}): "C1", frozenset({"currency", "receiver_bank_country"}): "C1 via G1 affinities",
    frozenset({"sender_bank_country", "sender_iban"}): "P2", frozenset({"receiver_bank_country", "receiver_iban"}): "P2",
    frozenset({"sender_bank_country", "sender_structured"}): "P2 (format by country)", frozenset({"receiver_bank_country", "receiver_structured"}): "P2 (format by country)",
    frozenset({"currency", "sender_iban"}): "C1 + P2 via country", frozenset({"currency", "fx_conversions"}): "C2 + C1",
    frozenset({"sender_bank_country", "utc_quarter_day"}): "T1 (local clock)", frozenset({"currency", "utc_quarter_day"}): "T1 via C1",
    frozenset({"sender_bank_country", "receiver_bank_country"}): "G1 (pair affinities)", frozenset({"domestic", "sender_bank_country"}): "G1",
    frozenset({"domestic", "receiver_bank_country"}): "G1", frozenset({"sender_bank_country", "sender_type"}): "P5 (bank customer mix)",
    frozenset({"receiver_type", "receiver_bank_country"}): "P5 (bank customer mix)",
    # resolved after triage: mechanisms that operate at path or bank level (cannot be expressed by country strata alone)
    frozenset({"sender_bank_country", "fx_conversions"}): "C2 (path currency borders)", frozenset({"receiver_bank_country", "fx_conversions"}): "C2 (path currency borders)",
    frozenset({"receiver_bank_country", "manual_step"}): "D1/D2 (bank STP attribute)", frozenset({"sender_bank_country", "manual_step"}): "D1/D2 (bank STP attribute)",
    frozenset({"currency", "routing_type"}): "R2 + C3 (bank cover propensity; currency from route)", frozenset({"participants", "home_currency"}): "C3 (currency drawn from route)",
    frozenset({"routing_type", "home_currency"}): "C3", frozenset({"receiver_bank_country", "home_currency"}): "C3 (receiver-currency share)",
    frozenset({"currency", "domestic"}): "C3 + G1 (receiver currency; domestic affinity)", frozenset({"utc_quarter_day", "weekend_utc"}): "T1 + T3 (weekend defined on local clock)",
    frozenset({"sender_bank_country", "sender_country_token"}): "P2 (address-format conventions by country)", frozenset({"sender_iban", "sender_structured"}): "P2 (format conventions by country/bank)", frozenset({"routing_type", "sender_bank_country"}): "R2 (bank cover propensity)",
    frozenset({"anomaly", "sender_type"}): "X1/X4 (sender constraints)", frozenset({"amount_decade", "anomaly"}): "X1/X3",
    frozenset({"home_currency", "currency"}): "C1", frozenset({"home_currency", "sender_bank_country"}): "C1 (country home share)",
    frozenset({"first_hop_swapped", "home_currency"}): "R5b", frozenset({"manual_step", "participants"}): "D1 (more banks, more manual steps)",
    frozenset({"manual_step", "routing_type"}): "D1 via R1", frozenset({"manual_step", "continuity"}): "D1 via pc",
    frozenset({"sender_iban", "receiver_iban"}): "P2 via G1 country affinities", frozenset({"sender_country_token", "sender_structured"}): "P3 (template)",
    frozenset({"receiver_country_token", "receiver_structured"}): "P3 (template)",
}

pairs = []
for a, b in itertools.combinations(FEATS, 2):
    vd, vv = cramers_v(dev[a], dev[b]), cramers_v(val[a], val[b])
    pairs.append(dict(a=a, b=b, v_dev=vd, v_val=vv, su_dev=sym_uncertainty(dev[a], dev[b]), stable=abs(vd - vv) < .01,
                      explained_by=EXPLAINS.get(frozenset({a, b}))))
P = pd.DataFrame(pairs).sort_values("v_dev", ascending=False)
strong = P[P.v_dev >= .05]
unexplained = strong[strong.explained_by.isna()].copy()


def residual_v(d, a, b, z, min_n=300):
    """Weighted mean Cramér's V of (a,b) within strata of z (one or two mediators): tests a ⟂ b | z.
    The heterogeneous 'Other' country bucket is excluded so that it cannot masquerade as residual dependence."""
    z = [z] if isinstance(z, str) else list(z)
    for c in z:
        if "country" in c:
            d = d[d[c] != "Other"]
    tot, acc = 0, 0.0
    for _, g in d.groupby(z):
        if len(g) >= min_n and g[a].nunique() > 1 and g[b].nunique() > 1:
            acc += len(g) * cramers_v(g[a], g[b]); tot += len(g)
    return acc / tot if tot else None


MEDIATORS = ["sender_bank_country", "receiver_bank_country", "participants", "currency", "domestic",
             ("sender_bank_country", "receiver_bank_country"), ("sender_bank_country", "participants"), ("receiver_bank_country", "participants"),
             ("currency", "participants"), ("sender_bank_country", "domestic")]
tri = []
for r in unexplained.itertuples():
    res = {}
    for z in MEDIATORS:
        zs = [z] if isinstance(z, str) else list(z)
        if r.a in zs or r.b in zs:
            continue
        v = residual_v(val, r.a, r.b, z)
        if v is not None:
            res[" × ".join(zs)] = v
    zbest = min(res, key=res.get)
    tri.append(dict(a=r.a, b=r.b, v_val=r.v_val, best_mediator=zbest, residual_v=res[zbest],
                    verdict="mediated (composite of existing rules)" if res[zbest] < .03 else "open candidate"))
TRI = pd.DataFrame(tri)
P = P.merge(TRI[["a", "b", "best_mediator", "residual_v", "verdict"]], on=["a", "b"], how="left")
P.loc[P.explained_by.notna() & (P.v_dev >= .05), "verdict"] = "explained by rule"

# ---------------------------------------------------------------- decision-tree candidate rules
def onehot(d, cols):
    return pd.get_dummies(d[cols].astype(str), prefix_sep="=")


def leaf_rules(tree, Xcols, Xd, yd, Xv, yv, target, classes=None, regress=False, min_cov=.005):
    t = tree.tree_; out = []

    def walk(node, conds):
        if t.children_left[node] == -1:
            md = np.ones(len(Xd), bool); mv = np.ones(len(Xv), bool)
            for col, thr, side in conds:
                md &= (Xd[col].values <= thr) if side == "le" else (Xd[col].values > thr)
                mv &= (Xv[col].values <= thr) if side == "le" else (Xv[col].values > thr)
            cov = md.mean()
            if cov < min_cov:
                return
            text = " AND ".join((f"NOT {c}" if s == "le" else c) for c, _, s in conds) or "(all rows)"
            if regress:
                out.append(dict(target=target, rule=f"IF {text} THEN mean ln(amount) = {yd[md].mean():.2f}", coverage=float(cov),
                                dev=float(yd[md].mean()), val=float(yv[mv].mean()) if mv.any() else None, val_coverage=float(mv.mean()),
                                sd_val=float(yv[mv].std()) if mv.any() else None))
            else:
                k = np.bincount(np.searchsorted(classes, yd[md]), minlength=len(classes)).argmax(); cls = classes[k]
                pd_, pv = float((yd[md] == cls).mean()), float((yv[mv] == cls).mean()) if mv.any() else None
                base = float((yv == cls).mean())
                out.append(dict(target=target, rule=f"IF {text} THEN {target} = {cls}", coverage=float(cov), dev_purity=pd_, val_purity=pv,
                                val_coverage=float(mv.mean()), base_rate=base, lift=(pv / base) if pv is not None and base > 0 else None))
            return
        col = Xcols[t.feature[node]]; thr = t.threshold[node]
        walk(t.children_left[node], conds + [(col, thr, "le")]); walk(t.children_right[node], conds + [(col, thr, "gt")])
    walk(0, [])
    return out


TARGETS = {
    "routing_type": ["participants", "currency", "sender_type", "receiver_type", "domestic", "amount_decade", "sender_bank_country"],
    "fx_conversions": ["participants", "domestic", "home_currency", "currency", "sender_bank_country", "receiver_bank_country", "routing_type"],
    "continuity": ["participants", "routing_type", "currency", "domestic", "sender_type"],
    "manual_step": ["participants", "routing_type", "sender_type", "receiver_type", "amount_decade", "utc_quarter_day", "weekend_utc", "domestic", "currency"],
    "home_currency": ["sender_bank_country", "sender_type", "receiver_type", "amount_decade", "domestic", "first_hop_swapped"],
    "sender_iban": ["sender_bank_country", "sender_type", "currency"],
}
trees = []
for target, cols in TARGETS.items():
    Xd, Xv = onehot(dev, cols), onehot(val, cols).reindex(columns=onehot(dev, cols).columns, fill_value=0)
    yd, yv = dev[target].values, val[target].values
    clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=2000, random_state=0).fit(Xd, yd)
    classes = np.array(sorted(set(yd)))
    imp = sorted(zip(Xd.columns, clf.feature_importances_), key=lambda x: -x[1])[:5]
    trees.append(dict(target=target, holdout_accuracy=float(clf.score(Xv, yv)), majority_baseline=float(pd.Series(yv).value_counts(normalize=True).iloc[0]),
                      top_splits=[dict(feature=f, importance=float(i)) for f, i in imp if i > 0],
                      leaves=leaf_rules(clf, list(Xd.columns), Xd, yd, Xv, yv, target, classes)))
# regression: ln(amount) on party types + sender country (rediscovers A1/A2 without being told)
cols = ["sender_type", "receiver_type", "sender_bank_country", "routing_type", "currency"]
Xd, Xv = onehot(dev, cols), onehot(val, cols).reindex(columns=onehot(dev, cols).columns, fill_value=0)
reg = DecisionTreeRegressor(max_depth=3, min_samples_leaf=2000, random_state=0).fit(Xd, dev.ln_amount)
imp = sorted(zip(Xd.columns, reg.feature_importances_), key=lambda x: -x[1])[:5]
r2v = float(reg.score(Xv, val.ln_amount))
trees.append(dict(target="ln_amount", holdout_r2=r2v, top_splits=[dict(feature=f, importance=float(i)) for f, i in imp if i > 0],
                  leaves=leaf_rules(reg, list(Xd.columns), Xd, dev.ln_amount.values, Xv, val.ln_amount.values, "ln_amount", regress=True)))

out = dict(sample=int(len(df)), dev_rows=int(len(dev)), val_rows=int(len(val)), features=FEATS,
           pairs=json.loads(P.to_json(orient="records")), strong_pairs=int(len(strong)), triage=json.loads(TRI.to_json(orient="records")),
           trees=trees)
(EVIDENCE / "discovery.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
print(f"pairs={len(P)} strong(V>=.05)={len(strong)} unexplained={len(unexplained)}")
print(TRI.to_string())
for t_ in trees:
    print(t_["target"], {k: t_[k] for k in t_ if k in ("holdout_accuracy", "majority_baseline", "holdout_r2")}, [s["feature"] for s in t_["top_splits"]][:4])
