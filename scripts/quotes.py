from dhanhq import DhanContext, dhanhq
from config import CLIENT_ID, ACCESS_TOKEN

dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(dhan_context)

stocks = {
    "MCX": 31181,
    "BSE": 19585,
    "CDSL": 21174,
    "ADANIENT": 25,
    "ADANIPOWER": 17388,
}

securities = {
    "NSE_EQ": list(stocks.values())
}

response = dhan.quote_data(securities)

if response["status"] != "success":
    print("API failed:")
    print(response)
else:
    data = response["data"]["data"]["NSE_EQ"]

    print("\nSTOCK QUOTES")
    print("-" * 90)
    print(f"{'Symbol':<12} {'Price':>10} {'Open':>10} {'High':>10} {'Low':>10} {'Volume':>12}")
    print("-" * 90)

    for symbol, security_id in stocks.items():
        quote = data[str(security_id)]
        ohlc = quote["ohlc"]

        print(
            f"{symbol:<12} "
            f"{quote['last_price']:>10} "
            f"{ohlc['open']:>10} "
            f"{ohlc['high']:>10} "
            f"{ohlc['low']:>10} "
            f"{quote['volume']:>12}"
        )