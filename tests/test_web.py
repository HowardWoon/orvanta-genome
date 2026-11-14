"""Static web edition: built, modular, data reconciled with the evidence files, no row-level records, crawler-blocked."""
import json, re
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
need = pytest.mark.skipif(not (DIST / "index.html").exists(), reason="run python -m src.webdata && python -m src.web first")
rd = lambda f: json.loads((DIST / "data" / f"{f}.json").read_text(encoding="utf-8"))


@need
def test_cube_reconciles_to_10m_and_registry_matches_validation():
    ex = rd("explorer")
    ni = ex["cols"].index("n")
    assert sum(r[ni] for r in ex["rows"]) == 10_000_000
    # every payment sits in exactly one amount bin and one duration bin
    a_tot = sum(sum(r[ex["cols"].index(f"a{k}")] for k in range(ex["nab"])) for r in ex["rows"])
    d_tot = sum(sum(r[ex["cols"].index(f"d{k}")] for k in range(ex["ndb"])) for r in ex["rows"])
    assert a_tot == d_tot == 10_000_000
    reg = rd("registry")
    val = json.loads((ROOT / "outputs" / "evidence" / "validation.json").read_text(encoding="utf-8"))
    rules = [r for r in reg["rules"] if r["kind"] == "rule"]
    assert {r["id"] for r in rules} == {r["id"] for r in val["rules"]}
    assert all(r["status"] == "PASS" for r in rules)
    assert set(reg["levels"]) == {"VALIDATED", "STRONGLY SUPPORTED", "SUPPORTED", "CANDIDATE", "INCONCLUSIVE", "REJECTED"}


@need
def test_bh_is_per_family():
    t = rd("tests")["tests"]
    fams = {}
    for x in t:
        if x["p"] is not None:
            fams.setdefault(x["family"], []).append(x)
    for fam, xs in fams.items():
        assert all(x["family_size"] == len(xs) for x in xs), fam
        for x in xs:                                         # BH-adjusted p is never below the raw p
            assert x["p_bh"] >= x["p"] - 1e-12


@need
def test_assets_present_and_referenced():
    reg = rd("registry")
    for r in reg["rules"]:
        for c in r.get("charts") or []:
            assert (DIST / "charts" / f"{c}.png").exists(), c
        if r["kind"] == "rule":
            assert (DIST / "reports" / f"{r['id']}.md").exists(), r["id"]
    for f in ("dashboard.pdf", "presentation.pdf", "validation_report.md"):
        assert (DIST / "downloads" / f).exists()
    js = (DIST / "js" / "main.js").read_text(encoding="utf-8")
    for mod in set(re.findall(r"'([a-z]+)', '[A-Z]+'\]", js)):   # every routed page module exists
        assert (DIST / "js" / "pages" / f"{mod}.js").exists(), mod


@need
def test_no_row_level_records_and_noindex():
    for p in (DIST / "data").glob("*.json"):
        s = p.read_text(encoding="utf-8")
        assert not re.search(r"_FAKE_\w{4,}", s), p.name       # no account identifiers (the dictionary may name the format)
        ibans = [m for m in re.findall(r"\b[A-Z]{2}\d{2}[A-Z0-9]{12,30}\b", s) if not re.fullmatch(r"[A9]+", m)]  # templates like AA9999… allowed
        assert not ibans, (p.name, ibans[:3])                  # no IBAN-shaped strings
    ex = rd("explorer")
    assert min(r[ex["cols"].index("n")] for r in ex["rows"]) >= 1 and len(ex["rows"]) < 20_000
    assert rd("routes")["min_n"] >= 150
    assert 'name="robots" content="noindex' in (DIST / "index.html").read_text(encoding="utf-8")
    assert "noindex" in (DIST / "vercel.json").read_text()
    assert (DIST / "robots.txt").read_text().strip().endswith("Disallow: /")
    assert ".env*" in (DIST / ".vercelignore").read_text()
    assert not list(DIST.glob(".env*"))


@need
def test_replay_counts_consistent_and_deidentified():
    rp = rd("replay")
    val = {r["id"]: r for r in json.loads((ROOT / "outputs" / "evidence" / "validation.json").read_text(encoding="utf-8"))["rules"]}
    by = {x["rule"]: x for x in rp["rules"]}
    for x in rp["rules"]:
        assert x["supporting"] + x["contradicting"] == x["eligible"], x["rule"]
        assert not {"oacc", "bacc", "details", "tokens", "rid"} & set(x["columns"]), x["rule"]
        assert len(x["supporting_rows"]) <= rp["n_sup"] and len(x["contradicting_rows"]) <= rp["n_cx"]
    assert by["C2"]["contradicting"] == int(val["C2"]["metrics"]["full"]["exceptions"])
    for rid in ("R6", "R7", "P2"):
        assert by[rid]["contradicting"] == 0


@need
def test_ledger_covers_every_rule_and_genealogy_is_recorded_only():
    led, reg, gen = rd("ledger"), rd("registry"), rd("genome")
    ids = [e["id"] for e in led["entries"]]
    assert len(ids) == len(set(ids))
    for r in (r for r in reg["rules"] if r["kind"] == "rule"):
        types = {e["type"] for e in led["entries"] if r["id"] in e["rules"]}
        assert {"rule", "validation"} <= types, r["id"]
    hyp = {h["id"] for h in reg["hypotheses"]}
    for g in gen["genealogy"]:
        assert all(h["id"] in hyp for h in g["hypotheses"]) and g["recorded"] == bool(g["hypotheses"])
    assert len(gen["blueprint"]) == 10 and len(gen["coverage"]) == 10
