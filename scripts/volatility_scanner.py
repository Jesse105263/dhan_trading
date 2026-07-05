import time
from dhanhq import DhanContext, dhanhq
import pandas as pd
from config import CLIENT_ID, ACCESS_TOKEN

dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(dhan_context)

watchlist = pd.read_csv("watchlist.csv")
watchlist = watchlist.drop_duplicates(subset=["symbol"])

security_master = pd.read_csv("security_id_list.csv", low_memory=False)

results = []

for symbol in watchlist["symbol"]:

    match = security_master[
        (security_master["SEM_TRADING_SYMBOL"].astype(str) == symbol)
        & (security_master["SEM_EXM_EXCH_ID"].astype(str) == "NSE")
        & (security_master["SEM_SERIES"].astype(str) == "EQ")
    ]

    if match.empty:
        print(f"Skipping {symbol}: security ID not found")
        continue

    security_id = int(match.iloc[0]["SEM_SMST_SECURITY_ID"])

    try:
        data = dhan.historical_daily_data(
            security_id=security_id,
            exchange_segment="NSE_EQ",
            instrument_type="EQUITY",
            from_date="2026-04-01",
            to_date="2026-06-20"
        )

        if data["status"] != "success":
            print(f"\n{symbol} failed:")
            print(data)
            continue

        if not isinstance(data.get("data"), dict):
            print(f"\n{symbol} returned unexpected data:")
            print(data)
            continue

        df = pd.DataFrame(data["data"])

        if df.empty or "close" not in df.columns:
            print(f"\n{symbol}: empty or invalid historical data")
            continue

        df["daily_return_pct"] = (
            df["close"] / df["close"].shift(1) - 1
        ) * 100

        last_close = df["close"].iloc[-1]

        hv20_daily = df["daily_return_pct"].tail(20).std()
        hv60_daily = df["daily_return_pct"].tail(60).std()

        hv20_annualized = hv20_daily * (252 ** 0.5)
        hv60_annualized = hv60_daily * (252 ** 0.5)

        high_period = df["high"].max()
        low_period = df["low"].min()

        pct_from_high = ((last_close - high_period) / high_period) * 100
        pct_from_low = ((last_close - low_period) / low_period) * 100

        avg_volume_20d = df["volume"].tail(20).mean()
        latest_volume = df["volume"].iloc[-1]

        relative_volume = latest_volume / avg_volume_20d

        results.append({
            "symbol": symbol,
            "security_id": security_id,
            "last_close": round(last_close, 2),
            "hv20_daily_pct": round(hv20_daily, 2),
            "hv60_daily_pct": round(hv60_daily, 2),
            "hv20_annualized_pct": round(hv20_annualized, 2),
            "hv60_annualized_pct": round(hv60_annualized, 2),
            "period_high": round(high_period, 2),
            "period_low": round(low_period, 2),
            "pct_from_period_high": round(pct_from_high, 2),
            "pct_from_period_low": round(pct_from_low, 2),
            "latest_volume": int(latest_volume),
            "avg_volume_20d": int(avg_volume_20d),
            "relative_volume": round(relative_volume, 2)
        })

        time.sleep(1)

    except Exception as e:
        print(f"Failed for {symbol}: {e}")

results_df = pd.DataFrame(results)

if results_df.empty:
    print("No valid results.")
else:
    results_df = results_df.drop_duplicates(subset=["symbol"])
    results_df = results_df.sort_values(by="hv20_daily_pct", ascending=False)

    print("\nVolatility Ranking")
    print(results_df.to_string(index=False))

    results_df.to_csv("volatility_ranking.csv", index=False)
    print("\nSaved to volatility_ranking.csv")