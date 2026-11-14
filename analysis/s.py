import duckdb, pandas as pd, sys
pd.set_option("display.width",250,"display.max_columns",50,"display.max_colwidth",90)
con=duckdb.connect(); con.execute("SET threads=10; SET memory_limit='9GB'; SET enable_progress_bar=false")
con.execute("CREATE VIEW t AS SELECT * FROM 'slim.parquet'")
def q(s,n=80):
    df=con.execute(s).df(); print(df.head(n).to_string(),"\n"); return df
