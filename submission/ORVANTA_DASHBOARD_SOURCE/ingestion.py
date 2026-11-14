"""Stage 1-2: raw CSV -> payments.parquet -> slim.parquet (typed + derived features).

Run:  python -m src.ingestion [--skip-full]
Design choices
  * DuckDB read_csv with quote/escape '"' parses the multi-line quoted address fields (RFC 4180);
    a naive newline count would overstate rows. Row count is asserted after every stage.
  * all_varchar=True keeps identifiers (leading zeros, IBANs) exactly as received.
  * DISCLAIMER is non-empty on exactly one row (the legal notice) and is dropped from analytic tables.
"""
from __future__ import annotations
import sys, time
from .config import RAW_CSV, FULL_PQ, SLIM_PQ, EXPECTED_ROWS, connect, duck, _p
import duckdb


def csv_to_parquet() -> int:
    con = duck(preserve_order=True)   # keep CSV row order: rid = CSV row number
    n_disc = con.execute(f"""SELECT count(*) FILTER (WHERE DISCLAIMER IS NOT NULL AND DISCLAIMER<>''), count(*)
        FROM read_csv('{_p(RAW_CSV)}', header=true, quote='"', escape='"', all_varchar=true, max_line_size=10000000, parallel=false)""").fetchone()
    assert n_disc[1] == EXPECTED_ROWS, f"raw row count {n_disc[1]} != {EXPECTED_ROWS}"
    print(f"raw rows={n_disc[1]:,}  rows with DISCLAIMER text={n_disc[0]}")
    con.execute(f"""COPY (SELECT * EXCLUDE (DISCLAIMER) FROM read_csv('{_p(RAW_CSV)}', header=true, quote='"', escape='"',
        all_varchar=true, max_line_size=10000000, parallel=false)) TO '{_p(FULL_PQ)}' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)""")
    n = con.execute(f"SELECT count(*) FROM '{_p(FULL_PQ)}'").fetchone()[0]
    assert n == EXPECTED_ROWS
    return n


SLIM_SQL = """
SELECT row_number() OVER () AS rid,
  EPOCH_SECONDS::BIGINT AS epoch,
  to_timestamp(EPOCH_SECONDS::BIGINT) AT TIME ZONE 'UTC' AS ts,
  CAST(to_timestamp(EPOCH_SECONDS::BIGINT) AT TIME ZONE 'UTC' AS DATE) AS d,
  hour(to_timestamp(EPOCH_SECONDS::BIGINT) AT TIME ZONE 'UTC') AS hr,
  dayofweek(to_timestamp(EPOCH_SECONDS::BIGINT) AT TIME ZONE 'UTC') AS dow,
  CURRENCY_CODE AS cur, USD_AMOUNT::DOUBLE AS amt, TOTAL_DURATION::INT AS dur,
  CURRENCY_CONVERSION_COUNT::INT AS fx, PARTICIPANT_COUNT::INT AS pc,
  ORDERING_BIC8 AS obic, BENEFICIARY_BIC8 AS bbic, BIC8_PATH AS path, CONTINUITY_QFLAG AS cont,
  TRANSACTION_TYPE_CODE AS ttype, ORDERING_ACCOUNT AS oacc, BENEFICIARY_ACCOUNT AS bacc,
  ORDERING_TYPE AS otype, BENEFICIARY_TYPE AS btype, ANOMALY_TYPE AS anom,
  substr(ORDERING_BIC8,5,2) AS o_bank_cc, substr(BENEFICIARY_BIC8,5,2) AS b_bank_cc,
  regexp_extract(ORDERING_TOKENS,  '.*<country_code:([A-Z]{{2}})>', 1) AS o_cust_cc,
  regexp_extract(BENEFICIARY_TOKENS,'.*<country_code:([A-Z]{{2}})>', 1) AS b_cust_cc,
  substr(CURRENCY_CODE,1,2) AS cur_cc,
  len(string_split(BIC8_PATH,';')) AS path_n,
  len(string_split(BIC8_PATH,';')) - len(list_filter(string_split(BIC8_PATH,';'), x -> x <> '...')) AS gaps,
  ORDERING_TOKENS LIKE '%<iban:%' AS o_iban, BENEFICIARY_TOKENS LIKE '%<iban:%' AS b_iban,
  ORDERING_DETAILS LIKE '%' || chr(10) || '1/%' AS o_struct, BENEFICIARY_DETAILS LIKE '%' || chr(10) || '1/%' AS b_struct
FROM read_parquet('{src}')
"""


def build_slim() -> int:
    con = duck(preserve_order=True)   # row_number() OVER () must follow file order so rid (and the hash-half splits) is deterministic
    con.execute(f"COPY ({SLIM_SQL.format(src=_p(FULL_PQ))}) TO '{_p(SLIM_PQ)}' (FORMAT parquet, COMPRESSION zstd)")
    n = con.execute(f"SELECT count(*) FROM '{_p(SLIM_PQ)}'").fetchone()[0]
    assert n == EXPECTED_ROWS
    return n


if __name__ == "__main__":
    t = time.time()
    if "--skip-full" not in sys.argv:
        print("parquet rows:", csv_to_parquet())
    print("slim rows:", build_slim(), f"({time.time()-t:.0f}s)")
