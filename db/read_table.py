import psycopg
import pandas as pd

import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

with psycopg.connect(host="localhost", port=5433, dbname="postgres", user="postgres") as conn:
	df = pd.read_sql("SELECT * FROM llm.subv_llm_detail", conn)

print(f"\nDataFrame shape {df.shape}\n")

print(f"DataFrame columns: {df.columns}\n")

print(f"DataFrame head:\n{df.head(10)}\n")