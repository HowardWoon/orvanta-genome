import duckdb, pandas as pd
pd.set_option("display.width",250,"display.max_columns",40)
con=duckdb.connect(); con.execute("SET threads=10; SET memory_limit='9GB'; SET enable_progress_bar=false")
con.execute("CREATE VIEW t AS SELECT * FROM 'C:/Users/Acer/Documents/UMDAC NaiLong/data/processed/slim.parquet'")
def q(s): print(con.execute(s).df().to_string(),"\n")
