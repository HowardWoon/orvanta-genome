"""Layer 3 · Graph & route intelligence on the directed payment pseudograph.

Run: python -m src.graph  -> outputs/evidence/graph.json
Nodes = BIC8 institutions; an edge (u→v) = one observed adjacent hop in BIC8_PATH ('...' removed, so a hidden
segment links the banks on either side — flagged separately). The pseudograph keeps parallel edges (multiplicity)
and loops (a bank revisited inside one path). No NetworkX: aggregation in DuckDB, PageRank by SciPy sparse power iteration.

Generator questions answered here
  G1  Are sender bank and receiver bank paired independently (configuration-model / gravity with unit exponents)?
  G2  Is the beneficiary bank country independent of the ordering bank country?
  G3  Are intermediaries drawn i.i.d. with replacement, proportional to size?  -> predicts the loop (revisit) rate.
  G4  How concentrated is the network (Gini, top-share), and are hubs automated (STP)?
"""
from __future__ import annotations
import json, math
import numpy as np
import pandas as pd
from scipy import sparse
from .config import connect, EVIDENCE

con = connect()
G = {}
df = lambda s: con.execute(s).df()
rec = lambda d: json.loads(d.to_json(orient="records"))


def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


# ---------------------------------------------------------------- edges of the pseudograph
con.execute("""CREATE OR REPLACE TEMP TABLE hops AS
  SELECT lst[i] u, lst[i+1] v FROM (SELECT list_filter(string_split(path,';'),x->x<>'...') lst FROM t), range(1, len(lst)) r(i)""")
con.execute("CREATE OR REPLACE TEMP TABLE E AS SELECT u, v, count(*) w FROM hops GROUP BY 1,2")
s = con.execute("""SELECT (SELECT count(*) FROM hops) hops, (SELECT count(*) FROM E) edges,
   (SELECT count(DISTINCT x) FROM (SELECT u x FROM E UNION SELECT v FROM E)) nodes,
   (SELECT sum(w) FROM E WHERE u=v) self_hops,
   (SELECT count(*) FROM E e1 WHERE EXISTS (SELECT 1 FROM E e2 WHERE e2.u=e1.v AND e2.v=e1.u) AND e1.u<>e1.v) recip_edges,
   (SELECT median(w) FROM E) med_mult, (SELECT max(w) FROM E) max_mult""").df().iloc[0]
G["network"] = {k: float(v) for k, v in s.items()}
G["network"]["density"] = G["network"]["edges"] / (G["network"]["nodes"] ** 2)
G["network"]["reciprocity"] = G["network"]["recip_edges"] / G["network"]["edges"]

# node strength & concentration
st = df("""SELECT b, sum(o) out_s, sum(i) in_s FROM (SELECT u b, w o, 0 i FROM E UNION ALL SELECT v, 0, w FROM E) GROUP BY 1""")
st["tot"] = st.out_s + st.in_s
srt = np.sort(st.tot.values)[::-1]
G["concentration"] = dict(gini_strength=gini(st.tot), top1pct_share=float(srt[: max(1, len(srt) // 100)].sum() / srt.sum()),
                          top10pct_share=float(srt[: max(1, len(srt) // 10)].sum() / srt.sum()), hhi=float(((srt / srt.sum()) ** 2).sum()))
cc = np.sort(st.tot.values); ccdf = 1 - np.arange(len(cc)) / len(cc)
idx = np.unique(np.geomspace(1, len(cc), 60).astype(int) - 1)
G["strength_ccdf"] = [{"s": float(cc[i]), "p": float(ccdf[i])} for i in idx]
lg = np.log(st.tot[st.tot > 0])
G["strength_lognormal"] = dict(mu=float(lg.mean()), sd=float(lg.std()), skew=float(pd.Series(lg).skew()))

# ---------------------------------------------------------------- PageRank (weighted, damping .85)
nodes = st.b.tolist(); ix = {b: i for i, b in enumerate(nodes)}
e = df("SELECT u, v, w FROM E")
A = sparse.csr_matrix((e.w.values.astype(float), (e.u.map(ix).values, e.v.map(ix).values)), shape=(len(nodes), len(nodes)))
out = np.asarray(A.sum(1)).ravel(); out[out == 0] = 1
P = sparse.diags(1 / out) @ A
pr = np.ones(len(nodes)) / len(nodes)
for _ in range(100):
    new = .15 / len(nodes) + .85 * (P.T @ pr)
    new += (1 - new.sum()) / len(nodes)
    if np.abs(new - pr).sum() < 1e-12:
        break
    pr = new
st["pagerank"] = pr
slow = df("SELECT obic b, avg((dur>120)::INT) slow, count(*) n2 FROM t WHERE pc=2 GROUP BY 1")
top = st.merge(slow, on="b", how="left").sort_values("pagerank", ascending=False)
top["cc"] = top.b.str[4:6]
G["top_hubs"] = rec(top.head(15)[["b", "cc", "pagerank", "out_s", "in_s", "slow"]])
q = top.dropna(subset=["slow"]).copy(); q["pr_decile"] = pd.qcut(q.pagerank.rank(method="first"), 10, labels=False) + 1
G["hub_stp"] = rec(q.groupby("pr_decile").agg(slow_bank_share=("slow", lambda x: float((x > .9).mean())), banks=("b", "size")).reset_index())

# ---------------------------------------------------------------- G1 · independent pairing of sender & receiver banks
pair = df("""WITH d AS (SELECT obic, bbic FROM t), o AS (SELECT obic, count(*) nob FROM d GROUP BY 1), b AS (SELECT bbic, count(*) nb FROM d GROUP BY 1),
   p AS (SELECT obic, bbic, count(*) n FROM d GROUP BY 1,2)
   SELECT o.nob, b.nb, coalesce(p.n,0) n FROM o JOIN b ON TRUE LEFT JOIN p USING(obic,bbic) WHERE o.nob >= 3000 AND b.nb >= 3000""")
N = 1e7; pair["E"] = pair.nob * pair.nb / N
ok = pair[pair.E >= 5]
chi2 = float(((ok.n - ok.E) ** 2 / ok.E).sum()); dof = len(ok) - 1
G["G1_pairing"] = dict(pairs_tested=int(len(ok)), chi2_per_dof=chi2 / dof, corr_log=float(np.corrcoef(np.log(ok.n + .5), np.log(ok.E))[0, 1]),
                       slope_log=float(np.polyfit(np.log(ok.E), np.log(ok.n + .5), 1)[0]), mean_ratio=float(ok.n.sum() / ok.E.sum()))
smp = ok.sample(min(2500, len(ok)), random_state=3)
G["G1_scatter"] = rec(smp[["E", "n"]])


# G1b · conditional on country pair, and symmetry of country affinities
pc_ = df("""WITH d AS (SELECT obic,bbic,o_bank_cc oc,b_bank_cc bc FROM t),
 cp AS (SELECT oc,bc,count(*) ncp FROM d GROUP BY 1,2), oc AS (SELECT oc, count(*) noc FROM d GROUP BY 1), bcn AS (SELECT bc, count(*) nbc FROM d GROUP BY 1),
 o AS (SELECT obic, any_value(oc) oc, count(*) nob FROM d GROUP BY 1), b AS (SELECT bbic, any_value(bc) bc, count(*) nb FROM d GROUP BY 1),
 pr AS (SELECT obic,bbic,count(*) n FROM d GROUP BY 1,2)
 SELECT o.nob, b.nb, oc.noc, bcn.nbc, cp.ncp, coalesce(pr.n,0) n FROM o JOIN b ON TRUE JOIN oc ON oc.oc=o.oc JOIN bcn ON bcn.bc=b.bc JOIN cp ON cp.oc=o.oc AND cp.bc=b.bc LEFT JOIN pr USING(obic,bbic)
 WHERE o.nob>=2000 AND b.nb>=2000""")
pc_["E"] = pc_.ncp * (pc_.nob / pc_.noc) * (pc_.nb / pc_.nbc); okc = pc_[pc_.E >= 5]
G["G1_pairing"]["chi2_per_dof_given_country_pair"] = float(((okc.n - okc.E) ** 2 / okc.E).sum() / (len(okc) - 1))
rel = df("""WITH d AS (SELECT DISTINCT oacc,bacc,obic,bbic FROM t), o AS (SELECT obic, count(*) nob FROM d GROUP BY 1), b AS (SELECT bbic, count(*) nb FROM d GROUP BY 1),
 p AS (SELECT obic,bbic,count(*) n FROM d GROUP BY 1,2), tt_ AS (SELECT count(*) totn FROM d)
 SELECT o.nob, b.nb, coalesce(p.n,0) n, tt_.totn FROM o JOIN b ON TRUE JOIN tt_ ON TRUE LEFT JOIN p USING(obic,bbic) WHERE o.nob>=2000 AND b.nb>=2000""")
rel["E"] = rel.nob * rel.nb / rel.totn; okr = rel[rel.E >= 5]
G["G1_pairing"]["chi2_per_dof_unique_relationships"] = float(((okr.n - okr.E) ** 2 / okr.E).sum() / (len(okr) - 1))
cr = df("""WITH d AS (SELECT o_bank_cc o,b_bank_cc b FROM t), x AS (SELECT o,b,count(*) n FROM d GROUP BY 1,2), po AS (SELECT o,count(*)/1e7 p FROM d GROUP BY 1), pb AS (SELECT b,count(*)/1e7 q FROM d GROUP BY 1)
 SELECT x.o,x.b, n/(1e7*p*q) ratio FROM x JOIN po USING(o) JOIN pb USING(b) WHERE 1e7*p*q>=2000""")
sym = cr.merge(cr, left_on=["o", "b"], right_on=["b", "o"], suffixes=("", "_rev")); sym = sym[sym.o != sym.b]
_aff = dict(affinity_sd_offdiag=float(cr[cr.o != cr.b].ratio.std()), domestic_affinity_mean=float(cr[cr.o == cr.b].ratio.mean()),
            affinity_symmetry_corr=float(np.corrcoef(np.log(sym.ratio), np.log(sym.ratio_rev))[0, 1]))
G["country_affinity_top"] = rec(cr.sort_values("ratio", ascending=False).head(10)); G["country_affinity_bottom"] = rec(cr.sort_values("ratio").head(10))

# ---------------------------------------------------------------- G2 · country-level independence
cp = df("SELECT o_bank_cc o, b_bank_cc b, count(*) n FROM t GROUP BY 1,2").pivot(index="o", columns="b", values="n").fillna(0)
big_o = cp.sum(axis=1) >= 20000; big_b = cp.sum(axis=0) >= 20000; m = cp.loc[big_o, big_b].values
Ex = np.outer(m.sum(1), m.sum(0)) / m.sum()
chi = float(((m - Ex) ** 2 / Ex).sum()); dofc = (m.shape[0] - 1) * (m.shape[1] - 1)
G["G2_country"] = dict(chi2_per_dof=chi / dofc, cramers_v=float(math.sqrt(chi / (m.sum() * (min(m.shape) - 1)))), shape=list(m.shape),
                       domestic_obs=float(np.trace(cp.loc[big_o, big_b].reindex(columns=cp.index[big_o]).fillna(0).values) / m.sum()) if True else None)
dom = df("SELECT avg((o_bank_cc=b_bank_cc)::INT) obs FROM t").obs[0]
po = df("SELECT o_bank_cc c, count(*)/1e7 p FROM t GROUP BY 1"); pb = df("SELECT b_bank_cc c, count(*)/1e7 p FROM t GROUP BY 1")
G["G2_country"]["domestic_observed"] = float(dom); G["G2_country"]["domestic_expected_if_independent"] = float(po.merge(pb, on="c").eval("p_x*p_y").sum())
G["G2_country"].update(_aff)

# ---------------------------------------------------------------- G3 · intermediaries i.i.d. ∝ size -> loop rate
inter = df("""SELECT lst[i] b, count(*) n FROM (SELECT list_filter(string_split(path,';'),x->x<>'...') lst FROM t WHERE ttype<>'Direct'), range(2, len(lst)) r(i) GROUP BY 1""")
p_int = inter.n / inter.n.sum(); coll = float((p_int ** 2).sum())
sz = df("SELECT obic b, count(*) ns FROM t GROUP BY 1").merge(inter, on="b", how="inner")
G["G3_size_exponent"] = dict(beta=float(np.polyfit(np.log(sz.ns), np.log(sz.n), 1)[0]), corr=float(np.corrcoef(np.log(sz.ns), np.log(sz.n))[0, 1]), banks=int(len(sz)))
loops = df("""SELECT pc, avg((len(list_distinct(lst[2:len(lst)-1])) < len(lst[2:len(lst)-1]))::INT) obs_inter_repeat, count(*) n
   FROM (SELECT pc, list_filter(string_split(path,';'),x->x<>'...') lst FROM t WHERE pc BETWEEN 4 AND 9) GROUP BY 1 ORDER BY 1""")
# P(any repeat among K iid draws) = 1 - prod_{j<K} (1 - j*coll) approx (birthday with non-uniform p)
loops["pred_iid"] = [1 - math.prod(1 - j * coll for j in range(1, k - 2)) for k in loops.pc]   # K = pc-2 draws; birthday product over j=1..K-1
G["G3_loops"] = rec(loops); G["G3_collision_prob"] = coll
rep_all = df("""SELECT avg((len(list_distinct(lst))<len(lst))::INT) any_repeat, sum((len(list_distinct(lst))<len(lst))::INT) n FROM
   (SELECT list_filter(string_split(path,';'),x->x<>'...') lst FROM t)""").iloc[0]
G["pseudograph"] = dict(paths_with_revisit=float(rep_all.n), share=float(rep_all.any_repeat),
                        same_header_bank=float(df("SELECT count(*) c FROM t WHERE obic=bbic").c[0]))

# ---------------------------------------------------------------- route patterns (country sequences, aggregated)
G["route_patterns"] = rec(df("""SELECT ttype, array_to_string(list_transform(list_filter(string_split(path,';'),x->x<>'...'), b -> substr(b,5,2)), ' › ') route,
   count(*) n, median(dur) med_dur, avg(fx) fx, avg((cont='N')::INT) gap FROM t GROUP BY 1,2 HAVING count(*)>=200 ORDER BY n DESC LIMIT 400"""))
G["flow_matrix_top"] = rec(df("""WITH top AS (SELECT o_bank_cc c FROM t GROUP BY 1 ORDER BY count(*) DESC LIMIT 12)
   SELECT o_bank_cc o, b_bank_cc b, count(*) n FROM t WHERE o_bank_cc IN (SELECT c FROM top) AND b_bank_cc IN (SELECT c FROM top) GROUP BY 1,2"""))

(EVIDENCE / "graph.json").write_text(json.dumps(G, default=float))
print(json.dumps({k: G[k] for k in ["G1_pairing"] }, default=float)); print(json.dumps({k: G[k] for k in ["network", "concentration", "G1_pairing", "G2_country", "G3_size_exponent", "pseudograph"]}, indent=1, default=float))
print("loops", G["G3_loops"])
