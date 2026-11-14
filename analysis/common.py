"""Shared DuckDB connection + typed/enriched view `p` over payments.parquet.

Derived fields (all computed from the raw columns only — no external data):
  ts, d (date), hr (UTC hour), dow (0=Sun..6=Sat)
  amt, dur, fx, pc            numeric casts
  o_bank_cc / b_bank_cc       country code = chars 5-6 of the BIC8
  o_cust_cc / b_cust_cc       last <country_code:XX> token in the party tokens
  cur_cc                      first 2 letters of the ISO-4217 code (country of currency, 'EU' for EUR)
  path_n, gaps, hops_known    elements in BIC8_PATH, count of '...', known BICs
  o_iban / b_iban             party account rendered as IBAN token
  o_struct / b_struct         party details in structured '1/ 2/ 3/' layout (MT 50F/59F style)
"""
import duckdb, os

HERE = os.path.dirname(os.path.abspath(__file__))
PQ = os.path.join(HERE, "payments.parquet").replace("\\", "/")


def connect(threads=10):
    con = duckdb.connect()
    con.execute(f"SET threads={threads}; SET memory_limit='10GB'; SET preserve_insertion_order=false")
    con.execute(f"""
    CREATE OR REPLACE VIEW p AS
    SELECT *,
      to_timestamp(EPOCH_SECONDS::BIGINT) AT TIME ZONE 'UTC'        AS ts,
      CAST(to_timestamp(EPOCH_SECONDS::BIGINT) AT TIME ZONE 'UTC' AS DATE) AS d,
      hour(to_timestamp(EPOCH_SECONDS::BIGINT) AT TIME ZONE 'UTC')  AS hr,
      dayofweek(to_timestamp(EPOCH_SECONDS::BIGINT) AT TIME ZONE 'UTC') AS dow,
      USD_AMOUNT::DOUBLE              AS amt,
      TOTAL_DURATION::INT             AS dur,
      CURRENCY_CONVERSION_COUNT::INT  AS fx,
      PARTICIPANT_COUNT::INT          AS pc,
      substr(ORDERING_BIC8,5,2)       AS o_bank_cc,
      substr(BENEFICIARY_BIC8,5,2)    AS b_bank_cc,
      regexp_extract(ORDERING_TOKENS,  '.*<country_code:([A-Z]{{2}})>', 1) AS o_cust_cc,
      regexp_extract(BENEFICIARY_TOKENS,'.*<country_code:([A-Z]{{2}})>', 1) AS b_cust_cc,
      substr(CURRENCY_CODE,1,2)       AS cur_cc,
      len(string_split(BIC8_PATH,';'))                              AS path_n,
      len(string_split(BIC8_PATH,';')) - len(list_filter(string_split(BIC8_PATH,';'), x -> x <> '...')) AS gaps,
      ORDERING_TOKENS  LIKE '%<iban:%' AS o_iban,
      BENEFICIARY_TOKENS LIKE '%<iban:%' AS b_iban,
      ORDERING_DETAILS LIKE '%' || chr(10) || '1/%' AS o_struct,
      BENEFICIARY_DETAILS LIKE '%' || chr(10) || '1/%' AS b_struct
    FROM read_parquet('{PQ}')
    """)
    return con


def q(con, sql, show=True, n=60):
    df = con.execute(sql).df()
    if show:
        import pandas as pd
        with pd.option_context("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 80):
            print(df.head(n).to_string(), "\n")
    return df
