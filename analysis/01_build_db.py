"""Materialise the enriched view into a DuckDB database for fast repeated analysis."""
import duckdb, common, time
t=time.time()
con = common.connect()
con.execute("ATTACH 'swift.duckdb' AS db")
con.execute("CREATE OR REPLACE TABLE db.t AS SELECT * FROM p")
print("built", time.time()-t, con.execute("select count(*) from db.t").fetchone())
