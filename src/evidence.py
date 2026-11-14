"""Reproducible evidence for every reconstructed rule -> evidence.json (chart-ready aggregates only).

Run    : python -m src.evidence   (inputs: data/processed/*.parquet, data/metadata/*.csv)
Output : evidence.json
Only the Swift-provided dataset is used. No external data.
"""
import json, math
import numpy as np
import pandas as pd
from .config import connect, EVIDENCE, FULL_PQ, _p

con = connect()
con.execute("CREATE OR REPLACE TABLE m AS SELECT * FROM ccy")
E = {}
df = lambda s: con.execute(s).df()
rec = lambda d: json.loads(d.to_json(orient="records"))

# ---------- headline counts ----------
E["n"] = int(con.execute("select count(*) from t").fetchone()[0])
E["anom_counts"] = rec(df("select anom, count(*) n from t where anom is not null group by 1 order by 2 desc"))

# ---------- 1. TIME ----------
E["daily"] = rec(df("select strftime(d,'%Y-%m-%d') d, dayofweek(d) dow, count(*) n from t group by 1,2 order by 1"))
E["weekly"] = rec(df("""select strftime(date_trunc('week',ts),'%Y-%m-%d') wk, count(*) n, avg(ln(amt)) mlog,
  avg((otype='B')::int) ob, avg((ttype='Direct')::int) direct, median(dur) mdur from t group by 1 order by 1"""))
E["utc_hour_by_country"] = rec(df("""select o_bank_cc cc, hr, count(*) n from t
  where o_bank_cc in ('US','GB','DE','CN','JP','AU','AE','BR') group by 1,2 order by 1,2"""))
E["offsets"] = rec(df("select * from off where cc in ('US','CA','MX','BR','AR','GB','DE','FR','CH','ZA','RU','AE','IN','CN','SG','HK','JP','KR','AU','NZ') order by o"))
E["local_hour"] = rec(df("""select otype, ((hr + off.o + 24) % 24) lh, count(*) n from t join off on off.cc=o_bank_cc group by 1,2 order by 1,2"""))
E["local_dow"] = rec(df("""select dayofweek(ts + to_hours(off.o)) ldow, count(*) n from t join off on off.cc=o_bank_cc group by 1 order by 1"""))

# ---------- 2. CURRENCY & FX ----------
E["local_ccy_by_country"] = rec(df("""with x as (select substr(list_filter(string_split(path,';'),x->x<>'...')[1],5,2) cc, t.cur, m.hcur from t join m on m.cc=substr(list_filter(string_split(path,';'),x->x<>'...')[1],5,2)),
   y as (select cc, count(*) n, avg((cur=hcur)::int) local_sh, avg((cur<>hcur and cur='EUR')::int) eur, avg((cur<>hcur and cur='USD')::int) usd,
   avg((cur<>hcur and cur='GBP')::int) gbp, avg((cur<>hcur and cur='CHF')::int) chf from x group by 1) select * from y where n>=60000 order by n desc"""))
E["vehicle_ccy"] = rec(df("""select t.cur, count(*) n from t join m on m.cc=substr(list_filter(string_split(path,';'),x->x<>'...')[1],5,2) where t.cur<>m.hcur group by 1 order by 2 desc limit 8"""))
# FX rule validation on full data: fx == # adjacent known-BIC pairs whose home currencies differ
con.execute("""CREATE TABLE w AS SELECT rid, fx, pc, generate_subscripts(lst,1) i, unnest(lst) b
  FROM (SELECT rid, fx, pc, list_filter(string_split(path,';'), x->x<>'...') lst FROM t)""")
con.execute("""CREATE TABLE w1 AS SELECT rid, any_value(fx) fx, any_value(pc) pc, list(hcur ORDER BY i) cl
  FROM w JOIN m ON m.cc=substr(b,5,2) GROUP BY rid""")
con.execute("DROP TABLE w")
fxv = df("""select count(*) n, sum((fx = len(list_filter(range(1,len(cl)), i -> cl[i]<>cl[i+1])))::int) exact from w1""")
E["fx_rule"] = {"n": int(fxv.n[0]), "exact": int(fxv.exact[0])}
E["fx_by_pc"] = rec(df("select pc, fx, count(*) n from t where pc<=6 group by 1,2 order by 1,2"))
con.execute("DROP TABLE w1")

# ---------- 3. ROUTING ----------
E["hops"] = rec(df("select pc, count(*) n, sum((ttype='Covered')::int) cov from t group by 1 order by 1"))
E["gap_by_pc"] = rec(df("select pc, count(*) n, avg((cont='N')::int) p from t where pc<=10 group by 1 order by 1"))
E["gaps_direct"] = rec(df("select gaps, count(*) n from t where pc=2 group by 1 order by 1"))
E["direct_share_bank"] = rec(df("""with x as (select obic, count(*) n, avg((ttype='Direct')::int) pd from t group by 1 having n>=1000)
  select round(pd,2) b, count(*) banks from x group by 1 order by 1"""))
E["intermediary_vs_size"] = rec(df("""with i as (select lst[pos] b from (select list_filter(string_split(path,';'), x->x<>'...') lst from t where ttype<>'Direct'), range(2,len(lst)) r(pos)),
  a as (select b, count(*) ni from i group by 1), o as (select obic b, count(*) nsend from t group by 1)
  select a.b, ni, nsend from a join o using(b)"""))
x = pd.DataFrame(E.pop("intermediary_vs_size"))
E["intermediary_corr"] = float(np.corrcoef(np.log(x.ni), np.log(x["nsend"]))[0, 1])
# downsample for scatter
E["intermediary_scatter"] = rec(x.sample(min(1500, len(x)), random_state=1)[["ni", "nsend"]])

# ---------- 4. DURATION ----------
E["dur_hist_pc2"] = rec(df("select floor(log2(dur))::int lb, count(*) n from t where pc=2 group by 1 order by 1"))
con.execute("CREATE TABLE ob AS SELECT obic b, count(*) n, avg((dur>120)::int) s FROM t WHERE pc=2 GROUP BY 1")
con.execute("CREATE TABLE bb AS SELECT bbic b, count(*) n, avg((dur>120)::int) s FROM t WHERE pc=2 GROUP BY 1")
E["dur_bank_class"] = rec(df("""select case when ob.s>0.95 then 'slow' else 'fast' end o_cls, case when bb.s>0.95 then 'slow' else 'fast' end b_cls,
  count(*) n, avg((dur>120)::int) slow_share, median(dur) med from t join ob on ob.b=obic join bb on bb.b=bbic
  where pc=2 and ob.n>=30 and bb.n>=30 group by all order by 1,2"""))
E["bank_slow_hist"] = rec(df("select round(s,1) b, count(*) banks from ob where n>=2000 group by 1 order by 1"))
E["stp_by_size"] = rec(df("""select case when n<100 then '<100' when n<1000 then '100-999' when n<10000 then '1k-9.9k' else '10k+' end sz,
  min(n) mn, count(*) banks, avg((s>0.9)::int) slow_bank_share from ob group by 1 order by mn"""))
E["dur_by_pc"] = rec(df("select pc, quantile_cont(dur,[.1,.5,.9]) q from t where pc<=9 group by 1 order by 1"))
E["dur_by_type_pc3"] = rec(df("select ttype, median(dur) med, avg(dur) mean from t where pc=3 group by 1"))

# ---------- 5. AMOUNT ----------
E["amt_by_type"] = rec(df("""select otype||btype seg, count(*) n, avg(ln(amt)) mu, stddev(ln(amt)) sd, median(amt) med
  from t where anom is null group by 1 order by 1"""))
E["amt_hist"] = rec(df("""select otype||btype seg, floor(log10(amt)*4)/4 lb, count(*) n from t where anom is null group by 1,2 order by 1,2"""))
con.execute("""CREATE TABLE r AS SELECT oacc, obic, o_bank_cc, ln(amt) - (6 + 2*(otype='B')::int + 2*(btype='B')::int) res
  FROM t WHERE anom IS NULL""")
E["amt_country"] = rec(df("select o_bank_cc cc, count(*) n, avg(res) eff from r group by 1 having n>=20000 order by eff"))
E["amt_bene_country_sd"] = float(con.execute("""with x as (select b_bank_cc, avg(ln(amt) - (6 + 2*(otype='B')::int + 2*(btype='B')::int)) e, count(*) n
  from t where anom is null group by 1 having n>=20000) select stddev(e) from x""").fetchone()[0])
con.execute("CREATE TABLE r1 AS SELECT *, res - avg(res) OVER (PARTITION BY o_bank_cc) r_c FROM r")
con.execute("CREATE TABLE r2 AS SELECT *, r_c - avg(r_c) OVER (PARTITION BY obic) r_b FROM r1")
con.execute("CREATE TABLE r3 AS SELECT *, r_b - avg(r_b) OVER (PARTITION BY oacc) r_a, count(*) OVER (PARTITION BY oacc) na FROM r2")
v = df("""select var_pop(res) tot, var_pop(res)-var_pop(r_c) country, var_pop(r_c)-var_pop(r_b) bank from r3""")
va = df("select var_pop(r_b)-var_pop(r_a) acct, var_pop(r_a) noise from r3 where na>=30")
E["amt_variance"] = {"total": float(v.tot[0]), "country": float(v.country[0]), "bank": float(v.bank[0]),
                     "account": float(va.acct[0]), "noise": float(va.noise[0])}
for tname in ["r", "r1", "r2", "r3"]:
    con.execute(f"DROP TABLE {tname}")

# ---------- 6. PARTIES, ACCOUNTS, TEXT ----------
E["iban_by_country"] = rec(df("select o_bank_cc cc, count(*) n, avg(o_iban::int) iban, avg(o_struct::int) strct from t group by 1 having n>=20000 order by iban desc"))
E["type_mix"] = rec(df("select otype, btype, count(*) n from t group by 1,2 order by 1,2"))
E["ob_share_by_country"] = rec(df("select o_bank_cc cc, count(*) n, avg((otype='B')::int) ob, avg((btype='B')::int) bb from t group by 1 having n>=20000 order by ob"))
E["cust_country_match"] = rec(df("""select 'ordering' side, avg((o_cust_cc=o_bank_cc)::int) FILTER (WHERE o_cust_cc<>'') match_bank, avg((o_cust_cc<>'')::int) has_cc from t
  union all select 'beneficiary', avg((b_cust_cc=b_bank_cc)::int) FILTER (WHERE b_cust_cc<>''), avg((b_cust_cc<>'')::int) from t"""))
E["country_dist_compare"] = rec(df("""with o as (select o_bank_cc cc, count(*)/1e7 o_bank from t group by 1), b as (select b_bank_cc cc, count(*)/1e7 b_bank from t group by 1),
  c as (select b_cust_cc cc, count(*) / (select count(*) from t where b_cust_cc<>'') b_cust from t where b_cust_cc<>'' group by 1)
  select cc, coalesce(o_bank,0) o_bank, coalesce(b_bank,0) b_bank, coalesce(b_cust,0) b_cust from c full join o using(cc) full join b using(cc)
  order by greatest(coalesce(o_bank,0), coalesce(b_cust,0)) desc limit 16"""))
E["acct_activity"] = rec(df("""with x as (select oacc, count(*) n from t group by 1) select floor(log10(n))::int l, count(*) accts, sum(n) tx from x group by 1 order by 1"""))
FULL = _p(FULL_PQ)
tk = df(f"""select ORDERING_TYPE ty, list_distinct(regexp_extract_all(ORDERING_TOKENS, '<([a-z_]+)[:>]', 1)) tl from '{FULL}' using sample 500000""")
rows = []
for ty, g in tk.groupby("ty"):
    from collections import Counter
    c = Counter(tok for tl in g.tl for tok in tl)
    for tok, n in c.items():
        rows.append({"ty": ty, "tok": tok, "share": n / len(g)})
E["token_presence"] = rows

# ---------- 7. ANOMALIES ----------
E["anom_profile"] = rec(df("""select coalesce(anom,'NORMAL') a, count(*) n, avg((otype='B')::int) oB, avg((btype='B')::int) bB, median(amt) med_amt,
  median(dur) med_dur from t group by 1 order by n"""))
E["romance_steps"] = rec(df("""with g as (select t.* from t join (select distinct oacc,bacc from t where anom='ROMANCE_SCAM') k using(oacc,bacc)),
  x as (select *, row_number() over (partition by oacc,bacc order by epoch) k, count(*) over (partition by oacc,bacc) n from g)
  select k, avg(ln(amt)) mlog, count(*) c from x group by 1 order by 1"""))
E["romance_series"] = rec(df("""with x as (select oacc,bacc,count(*) n from t where anom='ROMANCE_SCAM' group by 1,2) select n, count(*) series from x group by 1 order by 1"""))
E["romance_gap"] = rec(df("""with x as (select epoch - lag(epoch) over (partition by oacc,bacc order by epoch) gap from t where anom='ROMANCE_SCAM')
  select quantile_cont(gap,[.25,.5,.75]) q, avg(gap) mean from x where gap is not null"""))
E["romance_sender_cc"] = rec(df("select o_bank_cc cc, count(*) n from t where anom='ROMANCE_SCAM' group by 1 order by 2 desc limit 8"))
E["dup_groups"] = rec(df("""with x as (select oacc,bacc,amt, count(*) n, max(epoch)-min(epoch) span, count(distinct path) np, count(distinct dur) nd from t where anom='DUPLICATE_PAYMENT' group by all)
  select n, count(*) ngroups, max(span) max_span, median(span) med_span, max(np) max_paths, max(nd) max_durs from x group by 1 order by 1"""))
con.execute("CREATE TABLE ce AS SELECT o_bank_cc, avg(ln(amt) - (6 + 2*(otype='B')::int + 2*(btype='B')::int)) ce FROM t WHERE anom IS NULL GROUP BY 1")
ff = df("""select (ln(amt) - (6 + 2*(otype='B')::int + 2*(btype='B')::int) - ce)/ln(10) r from t join ce using(o_bank_cc) where anom='FAT_FINGER_MISTAKE'""")
h, e = np.histogram(ff.r, bins=np.arange(-4.5, 6.5, 0.5))
E["fat_finger_hist"] = [{"lb": float(a), "n": int(b)} for a, b in zip(e[:-1], h)]
nn = df("""select (ln(amt) - (6 + 2*(otype='B')::int + 2*(btype='B')::int) - ce)/ln(10) r from t join ce using(o_bank_cc) where anom is null using sample 200000""")
h2, _ = np.histogram(nn.r, bins=e)
E["normal_resid_hist"] = [{"lb": float(a), "n": int(b)} for a, b in zip(e[:-1], h2)]
E["fat_finger_up_share"] = float((ff.r > 0).mean())
E["mule"] = rec(df("""with s as (select * from t where anom in ('CEO_SCAM','ACCOUNT_REPLACEMENT_SCAM','CUSTOMER_RECALL','FAT_FINGER_MISTAKE')),
  b as (select bacc, sum((anom is null)::int) n_clean, count(distinct oacc) ns from t where bacc in (select bacc from s) group by 1)
  select s.anom a, count(*) n, avg((b.n_clean=0)::int) only_anom_bacc, median(b.ns) med_senders from s join b using(bacc) group by 1"""))
E["scam_bank"] = rec(df("""select coalesce(anom,'NORMAL') a, avg((o2.s>0.9)::int) slow_o, avg((b2.s>0.9)::int) slow_b, median(b2.n) bene_bank_size
  from t join ob o2 on o2.b=obic join bb b2 on b2.b=bbic group by 1 order by 1"""))


# ---------- NEW: endpoint swap, Simpson check, detectors ----------
E["endpoint_swap"] = rec(df("""with x as (select list_filter(string_split(path,';'),x->x<>'...') k, obic, bbic from t)
  select (k[1]<>obic) first_differs, (k[-1]<>bbic) last_differs, count(*) n from x group by 1,2 order by 1,2"""))
E["swap_by_anom"] = rec(df("""with x as (select coalesce(anom,'NORMAL') a, list_filter(string_split(path,';'),x->x<>'...') k, obic, bbic from t)
  select a, avg((k[1]<>obic)::int) p_first, avg((k[-1]<>bbic)::int) p_last, count(*) n from x group by 1 order by 1"""))
E["simpson_hour"] = rec(df("""WITH ob AS (SELECT obic b, avg((dur>120)::INT) s FROM t WHERE pc=2 GROUP BY 1 HAVING count(*)>=30),
  bb AS (SELECT bbic b, avg((dur>120)::INT) s FROM t WHERE pc=2 GROUP BY 1 HAVING count(*)>=30),
  x AS (SELECT t.*, (dur>120)::INT y FROM t JOIN ob ON ob.b=obic JOIN bb ON bb.b=bbic WHERE pc=2 AND ob.s<.95 AND bb.s<.95),
  fe AS (SELECT *, y - avg(y) OVER (PARTITION BY obic) - avg(y) OVER (PARTITION BY bbic) + avg(y) OVER () r FROM x)
  SELECT hr, avg(y) raw, avg(r) adjusted, count(*) n FROM fe GROUP BY 1 ORDER BY 1"""))
E["dup_detector"] = rec(df("""with g as (select oacc,bacc,amt,path,dur from t group by all having count(*)>1 and max(epoch)-min(epoch)<=7200)
  select coalesce(t.anom,'NORMAL') a, count(*) n from t join g using(oacc,bacc,amt,path,dur) group by 1 order by 2 desc"""))
E["romance_detector"] = rec(df("""with s as (select oacc,bacc from t where otype='C' group by 1,2 having count(*)>=3 and max(epoch)-min(epoch)<=4200 and corr(epoch, ln(amt))>0.5)
  select coalesce(t.anom,'NORMAL') a, count(*) n from t join s using(oacc,bacc) group by 1 order by 2 desc"""))
E["corridors"] = rec(df("""select o_bank_cc o, b_bank_cc b, count(*) n, median(amt) med_amt, avg((ttype='Direct')::int) direct, median(dur) med_dur,
  avg(fx) fx, count(*) filter (where anom is not null) anomalies from t group by 1,2 order by n desc limit 300"""))

with open(EVIDENCE / "evidence.json", "w") as f:
    json.dump(E, f, default=float)
print("evidence.json written; keys:", len(E))
