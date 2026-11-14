"""Run every rule validator on all splits + cross-check SQL vs pure-Python implementations.

Run:  python -m src.validation
Outputs: outputs/evidence/validation.json, findings/validation_report.md
"""
from __future__ import annotations
import json, time, datetime as dt
import pandas as pd
from .config import connect, EVIDENCE, FINDINGS, METADATA
from .rules import RULES
from . import rulelib


def cross_check(con, n=200_000) -> dict:
    """Recompute R6, R7, C2 in pure Python on a random sample and compare with the dataset fields."""
    home = dict(pd.read_csv(METADATA / "cc_currency_map.csv")[["cc", "cur"]].values)
    s = con.execute(f"SELECT path, pc, cont, fx FROM t USING SAMPLE {n} ROWS (reservoir, 42)").df()
    pc_ok = (s.path.map(rulelib.participant_count) == s.pc).mean()
    cont_ok = (s.path.map(rulelib.continuity_flag) == s.cont).mean()
    fx_ok = (s.path.map(lambda p: rulelib.fx_count(p, home)) == s.fx).mean()
    return dict(sample=n, R6_python_match=float(pc_ok), R7_python_match=float(cont_ok), C2_python_match=float(fx_ok))


def fmt(v):
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def md_table(df: pd.DataFrame) -> str:
    """Dependency-free markdown table (tabulate is not installed)."""
    cols = list(df.columns)
    rows = ["| split | " + " | ".join(map(str, cols)) + " |", "|---" * (len(cols) + 1) + "|"]
    for idx, r in df.iterrows():
        rows.append(f"| {idx} | " + " | ".join("" if pd.isna(v) else fmt(v) for v in r.values) + " |")
    return "\n".join(rows)


def main():
    con = connect()
    results, t0 = [], time.time()
    for r in RULES:
        t = time.time()
        try:
            metrics, ok = r["fn"](con)
            status = "PASS" if ok else "FAIL"
        except Exception as e:  # a failing validator must be visible, never silent
            metrics, status = {"error": repr(e)}, "ERROR"
        results.append(dict(id=r["id"], title=r["title"], type=r["type"], criterion=r["criterion"], status=status,
                            seconds=round(time.time() - t, 1), metrics=metrics))
        print(f"{r['id']:5s} {status:5s} {time.time()-t:6.1f}s  {r['title']}")
    xc = cross_check(con)
    print("cross-check:", xc)
    out = dict(generated=dt.datetime.now().isoformat(timespec="seconds"), runtime_s=round(time.time() - t0, 1),
               rules=results, cross_check=xc)
    (EVIDENCE / "validation.json").write_text(json.dumps(out, indent=1, default=float))

    # Markdown report
    L = ["# Validation report", "", f"Generated {out['generated']} · runtime {out['runtime_s']} s · 10,000,000 rows.", "",
         "Splits: **full**; **half_0 / half_1** = random halves by `hash(rid) % 2` (independent-subset check); "
         "**P1 / P2** = before / after 2023-06-15 (temporal check). A rule passes only if its criterion holds on every split it reports. "
         "D1 is a true out-of-sample test: bank speed classes are learned on half_0 and evaluated on half_1.", "",
         "| ID | Type | Rule | Criterion | Status |", "|---|---|---|---|---|"]
    for r in results:
        L.append(f"| {r['id']} | {r['type']} | {r['title']} | {r['criterion']} | **{r['status']}** |")
    L += ["", f"Two-implementation check (pure Python `src/rulelib.py` vs dataset fields, {xc['sample']:,}-row random sample): "
          f"R6 {xc['R6_python_match']:.6f}, R7 {xc['R7_python_match']:.6f}, C2 {xc['C2_python_match']:.6f}.", "", "## Metrics by split", ""]
    for r in results:
        L.append(f"### {r['id']} — {r['title']}  ({r['status']})")
        m = r["metrics"]
        if isinstance(m, dict) and m and all(isinstance(v, dict) for v in m.values()):
            df = pd.DataFrame(m).T
            L.append(md_table(df))
        else:
            L.append(f"`{m}`")
        L.append("")
    (FINDINGS / "validation_report.md").write_text("\n".join(L), encoding="utf-8")
    n_pass = sum(r["status"] == "PASS" for r in results)
    print(f"{n_pass}/{len(results)} rules pass; report -> findings/validation_report.md")


if __name__ == "__main__":
    main()
