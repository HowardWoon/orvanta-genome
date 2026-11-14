"""Convert the raw Swift CSV (multi-line quoted fields) to Parquet for fast analysis. Raw file is NOT modified."""
import duckdb, time, sys
t=time.time()
con=duckdb.connect()
con.execute("SET threads=10; SET memory_limit='10GB'; SET preserve_insertion_order=false")
con.execute("""
COPY (SELECT * EXCLUDE (DISCLAIMER) FROM read_csv('swift_umdac_datathon_2026_fictitious_payment_data.csv',
  header=true, quote='"', escape='"', all_varchar=true, max_line_size=10000000, parallel=false))
TO 'analysis/payments.parquet' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 500000)""")
print("done", time.time()-t, con.execute("select count(*) from 'analysis/payments.parquet'").fetchone())
