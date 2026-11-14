"""Forensic Replay: exact support / violation counts and small controlled record samples per rule (web/build_data/replay.json).

Run: python -m src.replay   (≈ 5 min; one full unnest of every path for C2/C3)

For each row-level rule we store
  * the condition (SQL and plain language), the eligible population, exact supporting and contradicting counts over all 10M rows;
  * up to N_SUP supporting and N_CX contradicting records chosen by a deterministic hash order (seed 2026) — approximately uniform
    over the eligible rows, reproducible, and small. All contradicting records are kept when there are at most N_CX.
Shipped fields are restricted to the generator-relevant columns. Account numbers, party names, free-text details and tokens are NEVER
included; the row id is replaced by a one-way hash. BIC8 codes in this dataset are synthetic.
"""
from __future__ import annotations
import json, time
from .config import connect, ROOT

OUT = ROOT / "web" / "build_data" / "replay.json"
N_SUP, N_CX, SEED = 25, 50, 2026
BASE = ("substr(sha256(rid::VARCHAR || 'orvanta'),1,10) AS rec, strftime(ts,'%Y-%m-%d %H:%M:%S') AS utc, cur, round(amt,2) AS usd, dur, fx, pc, ttype, cont, "
        "otype, btype, coalesce(anom,'NORMAL') AS anom, path, obic, bbic")
ORDER = f"ORDER BY hash(rid + {SEED})"


def main():
    t0 = time.time()
    con = connect()
    con.execute(f"""CREATE OR REPLACE TEMP TABLE w AS
      SELECT r.*, cl.cl FROM t r JOIN (
        SELECT rid, list(hcur ORDER BY i) cl FROM (
          SELECT rid, generate_subscripts(lst,1) i, unnest(lst) b FROM (SELECT rid, list_filter(string_split(path,';'),x->x<>'...') lst FROM t)) u
        LEFT JOIN ccy ON ccy.cc = substr(b,5,2) GROUP BY rid) cl USING (rid)""")
    print(f"route currency lists built in {time.time()-t0:.0f}s")
    kn = "len(list_filter(string_split(path,';'), x -> x <> '...'))"
    borders = "len(list_filter(range(1,len(cl)), i -> cl[i] <> cl[i+1]))"
    resid = "log10(amt) - (6 + 2*(otype='B')::INT + 2*(btype='B')::INT)/ln(10)"
    first = "list_filter(string_split(path,';'), x -> x <> '...')[1]"
    last = "list_filter(string_split(path,';'), x -> x <> '...')[-1]"
    R = [
        dict(rule="R6", title="PARTICIPANT_COUNT equals the number of known BICs in the path", kind="deterministic",
             plain="A record supports R6 when PARTICIPANT_COUNT equals the count of BIC8 entries in BIC8_PATH that are not '...'.",
             eligible="TRUE", support=f"pc = {kn}", extra=f"{kn} AS known_bics"),
        dict(rule="R7", title="CONTINUITY_QFLAG = 'N' exactly when the path contains '...'", kind="deterministic",
             plain="Supports R7 when the flag is N and the path has a hidden hop, or the flag is Y and it has none.",
             eligible="TRUE", support="(cont = 'N') = (list_contains(string_split(path,';'), '...'))", extra="list_contains(string_split(path,';'),'...') AS has_gap"),
        dict(rule="R1", title="Direct ⇔ exactly 2 participants", kind="deterministic",
             plain="Supports when TRANSACTION_TYPE_CODE is Direct and PARTICIPANT_COUNT = 2, or non-Direct and PARTICIPANT_COUNT > 2.",
             eligible="TRUE", support="(ttype = 'Direct') = (pc = 2)", extra="pc - 2 AS intermediaries"),
        dict(rule="C2", title="FX conversions = home-currency changes along the path", kind="deterministic",
             plain="Walk the known BICs; map each to its country's home currency; count adjacent changes. Supports C2 when that count equals CURRENCY_CONVERSION_COUNT. The 2 contradicting rows are the only payments in the dataset touching an Eritrean bank: Eritrea never sends, so its home currency is unobservable (shown missing in route_currencies) and the prediction undercounts by exactly one border.",
             eligible="TRUE", support=f"fx = {borders}", extra=f"{borders} AS predicted_fx, array_to_string(cl,'›') AS route_currencies", src="w"),
        dict(rule="C3", title="Payment currency is one of the route banks' home currencies", kind="stochastic (98.7%)",
             plain="Supports C3 when CURRENCY_CODE is the home currency of at least one bank on the path. Contradicting records use an outside 'vehicle' currency.",
             eligible="TRUE", support="list_contains(cl, cur)", extra="array_to_string(cl,'›') AS route_currencies", src="w"),
        dict(rule="R5", title="Path endpoints equal the header BICs (each replaced independently w.p. ≈5%)", kind="stochastic (≈95% per end)",
             plain="Supports the 'unchanged' branch when the first known path BIC equals ORDERING_BIC8 and the last equals BENEFICIARY_BIC8. Contradicting records are the ≈5% replacements the rule predicts — exceptions inside the rule, not failures of it.",
             eligible="TRUE", support=f"{first} = obic AND {last} = bbic", extra=f"{first} <> obic AS first_replaced, {last} <> bbic AS last_replaced"),
        dict(rule="P2", title="IBAN country prefix equals the bank's BIC country", kind="deterministic",
             plain="Among IBAN-formatted ordering accounts, supports P2 when the 2-letter IBAN prefix equals the ordering bank's country. Only the prefix is shown, never the account.",
             eligible="o_iban", support="substr(replace(oacc,'_FAKE_',''),1,2) = o_bank_cc", extra="substr(replace(oacc,'_FAKE_',''),1,2) AS iban_prefix, o_bank_cc AS bic_country"),
        dict(rule="R1-tail", title="Long-route tail: K ~ Geometric(1/e) predicts ≈3 rows with ≥ 17 participants", kind="tail check",
             plain="All rows with PARTICIPANT_COUNT ≥ 17. The rule predicts 10M·e^-15 ≈ 3.1; the records below are the complete set.",
             eligible="pc >= 17", support="TRUE", extra="pc - 2 AS intermediaries"),
        dict(rule="X3", title="Fat-finger amounts sit ≈ two decades from the A1 expectation", kind="anomaly profile",
             plain="Among FAT_FINGER_MISTAKE rows, supports X3 when |log10(amount / A1 baseline)| > 1.3. Contradicting rows are fat-finger labels whose amount looks ordinary — the label overlaps normal noise.",
             eligible="anom = 'FAT_FINGER_MISTAKE'", support=f"abs({resid}) > 1.3", extra=f"round({resid},2) AS log10_vs_A1_baseline"),
        dict(rule="X2", title="Duplicate payments repeat amount, path and duration within 2 hours", kind="anomaly profile",
             plain="DUPLICATE_PAYMENT rows. A record supports X2 when another labelled row shares its amount, path and duration within 7,200 s.",
             eligible="anom = 'DUPLICATE_PAYMENT'",
             support="EXISTS (SELECT 1 FROM t t2 WHERE t2.anom='DUPLICATE_PAYMENT' AND t2.rid<>t.rid AND t2.amt=t.amt AND t2.path=t.path AND t2.dur=t.dur AND abs(t2.epoch-t.epoch)<=7200)",
             extra="(SELECT count(*) FROM t t2 WHERE t2.anom='DUPLICATE_PAYMENT' AND t2.amt=t.amt AND t2.path=t.path AND t2.dur=t.dur AND abs(t2.epoch-t.epoch)<=7200) AS copies_in_group"),
    ]
    out = []
    for r in R:
        s = time.time(); src = r.get("src", "t")
        tot, sup = con.execute(f"SELECT count(*), sum(({r['support']})::INT) FROM {src} t WHERE {r['eligible']}").fetchone()
        sup = int(sup or 0); tot = int(tot); cx = tot - sup
        cols = f"{BASE}, {r['extra']}"
        S = con.execute(f"SELECT {cols} FROM {src} t WHERE {r['eligible']} AND ({r['support']}) {ORDER} LIMIT {N_SUP}").df()
        X = con.execute(f"SELECT {cols} FROM {src} t WHERE {r['eligible']} AND NOT ({r['support']}) {ORDER} LIMIT {N_CX}").df()
        out.append(dict(rule=r["rule"], title=r["title"], kind=r["kind"], plain=r["plain"],
                        condition=dict(eligible=r["eligible"], supports=r["support"]), eligible=tot, supporting=sup, contradicting=cx,
                        support_rate=sup / tot if tot else None, sample=dict(method=f"deterministic hash order (hash(rid + {SEED})), first rows taken; approximately uniform over the eligible rows",
                                                                             supporting_shown=len(S), contradicting_shown=len(X), all_contradicting_shown=cx <= N_CX),
                        columns=list(S.columns), supporting_rows=S.astype(object).where(S.notna(), None).values.tolist(),
                        contradicting_rows=X.astype(object).where(X.notna(), None).values.tolist()))
        print(f"{r['rule']:8s} eligible {tot:>10,}  supporting {sup:>10,}  contradicting {cx:>9,}  ({time.time()-s:.0f}s)")
    OUT.write_text(json.dumps(dict(generated=time.strftime("%Y-%m-%dT%H:%M:%S"), seed=SEED, n_sup=N_SUP, n_cx=N_CX,
                                   privacy="no account numbers, names, free-text details or tokens; row ids hashed; BIC8 codes are synthetic",
                                   rules=out), default=str, separators=(",", ":")), encoding="utf-8")
    print(f"replay.json {OUT.stat().st_size/1e3:.0f} kB in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
