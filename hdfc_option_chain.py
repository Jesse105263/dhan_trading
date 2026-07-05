from dhanhq import DhanContext, dhanhq
import pandas as pd
from config import CLIENT_ID, ACCESS_TOKEN

dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(dhan_context)

option_chain_response = dhan.option_chain(
    under_security_id=1333,
    under_exchange_segment="NSE_EQ",
    expiry="2026-06-30"
)

spot = option_chain_response["data"]["data"]["last_price"]
oc = option_chain_response["data"]["data"]["oc"]

rows = []

for strike, row in oc.items():
    strike_price = float(strike)

    if 700 <= strike_price <= 850:
        ce = row["ce"]
        pe = row["pe"]

        rows.append({
            "strike": strike_price,

            "ce_ltp": ce["last_price"],
            "ce_oi": ce["oi"],
            "ce_iv": round(ce["implied_volatility"], 2),
            "ce_delta": round(ce["greeks"]["delta"], 3),

            "pe_ltp": pe["last_price"],
            "pe_oi": pe["oi"],
            "pe_iv": round(pe["implied_volatility"], 2),
            "pe_delta": round(pe["greeks"]["delta"], 3),
        })

option_chain = pd.DataFrame(rows)
option_chain = option_chain.sort_values("strike")

atm_row = option_chain.iloc[(option_chain["strike"] - spot).abs().argsort()[:1]]

atm_strike = atm_row["strike"].iloc[0]
atm_ce_price = atm_row["ce_ltp"].iloc[0]
atm_pe_price = atm_row["pe_ltp"].iloc[0]

straddle_cost = atm_ce_price + atm_pe_price
upside_breakeven = atm_strike + straddle_cost
downside_breakeven = atm_strike - straddle_cost

atm_ce_iv = atm_row["ce_iv"].iloc[0]
atm_pe_iv = atm_row["pe_iv"].iloc[0]
atm_avg_iv = (atm_ce_iv + atm_pe_iv) / 2

max_call_row = option_chain.loc[option_chain["ce_oi"].idxmax()]
max_put_row = option_chain.loc[option_chain["pe_oi"].idxmax()]

print("\nATM Summary")
print("Spot Price:", spot)
print("ATM Strike:", atm_strike)
print("CE Price:", atm_ce_price)
print("PE Price:", atm_pe_price)
print("Straddle Cost:", round(straddle_cost, 2))
print("Upside Breakeven:", round(upside_breakeven, 2))
print("Downside Breakeven:", round(downside_breakeven, 2))
print("ATM Average IV:", round(atm_avg_iv, 2))

print("\nOI Analysis")
print(f"Highest Call OI : Strike {max_call_row['strike']} OI={int(max_call_row['ce_oi'])}")
print(f"Highest Put OI  : Strike {max_put_row['strike']} OI={int(max_put_row['pe_oi'])}")

option_chain.to_csv("option_chain.csv", index=False)

print("\nOption Chain")
print(option_chain.to_string(index=False))

print("\nSaved to option_chain.csv")