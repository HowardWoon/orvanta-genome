"""Cross-deliverable consistency check: validation ↔ register ↔ registry ↔ ledger ↔ PDFs ↔ research report ↔ website data.

Usage: python scripts/consistency_check.py   (exit 1 on any failure). Also run by tests/test_consistency.py.
Every expected value is read from validation.json / register.json, never typed here.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.levels import level  # noqa: E402

rd = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))
pdf_text = lambda p: " ".join(pg.extract_text() for pg in PdfReader(str(ROOT / p)).pages)
norm = lambda s: re.sub(r"\s+", " ", s.replace(" ", " ").replace("\xa0", " "))


def check() -> list[str]:
    fail = []
    val = {r["id"]: r for r in rd("outputs/evidence/validation.json")["rules"]}
    regj = {r["id"]: r for r in rd("outputs/evidence/register.json")}
    web = rd("web/build_data/registry.json"); wr = {r["id"]: r for r in web["rules"] if r["kind"] == "rule"}
    led = rd("web/build_data/ledger.json"); rep = {x["rule"]: x for x in rd("web/build_data/replay.json")["rules"]}
    # identities, titles, levels, pass status
    if not (set(val) == set(regj) == set(wr)): fail.append(f"rule id sets differ: validation {len(val)}, register {len(regj)}, registry {len(wr)}")
    for rid, v in val.items():
        if v["status"] != "PASS": fail.append(f"{rid} validator not PASS")
        if rid in wr and wr[rid]["title"] != v["title"]: fail.append(f"{rid} title differs between validation and web registry")
        if rid in wr and rid in regj and wr[rid]["level"] != level(rid, regj[rid]["confidence"]): fail.append(f"{rid} level mismatch")
        types = {e["type"] for e in led["entries"] if rid in e["rules"]}
        if not {"rule", "validation"} <= types: fail.append(f"{rid} lacks EV-RULE/EV-VAL evidence")
    # headline numbers
    c2, r1, r2 = (val[k]["metrics"]["full"] for k in ("C2", "R1", "R2"))
    if rep["C2"]["contradicting"] != int(c2["exceptions"]): fail.append("replay C2 contradicting ≠ validator exceptions")
    expect = {"C2 matches": f"{int(c2['n'] - c2['exceptions']):,}", "R1 q": f"{r1['q_mle']:.4f}", "R2 cover-prone": f"{r2['oos_cover_banks_share']:.0%}", "C2 alternative": f"{c2['alt_distinct']:.1%}"}
    docs = {"dashboard.pdf": norm(pdf_text("submission/dashboard.pdf")), "presentation.pdf": norm(pdf_text("submission/presentation.pdf")),
            "research report": norm((ROOT / "submission/ORVANTA_Comprehensive_Research_Report.md").read_text(encoding="utf-8"))}
    need = {"dashboard.pdf": ["C2 matches", "C2 alternative"], "presentation.pdf": ["C2 matches", "R1 q", "R2 cover-prone", "C2 alternative"], "research report": list(expect)}
    for d, keys in need.items():
        for k in keys:
            if expect[k] not in docs[d]: fail.append(f"{d}: missing {k} ({expect[k]})")
    for d, t in docs.items():
        if "90.6%" in t and d != "research report": fail.append(f"{d}: stale 90.6% figure")
        if "to be verified" in t.lower(): fail.append(f"{d}: unverified-reference note left in")
        if "ukfinance" in t.lower(): fail.append(f"{d}: removed (unverifiable) reference still cited")
        if re.search(r"\b34 validated rules\b", t): fail.append(f"{d}: claims all 34 rules are validated")
    # report covers every rule
    for rid in val:
        if f"### {rid} —" not in docs["research report"]: fail.append(f"research report lacks rule {rid}")
    # page / slide limits and one summary slide per feature group
    nd, ns = len(PdfReader(str(ROOT / "submission/dashboard.pdf")).pages), len(PdfReader(str(ROOT / "submission/presentation.pdf")).pages)
    if not 5 <= nd <= 15: fail.append(f"dashboard has {nd} pages")
    if not 10 <= ns <= 20: fail.append(f"presentation has {ns} slides")
    html = (ROOT / "outputs/pdf_build/presentation.html").read_text(encoding="utf-8")
    eyebrows = re.findall(r"<span class='eyebrow'>([^<]+)</span>", html)
    feature = [e for e in eyebrows if not re.search(r"(?i)methodology|headline|challenge|blueprint|discover|robustness|limits|conclusion|references|UMDAC", e)]
    if len(feature) != len(set(feature)): fail.append(f"duplicate feature-group slides: {feature}")
    # website shows exact-match shares without rounding to 1
    if "0.9999998" not in wr["C2"]["effect_size"]: fail.append("web registry rounds C2 share")
    return fail


if __name__ == "__main__":
    f = check()
    print("\n".join(f) if f else "consistency check: all deliverables agree")
    sys.exit(1 if f else 0)
