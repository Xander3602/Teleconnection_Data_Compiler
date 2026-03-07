import pandas as pd
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")

df = pd.read_csv(os.path.join(DATA_DIR, "JMA_IOD_Data.csv"))

print(df.head())

# Reshape DataFrame so it has columns: year, month, DMI index
df_long = df.melt(id_vars=df.columns[0], var_name="month", value_name="DMI index")
df_long = df_long.rename(columns={df.columns[0]: "year"})

print(df_long.head())

month_mapping = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}
df_long["month"] = df_long["month"].map(month_mapping)

#reorder based on oldest year to newest year
df_long = df_long.sort_values(by=["year", "month"])

print(df_long.head())

#convert year to integer
df_long["year"] = df_long["year"].astype(int)

print(df_long.head())

#save to csv
df_long.to_csv(os.path.join(DATA_DIR, "JMA_IOD_Data_long.csv"), index=False)