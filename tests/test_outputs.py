"""Contract tests on generated artefacts (skip cleanly if the pipeline has not been run)."""
import json
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
TAB, EVD = ROOT / "outputs" / "tables", ROOT / "outputs" / "evidence"
need = pytest.mark.skipif(not (EVD / "validation.json").exists(), reason="run the pipeline first")


@need
@pytest.mark.parametrize("name", ["main", "amount", "duration", "route", "hour"])
def test_cubes_reconcile_to_ten_million(name):
    df = pd.read_parquet(TAB / f"cube_{name}.parquet")
    assert int(df.n.sum()) == 10_000_000
    assert set(df.otype.unique()) <= {"B", "C"} and set(df.ttype.unique()) == {"Direct", "Indirect", "Covered"}


@need
def test_anomaly_counts_match_profile():
    df = pd.read_parquet(TAB / "cube_main.parquet")
    got = df.groupby("anom").n.sum().to_dict()
    prof = json.loads((ROOT / "data" / "metadata" / "full_dataset_profile.json").read_text())["categorical_distributions"]["ANOMALY_TYPE"] \
        if (ROOT / "data" / "metadata" / "full_dataset_profile.json").exists() else None
    expected = {"ROMANCE_SCAM": 2476, "FAT_FINGER_MISTAKE": 1940, "CEO_SCAM": 945, "DUPLICATE_PAYMENT": 679,
                "ACCOUNT_REPLACEMENT_SCAM": 649, "CUSTOMER_RECALL": 317, "NORMAL": 9_992_994}
    assert got == expected
    if prof:  # independent pandas-based profile produced before this pipeline existed
        assert prof["ROMANCE_SCAM"] == expected["ROMANCE_SCAM"] and prof[""] == expected["NORMAL"]


@need
def test_validation_all_rules_pass_and_cross_check_exact():
    v = json.loads((EVD / "validation.json").read_text())
    failing = [r["id"] for r in v["rules"] if r["status"] != "PASS"]
    assert not failing, f"failing validators: {failing}"
    assert v["cross_check"]["C2_python_match"] == 1.0
    assert v["cross_check"]["R6_python_match"] == 1.0


@need
def test_fx_rule_exception_count_is_tiny():
    v = {r["id"]: r for r in json.loads((EVD / "validation.json").read_text())["rules"]}
    assert v["C2"]["metrics"]["full"]["exceptions"] <= 10
