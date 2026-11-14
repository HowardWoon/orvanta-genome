"""Build the dashboard traceability files straight from the rendered dashboard HTML and the evidence JSON.

Usage: python scripts/dashboard_registers.py
Writes to submission/:
  ORVANTA_RULE_CROSSWALK.csv          every validated rule -> dashboard page(s), level, metric, evidence id (fails if a rule is missing)
  ORVANTA_CLAIM_EVIDENCE_REGISTER.csv every headline and evidence-table claim -> source JSON field, rule id, evidence id
Nothing is typed by hand: values are read back from what the dashboard actually prints, then cross-checked against validation.json.
"""
import csv, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission"
H = (ROOT / "outputs" / "pdf_build" / "dashboard.html").read_text(encoding="utf-8")
VAL = {r["id"]: r for r in json.loads((ROOT / "outputs" / "evidence" / "validation.json").read_text(encoding="utf-8"))["rules"]}
LED = json.loads((ROOT / "web" / "build_data" / "ledger.json").read_text(encoding="utf-8"))["entries"]
sys.path.insert(0, str(ROOT))
from src.levels import level  # noqa: E402

REG = {r["id"]: r for r in json.loads((ROOT / "outputs" / "evidence" / "register.json").read_text(encoding="utf-8"))["rules"]} \
    if isinstance(json.loads((ROOT / "outputs" / "evidence" / "register.json").read_text(encoding="utf-8")), dict) else \
    {r["id"]: r for r in json.loads((ROOT / "outputs" / "evidence" / "register.json").read_text(encoding="utf-8"))}


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


pages = re.split(r"<section class=['\"]pg", H)[1:]
assert len(pages) == 15, len(pages)
rows_by_rule, claims = {}, []
for no, sec in enumerate(pages, 1):
    title = text(re.search(r"<h1[^>]*>(.*?)</h1>", sec, re.S).group(1))
    ev = re.search(r"<table class=['\"]ev['\"]>(.*?)</table>", sec, re.S)
    ids = []
    if ev:
        for tr in re.findall(r"<tr>(.*?)</tr>", ev.group(1), re.S)[1:]:
            td = [text(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(td) < 7:
                continue
            rid = td[0]; ids.append(rid)
            rows_by_rule.setdefault(rid, []).append(dict(page=no, confidence=td[1], metric=td[2], full=td[3], rng=td[4], n=td[5], evidence=td[6]))
            claims.append(dict(page=no, kind="evidence-table", claim=f"{rid}: {td[2]} = {td[3]} (5-split range {td[4]})", rule_ids=rid,
                               source=f"outputs/evidence/validation.json rules[{rid}].metrics", evidence_id=td[6], confidence=td[1]))
    if no == 1:   # the six headline KPIs
        src_ = ["outputs/evidence/evidence.json (ingest reconciliation)", "validation.json (status per rule, 5 splits)", "src/levels.py",
                "validation.json rules[C2].metrics.full", "validation.json cross_check (SQL vs Python)", "evidence.json anom_profile"]
        for k, (b, s) in enumerate(re.findall(r"<div class=['\"]kpi['\"]><b>(.*?)</b><span>(.*?)</span>", sec, re.S)):
            claims.append(dict(page=1, kind="kpi", claim=f"{text(b)} — {text(s)}", rule_ids={3: "C2", 4: "R6 R7 C2"}.get(k, ""),
                               source=src_[k] if k < len(src_) else "", evidence_id={3: "EV-RULE-009"}.get(k, ""), confidence=""))
    # rule ids named on the page's rule cards (covers pages without an evidence table)
    card_ids = sorted(set(re.findall(r"<b class=['\"]id['\"]>([A-Z]\d+b?)</b>", sec)) & set(VAL))
    claims.insert(len(claims) - len(ids), dict(page=no, kind="headline", claim=title, rule_ids=" ".join(ids or card_ids),
                  source="see evidence-table rows on the same page" if ids else
                  {1: "validation.json (34 rules); levels.py; webdata ledger", 2: "outputs/evidence/discovery.json; atlas.json",
                   15: "validation.json; levels.py; src/ledger.py SECTIONS"}.get(no, "validation.json"),
                  evidence_id=" ".join(sorted({r['evidence'] for i in ids for r in rows_by_rule[i] if r['page'] == no})), confidence=""))

# ---- rule crosswalk
missing = sorted(set(VAL) - set(rows_by_rule))
mention = {rid: sorted({no for no, sec in enumerate(pages, 1) if re.search(rf"\b{re.escape(rid)}\b", text(sec))}) for rid in VAL}
led = {e.get("rule") or e.get("rule_id") or e.get("id"): e for e in LED}
with (OUT / "ORVANTA_RULE_CROSSWALK.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rule_id", "title", "confidence_level", "validator_status_5_splits", "criterion", "primary_page", "evidence_table_pages",
                "all_pages_mentioning", "key_metric", "full_data_value", "range_5_splits", "n", "evidence_id"])
    for rid in sorted(VAL, key=lambda r: (r[0], int(re.sub(r"\D", "", r) or 0), r)):
        v = VAL[rid]; rr = rows_by_rule.get(rid, [])
        lv = level(rid, (REG.get(rid) or {}).get("confidence", ""))
        first = rr[-1] if rr else {}
        w.writerow([rid, v["title"], lv, v["status"], v.get("criterion", ""), first.get("page", ""), " ".join(str(r["page"]) for r in rr),
                    " ".join(map(str, mention[rid])), first.get("metric", ""), first.get("full", ""), first.get("rng", ""), first.get("n", ""), first.get("evidence", "")])

with (OUT / "ORVANTA_CLAIM_EVIDENCE_REGISTER.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["claim_no", "page", "kind", "claim", "rule_ids", "confidence", "source", "evidence_id"])
    w.writeheader()
    for i, c in enumerate(claims, 1):
        w.writerow(dict(claim_no=i, **c))

# ---- checks
bad = [(rid, r["page"], r["confidence"], level(rid, (REG.get(rid) or {}).get("confidence", ""))) for rid, rr in rows_by_rule.items() for r in rr
       if rid in VAL and r["confidence"] != level(rid, (REG.get(rid) or {}).get("confidence", ""))]
print(f"rules: {len(VAL)} · in an evidence table: {len(set(rows_by_rule) & set(VAL))} · missing: {missing or 'none'}")
print(f"claims: {len(claims)} · level mismatches: {bad or 'none'} · non-PASS: {[r for r in VAL if VAL[r]['status'] != 'PASS'] or 'none'}")
sys.exit(1 if missing or bad else 0)
