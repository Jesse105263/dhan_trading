from dhanhq import DhanContext, dhanhq
import pandas as pd
from config import CLIENT_ID, ACCESS_TOKEN

dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(dhan_context)

data = dhan.historical_daily_data(
    security_id=2885,
    exchange_segment="NSE_EQ",
    instrument_type="EQUITY",
    from_date="2026-05-01",
    to_date="2026-06-20"
)

df = pd.DataFrame(data["data"])
df["daily_return_pct"] = (df["close"] / df["close"].shift(1) - 1) * 100

print(df[["close", "daily_return_pct"]].head(10))
print("\nAverage Daily Move (%)")
print(df["daily_return_pct"].std())
print(df.head())