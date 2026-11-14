"""Contracts on the research layer: discovery coverage, forensics, atlas integrity, lineage, registry completeness."""
import json
from pathlib import Path
import pytest

EVD = Path(__file__).resolve().parents[1] / "outputs" / "evidence"
need = pytest.mark.skipif(not (EVD / "lineage.json").exists(), reason="run the pipeline first")
J = lambda f: json.loads((EVD / f).read_text(encoding="utf-8"))
REQUIRED = ["id", "group", "hypothesis", "formulation", "logic", "sample_size", "effect_size", "validation", "counterexamples", "confidence", "economic", "limitations"]


@need
def test_every_strong_dependency_is_explained_or_mediated():
    d = J("discovery.json")
    strong = [p for p in d["pairs"] if p["v_dev"] >= .05]
    open_ = [p for p in strong if not p.get("explained_by") and not str(p.get("verdict", "")).startswith("mediated")]
    assert not open_, [(p["a"], p["b"]) for p in open_]
    assert all(abs(p["v_dev"] - p["v_val"]) < .02 for p in strong)          # dependencies replicate on the holdout half


@need
def test_registry_has_every_required_field():
    for r in J("register.json"):
        missing = [k for k in REQUIRED if not r.get(k)]
        assert not missing, (r["id"], missing)
        assert (EVD / "reports" / f"{r['id']}.md").exists()


@need
def test_atlas_edges_reference_existing_rules_and_nodes():
    a = J("atlas.json"); rules = {r["id"] for r in J("register.json")}; nodes = {n["id"] for n in a["nodes"]}
    for e in a["edges"]:
        assert e["source"] in nodes and e["target"] in nodes
        assert set(e["rules"]) <= rules, e
        assert e["kind"] in a["legend"]
    assert any(e["kind"] == "independent" for e in a["edges"]) and any(e["kind"] == "unresolved" for e in a["edges"])


@need
def test_forensics_change_points_on_mondays_and_fingerprint():
    f = J("forensics.json")
    assert f["change_points"]["weekdays"] and set(f["change_points"]["weekdays"]) == {"Monday"}
    u = {r["usd_denominated"]: r["whole_units"] for r in f["usd_roundness"]}
    assert u[True] > .3 and u[False] < .013


@need
def test_lineage_contract_and_hashes():
    li = J("lineage.json")
    assert li["contract_ok"]
    assert all(len(a["sha256"]) == 64 for a in li["artefacts"])
    assert any(a["path"].endswith("slim.parquet") and a["rows"] == 10_000_000 for a in li["artefacts"])
