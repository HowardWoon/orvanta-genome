"""Evidence Ledger, Generator Blueprint, Rule Genealogy and feature-coverage matrix (web/build_data/{ledger,genome}.json).

Run after src.webdata and src.replay:  python -m src.ledger
Everything here is assembled from artefacts that already exist (validation.json via registry.json, tests.json, meta.json, replay.json,
findings/hypotheses.md via registry.json). Nothing is typed by hand except the mapping of rules to blueprint sections and the section
names. Genealogy uses only the recorded hypothesis log (H1–H37, in the order tested) — no history is invented for any rule.
"""
from __future__ import annotations
import json, re
from .config import ROOT

B = ROOT / "web" / "build_data"
rd = lambda f: json.loads((B / f"{f}.json").read_text(encoding="utf-8"))

SECTIONS = [  # (section, rule ids, what the section covers)
    ("Temporal generation", ["T1", "T3", "T4", "T4b"], "when a payment is stamped"),
    ("Payment amount generation", ["A1", "A2", "A3", "F1"], "how large it is"),
    ("Currency selection", ["C1", "C3", "R5b"], "which currency it is sent in"),
    ("Institution assignment", ["R3", "G3", "G1", "P5", "R5"], "which banks send, relay and receive"),
    ("Routing construction", ["R1", "R2", "R4", "R7"], "how many hops, which type, what is hidden"),
    ("Participant & FX mechanics", ["R6", "C2"], "derived counts"),
    ("Duration generation", ["D1", "D2", "D3"], "how long settlement takes"),
    ("Party-detail generation", ["P2", "P4", "P1b"], "accounts, IBANs and party types"),
    ("Token generation", ["P1b"], "engineered token summaries of the details fields"),
    ("Anomaly labelling", ["X1", "X2", "X3", "X4", "X5", "X6"], "how labels are injected"),
]
TOKEN_NOTE = ("Token fields are engineered pattern summaries supplied with the data, not original text. We measured their presence and "
              "co-occurrence (Token page) but found no generator rule beyond the layout and party-type structure in P1b/P4 — this section is "
              "deliberately thin rather than padded.")


def main():
    reg, meta, tests = rd("registry"), rd("meta"), rd("tests")
    rep = rd("replay") if (B / "replay.json").exists() else {"rules": []}
    rules = {r["id"]: r for r in reg["rules"] if r["kind"] == "rule"}
    sha = {a["path"]: (a.get("sha256") or "")[:12] for a in meta["lineage"]["artefacts"]}
    VAL = ("outputs/evidence/validation.json", sha.get("outputs/evidence/validation.json", ""))
    led = []
    add = lambda **k: led.append(k)
    for i, q in enumerate(meta["quality"], 1):
        add(id=f"EV-DATA-{i:03d}", type="data", rules=[], title=q["check"], method="ingestion / profiling check (DuckDB over all rows)",
            parameters="", result=f"{q['result']} — {q['status']}", n="10,000,000", uncertainty="exact count", source="web/build_data/meta.json → quality",
            sha=sha.get("data/processed/slim.parquet", ""), detail=q["detail"])
    for i, a in enumerate(meta["lineage"]["artefacts"], len(meta["quality"]) + 1):
        add(id=f"EV-DATA-{i:03d}", type="data", rules=[], title=f"Artefact {a['path']}", method=f"produced by {a['producer']}", parameters="",
            result=f"{a.get('rows') or '—'} rows · {a['bytes']:,} bytes", n=str(a.get("rows") or "—"), uncertainty="SHA-256 fingerprint",
            source="outputs/evidence/lineage.json", sha=(a.get("sha256") or "")[:12], detail=a.get("sha256", ""))
    for i, (rid, r) in enumerate(rules.items(), 1):
        full = r.get("metrics", {}).get("full", {})
        add(id=f"EV-RULE-{i:03d}", type="rule", rules=[rid], title=f"{rid} · {r['title']}", method=r["method"], parameters=r["criterion"],
            result=r["effect_size"], n=r["sample_size"], uncertainty="; ".join(f"{k}={v:.4g}" for k, v in full.items() if isinstance(v, (int, float)) and k != "n")[:300],
            source=VAL[0], sha=VAL[1], detail=r["formulation"], chart=(r.get("charts") or [None])[0])
        splits = r.get("metrics", {})
        add(id=f"EV-VAL-{i:03d}", type="validation", rules=[rid], title=f"{rid} on five splits", method="same validator re-run on full, half_0, half_1 (hash of row id), P1, P2 (15 Jun 2023)",
            parameters=r["criterion"], result=f"{r['status']} on {len(splits)} splits", n=" · ".join(f"{s}: {int(m.get('n', 0)):,}" for s, m in splits.items() if m.get("n")) or r["sample_size"],
            uncertainty="acceptance must hold on every split", source=VAL[0], sha=VAL[1], detail=r["validation"])
    for i, x in enumerate(rep["rules"], 1):
        rid = x["rule"].split("-")[0]
        add(id=f"EV-CX-{i:03d}", type="counterexample", rules=[rid], title=f"{x['rule']} · {x['title']}", method="exact count over all eligible rows + hash-ordered record sample",
            parameters=f"eligible: {x['condition']['eligible']} · supports: {x['condition']['supports']}",
            result=f"{x['supporting']:,} supporting · {x['contradicting']:,} contradicting ({(x['support_rate'] or 0):.6%} support)", n=f"{x['eligible']:,}",
            uncertainty="exact (no sampling in the counts)", source="web/build_data/replay.json", sha="", detail=x["plain"], replay=x["rule"])
    for i, t in enumerate(tests["tests"], 1):
        rid = re.match(r"([A-Z]\d+b?)\b", t["family"])
        add(id=f"EV-STAT-{i:03d}", type="statistical test", rules=[rid.group(1)] if rid and rid.group(1) in rules else [], title=f"{t['family']} · {t['test']}",
            method=t["test"], parameters=f"family of {t.get('family_size') or '—'} tests; BH within family", result=t["effect"], n=str(t["n"]),
            uncertainty=("p = %.3g · p(BH) = %.3g" % (t["p"], t["p_bh"])) if t["p"] is not None and t.get("p_bh") is not None else "effect size only",
            source="web/build_data/tests.json", sha="")
    pairs = [p for p in meta["discovery"]["pairs"] if p.get("verdict")]
    for i, p in enumerate(sorted(pairs, key=lambda p: -p["v_dev"]), 1):
        ex = [e for e in re.split(r"[,\s]+", p.get("explained_by") or "") if e in rules]
        add(id=f"EV-DISC-{i:03d}", type="discovery", rules=ex, title=f"{p['a']} × {p['b']}", method="Cramér's V on development half, re-measured on validation half",
            parameters="strong = V ≥ threshold and stable across halves", result=f"V dev {p['v_dev']:.3f} / val {p['v_val']:.3f} → {p['verdict']}", n=f"{meta['discovery']['dev_rows']:,} + {meta['discovery']['val_rows']:,}",
            uncertainty=f"residual V after mediation {p['residual_v']:.3f}" if p.get("residual_v") is not None else "—", source="outputs/evidence/discovery.json",
            sha=sha.get("outputs/evidence/discovery.json", ""))
    (B / "ledger.json").write_text(json.dumps(dict(generated=reg["generated"], n=len(led), entries=led), separators=(",", ":"), default=str), encoding="utf-8")

    # ---- genealogy (recorded hypothesis log only)
    gen = {}
    for h in reg["hypotheses"]:
        for rid in re.findall(r"\b([A-Z]\d+b?)\b", h.get("consequence") or ""):
            if rid in rules:
                gen.setdefault(rid, []).append(dict(id=h["id"], hypothesis=h["hypothesis"], test=h["test"], outcome=h["outcome"], consequence=h["consequence"]))
    genealogy = []
    for rid, r in rules.items():
        steps = gen.get(rid, [])
        genealogy.append(dict(rule=rid, title=r["title"], level=r["level"], hypotheses=steps, alternative=r.get("alternative"),
                              counterexamples=r.get("violation", {}).get("text"), validation=r["validation"], recorded=bool(steps)))
    # ---- blueprint
    bp = []
    for name, ids, what in SECTIONS:
        rs = [rules[i] for i in ids if i in rules]
        bp.append(dict(section=name, covers=what, mechanisms=[dict(rule=r["id"], level=r["level"], statement=r["formulation"]) for r in rs],
                       unresolved=[dict(rule=r["id"], text=r["limitations"]) for r in rs if r["level"] in ("INCONCLUSIVE", "SUPPORTED") and r.get("limitations") and r["limitations"] != "—"],
                       note=TOKEN_NOTE if name == "Token generation" else ""))
    # ---- coverage per feature group
    cov = []
    for g, ids in reg["groups"].items():
        rs = [rules[i] for i in ids if i in rules]
        cov.append(dict(group=g, rules=len(rs), validated=sum(r["level"] == "VALIDATED" for r in rs), strong=sum(r["level"] == "STRONGLY SUPPORTED" for r in rs),
                        supported=sum(r["level"] == "SUPPORTED" for r in rs), inconclusive=sum(r["level"] == "INCONCLUSIVE" for r in rs),
                        hypotheses=len({h["id"] for i in ids for h in gen.get(i, [])}), charts=len({c for r in rs for c in (r.get("charts") or [])}),
                        tests=sum(1 for t in tests["tests"] if (m := re.match(r"([A-Z]\d+b?)\b", t["family"])) and m.group(1) in ids),
                        replay=sum(1 for x in rep["rules"] if x["rule"].split("-")[0] in ids), economic=sum(1 for r in rs if r.get("economic") and r["economic"] not in ("—", "-")),
                        open=[f"{r['id']}: {r['limitations']}" for r in rs if r["level"] == "INCONCLUSIVE"]))
    (B / "genome.json").write_text(json.dumps(dict(blueprint=bp, genealogy=genealogy, coverage=cov), separators=(",", ":"), default=str), encoding="utf-8")
    print(f"ledger.json {len(led)} entries · genome.json {len(bp)} sections, {sum(g['recorded'] for g in genealogy)}/{len(genealogy)} rules with recorded genealogy")


if __name__ == "__main__":
    main()
