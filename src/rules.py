"""Rule validators. Each returns a structured result evaluated on 5 splits:
full · half_0 · half_1 (random halves by hash(rid)) · P1 · P2 (before/after SPLIT_DATE).

A rule PASSES only if its acceptance criterion holds on every split. Rule types (task brief §11.1):
A deterministic · B probabilistic · C conditional · D template · E composite.
Effect sizes, not p-values, are the acceptance metrics: with n = 10M every non-zero difference is 'significant'.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from scipy import stats
from .config import SPLITS, SPLIT_LABEL

RULES = []


def rule(rid, title, rtype, criterion):
    def deco(fn):
        RULES.append(dict(id=rid, title=title, type=rtype, criterion=criterion, fn=fn))
        return fn
    return deco


def by_split(con, select_sql, where="TRUE", src="tt"):
    """Run an aggregate SELECT once per split via GROUPING SETS; returns DataFrame indexed by split."""
    df = con.execute(f"SELECT {SPLIT_LABEL} AS split, {select_sql} FROM {src} WHERE {where} GROUP BY {SPLITS}").df()
    return df.set_index("split").sort_index()


def records(df):
    return {k: {c: (None if pd.isna(v) else float(v)) for c, v in row.items()} for k, row in df.iterrows()}


# ---------------------------------------------------------------- ROUTING (deterministic)
@rule("R6", "PARTICIPANT_COUNT = number of known BICs in BIC8_PATH", "A", "share_exact == 1")
def r6(con):
    d = by_split(con, "avg((pc = path_n - gaps)::INT) share_exact, count(*) n")
    return records(d), bool((d.share_exact == 1).all())


@rule("R7", "CONTINUITY_QFLAG = 'N' iff path contains '...'", "A", "share_exact == 1")
def r7(con):
    d = by_split(con, "avg(((cont='N') = (gaps>0))::INT) share_exact, count(*) n")
    return records(d), bool((d.share_exact == 1).all())


@rule("R5", "Path endpoints differ from ORDERING/BENEFICIARY_BIC8 independently with p≈0.05 each", "B",
      "first & last mismatch in [0.045,0.055] and joint/product ratio in [0.9,1.1]")
def r5(con):
    d = by_split(con, """avg((list_filter(string_split(path,';'),x->x<>'...')[1]<>obic)::INT) p_first,
                        avg((list_filter(string_split(path,';'),x->x<>'...')[-1]<>bbic)::INT) p_last,
                        avg((list_filter(string_split(path,';'),x->x<>'...')[1]<>obic AND list_filter(string_split(path,';'),x->x<>'...')[-1]<>bbic)::INT) p_both""")
    d["indep_ratio"] = d.p_both / (d.p_first * d.p_last)
    ok = d.p_first.between(.045, .055).all() and d.p_last.between(.045, .055).all() and d.indep_ratio.between(.9, 1.1).all()
    return records(d), bool(ok)


@rule("R5b", "On endpoint mismatch, currency follows the path's first bank; account/IBAN follows ORDERING_BIC8", "E",
      "home-ccy share via path[1] > 0.85 and via ORDERING_BIC8 < 0.25; IBAN prefix = ORDERING_BIC8 country == 1")
def r5b(con):
    d = by_split(con, """avg((cur = c1.hcur)::INT) ccy_follows_path_first, avg((cur = c2.hcur)::INT) ccy_follows_obic,
        avg(CASE WHEN o_iban THEN (substr(oacc,7,2)=o_bank_cc)::INT END) iban_follows_obic, count(*) n""",
        where="list_filter(string_split(path,';'),x->x<>'...')[1] <> obic",
        src="tt LEFT JOIN ccy c1 ON c1.cc = substr(list_filter(string_split(path,';'),x->x<>'...')[1],5,2) LEFT JOIN ccy c2 ON c2.cc=o_bank_cc")
    ok = (d.ccy_follows_path_first > .85).all() and (d.ccy_follows_obic < .25).all() and (d.iban_follows_obic == 1).all()
    return records(d), bool(ok)


# ---------------------------------------------------------------- ROUTING (probabilistic)
@rule("R1", "Intermediaries K = floor(Exp(1)): P(K=k) = (1-1/e)e^-k", "B",
      "MLE continuation q within ±0.005 of 1/e and Cohen's w < 0.01 on every split")
def r1(con):
    raw = con.execute(f"SELECT {SPLIT_LABEL} split, pc-2 AS k, count(*) n FROM tt GROUP BY GROUPING SETS ((pc), (pc,h), (pc,per))").df()
    out, ok = {}, True
    for s, g in raw.groupby("split"):
        g = g.sort_values("k"); n = g.n.sum(); kbar = (g.k * g.n).sum() / n
        q = kbar / (1 + kbar)                                   # geometric MLE
        obs = [g[g.k == k].n.sum() for k in range(6)] + [g[g.k >= 6].n.sum()]
        exp = [n * (1 - math.exp(-1)) * math.exp(-k) for k in range(6)] + [n * math.exp(-6)]
        chi2 = sum((o - e) ** 2 / e for o, e in zip(obs, exp)); w = math.sqrt(chi2 / n)
        ratios = [obs[k + 1] / obs[k] for k in range(4)]
        out[s] = dict(n=float(n), q_mle=q, inv_e=math.exp(-1), cohen_w=w, chi2=chi2, p_direct=obs[0] / n,
                      ratio_1=ratios[0], ratio_2=ratios[1], ratio_3=ratios[2], ratio_4=ratios[3])
        ok &= abs(q - math.exp(-1)) < .005 and w < .01
    return out, bool(ok)


@rule("R2", "Covered vs Indirect is a per-sending-bank propensity (cover-prone banks ≈61%, others ≈7%, out of sample), independent of route length", "C",
      "Cramér's V(type×K) < 0.01 on every split; out-of-sample: banks classed as cover banks on half_0 send >50% Covered on half_1, others <10%")
def r2(con):
    # Revised after the discovery engine flagged routing_type × sender_bank_country (V≈0.095) as unexplained:
    # the original 'constant 11.3%' held across K but not across sending banks.
    raw = con.execute(f"""SELECT {SPLIT_LABEL} split, least(pc-2,5) k, count(*) FILTER (WHERE ttype='Covered') ncov,
        count(*) FILTER (WHERE ttype='Indirect') ind FROM tt WHERE ttype<>'Direct' GROUP BY GROUPING SETS ((least(pc-2,5)),(least(pc-2,5),h),(least(pc-2,5),per))""").df()
    out, ok = {}, True
    for s, g in raw.groupby("split"):
        tab = g[["ncov", "ind"]].values; chi2 = stats.chi2_contingency(tab)[0]; n = tab.sum()
        v = math.sqrt(chi2 / n); share = g.ncov.sum() / n
        out[s] = dict(n=float(n), pooled_covered_share=share, cramers_v_vs_K=v, **{f"share_k{int(k)}": c / (c + i) for k, c, i in g[["k", "ncov", "ind"]].values})
        ok &= v < .01
    oos = con.execute("""WITH tr AS (SELECT obic, avg(CASE WHEN ttype<>'Direct' THEN (ttype='Covered')::INT END) s FROM tt WHERE h=0 GROUP BY 1
                                     HAVING count(*) FILTER (WHERE ttype<>'Direct')>=100)
        SELECT (tr.s>0.5) cover_bank, count(*) n, avg((ttype='Covered')::INT) share_test, count(DISTINCT obic) banks
        FROM tt JOIN tr USING(obic) WHERE h=1 AND ttype<>'Direct' GROUP BY 1""").df().set_index("cover_bank")
    cv = con.execute("""WITH x AS (SELECT o_bank_cc, avg(CASE WHEN ttype<>'Direct' THEN (ttype='Covered')::INT END) s FROM t GROUP BY 1 HAVING count(*)>=40000)
                        SELECT min(s), max(s) FROM x""").fetchone()
    out["full"].update(oos_cover_banks_share=float(oos.loc[True, "share_test"]), oos_other_banks_share=float(oos.loc[False, "share_test"]),
                       cover_banks=float(oos.loc[True, "banks"]), other_banks=float(oos.loc[False, "banks"]), country_share_min=cv[0], country_share_max=cv[1])
    ok &= oos.loc[True, "share_test"] > .5 and oos.loc[False, "share_test"] < .1
    return out, bool(ok)


@rule("P5", "Customer-type mix is a bank attribute: each bank has its own business share of senders and of receivers", "C",
      "split-half correlation of bank-level business share > 0.95 on both sides (banks ≥200 rows per half); within-country dispersion ≫ binomial")
def p5(con):
    m = {}
    for side, bic, ty in (("sender", "obic", "otype"), ("receiver", "bbic", "btype")):
        r = con.execute(f"""WITH a AS (SELECT {bic} b, avg(({ty}='B')::INT) s0 FROM tt WHERE h=0 GROUP BY 1 HAVING count(*)>=200),
                                 c AS (SELECT {bic} b, avg(({ty}='B')::INT) s1 FROM tt WHERE h=1 GROUP BY 1 HAVING count(*)>=200)
                            SELECT corr(s0,s1), count(*), min((s0+s1)/2), max((s0+s1)/2) FROM a JOIN c USING(b)""").fetchone()
        m.update({f"{side}_split_half_r": r[0], f"{side}_banks": r[1], f"{side}_bank_share_min": r[2], f"{side}_bank_share_max": r[3]})
    return {"full": m}, bool(m["sender_split_half_r"] > .95 and m["receiver_split_half_r"] > .95)


@rule("R4", "Each link hidden with p=0.05: P(N | pc) = 1-0.95^(pc-1)", "B", "max |obs-pred| over pc 2..7 < 0.006")
def r4(con):
    raw = con.execute(f"SELECT {SPLIT_LABEL} split, pc, avg((cont='N')::INT) p, count(*) n FROM tt WHERE pc<=7 GROUP BY GROUPING SETS ((pc),(pc,h),(pc,per))").df()
    out, ok = {}, True
    for s, g in raw.groupby("split"):
        g = g.assign(pred=1 - .95 ** (g.pc - 1)); dev = (g.p - g.pred).abs().max()
        # MLE of p_link from P(Y)=(1-p)^(pc-1):  maximise sum n_N log(1-(1-p)^m) + n_Y m log(1-p)
        grid = np.linspace(.03, .07, 4001)
        ll = [sum(r.n * (r.p * math.log(1 - (1 - pl) ** (r.pc - 1)) + (1 - r.p) * (r.pc - 1) * math.log(1 - pl)) for r in g.itertuples()) for pl in grid]
        out[s] = dict(max_abs_dev=dev, p_link_mle=float(grid[int(np.argmax(ll))]))
        ok &= dev < .006
    return out, bool(ok)


@rule("R3", "Intermediaries chosen in proportion to bank size, not by payment currency", "C",
      "corr(log intermediary uses, log payments sent) > 0.9; share in payment-currency zone < 0.25")
def r3(con):
    d = con.execute("""WITH i AS (SELECT lst[pos] b, cur FROM (SELECT list_filter(string_split(path,';'),x->x<>'...') lst, cur FROM t WHERE ttype<>'Direct'), range(2,len(lst)) r(pos)),
      a AS (SELECT b, count(*) ni FROM i GROUP BY 1), o AS (SELECT obic b, count(*) ns FROM t GROUP BY 1)
      SELECT corr(ln(ni), ln(ns)) c, (SELECT avg((ccy.hcur=i.cur)::INT) FROM i JOIN ccy ON ccy.cc=substr(i.b,5,2)) in_zone FROM a JOIN o USING(b)""").fetchone()
    return {"full": dict(corr_log=d[0], share_in_currency_zone=d[1])}, bool(d[0] > .9 and d[1] < .25)


# ---------------------------------------------------------------- CURRENCY
@rule("C2", "FX count = adjacent known-BIC pairs with different home currencies", "A", "share_exact >= 0.99999")
def c2(con):
    con.execute("""CREATE OR REPLACE TEMP TABLE fxw AS SELECT rid, h, per, fx, list(hcur ORDER BY i) cl FROM
      (SELECT rid, (hash(rid)%2)::INT h, CASE WHEN d < DATE '2023-06-15' THEN 'P1' ELSE 'P2' END per, fx, generate_subscripts(lst,1) i, unnest(lst) b
       FROM (SELECT *, list_filter(string_split(path,';'),x->x<>'...') lst FROM t)) w LEFT JOIN ccy ON ccy.cc=substr(b,5,2) GROUP BY rid, h, per, fx""")
    d = by_split(con, "avg((fx = len(list_filter(range(1,len(cl)), i -> cl[i]<>cl[i+1])))::INT) share_exact, count(*) n, "
                      "count(*) - sum((fx = len(list_filter(range(1,len(cl)), i -> cl[i]<>cl[i+1])))::INT) exceptions", src="fxw")
    alt = by_split(con, "avg((fx = len(list_distinct(cl))-1)::INT) alt_distinct", src="fxw")
    d = d.join(alt); con.execute("DROP TABLE fxw")
    return records(d), bool((d.share_exact >= .99999).all())


@rule("C1", "Payment currency = home currency of the instructing (first-path) bank ~93%", "C",
      "share in [0.91,0.95] on every split; per-country share range reported")
def c1(con):
    d = by_split(con, "avg((cur=hcur)::INT) home_share, count(*) n",
                 src="tt JOIN ccy ON ccy.cc = substr(list_filter(string_split(path,';'),x->x<>'...')[1],5,2)")
    return records(d), bool(d.home_share.between(.91, .95).all())


# ---------------------------------------------------------------- AMOUNT
@rule("A1", "ln(amount) = 6 + 2·[O=B] + 2·[B=B], σ≈2.28 (no interaction)", "C",
      "intercept∈[5.9,6.2], both effects∈[1.85,2.15], |interaction|<0.1, σ spread across cells <0.03")
def a1(con):
    raw = con.execute(f"""SELECT {SPLIT_LABEL} split, otype, btype, avg(ln(amt)) mu, stddev(ln(amt)) sd, count(*) n FROM tt WHERE anom IS NULL
                         GROUP BY GROUPING SETS ((otype,btype),(otype,btype,h),(otype,btype,per))""").df()
    out, ok = {}, True
    for s, g in raw.groupby("split"):
        m = {(r.otype, r.btype): r.mu for r in g.itertuples()}; sd = g.sd
        b0 = m[("C", "C")]; bo = m[("B", "C")] - b0; bb = m[("C", "B")] - b0; ia = m[("B", "B")] - m[("B", "C")] - m[("C", "B")] + b0
        out[s] = dict(intercept=b0, effect_ordering_B=bo, effect_beneficiary_B=bb, interaction=ia, sd_min=sd.min(), sd_max=sd.max())
        ok &= 5.9 <= b0 <= 6.2 and 1.85 <= bo <= 2.15 and 1.85 <= bb <= 2.15 and abs(ia) < .1 and sd.max() - sd.min() < .03
    return out, bool(ok)


@rule("A2", "Ordering-country effect replicates across independent halves (beneficiary country ≈ no effect)", "C",
      "corr(country effect half_0, half_1) > 0.95; sd(ordering effects) > 3×sd(beneficiary effects)")
def a2(con):
    d = con.execute("""WITH r AS (SELECT (hash(rid)%2)::INT h, o_bank_cc, b_bank_cc, ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT) res FROM t WHERE anom IS NULL),
       o AS (SELECT o_bank_cc cc, avg(res) FILTER (WHERE h=0) e0, avg(res) FILTER (WHERE h=1) e1, count(*) n FROM r GROUP BY 1 HAVING count(*)>=20000),
       b AS (SELECT b_bank_cc cc, avg(res) e FROM r GROUP BY 1 HAVING count(*)>=20000)
       SELECT corr(e0,e1), stddev((e0+e1)/2), (SELECT stddev(e) FROM b), count(*) FROM o""").fetchone()
    return {"full": dict(split_half_corr=d[0], sd_ordering=d[1], sd_beneficiary=d[2], countries=d[3])}, bool(d[0] > .95 and d[1] > 3 * d[2])


# ---------------------------------------------------------------- DURATION (out-of-sample)
@rule("D1", "Duration = sum of per-bank steps; bank speed class learned on half_0 predicts half_1", "E",
      "out-of-sample: fast→fast slow-share < 0.2, any slow bank > 0.9, median(slow,slow)/median(one slow) in [1.6,2.4]")
def d1(con):
    d = con.execute("""WITH tr AS (SELECT * FROM tt WHERE h=0 AND pc=2), te AS (SELECT * FROM tt WHERE h=1 AND pc=2),
      ob AS (SELECT obic b, avg((dur>120)::INT) s, count(*) n FROM tr GROUP BY 1 HAVING count(*)>=30),
      bb AS (SELECT bbic b, avg((dur>120)::INT) s, count(*) n FROM tr GROUP BY 1 HAVING count(*)>=30)
      SELECT CASE WHEN ob.s>.95 THEN 'slow' ELSE 'fast' END oc, CASE WHEN bb.s>.95 THEN 'slow' ELSE 'fast' END bc,
             count(*) n, avg((dur>120)::INT) slow_share, median(dur) med FROM te JOIN ob ON ob.b=te.obic JOIN bb ON bb.b=te.bbic GROUP BY 1,2 ORDER BY 1,2""").df()
    k = {(r.oc, r.bc): r for r in d.itertuples()}
    one = (k[("fast", "slow")].med + k[("slow", "fast")].med) / 2
    ratio = k[("slow", "slow")].med / one
    res = {f"{r.oc}->{r.bc}": dict(n=float(r.n), slow_share=r.slow_share, median_s=r.med) for r in d.itertuples()}
    res["additivity_ratio"] = dict(value=ratio)
    ok = k[("fast", "fast")].slow_share < .2 and min(k[("fast", "slow")].slow_share, k[("slow", "fast")].slow_share, k[("slow", "slow")].slow_share) > .9 and 1.6 <= ratio <= 2.4
    return res, bool(ok)


@rule("D2", "Manual (slow) processing is a bank attribute: hour/weekday/amount effects vanish once bank fixed effects are removed", "C",
      "after two-way (sender bank, receiver bank) demeaning among fast-fast pairs: residual range across UTC hours < 0.015, weekdays < 0.015, |corr with ln amount| < 0.02")
def d2(con):
    # Raw hour differences exist (≈0.037) but are bank-mix driven (Simpson): banks in different time zones have different
    # STP rates. Residual r = slow - mean(sender bank) - mean(receiver bank) + grand mean (one-step two-way demeaning).
    d = con.execute("""WITH ob AS (SELECT obic b, avg((dur>120)::INT) s FROM t WHERE pc=2 GROUP BY 1 HAVING count(*)>=30),
      bb AS (SELECT bbic b, avg((dur>120)::INT) s FROM t WHERE pc=2 GROUP BY 1 HAVING count(*)>=30),
      x AS (SELECT t.*, (dur>120)::INT y FROM t JOIN ob ON ob.b=obic JOIN bb ON bb.b=bbic WHERE pc=2 AND ob.s<.95 AND bb.s<.95),
      fe AS (SELECT *, y - avg(y) OVER (PARTITION BY obic) - avg(y) OVER (PARTITION BY bbic) + avg(y) OVER () r FROM x)
      SELECT (SELECT max(s)-min(s) FROM (SELECT avg(y) s FROM fe GROUP BY hr)),
             (SELECT max(s)-min(s) FROM (SELECT avg(r) s FROM fe GROUP BY hr)),
             (SELECT max(s)-min(s) FROM (SELECT avg(r) s FROM fe GROUP BY dow)),
             (SELECT corr(ln(amt), r) FROM fe)""").fetchone()
    return {"full": dict(raw_range_by_hour=d[0], fe_range_by_hour=d[1], fe_range_by_weekday=d[2], fe_corr_ln_amount=d[3])}, \
        bool(d[1] < .015 and d[2] < .015 and abs(d[3]) < .02)


# ---------------------------------------------------------------- TIME
@rule("T1", "Activity follows the instructing bank's local clock (fixed offsets)", "C",
      "night share (01-05h local) < 0.06 on every split vs > 0.15 with UTC")
def t1(con):
    d = by_split(con, "avg((((hr+o+24)%24) BETWEEN 1 AND 5)::INT) night_local, avg((hr BETWEEN 1 AND 5)::INT) night_utc",
                 src="tt JOIN off ON off.cc = substr(list_filter(string_split(path,';'),x->x<>'...')[1],5,2)")
    return records(d), bool((d.night_local < .06).all())


@rule("T3", "One weekday shape for all countries (local weekday)", "B",
      "max deviation of any country's weekday share from pooled share < 0.01 (countries ≥50k rows)")
def t3(con):
    d = con.execute("""WITH x AS (SELECT o_bank_cc cc, dayofweek(ts + to_hours(o)) ld FROM t JOIN off ON off.cc=o_bank_cc),
      c AS (SELECT cc, ld, count(*)/sum(count(*)) OVER (PARTITION BY cc) s FROM x GROUP BY 1,2),
      p AS (SELECT ld, count(*)/sum(count(*)) OVER () ps FROM x GROUP BY 1),
      big AS (SELECT cc FROM x GROUP BY 1 HAVING count(*)>=50000)
      SELECT max(abs(s-ps)), count(DISTINCT cc) FROM c JOIN p USING(ld) WHERE cc IN (SELECT cc FROM big)""").fetchone()
    return {"full": dict(max_dev=d[0], countries=d[1])}, bool(d[0] < .01)


@rule("T4", "Weekly volume multiplier is global (shared by all countries)", "B",
      "min corr of weekly volume between top-10 countries and the total > 0.98")
def t4(con):
    d = con.execute("""WITH w AS (SELECT date_trunc('week',ts) wk, o_bank_cc cc, count(*) n FROM t WHERE d BETWEEN DATE '2023-05-01' AND DATE '2023-07-30' GROUP BY 1,2),
      tot AS (SELECT wk, sum(n) n FROM w GROUP BY 1), top AS (SELECT cc FROM w GROUP BY 1 ORDER BY sum(n) DESC LIMIT 10)
      SELECT min(c) FROM (SELECT corr(w.n, tot.n) c FROM w JOIN tot USING(wk) WHERE cc IN (SELECT cc FROM top) GROUP BY cc)""").fetchone()
    return {"full": dict(min_corr=d[0])}, bool(d[0] > .98)


# ---------------------------------------------------------------- PARTIES
@rule("P2", "IBAN prefix always equals BIC country; IBAN used only by IBAN-country banks", "A",
      "prefix match == 1; countries with 0<share<0.5 == 0")
def p2(con):
    d = by_split(con, "avg(CASE WHEN o_iban THEN (substr(oacc,7,2)=o_bank_cc)::INT END) o_prefix, avg(CASE WHEN b_iban THEN (substr(bacc,7,2)=b_bank_cc)::INT END) b_prefix")
    mixed = con.execute("SELECT count(*) FROM (SELECT o_bank_cc, avg(o_iban::INT) s, count(*) n FROM t GROUP BY 1 HAVING n>=1000) WHERE s>0 AND s<.5").fetchone()[0]
    r = records(d); r["full"]["countries_ambiguous"] = mixed
    return r, bool((d.o_prefix == 1).all() and (d.b_prefix == 1).all() and mixed == 0)


@rule("P4", "Ordering party lives in its bank's country; beneficiary residence is decoupled from its bank", "C",
      "ordering match == 1, beneficiary match < 0.02 on every split")
def p4(con):
    d = by_split(con, "avg(CASE WHEN o_cust_cc<>'' THEN (o_cust_cc=o_bank_cc)::INT END) o_match, avg(CASE WHEN b_cust_cc<>'' THEN (b_cust_cc=b_bank_cc)::INT END) b_match")
    return records(d), bool((d.o_match == 1).all() and (d.b_match < .02).all())


@rule("P1b", "Beneficiary type independent of ordering type", "B", "|P(bB|oB)-P(bB|oC)| < 0.005")
def p1b(con):
    d = by_split(con, "avg(CASE WHEN otype='B' THEN (btype='B')::INT END) pB_given_oB, avg(CASE WHEN otype='C' THEN (btype='B')::INT END) pB_given_oC")
    d["diff"] = (d.pB_given_oB - d.pB_given_oC).abs()
    return records(d), bool((d["diff"] < .005).all())


# ---------------------------------------------------------------- ANOMALIES
@rule("X1", "ROMANCE_SCAM: consumer bursts of 2-8 escalating payments (×~1.5 each)", "E",
      "sender C share == 1; within-series ln step in [0.3,0.5]; every series fully labelled")
def x1(con):
    d = con.execute("""WITH s AS (SELECT oacc,bacc FROM t WHERE anom='ROMANCE_SCAM' GROUP BY 1,2),
      g AS (SELECT t.*, ln(amt) - avg(ln(amt)) OVER (PARTITION BY oacc,bacc) y, epoch - avg(epoch) OVER (PARTITION BY oacc,bacc) x,
                   row_number() OVER (PARTITION BY oacc,bacc ORDER BY epoch) k FROM t JOIN s USING(oacc,bacc)),
      st AS (SELECT oacc,bacc, regr_slope(ln(amt), k) slope FROM g GROUP BY 1,2)
      SELECT (SELECT avg((otype='C')::INT) FROM t WHERE anom='ROMANCE_SCAM'), (SELECT median(slope) FROM st), (SELECT avg(slope) FROM st),
             (SELECT avg((anom='ROMANCE_SCAM')::INT) FROM g), (SELECT count(*) FROM s)""").fetchone()
    return {"full": dict(sender_consumer_share=d[0], median_ln_step=d[1], mean_ln_step=d[2], labelled_share_in_series=d[3], series=d[4])}, \
        bool(d[0] == 1 and .3 <= d[1] <= .5 and d[3] == 1)


@rule("X2", "DUPLICATE_PAYMENT: 2-5 identical copies (amount, path, duration) within 2h; all copies labelled", "A",
      "every group has 1 path & 1 duration; span ≤ 7200s; sizes ⊂ {2..5}")
def x2(con):
    d = con.execute("""SELECT count(*), max(np), max(nd), max(span), min(n), max(n) FROM (SELECT oacc,bacc,amt, count(*) n, count(DISTINCT path) np,
        count(DISTINCT dur) nd, max(epoch)-min(epoch) span FROM t WHERE anom='DUPLICATE_PAYMENT' GROUP BY ALL)""").fetchone()
    return {"full": dict(groups=d[0], max_paths=d[1], max_durations=d[2], max_span_s=d[3], min_size=d[4], max_size=d[5])}, \
        bool(d[1] == 1 and d[2] == 1 and d[3] <= 7200 and d[4] >= 2 and d[5] <= 5)


@rule("X3", "FAT_FINGER_MISTAKE: amount ×100 or ÷100 relative to expectation", "C",
      "bimodal log10 residual: both modes within ±0.6 of ±2; up share in [0.65,0.9]")
def x3(con):
    r = con.execute("""WITH ce AS (SELECT o_bank_cc, avg(ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)) ce FROM t WHERE anom IS NULL GROUP BY 1)
      SELECT (ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)-ce)/ln(10) r FROM t JOIN ce USING(o_bank_cc) WHERE anom='FAT_FINGER_MISTAKE'""").df().r.values
    from sklearn.mixture import GaussianMixture
    gm = GaussianMixture(2, random_state=0).fit(r.reshape(-1, 1))
    mu = sorted(gm.means_.ravel()); sd = float(np.sqrt(gm.covariances_.ravel()).mean())
    up = float((r > 0).mean())
    return {"full": dict(mode_low=mu[0], mode_high=mu[1], component_sd=sd, up_share=up, n=float(len(r)))}, \
        bool(abs(mu[0] + 2) < .6 and abs(mu[1] - 2) < .6 and .65 <= up <= .9)


@rule("X4", "CEO & ACCOUNT_REPLACEMENT scams pay mule accounts at small banks", "C",
      "share of beneficiary accounts receiving only anomalous money > 0.35 (vs < 0.25 for error types)")
def x4(con):
    d = con.execute("""WITH s AS (SELECT * FROM t WHERE anom IS NOT NULL), b AS (SELECT bacc, sum((anom IS NULL)::INT) clean FROM t WHERE bacc IN (SELECT bacc FROM s) GROUP BY 1)
      SELECT anom, avg((clean=0)::INT) only_anom FROM s JOIN b USING(bacc) GROUP BY 1""").df().set_index("anom").only_anom
    ok = d["CEO_SCAM"] > .35 and d["ACCOUNT_REPLACEMENT_SCAM"] > .35 and d["FAT_FINGER_MISTAKE"] < .25 and d["CUSTOMER_RECALL"] < .25
    return {"full": {k: float(v) for k, v in d.items()}}, bool(ok)


@rule("X5", "CUSTOMER_RECALL has no observable signature (negative result)", "B",
      "no feature differs from normal after Bonferroni (α=0.05/m)")
def x5(con):
    feats = {"weekend": "(dow IN (0,6))::INT", "domestic": "(o_bank_cc=b_bank_cc)::INT", "gap": "(cont='N')::INT", "ord_B": "(otype='B')::INT",
             "ben_B": "(btype='B')::INT", "direct": "(ttype='Direct')::INT", "slow": "(dur>120)::INT", "fx0": "(fx=0)::INT", "iban_b": "b_iban::INT",
             "struct_o": "o_struct::INT"}
    sel = ", ".join(f"avg({v}) FILTER (WHERE anom='CUSTOMER_RECALL') r_{k}, avg({v}) FILTER (WHERE anom IS NULL) n_{k}" for k, v in feats.items())
    row = con.execute(f"SELECT count(*) FILTER (WHERE anom='CUSTOMER_RECALL') nr, {sel} FROM t").df().iloc[0]
    nr = row.nr; m = len(feats); res, ok = {}, True
    for k in feats:
        p0, p1 = row[f"n_{k}"], row[f"r_{k}"]; z = (p1 - p0) / math.sqrt(p0 * (1 - p0) / nr); p = 2 * stats.norm.sf(abs(z))
        res[k] = dict(recall=p1, normal=p0, z=z, p=p, p_bonf=min(1, p * m)); ok &= p * m > .05
    # amount: Mann-Whitney on residual
    a = con.execute("""SELECT anom, ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT) r FROM t WHERE anom='CUSTOMER_RECALL'
                       UNION ALL SELECT * FROM (SELECT anom, ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT) FROM t WHERE anom IS NULL USING SAMPLE 50000 (reservoir, 7))""").df()
    u = stats.mannwhitneyu(a[a.anom == "CUSTOMER_RECALL"].r, a[a.anom.isna()].r)
    res["amount_resid_mwu"] = dict(p=float(u.pvalue), p_bonf=min(1, float(u.pvalue) * (m + 1)))
    return res, bool(ok and u.pvalue * (m + 1) > .05)


@rule("X6", "Anomaly label is independent of routing type", "B", "Cramér's V(anomaly × ttype) < 0.01")
def x6(con):
    tab = con.execute("SELECT coalesce(anom,'NORMAL') a, ttype, count(*) n FROM t GROUP BY 1,2").df().pivot(index="a", columns="ttype", values="n").fillna(0)
    chi2, p, dof, _ = stats.chi2_contingency(tab.values); v = math.sqrt(chi2 / (tab.values.sum() * (min(tab.shape) - 1)))
    return {"full": dict(chi2=chi2, p=p, dof=dof, cramers_v=v)}, bool(v < .01)


# ---------------------------------------------------------------- GRAPH (added in hybrid layer)
@rule("G3", "Intermediaries drawn i.i.d. with replacement ∝ bank size — predicts the path revisit (loop) rate", "E",
      "size exponent β∈[0.9,1.1]; predicted vs observed intermediary-repeat rate within 10% relative for pc 4–8 on every split")
def g3(con):
    inter = con.execute("""SELECT lst[i] b, count(*) n FROM (SELECT list_filter(string_split(path,';'),x->x<>'...') lst FROM t WHERE ttype<>'Direct'),
                           range(2, len(lst)) r(i) GROUP BY 1""").df()
    coll = float(((inter.n / inter.n.sum()) ** 2).sum())
    sz = con.execute("SELECT obic b, count(*) ns FROM t GROUP BY 1").df().merge(inter, on="b")
    beta = float(np.polyfit(np.log(sz.ns), np.log(sz.n), 1)[0])
    raw = con.execute(f"""SELECT {SPLIT_LABEL} split, pc, avg((len(list_distinct(lst[2:len(lst)-1])) < len(lst[2:len(lst)-1]))::INT) obs
        FROM (SELECT *, list_filter(string_split(path,';'),x->x<>'...') lst FROM tt WHERE pc BETWEEN 4 AND 8) GROUP BY GROUPING SETS ((pc),(pc,h),(pc,per))""").df()
    raw["pred"] = [1 - math.prod(1 - j * coll for j in range(1, int(k) - 2)) for k in raw.pc]
    raw["rel_err"] = (raw.obs / raw.pred - 1).abs()
    out = {s: dict(max_rel_err=float(g.rel_err.max()), **{f"pc{int(r.pc)}_obs": float(r.obs) for r in g.itertuples()}, **{f"pc{int(r.pc)}_pred": float(r.pred) for r in g.itertuples()})
           for s, g in raw.groupby("split")}
    out["full"].update(beta=beta, collision_prob=coll)
    return out, bool(.9 <= beta <= 1.1 and raw.rel_err.max() < .1)


@rule("G1", "Sender and receiver banks are NOT paired independently (directional affinities) — independence rejected", "C",
      "χ²/dof > 10 for raw pairs, unique relationships and within country pairs; country affinity symmetry r < 0.3")
def g1(con):
    import json as _j
    from .config import EVIDENCE as _E
    g = _j.loads((_E / "graph.json").read_text())  # computed by src.graph (heavy pair cross-join kept out of the validator loop)
    p, c = g["G1_pairing"], g["G2_country"]
    m = dict(chi2_dof_raw=p["chi2_per_dof"], chi2_dof_unique=p["chi2_per_dof_unique_relationships"], chi2_dof_within_country=p["chi2_per_dof_given_country_pair"],
             domestic_affinity=c["domestic_affinity_mean"], affinity_symmetry_r=c["affinity_symmetry_corr"], country_cramers_v=c["cramers_v"])
    return {"full": m}, bool(min(m["chi2_dof_raw"], m["chi2_dof_unique"], m["chi2_dof_within_country"]) > 10 and m["affinity_symmetry_r"] < .3)


@rule("A3", "Within-country log-amount residual is Normal (lognormal amounts, no power-law tail)", "B",
      "|skew|<0.05, |excess kurtosis|<0.1, KS D<0.01 on every split; Hill α drifts (>0.5 between k=100 and k=100k)")
def a3(con):
    out, ok = {}, True
    for s, w in [("full", "TRUE"), ("half_0", "h=0"), ("half_1", "h=1"), ("P1", "per='P1'"), ("P2", "per='P2'")]:
        r = con.execute(f"""SELECT ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT) - avg(ln(amt)-(6+2*(otype='B')::INT+2*(btype='B')::INT)) OVER (PARTITION BY o_bank_cc) r
                           FROM tt WHERE anom IS NULL AND {w} USING SAMPLE 200000 (reservoir, 3)""").df().r.values
        sk, ku, D = float(stats.skew(r)), float(stats.kurtosis(r)), float(stats.kstest(r / r.std(), "norm").statistic)
        out[s] = dict(sd=float(r.std()), skew=sk, excess_kurtosis=ku, ks_D=D); ok &= abs(sk) < .05 and abs(ku) < .1 and D < .01
    top = con.execute("SELECT amt FROM t WHERE anom IS NULL ORDER BY amt DESC LIMIT 100001").df().amt.values
    hill = {k: float(1 / np.mean(np.log(top[:k] / top[k]))) for k in (100, 100000)}
    out["full"].update(hill_alpha_k100=hill[100], hill_alpha_k100000=hill[100000])
    return out, bool(ok and hill[100] - hill[100000] > .5)


@rule("D3", "Manual processing step ≈ Gamma(shape≈2, scale≈820 s); fast step pair ≈ Gamma(3, 8.7 s)", "B",
      "manual-step gamma shape∈[1.6,2.5] and KS D<0.05 better than lognormal; fast-pair gamma shape∈[2.5,3.6], KS D<0.05")
def d3(con):
    import json as _j
    from .config import EVIDENCE as _E
    s = _j.loads((_E / "stats.json").read_text())
    ms, fs = s["manual_step"], s["fast_step"]
    m = dict(manual_shape=ms["gamma_shape"], manual_scale_s=ms["gamma_scale"], manual_ks_gamma=ms["ks_gamma"], manual_ks_lognormal=ms["ks_lognormal"],
             fast_pair_shape=fs["gamma_shape"], fast_pair_scale_s=fs["gamma_scale"], fast_ks=fs["ks_D"], n_manual=ms["n"], n_fast=fs["n"])
    ok = 1.6 <= m["manual_shape"] <= 2.5 and m["manual_ks_gamma"] < .05 and m["manual_ks_gamma"] < m["manual_ks_lognormal"] and 2.5 <= m["fast_pair_shape"] <= 3.6 and m["fast_ks"] < .05
    return {"full": m}, bool(ok)


@rule("C3", "Payment currency is drawn from the currencies on the route: first bank ≈ 95% (direct), receiver bank ≈ 3.8%, +≈2.4 pts per intermediary, outside-route vehicle ≈ 1.3%", "E",
      "≥98% of payments in a route-bank currency on every split; receiver-only share stable across route lengths (range < 0.006); intermediary-only share rises ≈ linearly per intermediary (slope 0.02–0.035)")
def c3(con):
    # Found by the discovery engine (routing_type × home_currency, participants × home_currency unexplained).
    con.execute("""CREATE OR REPLACE TEMP TABLE c3w AS SELECT rid, h, per, cur, pc, generate_subscripts(lst,1) i, unnest(lst) b
                   FROM (SELECT rid, h, per, cur, pc, list_filter(string_split(path,';'),x->x<>'...') lst FROM tt USING SAMPLE 3000000 ROWS (reservoir, 31))""")
    con.execute("""CREATE OR REPLACE TEMP TABLE c3r AS SELECT rid, any_value(h) h, any_value(per) per, any_value(cur) cur, any_value(pc) pc,
                   list(ccy.hcur ORDER BY i) cl FROM c3w LEFT JOIN ccy ON ccy.cc=substr(b,5,2) GROUP BY rid""")
    raw = con.execute(f"""SELECT {SPLIT_LABEL} split, least(pc,6) k, count(*) n, avg(list_contains(cl,cur)::INT) in_route, avg((cur=cl[1])::INT) first_bank,
        avg((cur<>cl[1] AND cur=cl[-1])::INT) receiver_only, avg((cur<>cl[1] AND cur<>cl[-1] AND list_contains(cl,cur))::INT) intermediary_only,
        avg((NOT list_contains(cl,cur))::INT) outside FROM c3r GROUP BY GROUPING SETS ((least(pc,6)),(least(pc,6),h),(least(pc,6),per))""").df()
    con.execute("DROP TABLE c3w"); con.execute("DROP TABLE c3r")
    out, ok = {}, True
    for s, g in raw.groupby("split"):
        g = g.sort_values("k"); w = g.n / g.n.sum()
        slope = float(np.polyfit(g.k - 2, g.intermediary_only, 1, w=np.sqrt(g.n))[0])
        rec_range = float(g.receiver_only.max() - g.receiver_only.min()); in_route = float((g.in_route * w).sum())
        out[s] = dict(n_sample=float(g.n.sum()), in_route_share=in_route, receiver_only_mean=float((g.receiver_only * w).sum()), receiver_only_range=rec_range,
                      intermediary_slope_per_hop=slope, outside_share=float((g.outside * w).sum()), first_bank_direct=float(g[g.k == 2].first_bank.iloc[0]))
        ok &= in_route >= .98 and rec_range < .006 and .02 <= slope <= .035
    return out, bool(ok)


@rule("F1", "Fingerprint: USD-denominated amounts keep whole-unit roundness (≈39% .00) while converted currencies have uniform cents (≈1%)", "D",
      "USD whole-unit share > 0.30 and non-USD share in [0.008,0.013] on every split")
def f1(con):
    d = by_split(con, """avg(CASE WHEN cur='USD' THEN (CAST(round(amt*100) AS BIGINT) % 100 = 0)::INT END) usd_whole_share,
                         avg(CASE WHEN cur<>'USD' THEN (CAST(round(amt*100) AS BIGINT) % 100 = 0)::INT END) non_usd_whole_share,
                         count(*) FILTER (WHERE cur='USD') n_usd""", where="anom IS NULL")
    return records(d), bool((d.usd_whole_share > .30).all() and d.non_usd_whole_share.between(.008, .013).all())


@rule("T4b", "Weekly volume levels are piecewise-constant with every change point on a Monday (week boundary)", "B",
      "binary segmentation (BIC penalty) on weekday-normalised log volume: ≥1 change point, 100% on Mondays, residual sd < 0.03")
def t4b(con):
    import json as _j
    from .config import EVIDENCE as _E
    c = _j.loads((_E / "forensics.json").read_text())["change_points"]
    m = dict(change_points=len(c["change_points"]), share_on_monday=c["share_on_monday"], residual_sd_log=c["residual_sd_log"], segments=len(c["segments"]))
    return {"full": m}, bool(m["change_points"] >= 1 and m["share_on_monday"] == 1 and m["residual_sd_log"] < .03)
