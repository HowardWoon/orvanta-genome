"""H38: on routes with no EUR- or USD-home bank, how often is the payment in EUR / USD (an outside-route 'vehicle' currency)?

Run:  python -m src.h38        (after src.metadata; writes outputs/evidence/h38_vehicle.json and .txt)
Supports rule C3: outside-route currencies are a route-independent vehicle draw (flat across route length and stable on all 5 splits).
"""
from __future__ import annotations
import json
from .config import connect, EVIDENCE, SPLITS, SPLIT_LABEL

ROUTE = """WITH r AS (SELECT rid, any_value(cur) cur, any_value(pc) pc, any_value(h) h, any_value(per) per,
                     list(DISTINCT c.hcur) hc
              FROM (SELECT rid, cur, pc, h, per, unnest(list_filter(string_split(path, ';'), x -> x <> '...')) b FROM tt) u
              JOIN ccy c ON c.cc = substr(u.b, 5, 2) GROUP BY rid)"""


def main():
    con = connect()
    sp = con.execute(f"""{ROUTE} SELECT {SPLIT_LABEL} split, count(*) n, avg((cur = 'EUR')::INT) eur, avg((cur = 'USD')::INT) usd,
                         avg((cur NOT IN ('EUR', 'USD') AND NOT list_contains(hc, cur))::INT) other_out
                         FROM r WHERE NOT list_contains(hc, 'EUR') AND NOT list_contains(hc, 'USD') GROUP BY {SPLITS} ORDER BY 1""").df()
    pc = con.execute(f"""{ROUTE} SELECT least(pc, 5) pc, count(*) n, avg((cur = 'EUR')::INT) eur, avg((cur = 'USD')::INT) usd
                         FROM r WHERE NOT list_contains(hc, 'EUR') AND NOT list_contains(hc, 'USD') GROUP BY 1 ORDER BY 1""").df()
    out = con.execute(f"""{ROUTE} SELECT avg((NOT list_contains(hc, cur))::INT), sum((NOT list_contains(hc, cur))::INT),
                          sum((NOT list_contains(hc, cur) AND cur IN ('EUR', 'USD'))::INT) FROM r""").fetchone()
    res = {"splits": sp.to_dict("records"), "by_pc": pc.to_dict("records"),
           "outside_share": float(out[0]), "outside_n": int(out[1]), "outside_eur_usd": int(out[2])}
    (EVIDENCE / "h38_vehicle.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    (EVIDENCE / "h38_vehicle.txt").write_text(sp.to_string(index=False) + "\n" + pc.to_string(index=False) +
                                              f"\noutside share {(res['outside_share'], res['outside_n'], res['outside_eur_usd'])}\n", encoding="utf-8")
    print(f"H38: {int(sp.loc[sp.split == 'full', 'n'].iloc[0]):,} routes without an EUR/USD bank; outside-route share {res['outside_share']:.4%}")


if __name__ == "__main__":
    main()
