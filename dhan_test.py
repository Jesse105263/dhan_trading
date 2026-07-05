from dhanhq import DhanContext, dhanhq
from config import CLIENT_ID, ACCESS_TOKEN

dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(dhan_context)

# print(dir(dhan))

# print(dhan.quote_data)

# import inspect
# print(inspect.signature(dhan.quote_data))

# help(dhan.quote_data)

# import inspect
# print(inspect.signature(dhan.fetch_security_list))

# print(dhan.fetch_security_list())

data = dhan.option_chain(
    31181,
    "NSE_EQ",
    "2026-06-30"
)

chain = data["data"]["data"]
spot = chain["last_price"]
oc = chain["oc"]

print("Spot:", spot)

for strike, row in oc.items():
    strike_price = float(strike)

    if 2600 <= strike_price <= 3100:
        ce = row["ce"]
        pe = row["pe"]

        print(
            strike_price,
            "CE LTP:", ce["last_price"],
            "CE OI:", ce["oi"],
            "CE IV:", round(ce["implied_volatility"], 2),
            "| PE LTP:", pe["last_price"],
            "PE OI:", pe["oi"],
            "PE IV:", round(pe["implied_volatility"], 2)
        )