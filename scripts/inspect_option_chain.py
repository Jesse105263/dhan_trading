import pandas as pd
from dhanhq import DhanContext, dhanhq
from config import CLIENT_ID, ACCESS_TOKEN

SYMBOL = "ZYDUSLIFE"

dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(dhan_context)

security_master = pd.read_csv("security_id_list.csv", low_memory=False)

match = security_master[
    (security_master["SEM_TRADING_SYMBOL"].astype(str) == SYMBOL)
    &
    (security_master["SEM_EXM_EXCH_ID"].astype(str) == "NSE")
    &
    (security_master["SEM_SERIES"].astype(str) == "EQ")
]

if match.empty:
    print(f"Security ID not found for {SYMBOL}")
    exit()

security_id = int(match.iloc[0]["SEM_SMST_SECURITY_ID"])

expiry_response = dhan.expiry_list(
    under_security_id=security_id,
    under_exchange_segment="NSE_EQ"
)

print("\nExpiry Response")
print(expiry_response)

expiry = expiry_response["data"]["data"][0]

option_response = dhan.option_chain(
    under_security_id=security_id,
    under_exchange_segment="NSE_EQ",
    expiry=expiry
)

print("\nOption Chain Status")
print(option_response["status"])

data = option_response["data"]["data"]
spot = data["last_price"]
oc = data["oc"]

print("\nSpot:", spot)
print("Expiry:", expiry)

rows = []

for strike, row in oc.items():
    strike_price = float(strike)

    if abs(strike_price - spot) <= spot * 0.05:
        ce = row["ce"]
        pe = row["pe"]

        rows.append({
            "strike": strike_price,
            "ce_ltp": ce["last_price"],
            "ce_iv": ce["implied_volatility"],
            "ce_oi": ce["oi"],
            "pe_ltp": pe["last_price"],
            "pe_iv": pe["implied_volatility"],
            "pe_oi": pe["oi"],
        })

df = pd.DataFrame(rows)
df = df.sort_values("strike")

print("\nNearby Option Chain")
print(df.to_string(index=False))