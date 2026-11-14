"""Pre-aggregated cubes for the interactive dashboard (no raw rows ship to the app).

Run: python -m src.cube   -> outputs/tables/cube_*.parquet
Every cube shares the filter dimensions  d · ttype · anom · curg · otype · btype,
so every dashboard filter (date range, routing type, anomaly, currency, party types) applies to every cube-driven chart.
Additive measures only (counts, sums, sums of squares) -> exact re-aggregation after filtering.
"""
from __future__ import annotations
import time
from .config import connect, TABLES, _p

DIMS = "d, ttype, coalesce(anom,'NORMAL') anom, curg, otype, btype"
GB = "d, ttype, anom, curg, otype, btype"


def main():
    con = connect()
    con.execute("""CREATE OR REPLACE TEMP TABLE topc AS SELECT cur FROM t GROUP BY 1 ORDER BY count(*) DESC LIMIT 12""")
    con.execute("""CREATE OR REPLACE TEMP VIEW b AS SELECT t.*, CASE WHEN cur IN (SELECT cur FROM topc) THEN cur ELSE 'Other' END curg,
        ((hr + coalesce(off.o,0) + 24) % 24) lh FROM t LEFT JOIN off ON off.cc = substr(list_filter(string_split(path,';'),x->x<>'...')[1],5,2)""")
    cubes = {
        "main": f"""SELECT {DIMS}, count(*) n, sum(amt) s_amt, sum(ln(amt)) s_lnamt, sum(ln(amt)^2) ss_lnamt, sum((dur>120)::INT) n_slow,
                    sum(dur) s_dur, sum((cont='N')::INT) n_gap, sum(fx) s_fx, sum(pc) s_pc, sum((o_bank_cc=b_bank_cc)::INT) n_dom FROM b GROUP BY {GB}""",
        "amount": f"SELECT {DIMS}, floor(log10(amt)*4)/4 amt_bin, count(*) n FROM b GROUP BY {GB}, amt_bin",
        "duration": f"SELECT {DIMS}, floor(log2(dur))::INT dur_bin, count(*) n FROM b GROUP BY {GB}, dur_bin",
        "route": f"SELECT {DIMS}, least(pc,9) pc, least(fx,6) fx, cont, count(*) n FROM b GROUP BY {GB}, least(pc,9), least(fx,6), cont",
        "hour": f"SELECT {DIMS}, lh, count(*) n FROM b GROUP BY {GB}, lh",
    }
    for name, sql in cubes.items():
        t = time.time(); path = TABLES / f"cube_{name}.parquet"
        con.execute(f"COPY ({sql}) TO '{_p(path)}' (FORMAT parquet, COMPRESSION zstd)")
        rows, tot = con.execute(f"SELECT count(*), sum(n) FROM '{_p(path)}'").fetchone()
        assert tot == 10_000_000, f"{name} does not reconcile: {tot}"
        print(f"cube_{name}: {rows:,} rows, n reconciles to {int(tot):,}, {path.stat().st_size/1e6:.1f} MB, {time.time()-t:.0f}s")


if __name__ == "__main__":
    main()
