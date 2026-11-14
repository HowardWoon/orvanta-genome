"""Slim analytic table (no free-text columns) to fit limited disk; text features derived as flags."""
import common, time
t=time.time()
con = common.connect()
con.execute("""COPY (SELECT row_number() OVER () AS rid, EPOCH_SECONDS::BIGINT AS epoch, ts, d, hr, dow, CURRENCY_CODE AS cur, amt, dur, fx, pc,
  ORDERING_BIC8 AS obic, BENEFICIARY_BIC8 AS bbic, BIC8_PATH AS path, CONTINUITY_QFLAG AS cont, TRANSACTION_TYPE_CODE AS ttype,
  ORDERING_ACCOUNT AS oacc, BENEFICIARY_ACCOUNT AS bacc, ORDERING_TYPE AS otype, BENEFICIARY_TYPE AS btype, ANOMALY_TYPE AS anom,
  o_bank_cc, b_bank_cc, o_cust_cc, b_cust_cc, cur_cc, path_n, gaps, o_iban, b_iban, o_struct, b_struct
  FROM p) TO 'slim.parquet' (FORMAT parquet, COMPRESSION zstd)""")
print("built", time.time()-t)
