import pandas as pd

watchlist = pd.read_csv("watchlist.csv")
security_master = pd.read_csv("security_id_list.csv", low_memory=False)

for symbol in watchlist["symbol"]:
    match = security_master[
        (security_master["SEM_TRADING_SYMBOL"].astype(str) == symbol)
        & (security_master["SEM_EXM_EXCH_ID"].astype(str) == "NSE")
        & (security_master["SEM_SERIES"].astype(str) == "EQ")
    ]

    print("\n", symbol)
    print(match[["SEM_SMST_SECURITY_ID", "SEM_TRADING_SYMBOL", "SM_SYMBOL_NAME"]].to_string(index=False))