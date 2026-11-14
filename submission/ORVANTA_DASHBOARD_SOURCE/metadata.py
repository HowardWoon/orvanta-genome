"""Stage 2b: derive the three country lookup tables the validators use, directly from the data.

Run:  python -m src.metadata            (after src.ingestion; writes data/metadata/*.csv)
      python -m src.metadata --check    (compare a fresh derivation with the files on disk, write nothing)

  cc_currency_map.csv  cc -> home currency = modal CURRENCY_CODE of payments whose first known path bank is in cc
  country_offsets.csv  cc -> UTC offset (h) = 07:00 local minus the UTC half-hour with the steepest volume rise (rule T1), truncated,
                       for countries with >= MIN_OFFSET_ROWS first-bank payments
  country_effects.csv  ordering-bank country -> n, business share of senders, mean ln-amount residual under the A1 model (rule A2),
                       for countries with >= MIN_EFFECT_ROWS payments
These were first produced during exploration; this module makes them reproducible from the raw data alone.
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd
from .config import METADATA, SLIM_PQ, _p
import duckdb

MIN_OFFSET_ROWS = 5_000
MIN_EFFECT_ROWS = 15_000
FIRST_CC = "substr(list_filter(string_split(path,';'), x -> x <> '...')[1], 5, 2)"


def derive(con) -> dict[str, pd.DataFrame]:
    src = f"read_parquet('{_p(SLIM_PQ)}')"
    ccy = con.execute(f"""SELECT cc, cur FROM (SELECT {FIRST_CC} cc, cur, count(*) n,
                            row_number() OVER (PARTITION BY {FIRST_CC} ORDER BY count(*) DESC, cur) r
                          FROM {src} GROUP BY 1, 2) WHERE r = 1 ORDER BY cc""").df()
    # half-hour bins of the UTC day; the steepest rise marks 07:00 local; half-hour zones (IN +5:30) are truncated to whole hours
    hb = con.execute(f"SELECT {FIRST_CC} cc, ((epoch % 86400) // 1800)::INT b, count(*) n FROM {src} GROUP BY 1, 2").df()
    tot = hb.groupby("cc").n.sum(); big = tot[tot >= MIN_OFFSET_ROWS].index
    prof = hb[hb.cc.isin(big)].pivot(index="cc", columns="b", values="n").reindex(columns=range(48)).fillna(0)
    rise = prof.values - np.roll(prof.values, 1, axis=1)
    raw = (7 - rise.argmax(axis=1) / 2 + 12) % 24 - 12
    off = pd.DataFrame({"offset": np.trunc(raw).astype(int)}, index=prof.index).sort_index()
    off.index.name = None
    # A2: mean residual of ln(amount) under the A1 party-type model (6 + 2·[O=B] + 2·[B=B]), by ordering-bank country, anomalies excluded
    eff = con.execute(f"""SELECT o_bank_cc cc, count(*) n, avg((otype = 'B')::INT) ob,
                                 avg(ln(amt) - 6 - 2 * (otype = 'B')::INT - 2 * (btype = 'B')::INT) amt_eff
                          FROM {src} WHERE anom IS NULL OR anom = ''
                          GROUP BY 1 HAVING count(*) >= {MIN_EFFECT_ROWS} ORDER BY n DESC""").df()
    return {"cc_currency_map": ccy, "country_offsets": off, "country_effects": eff}


def compare(name: str, new: pd.DataFrame) -> str:
    path = METADATA / f"{name}.csv"
    if not path.exists():
        return f"{name}: no file on disk"
    old = pd.read_csv(path, index_col=0 if name == "country_offsets" else None, keep_default_na=False)
    if name == "cc_currency_map":
        o, n = old.set_index("cc").cur, new.set_index("cc").cur
    elif name == "country_offsets":
        o, n = old["offset"], new["offset"]
    else:
        o, n = old.set_index("cc").amt_eff.round(3), new.set_index("cc").amt_eff.round(3)
    both = o.index.intersection(n.index)
    diff = int((o[both] != n[both]).sum())
    return f"{name}: on disk {len(o)}, derived {len(n)}, common {len(both)}, differing {diff}"


if __name__ == "__main__":
    con = duckdb.connect(); con.execute("SET preserve_insertion_order=false")
    tabs = derive(con)
    for k, v in tabs.items():
        print(compare(k, v))
        if "--check" not in sys.argv:
            v.to_csv(METADATA / f"{k}.csv", index=(k == "country_offsets"))
