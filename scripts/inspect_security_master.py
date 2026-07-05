import pandas as pd

security_master = pd.read_csv(
    "security_id_list.csv",
    low_memory=False
)

print("\nColumns:\n")
for c in security_master.columns:
    print(c)

print("\n\nSample Option Rows:\n")

option_rows = security_master[
    security_master["SEM_INSTRUMENT_NAME"].astype(str).str.contains("OPT", na=False)
]

print(option_rows.head(5).T)