import time
from datetime import date
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import CLIENT_ID, ACCESS_TOKEN
from services.expiry_service import ExpiryService

SECURITY_MASTER_FILE = "security_id_list.csv"
UNIVERSE_FILE = "fno_universe.csv"

OPTION_CHAIN_OUT = "option_chain_scanner.csv"
OPTION_CHAIN_DETAILS_OUT = "option_chain_details.csv"
FAILURES_OUT = "option_chain_failures.csv"

BASE_URL = "https://api.dhan.co/v2"
MAX_WORKERS = 4

HEADERS = {
    "access-token": ACCESS_TOKEN,
    "client-id": CLIENT_ID,
    "Content-Type": "application/json",
}


def safe_float(x):
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def safe_int(x):
    try:
        if x is None or x == "":
            return 0
        return int(float(x))
    except Exception:
        return 0


def clean_symbol(x):
    return str(x).strip().upper().replace("-EQ", "")


def find_col(df, possible_names):
    lower_map = {c.lower().strip(): c for c in df.columns}
    for name in possible_names:
        if name.lower().strip() in lower_map:
            return lower_map[name.lower().strip()]
    return None


def post_with_retries(url, payload, retries=3, sleep_seconds=0.6):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, headers=HEADERS, json=payload, timeout=20)

            if r.status_code == 429:
                time.sleep(sleep_seconds * attempt * 2)
                continue

            if r.status_code >= 500:
                time.sleep(sleep_seconds * attempt)
                continue

            data = r.json()

            if r.status_code != 200:
                return None, f"HTTP {r.status_code}: {data}"

            return data, None

        except Exception as e:
            last_error = str(e)
            time.sleep(sleep_seconds * attempt)

    return None, last_error or "request_failed"


def load_security_master():
    df = pd.read_csv(SECURITY_MASTER_FILE, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    return df


def load_universe():
    universe = pd.read_csv(UNIVERSE_FILE)
    universe.columns = [c.strip() for c in universe.columns]

    if "symbol" not in universe.columns:
        raise Exception("fno_universe.csv must contain a symbol column")

    return sorted({clean_symbol(x) for x in universe["symbol"].dropna()})


def build_underlying_lookup(master):
    exch_col = find_col(master, ["SEM_EXM_EXCH_ID", "exchange", "exch_id"])
    seg_col = find_col(master, ["SEM_SEGMENT", "segment"])
    inst_col = find_col(master, ["SEM_INSTRUMENT_NAME", "instrument", "instrument_name"])
    sec_col = find_col(master, ["SEM_SMST_SECURITY_ID", "security_id", "securityId"])
    trading_col = find_col(master, ["SEM_TRADING_SYMBOL", "trading_symbol", "symbol"])
    custom_col = find_col(master, ["SEM_CUSTOM_SYMBOL", "custom_symbol", "name"])

    if sec_col is None:
        raise Exception("security_id column not found in security master")

    df = master.copy()

    if exch_col:
        df = df[df[exch_col].astype(str).str.upper().eq("NSE")]

    if seg_col:
        df = df[df[seg_col].astype(str).str.upper().isin(["E", "NSE_EQ", "EQ"])]

    if inst_col:
        df = df[df[inst_col].astype(str).str.upper().isin(["EQUITY", "EQ"])]

    lookup = {}

    for _, row in df.iterrows():
        security_id = str(int(float(row[sec_col])))

        if trading_col:
            key = clean_symbol(row[trading_col])
            if key and key not in lookup:
                lookup[key] = security_id

        if custom_col:
            key = clean_symbol(row[custom_col])
            if key and key not in lookup:
                lookup[key] = security_id

    return lookup


def get_expiry_list(underlying_security_id):
    url = f"{BASE_URL}/optionchain/expirylist"

    payload = {
        "UnderlyingScrip": int(underlying_security_id),
        "UnderlyingSeg": "NSE_EQ",
    }

    data, error = post_with_retries(url, payload)

    if error:
        return [], error

    expiry_data = data.get("data", data)

    if isinstance(expiry_data, dict):
        expiries = expiry_data.get("data", expiry_data.get("expiry_list", []))
    elif isinstance(expiry_data, list):
        expiries = expiry_data
    else:
        expiries = []

    return [str(x)[:10] for x in expiries if x], None


def get_option_chain(underlying_security_id, expiry):
    url = f"{BASE_URL}/optionchain"

    payload = {
        "UnderlyingScrip": int(underlying_security_id),
        "UnderlyingSeg": "NSE_EQ",
        "Expiry": expiry,
    }

    return post_with_retries(url, payload)


def extract_chain_metrics(symbol, underlying_security_id, expiry, response):
    data = response.get("data", response)

    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]

    spot = (
        safe_float(data.get("last_price"))
        or safe_float(data.get("ltp"))
        or safe_float(data.get("underlying_value"))
        or safe_float(data.get("spot"))
    )

    oc = data.get("oc") or data.get("option_chain") or data.get("optionChain")

    if not isinstance(oc, dict) or len(oc) == 0:
        raise Exception("empty_option_chain")

    rows = []

    for strike_raw, item in oc.items():
        strike = safe_float(strike_raw)

        if strike is None:
            strike = safe_float(item.get("strike_price") or item.get("strikePrice"))

        if strike is None:
            continue

        ce = item.get("ce") or item.get("CE") or {}
        pe = item.get("pe") or item.get("PE") or {}

        ce_ltp = safe_float(ce.get("last_price")) or safe_float(ce.get("ltp")) or safe_float(ce.get("last_traded_price"))
        pe_ltp = safe_float(pe.get("last_price")) or safe_float(pe.get("ltp")) or safe_float(pe.get("last_traded_price"))

        ce_iv = safe_float(ce.get("implied_volatility")) or safe_float(ce.get("iv")) or safe_float(ce.get("IV"))
        pe_iv = safe_float(pe.get("implied_volatility")) or safe_float(pe.get("iv")) or safe_float(pe.get("IV"))

        ce_oi = safe_int(ce.get("oi") or ce.get("open_interest") or ce.get("openInterest"))
        pe_oi = safe_int(pe.get("oi") or pe.get("open_interest") or pe.get("openInterest"))

        rows.append(
            {
                "symbol": symbol,
                "underlying_security_id": underlying_security_id,
                "expiry": expiry,
                "spot": spot,
                "strike": strike,
                "ce_ltp": ce_ltp,
                "pe_ltp": pe_ltp,
                "ce_iv": ce_iv,
                "pe_iv": pe_iv,
                "ce_oi": ce_oi,
                "pe_oi": pe_oi,
            }
        )

    chain = pd.DataFrame(rows)

    if chain.empty:
        raise Exception("no_valid_strikes")

    if spot is None:
        valid = chain.dropna(subset=["ce_ltp", "pe_ltp"])
        if valid.empty:
            raise Exception("spot_missing")
        spot = valid["strike"].median()
        chain["spot"] = spot

    chain["distance"] = (chain["strike"] - spot).abs()
    atm = chain.sort_values("distance").iloc[0]

    atm_ce_ltp = safe_float(atm["ce_ltp"]) or 0
    atm_pe_ltp = safe_float(atm["pe_ltp"]) or 0
    straddle_cost = atm_ce_ltp + atm_pe_ltp

    iv_values = []
    if safe_float(atm["ce_iv"]) is not None:
        iv_values.append(safe_float(atm["ce_iv"]))
    if safe_float(atm["pe_iv"]) is not None:
        iv_values.append(safe_float(atm["pe_iv"]))

    atm_iv = sum(iv_values) / len(iv_values) if iv_values else None

    calls_above = chain[chain["strike"] >= spot].copy()
    puts_below = chain[chain["strike"] <= spot].copy()

    if calls_above.empty:
        calls_above = chain.copy()

    if puts_below.empty:
        puts_below = chain.copy()

    max_call = calls_above.sort_values("ce_oi", ascending=False).iloc[0]
    max_put = puts_below.sort_values("pe_oi", ascending=False).iloc[0]

    breakeven_pct = (straddle_cost / spot) * 100 if spot else None

    summary = {
        "symbol": symbol,
        "underlying_security_id": underlying_security_id,
        "expiry": expiry,
        "spot": round(spot, 2),
        "atm_strike": atm["strike"],
        "atm_ce_ltp": round(atm_ce_ltp, 2),
        "atm_pe_ltp": round(atm_pe_ltp, 2),
        "atm_iv": round(atm_iv, 2) if atm_iv is not None else None,
        "straddle_cost": round(straddle_cost, 2),
        "breakeven_pct": round(breakeven_pct, 2) if breakeven_pct is not None else None,
        "max_call_oi_strike": max_call["strike"],
        "max_call_oi": int(max_call["ce_oi"]),
        "max_put_oi_strike": max_put["strike"],
        "max_put_oi": int(max_put["pe_oi"]),
        "strikes_count": len(chain),
    }

    return summary, chain.to_dict("records")


def scan_symbol(symbol, underlying_lookup):
    underlying_security_id = underlying_lookup.get(symbol)

    if not underlying_security_id:
        return None, [], {
            "symbol": symbol,
            "stage": "resolve_underlying_security_id",
            "reason": "underlying_security_id_not_found",
        }

    expiries, expiry_error = get_expiry_list(underlying_security_id)

    if expiry_error:
        return None, [], {
            "symbol": symbol,
            "underlying_security_id": underlying_security_id,
            "stage": "expiry_list",
            "reason": expiry_error,
        }

    if not expiries:
        return None, [], {
            "symbol": symbol,
            "underlying_security_id": underlying_security_id,
            "stage": "expiry_list",
            "reason": "no_expiries_returned",
        }

    parsed_expiries = [
        date.fromisoformat(expiry)
        for expiry in expiries
    ]
    eligible_expiries = ExpiryService.eligible_expiries_from(
        parsed_expiries,
        as_of_date=date.today(),
    )
    last_error = None

    for expiry_date in eligible_expiries[:3]:
        expiry = expiry_date.isoformat()
        response, chain_error = get_option_chain(underlying_security_id, expiry)

        if chain_error:
            last_error = chain_error
            continue

        try:
            summary, details = extract_chain_metrics(symbol, underlying_security_id, expiry, response)
            return summary, details, None
        except Exception as e:
            last_error = str(e)
            continue

    return None, [], {
        "symbol": symbol,
        "underlying_security_id": underlying_security_id,
        "stage": "option_chain",
        "reason": last_error or "all_expiries_failed",
    }


def main():
    start = time.time()

    master = load_security_master()
    symbols = load_universe()
    underlying_lookup = build_underlying_lookup(master)

    print(f"Loaded F&O symbols: {len(symbols)}")
    print(f"Using {MAX_WORKERS} workers")

    results = []
    details = []
    failures = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(scan_symbol, symbol, underlying_lookup): symbol
            for symbol in symbols
        }

        completed = 0

        for future in as_completed(future_map):
            symbol = future_map[future]
            completed += 1

            try:
                summary, detail_rows, failure = future.result()

                if summary:
                    results.append(summary)
                    details.extend(detail_rows)
                    print(f"[{completed}/{len(symbols)}] OK: {symbol}")
                else:
                    failures.append(failure)
                    print(f"[{completed}/{len(symbols)}] FAILED: {symbol} | {failure.get('reason')}")

            except Exception as e:
                failures.append(
                    {
                        "symbol": symbol,
                        "stage": "thread_execution",
                        "reason": str(e),
                    }
                )
                print(f"[{completed}/{len(symbols)}] FAILED: {symbol} | {e}")

    results_df = pd.DataFrame(results)
    details_df = pd.DataFrame(details)
    failures_df = pd.DataFrame(failures)

    if not results_df.empty:
        results_df = results_df.sort_values("symbol").reset_index(drop=True)

    if not details_df.empty:
        details_df = details_df.sort_values(["symbol", "strike"]).reset_index(drop=True)

    if not failures_df.empty:
        failures_df = failures_df.sort_values("symbol").reset_index(drop=True)

    results_df.to_csv(OPTION_CHAIN_OUT, index=False)
    details_df.to_csv(OPTION_CHAIN_DETAILS_OUT, index=False)
    failures_df.to_csv(FAILURES_OUT, index=False)

    elapsed = round(time.time() - start, 2)

    print("")
    print("Done")
    print(f"Success: {len(results_df)}")
    print(f"Failures: {len(failures_df)}")
    print(f"Option detail rows: {len(details_df)}")
    print(f"Elapsed seconds: {elapsed}")
    print(f"Saved: {OPTION_CHAIN_OUT}")
    print(f"Saved: {OPTION_CHAIN_DETAILS_OUT}")
    print(f"Saved: {FAILURES_OUT}")


if __name__ == "__main__":
    main()