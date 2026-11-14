"""Browser data layer for the web platform (web/dist/data/*.json).

Run: python -m src.webdata   (after validation/register/atlas/lineage)
The browser never receives row-level records. Interactive analysis runs on additive cubes whose cells carry their own
binned distributions, so any filter combination re-aggregates exactly (counts, sums, sums of squares, histogram bins).

Files
  meta.json         dataset summary, field dictionary, data-quality checks, lineage, recent pipeline activity
  explorer.json     10-dimension cube: ttype·currency·anomaly·sender·receiver·participants·fx·continuity·manual·period
                    measures n, Σln(amt), Σln(amt)², Σdur, amount histogram (log10, 0.5 bins), duration histogram (log2 bins)
  temporal.json     daily × ttype × anomaly × sender × receiver cube (time filters) + local hour / weekday profiles
  routes.json       country-level route patterns with type, currency, continuity, participants, duration stats
  institutions.json top 600 banks: volumes by role, STP rate, cover propensity, business shares
  tokens.json       token presence by side × party type × anomaly (500k-row sample of the text columns)
  registry.json     34 validated rules + rejected candidates, six-level confidence with criteria, violations, related rules
  tests.json        hypothesis-test register with Benjamini–Hochberg adjustment
  sim.json          parameters of the reconstructed generator for the scenario simulator (all estimated from the data)
"""
from __future__ import annotations
import json, math, re, datetime as dt
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from .config import connect, ROOT, EVIDENCE, FINDINGS, FULL_PQ, _p

OUT = ROOT / "web" / "build_data"
OUT.mkdir(parents=True, exist_ok=True)
con = connect()
df = lambda s: con.execute(s).df()
J = lambda f: json.loads((EVIDENCE / f).read_text(encoding="utf-8"))
VAL, REG, AT, LI, ST, GR, FO, DI, EV = (J(f) for f in ("validation.json", "register.json", "atlas.json", "lineage.json", "stats.json",
                                                         "graph.json", "forensics.json", "discovery.json", "evidence.json"))
AMT_EDGES = np.arange(-2, 10.5, .5)          # log10 USD bins: [-2,-1.5), ... [10,10.5)
DUR_EDGES = np.arange(1, 16)                 # log2 seconds bins: floor(log2(dur)) in 1..15


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, separators=(",", ":"), default=float), encoding="utf-8")
    return (OUT / name).stat().st_size


def compact(d: pd.DataFrame):
    return {"cols": list(d.columns), "rows": d.values.tolist()}


con.execute("CREATE OR REPLACE TEMP TABLE topc AS SELECT cur FROM t GROUP BY 1 ORDER BY count(*) DESC LIMIT 12")
# ---------------------------------------------------------------- explorer cube
nab, ndb = len(AMT_EDGES) - 1, len(DUR_EDGES)
amt_idx = "least(greatest(floor((log10(amt)+2)/0.5)::INT,0),{})".format(nab - 1)
dur_idx = "least(greatest(floor(log2(dur))::INT,1),15)-1"
base = df(f"""SELECT ttype, CASE WHEN cur IN (SELECT cur FROM topc) THEN cur ELSE 'Other' END cur, coalesce(anom,'NORMAL') anom, otype, btype,
   least(pc,6) pc, least(fx,3) fx, cont, (dur>120)::INT manual, CASE WHEN d < DATE '2023-06-15' THEN 'P1' ELSE 'P2' END period,
   {amt_idx} ab, {dur_idx} db, count(*) n, sum(ln(amt)) s1, sum(ln(amt)*ln(amt)) s2, sum(dur) sd
   FROM t GROUP BY ALL""")
keys = ["ttype", "cur", "anom", "otype", "btype", "pc", "fx", "cont", "manual", "period"]
g = base.groupby(keys)
cells = g[["n", "s1", "s2", "sd"]].sum().reset_index()
ah = base.pivot_table(index=keys, columns="ab", values="n", aggfunc="sum", fill_value=0).reindex(columns=range(nab), fill_value=0)
dh = base.pivot_table(index=keys, columns="db", values="n", aggfunc="sum", fill_value=0).reindex(columns=range(ndb), fill_value=0)
cells = cells.set_index(keys).join(ah.add_prefix("a")).join(dh.add_prefix("d")).reset_index()
assert int(cells.n.sum()) == 10_000_000
cells["s1"] = cells.s1.round(4); cells["s2"] = cells.s2.round(3)
explorer = dict(dims=keys, amt_edges=AMT_EDGES.tolist(), dur_edges=DUR_EDGES.tolist(), nab=nab, ndb=ndb,
                labels={"ttype": "Routing type", "cur": "Currency", "anom": "Anomaly label", "otype": "Sender type", "btype": "Receiver type",
                        "pc": "Participants (6 = 6+)", "fx": "FX conversions (3 = 3+)", "cont": "Continuity flag", "manual": "Manual step (>120 s)", "period": "Period (P1 < 15 Jun ≤ P2)"},
                **compact(cells))
sizes = {"explorer.json": dump("explorer.json", explorer)}

# ---------------------------------------------------------------- temporal cube + profiles
tc = df("""SELECT strftime(d,'%Y-%m-%d') d, dayofweek(d) dow, ttype, coalesce(anom,'NORMAL') anom, otype, btype, count(*) n, sum(ln(amt)) s1,
           sum((dur>120)::INT) nm, sum(dur) sd FROM t GROUP BY ALL ORDER BY 1""")
tc["s1"] = tc.s1.round(3)
temporal = dict(cube=compact(tc), local_hour=EV["local_hour"], local_dow=EV["local_dow"], utc_hour=EV["utc_hour_by_country"],
                weekly=EV["weekly"], offsets=EV["offsets"], change_points=FO["change_points"])
sizes["temporal.json"] = dump("temporal.json", temporal)

# ---------------------------------------------------------------- route patterns (country level, aggregated) + institutions
rp = df("""SELECT ttype, array_to_string(list_transform(list_filter(string_split(path,';'),x->x<>'...'), b -> substr(b,5,2)), ' › ') route,
   CASE WHEN cur IN (SELECT cur FROM topc) THEN cur ELSE 'Other' END cur, cont, pc, count(*) n, median(dur) med_dur, quantile_cont(dur,.9) p90_dur,
   avg(fx) fx, avg((dur>120)::INT) manual, median(amt) med_amt FROM t GROUP BY ALL HAVING count(*) >= 150 ORDER BY n DESC""")
coverage = float(rp.n.sum() / 1e7)
rp = rp.round({"med_dur": 0, "p90_dur": 0, "fx": 3, "manual": 3, "med_amt": 2})
sizes["routes.json"] = dump("routes.json", dict(coverage=coverage, min_n=150, **compact(rp)))
inst = df("""WITH s AS (SELECT obic b, count(*) sent, avg((otype='B')::INT) sender_b, avg(CASE WHEN ttype<>'Direct' THEN (ttype='Covered')::INT END) cover_share,
      avg(CASE WHEN pc=2 THEN (dur>120)::INT END) manual_pc2 FROM t GROUP BY 1),
  r AS (SELECT bbic b, count(*) received, avg((btype='B')::INT) receiver_b FROM t GROUP BY 1),
  i AS (SELECT lst[k] b, count(*) as_intermediary FROM (SELECT list_filter(string_split(path,';'),x->x<>'...') lst FROM t WHERE ttype<>'Direct'), range(2,len(lst)) r(k) GROUP BY 1)
  SELECT b bic, substr(b,5,2) cc, coalesce(sent,0) sent, coalesce(received,0) received, coalesce(as_intermediary,0) as_intermediary,
         sender_b, receiver_b, cover_share, manual_pc2 FROM s FULL JOIN r USING(b) FULL JOIN i USING(b)
  ORDER BY coalesce(sent,0)+coalesce(received,0)+coalesce(as_intermediary,0) DESC LIMIT 600""").round(4)
hubs = {h["b"]: h["pagerank"] for h in GR["top_hubs"]}
sizes["institutions.json"] = dump("institutions.json", dict(total_banks=int(GR["network"]["nodes"]), network=GR["network"], concentration=GR["concentration"],
                                                           strength_ccdf=GR["strength_ccdf"], hub_stp=GR["hub_stp"], top_hubs=GR["top_hubs"], loops=GR["G3_loops"],
                                                           pairing=GR["G1_pairing"], country=GR["G2_country"], flow=GR["flow_matrix_top"], **compact(inst)))

# ---------------------------------------------------------------- tokens (text features, sample)
tk = df(f"""SELECT ORDERING_TYPE ot, BENEFICIARY_TYPE bt, coalesce(ANOMALY_TYPE,'NORMAL') an,
      list_distinct(regexp_extract_all(ORDERING_TOKENS, '<([a-z_]+)[:>]', 1)) o, list_distinct(regexp_extract_all(BENEFICIARY_TOKENS, '<([a-z_]+)[:>]', 1)) b,
      len(string_split(ORDERING_DETAILS, chr(10))) ol, ORDERING_DETAILS LIKE '%' || chr(10) || '1/%' os, ORDERING_DETAILS LIKE '//%' odbl
      FROM '{_p(FULL_PQ)}' USING SAMPLE 500000 ROWS (reservoir, 5)""")
rows = []
for side, col, ty in (("ordering", "o", "ot"), ("beneficiary", "b", "bt")):
    for grp, gdf in tk.groupby(ty):
        cnt = {}
        for lst in gdf[col]:
            for x in lst:
                cnt[x] = cnt.get(x, 0) + 1
        rows += [dict(side=side, party=grp, token=k, share=v / len(gdf), n=len(gdf)) for k, v in cnt.items()]
an_rows = []
for an, gdf in tk.groupby("an"):
    cnt = {}
    for lst in gdf["o"]:
        for x in lst:
            cnt[x] = cnt.get(x, 0) + 1
    an_rows += [dict(anom=an, token=k, share=v / len(gdf), n=len(gdf)) for k, v in cnt.items()]
co_tokens = ["business", "company_keyword", "first_name", "last_name", "street", "city", "post_code", "country_code", "country_name", "iban", "line_break", "finance_word"]
M = np.zeros((len(co_tokens), len(co_tokens)))
for lst in tk["o"]:
    s_ = set(lst); v = np.array([t_ in s_ for t_ in co_tokens], float); M += np.outer(v, v)
M /= len(tk)
sizes["tokens.json"] = dump("tokens.json", dict(sample=len(tk), presence=rows, by_anomaly=an_rows, cooc_tokens=co_tokens, cooc=M.round(4).tolist(),
                                               lines=tk.ol.value_counts().sort_index().to_dict(), structured_share=float(tk.os.mean()), double_slash_share=float(tk.odbl.mean())))

# ---------------------------------------------------------------- registry: confidence levels, violations, related, rejected candidates
GROUPS = {"Temporal": ["T1", "T3", "T4", "T4b"], "Currency & Value": ["C1", "C3", "A1", "A2", "A3", "F1"], "Institution": ["R5", "R5b", "G1", "P5", "R3"],
          "Route": ["R1", "R4", "R6", "G3", "R3"], "Duration & Continuity": ["D1", "D2", "D3", "R7", "R4"], "FX & Participant": ["C2", "R6", "C3"],
          "Transaction Type": ["R1", "R2"], "Party Details": ["P4", "P1b", "P2"], "Token": ["P2", "P1b"], "Anomaly": ["X1", "X2", "X3", "X4", "X5", "X6"]}
PRIMARY = {"T1": "Temporal", "T3": "Temporal", "T4": "Temporal", "T4b": "Temporal", "C1": "Currency & Value", "C3": "Currency & Value", "A1": "Currency & Value",
           "A2": "Currency & Value", "A3": "Currency & Value", "F1": "Currency & Value", "R5": "Institution", "R5b": "Institution", "G1": "Institution", "P5": "Institution",
           "R3": "Route", "R1": "Route", "R4": "Route", "R6": "FX & Participant", "G3": "Route", "D1": "Duration & Continuity", "D2": "Duration & Continuity",
           "D3": "Duration & Continuity", "R7": "Duration & Continuity", "C2": "FX & Participant", "R2": "Transaction Type", "P4": "Party Details", "P1b": "Party Details",
           "P2": "Token", "X1": "Anomaly", "X2": "Anomaly", "X3": "Anomaly", "X4": "Anomaly", "X5": "Anomaly", "X6": "Anomaly"}
from .levels import CRITERIA, VALIDATED, INCONCLUSIVE as INCONCL, level as _lv


def level(r):
    return _lv(r["id"], r["confidence"])


def violation(r):
    m = r["metrics"]; f = m.get("full", {}) if isinstance(m, dict) else {}
    if "exceptions" in f: return dict(rate=f["exceptions"] / f["n"], text=f"{int(f['exceptions'])} of {int(f['n']):,} rows violate the exact rule")
    if "share_exact" in f: return dict(rate=1 - f["share_exact"], text=f"{(1 - f['share_exact']) * f.get('n', 1e7):,.0f} violating rows")
    if "in_route_share" in f: return dict(rate=1 - f["in_route_share"], text=f"{(1 - f['in_route_share']):.2%} of payments use a currency of no route bank")
    if "home_share" in f: return dict(rate=1 - f["home_share"], text=f"{1 - f['home_share']:.1%} not in the instructing bank's home currency (explained by C3)")
    if "max_abs_dev" in f: return dict(rate=None, text=f"largest deviation from the formula {f['max_abs_dev']:.4f}")
    if "max_rel_err" in f: return dict(rate=None, text=f"largest relative error {f['max_rel_err']:.1%}")
    if "o_prefix" in f: return dict(rate=1 - f["o_prefix"], text=f"IBAN prefix mismatches: {(1 - f['o_prefix']):.4%}")
    return dict(rate=None, text=r.get("counterexamples", ""))


related = {}
for e in AT["edges"]:
    for a in e["rules"]:
        related.setdefault(a, set()).update(x for x in e["rules"] if x != a)
CHARTS = {"T1": ["time_localhour"], "T3": ["time_weekday"], "T4": ["time_daily"], "T4b": ["change_points"], "C1": ["ccy_mix"], "C2": ["fx_heat"], "C3": ["ccy_mix"],
          "A1": ["amt_segments"], "A2": ["amt_country"], "A3": ["stat_qq", "stat_hill"], "F1": ["f1_cents"], "R1": ["hops"], "R4": ["gaps"], "R5": ["endpoint_swap"],
          "R5b": ["endpoint_swap"], "G3": ["graph_loops"], "G1": ["graph_pairs"], "R3": ["graph_hubs"], "D1": ["dur_class", "dur_hist"], "D2": ["simpson"],
          "D3": ["dur_hist"], "P1b": ["tokens"], "P4": ["country_compare"], "X1": ["romance"], "X3": ["fatfinger"], "X4": ["mule"], "X5": ["recall"], "X2": ["anomaly_profile"],
          "X6": ["anomaly_profile"], "P5": ["tokens"], "P2": ["tokens"], "R2": ["hops"], "R6": ["fx_heat"], "R7": ["gaps"]}
ALT = {"C2": "FX = distinct currencies on route (91.7% on all rows); payment-currency start + borders (93.5%)", "R1": "Poisson hop counts (successive ratios not constant)",
       "R3": "intermediaries from the payment-currency zone (only 17% are)", "D2": "off-hours queuing (hour effect vanishes with bank fixed effects); large-amount review (reversed)",
       "T3": "Fri–Sat weekend for Gulf/Israel (identical shape)", "R2": "constant 11.3% Covered share (rejected: 3–50% by sending country, bank propensity)",
       "C3": "currency chosen before routing (cannot be excluded; route-first is the more parsimonious reading)", "X4": "account-replacement reuses payee name with swapped account (1/649)",
       "X5": "any of 11 tested features differs from normal (none after Bonferroni)", "R5": "random label noise (rejected: swapped BIC predicts currency and clock)",
       "A2": "beneficiary-country wealth effect (sd 0.23 vs 1.09)", "G1": "configuration-model pairing (χ²/dof 125–358)", "F1": "amounts drawn directly in USD (USD-only roundness contradicts)"}
reg = []
for r in REG:
    o = {k: r[k] for k in ("id", "title", "type", "status", "criterion", "confidence", "group", "hypothesis", "fields", "method", "counterexamples", "limitations",
                           "economic", "formulation", "logic", "sample_size", "effect_size", "validation", "metrics")}
    o.update(level=level(r), family=PRIMARY[r["id"]], tags=[gname for gname, ids in GROUPS.items() if r["id"] in ids], violation=violation(r),
             related=sorted(related.get(r["id"], [])), charts=CHARTS.get(r["id"], []), alternative=ALT.get(r["id"], "—"), kind="rule")
    reg.append(o)
HYP = []
for line in (FINDINGS / "hypotheses.md").read_text(encoding="utf-8").splitlines():
    m = re.match(r"\|\s*(H\d+)\s*\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|", line)
    if m:
        HYP.append(dict(id=m.group(1), hypothesis=m.group(2).strip(), test=m.group(3).strip(), outcome=m.group(4).strip(), consequence=m.group(5).strip()))
rejected = [h for h in HYP if h["outcome"].lower().startswith(("rejected", "**rejected", "not supported", "partly"))]
for h in rejected:
    reg.append(dict(id=h["id"], title=h["hypothesis"], kind="rejected-candidate", level="REJECTED", family="—", tags=[], type="—", status="REJECTED",
                    hypothesis=h["hypothesis"], method=h["test"], effect_size=h["outcome"], formulation=h["hypothesis"], logic=h["test"], validation=h["outcome"],
                    counterexamples=h["outcome"], limitations="—", economic="—", criterion="—", confidence="—", group="—", fields="—", sample_size="10,000,000",
                    violation=dict(rate=None, text=h["outcome"]), related=[], charts=[], alternative=h["consequence"], metrics={}))
sizes["registry.json"] = dump("registry.json", dict(levels=CRITERIA, groups=GROUPS, generated=VAL["generated"], rules=reg, hypotheses=HYP))

# ---------------------------------------------------------------- hypothesis-test register with Benjamini–Hochberg
tests = []
x5 = next(r for r in VAL["rules"] if r["id"] == "X5")["metrics"]
for k, v in x5.items():
    if "p" in v:
        tests.append(dict(family="X5 recall vs normal", test=f"{k}: two-proportion z" if "z" in v else f"{k}: Mann–Whitney U", p=v["p"],
                          effect=(f"z = {v['z']:.2f}; Δ = {v['recall'] - v['normal']:+.4f}" if "z" in v else "rank test on ln-amount residual"), n="317 vs 9,992,994"))
for pr in DI["pairs"]:
    n = DI["dev_rows"]; v = pr["v_dev"]
    # χ² from Cramér's V needs table shape; report effect size and a conservative χ² with df = 1 (lower bound on evidence)
    chi2 = v * v * n
    tests.append(dict(family="Discovery pair scan (dev half)", test=f"{pr['a']} × {pr['b']}: χ² independence", p=float(stats.chi2.sf(chi2, 1)), effect=f"Cramér's V = {v:.4f}", n=f"{n:,}"))
for c in FO["ci_tests"]:
    tests.append(dict(family="Conditional independence (2M sample)", test=f"{c['x']} ⟂ {c['y']} | {c['given']}", p=None, effect=f"Cramér's V = {c['cramers_v']:.4f}", n="2,000,000"))
def bh(pvals):
    """Benjamini–Hochberg adjusted p-values (step-up), applied WITHIN a test family."""
    p_ = np.asarray(pvals, float); m = len(p_); o = np.argsort(p_)
    q = p_[o] * m / (np.arange(m) + 1); q = np.minimum.accumulate(q[::-1])[::-1].clip(max=1)
    out = np.empty(m); out[o] = q; return out


m_ = 0
for fam in sorted({t_["family"] for t_ in tests}):
    idx = [i for i, t_ in enumerate(tests) if t_["family"] == fam and t_["p"] is not None]
    if idx:
        m_ += len(idx)
        for i, a in zip(idx, bh([tests[i]["p"] for i in idx])):
            tests[i]["p_bh"] = float(a); tests[i]["significant_bh_05"] = bool(a < .05); tests[i]["family_size"] = len(idx)
for t_ in tests:
    t_.setdefault("p_bh", None); t_.setdefault("significant_bh_05", None); t_.setdefault("family_size", None)
sizes["tests.json"] = dump("tests.json", dict(note="With n in the millions almost every p-value is tiny; decisions are made on effect sizes. BH is applied within each test family (pooling unrelated families would let a weak test borrow strength from thousands of near-zero p-values).",
                                              m=int(m_), tests=tests))

# ---------------------------------------------------------------- simulator parameters (all estimated from the data)
f = lambda rid: next(r for r in VAL["rules"] if r["id"] == rid)["metrics"]
r1, r4, r2, a1, a2 = f("R1")["full"], f("R4")["full"], f("R2")["full"], f("A1")["full"], f("A2")["full"]
pc2_manual = float(con.execute("SELECT avg((dur>120)::INT) FROM t WHERE pc=2").fetchone()[0])
m_bank = 1 - math.sqrt(1 - pc2_manual)          # per-bank manual probability that reproduces the pc=2 manual share under independence
ce = pd.DataFrame(EV["amt_country"])
sim = dict(
    route=dict(q=r1["q_mle"], p_link=r4["p_link_mle"], cover_bank_share=float(r2["cover_banks"] / (r2["cover_banks"] + r2["other_banks"])),
               cover_share_cover_banks=r2["oos_cover_banks_share"], cover_share_other=r2["oos_other_banks_share"], pooled_cover=r2["pooled_covered_share"]),
    amount=dict(intercept=a1["intercept"], b_sender=a1["effect_ordering_B"], b_receiver=a1["effect_beneficiary_B"], interaction=a1["interaction"],
                sd_noise=math.sqrt(ST["amount_residual"]["sd"] ** 2), sd_bank=math.sqrt(0.2197), country=ce[["cc", "eff", "n"]].to_dict("records")),
    duration=dict(fast_shape=ST["fast_step"]["gamma_shape"] / 2, fast_scale=ST["fast_step"]["gamma_scale"], manual_shape=ST["manual_step"]["gamma_shape"],
                  manual_scale=ST["manual_step"]["gamma_scale"], m_bank=m_bank, pc2_manual_observed=pc2_manual),
    support=dict(pc_max_observed=22, pc_reliable_max=9, note="Simulation outside pc 2–9 or outside observed country effects is extrapolation."),
    sources={"q": "R1 MLE", "p_link": "R4 MLE", "cover": "R2 out-of-sample classes", "amount": "A1 cell means, A2 country effects, residual sd (stats.json)",
             "duration": "D3 gamma fits (two fast steps → per-bank shape halved); m_bank solves 1-(1-m)² = observed pc=2 manual share"})
sizes["sim.json"] = dump("sim.json", sim)

# ---------------------------------------------------------------- meta: dataset summary, dictionary, quality, lineage, activity
q1 = con.execute("""SELECT count(*), count(DISTINCT cur), min(ts), max(ts), count(DISTINCT obic), count(DISTINCT bbic), count(*) FILTER (WHERE anom IS NOT NULL),
   count(*) FILTER (WHERE NOT regexp_full_match(cur,'[A-Z]{3}')), count(*) FILTER (WHERE NOT regexp_full_match(obic,'[0-9]{4}[A-Z]{2}[0-9A-Z]{2}')),
   count(*) FILTER (WHERE NOT regexp_full_match(bbic,'[0-9]{4}[A-Z]{2}[0-9A-Z]{2}')), count(*) FILTER (WHERE amt <= 0), count(*) FILTER (WHERE dur <= 0),
   count(*) FILTER (WHERE pc <> path_n - gaps), count(*) FILTER (WHERE (cont='N') <> (gaps>0)), count(*) FILTER (WHERE cont NOT IN ('Y','N')),
   count(*) FILTER (WHERE ttype NOT IN ('Direct','Indirect','Covered')), count(*) FILTER (WHERE otype NOT IN ('B','C') OR btype NOT IN ('B','C')),
   count(*) FILTER (WHERE path LIKE '%;;%' OR path LIKE ';%' OR path LIKE '%;'), count(DISTINCT oacc), count(DISTINCT bacc) FROM t""").fetchone()
dupe = con.execute("SELECT count(*) - count(DISTINCT (epoch, oacc, bacc, amt, cur, path, dur)) FROM t").fetchone()[0]
nulls = con.execute(f"""SELECT {', '.join(f"count(*) FILTER (WHERE {c} IS NULL OR CAST({c} AS VARCHAR)='')" for c in
                     ['EPOCH_SECONDS', 'CURRENCY_CODE', 'USD_AMOUNT', 'ORDERING_BIC8', 'BENEFICIARY_BIC8', 'BIC8_PATH', 'TOTAL_DURATION', 'CONTINUITY_QFLAG',
                      'CURRENCY_CONVERSION_COUNT', 'PARTICIPANT_COUNT', 'TRANSACTION_TYPE_CODE', 'ORDERING_ACCOUNT', 'BENEFICIARY_ACCOUNT', 'ORDERING_DETAILS',
                      'ORDERING_TOKENS', 'BENEFICIARY_DETAILS', 'BENEFICIARY_TOKENS', 'ORDERING_TYPE', 'BENEFICIARY_TYPE', 'ANOMALY_TYPE'])} FROM '{_p(FULL_PQ)}'""").fetchone()
FIELDS = [("EPOCH_SECONDS", "integer (Unix s, UTC)", "1,682,853,746 – 1,690,797,361", "raw", "time features; T1–T4b", "ts, date, UTC hour, local hour", "UTC only; local clock reconstructed (T1)"),
          ("CURRENCY_CODE", "string, ISO 4217", "85 codes", "raw", "C1, C3, F1", "home currency of route banks", "home-currency map inferred from data"),
          ("USD_AMOUNT", "decimal (USD)", "0.01 – 15,664,132,213.09", "raw", "A1–A3, F1, X3", "ln(amount)", "normalised; original-currency amount absent"),
          ("ORDERING_BIC8", "string NNNN·CC·LL", f"{q1[4]:,} banks", "raw", "R5, R5b, P2, P5, G1", "bank country", "account-servicing bank; 5% differ from path[1]"),
          ("BENEFICIARY_BIC8", "string NNNN·CC·LL", f"{q1[5]:,} banks", "raw", "R5, P4, P5, G1", "bank country", "5% differ from last path BIC"),
          ("BIC8_PATH", "string, ';'-separated", "2–22 known BICs; '...' = hidden", "raw", "R1–R7, C2, C3, G3", "known BICs, gaps, route countries", "hidden hops unobservable"),
          ("TOTAL_DURATION", "integer seconds", "2 – 21,649", "raw", "D1–D3", "manual flag (>120 s)", "elapsed time to completion or observation end; not proven settlement time"),
          ("CONTINUITY_QFLAG", "Y / N", "N on 7.7%", "derived in generator", "R7, R4", "—", "observability marker, not success/failure"),
          ("CURRENCY_CONVERSION_COUNT", "integer", "0–17", "derived in generator", "C2", "—", "= currency borders on known path"),
          ("PARTICIPANT_COUNT", "integer", "2–22", "derived in generator", "R6, R1", "K = pc − 2", "counts known BICs only"),
          ("TRANSACTION_TYPE_CODE", "Direct/Indirect/Covered", "63.2 / 32.6 / 4.2%", "raw", "R1, R2", "—", "—"),
          ("ORDERING_ACCOUNT", "string _FAKE_…", f"{q1[18]:,} accounts", "raw", "P2, X-detectors", "IBAN flag", "synthetic identifiers"),
          ("BENEFICIARY_ACCOUNT", "string _FAKE_…", f"{q1[19]:,} accounts", "raw", "P2, X4", "IBAN flag", "synthetic identifiers"),
          ("ORDERING_DETAILS", "free text, multi-line", "≤ 4×35 MT layout", "raw", "P2, P4", "structured flag, line count", "synthetic Faker-style text"),
          ("ORDERING_TOKENS", "engineered token string", "<type:len> tokens", "derived (engineered)", "P1b, P4", "token presence", "pattern summaries, not original content"),
          ("BENEFICIARY_DETAILS", "free text, multi-line", "≤ 4×35 MT layout", "raw", "P4", "structured flag", "synthetic"),
          ("BENEFICIARY_TOKENS", "engineered token string", "<type:len> tokens", "derived (engineered)", "P4", "address country token", "pattern summaries"),
          ("ORDERING_TYPE", "B / C", "78.7% B", "raw", "A1, P5, X1, X4", "—", "—"), ("BENEFICIARY_TYPE", "B / C", "28.8% B", "raw", "A1, P1b, P5", "—", "—"),
          ("ANOMALY_TYPE", "label or empty", "6 labels, 7,006 rows", "raw", "X1–X6", "NORMAL = empty", "CUSTOMER_RECALL undocumented by organiser")]
dictionary = [dict(field=a, dtype=b, observed=c, origin=d, rules=e, derived=f_, limitation=g_, missing=int(nm_)) for (a, b, c, d, e, f_, g_), nm_ in zip(FIELDS, nulls)]
quality = [dict(check="Rows parsed (RFC-4180, multi-line fields)", result="10,000,000", status="pass", detail="row count asserted after every stage"),
           dict(check="Exact duplicate rows (time, accounts, amount, currency, path, duration)", result=f"{int(dupe):,}", status="pass" if dupe == 0 else "info", detail="the one exact duplicate is a labelled DUPLICATE_PAYMENT pair sent in the same second (0-s gap), consistent with rule X2; kept"),
           dict(check="Currency codes not 3 upper-case letters", result=f"{q1[7]:,}", status="pass" if q1[7] == 0 else "fail", detail="regex [A-Z]{3}"),
           dict(check="ORDERING_BIC8 failing NNNN·CC·LL grammar", result=f"{q1[8]:,}", status="pass" if q1[8] == 0 else "fail", detail="regex"),
           dict(check="BENEFICIARY_BIC8 failing grammar", result=f"{q1[9]:,}", status="pass" if q1[9] == 0 else "fail", detail="regex"),
           dict(check="Non-positive amounts / durations", result=f"{q1[10]:,} / {q1[11]:,}", status="pass" if q1[10] + q1[11] == 0 else "fail", detail="domain check"),
           dict(check="PARTICIPANT_COUNT ≠ known BICs in path", result=f"{q1[12]:,}", status="pass" if q1[12] == 0 else "fail", detail="rule R6"),
           dict(check="CONTINUITY_QFLAG inconsistent with '...'", result=f"{q1[13]:,}", status="pass" if q1[13] == 0 else "fail", detail="rule R7"),
           dict(check="Unexpected categorical values (flag / type / party)", result=f"{q1[14] + q1[15] + q1[16]:,}", status="pass" if q1[14] + q1[15] + q1[16] == 0 else "fail", detail="domain sets"),
           dict(check="Malformed path separators (';;', leading/trailing ';')", result=f"{q1[17]:,}", status="pass" if q1[17] == 0 else "fail", detail="route structure"),
           dict(check="Header BIC ≠ path endpoint", result="≈9.7% of rows", status="info", detail="explained by rule R5 (5% swap per end), not an error"),
           dict(check="Country token absent from party details", result="≈39% per side", status="info", detail="analysis uses BIC country as primary"),
           dict(check="Detail text beyond MT 4×35", result="0.17% of rows", status="info", detail="generator quirk, kept"),
           dict(check="DISCLAIMER column", result="1 non-empty row", status="info", detail="legal notice; dropped from analytic tables")]
activity = sorted([dict(when=a["modified"], what=f"{a['producer']} wrote {a['path']}", sha=a["sha256"][:12]) for a in LI["artefacts"]] +
                  [dict(when=VAL["generated"], what=f"src.validation: {sum(r['status'] == 'PASS' for r in VAL['rules'])}/{len(VAL['rules'])} validators PASS in {VAL['runtime_s']} s", sha="")],
                  key=lambda x: x["when"], reverse=True)
dists = {}
for col, sql in {"Routing type": "ttype", "Currency (top 12)": "CASE WHEN cur IN (SELECT cur FROM topc) THEN cur ELSE 'Other' END", "Participants": "least(pc,9)::VARCHAR",
                 "FX conversions": "least(fx,6)::VARCHAR", "Continuity": "cont", "Sender type": "otype", "Receiver type": "btype", "Anomaly label": "coalesce(anom,'NORMAL')",
                 "Hidden-hop count": "least(gaps,4)::VARCHAR", "UTC hour": "lpad(hr::VARCHAR,2,'0')", "UTC weekday": "dayname(d)", "Sender IBAN format": "o_iban::VARCHAR",
                 "Structured sender details": "o_struct::VARCHAR", "Amount decade (log10 USD)": "greatest(least(floor(log10(amt))::INT,9),-2)::VARCHAR",
                 "Duration (log2 s bin)": "lpad(least(floor(log2(dur))::INT,14)::VARCHAR,2,'0')"}.items():
    d_ = df(f"SELECT {sql} AS k, count(*) AS n FROM t GROUP BY 1 ORDER BY 1")
    dists[col] = d_.to_dict("records")
ce_ = [(k, v) for k, v in VAL["cross_check"].items() if k != "sample"]
meta = dict(generated=dt.datetime.now().isoformat(timespec="seconds"), rows=int(q1[0]), currencies=int(q1[1]), start=str(q1[2]), end=str(q1[3]),
            ordering_banks=int(q1[4]), beneficiary_banks=int(q1[5]), banks_total=int(GR["network"]["nodes"]), anomalies=int(q1[6]), feature_groups=10, columns_raw=21,
            sender_accounts=int(q1[18]), beneficiary_accounts=int(q1[19]), dictionary=dictionary, quality=quality, distributions=dists,
            lineage=dict(artefacts=LI["artefacts"], contract=LI["schema_contract"], contract_ok=LI["contract_ok"], environment=LI["environment"], pipeline=LI["pipeline"], raw=LI["raw"]),
            activity=activity, validation=dict(generated=VAL["generated"], runtime_s=VAL["runtime_s"], cross_check=VAL["cross_check"]),
            discovery=dict(features=DI["features"], dev_rows=DI["dev_rows"], val_rows=DI["val_rows"], pairs=DI["pairs"], trees=DI["trees"]),
            forensics={k: FO[k] for k in ("benford", "usd_roundness", "cents00_by_currency", "cents_by_segment", "second_uniform", "minute_uniform", "duration_last_digit",
                                          "bic", "iban_single_length_share", "local_account_templates", "fixed_rate_search", "ci_tests", "change_points")},
            stats={k: ST[k] for k in ("ci", "anomaly_rates", "amount_residual", "hill", "exceedance", "fast_step", "manual_step", "sensitivity_D1",
                                      "R1_by_country", "R1_by_segment", "R4_by_ttype", "detectors", "fat_finger_pr_curve", "fat_finger_pr_auc", "top_amounts")},
            evidence={k: EV[k] for k in ("anom_profile", "romance_steps", "romance_series", "dup_groups", "fat_finger_hist", "normal_resid_hist", "mule", "scam_bank",
                                         "amt_country", "endpoint_swap", "swap_by_anom", "simpson_hour", "local_ccy_by_country", "vehicle_ccy", "country_dist_compare",
                                         "iban_by_country", "ob_share_by_country", "token_presence", "dup_detector", "romance_detector", "dur_bank_class", "stp_by_size")},
            atlas=AT)
sizes["meta.json"] = dump("meta.json", meta)
for k, v in sizes.items():
    print(f"{k:18s} {v / 1e6:6.2f} MB")
