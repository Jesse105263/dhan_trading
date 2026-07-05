import pandas as pd
import numpy as np

VOLATILITY_FILE = "volatility_ranking.csv"
OPTION_CHAIN_FILE = "option_chain_scanner.csv"
OPTION_CHAIN_DETAILS_FILE = "option_chain_details.csv"
SECURITY_MASTER_FILE = "security_id_list.csv"

OUTPUT_FILE = "daily_scanner.csv"
TOP_OUTPUT_FILE = "trade_candidates.csv"

MAX_LOSS_LIMIT = 20000


def safe_float(x):
    try:
        if pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def normalize_col_name(c):
    return str(c).strip().lower().replace(" ", "_").replace("-", "_")


def normalize_input_columns(df):
    df.columns = [normalize_col_name(c) for c in df.columns]
    return df


def clean_symbol(x):
    return str(x).strip().upper().replace("-EQ", "")


def ensure_col(df, col, default=np.nan):
    if col not in df.columns:
        df[col] = default
    return df


def normalize_0_100(series):
    series = pd.to_numeric(series, errors="coerce")
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series([50] * len(series), index=series.index)

    return ((series - min_val) / (max_val - min_val)) * 100


def rename_common_columns(df):
    rename_map = {}

    for c in df.columns:
        if c in ["trading_symbol", "symbol_name", "sem_trading_symbol"]:
            rename_map[c] = "symbol"
        elif c in ["hv_20", "historical_volatility_20", "historical_volatility20"]:
            rename_map[c] = "hv20"
        elif c in ["hv_60", "historical_volatility_60", "historical_volatility60"]:
            rename_map[c] = "hv60"
        elif c in ["rel_volume", "rvol", "rv"]:
            rename_map[c] = "relative_volume"

    df.rename(columns=rename_map, inplace=True)
    return df


def extract_underlying_symbol(raw):
    raw = clean_symbol(raw)

    if "-" in raw:
        return raw.split("-")[0].strip().upper()

    parts = raw.split()
    if len(parts) > 0:
        return parts[0].strip().upper()

    return raw


def find_col(df, possible_names):
    lookup = {c.lower().strip(): c for c in df.columns}
    for name in possible_names:
        key = name.lower().strip()
        if key in lookup:
            return lookup[key]
    return None


def build_lot_size_lookup():
    master = pd.read_csv(SECURITY_MASTER_FILE, low_memory=False)
    master.columns = [c.strip() for c in master.columns]

    exch_col = find_col(master, ["SEM_EXM_EXCH_ID", "exchange", "exch_id"])
    inst_col = find_col(master, ["SEM_INSTRUMENT_NAME", "instrument", "instrument_name"])
    trading_col = find_col(master, ["SEM_TRADING_SYMBOL", "trading_symbol", "symbol"])
    custom_col = find_col(master, ["SEM_CUSTOM_SYMBOL", "custom_symbol", "name"])
    lot_col = find_col(master, ["SEM_LOT_UNITS", "SEM_LOT_SIZE", "lot_size", "lot_units", "lot"])

    if lot_col is None:
        print("WARNING: Lot size column not found in security master.")
        return {}

    df = master.copy()

    if exch_col:
        df = df[df[exch_col].astype(str).str.upper().eq("NSE")]

    if inst_col:
        df = df[df[inst_col].astype(str).str.upper().isin(["OPTSTK", "FUTSTK"])]

    lookup = {}

    for _, row in df.iterrows():
        lot_size = safe_float(row[lot_col])

        if pd.isna(lot_size) or lot_size <= 0:
            continue

        symbols = []

        if trading_col:
            symbols.append(extract_underlying_symbol(row[trading_col]))

        if custom_col:
            symbols.append(extract_underlying_symbol(row[custom_col]))

        for symbol in symbols:
            if symbol and symbol not in lookup:
                lookup[symbol] = int(lot_size)

    return lookup


def classify_bias(row):
    spot = row.get("spot", np.nan)
    call_wall = row.get("max_call_oi_strike", np.nan)
    put_wall = row.get("max_put_oi_strike", np.nan)
    rvol = row.get("relative_volume", np.nan)

    if pd.isna(spot) or pd.isna(call_wall) or pd.isna(put_wall):
        return "Long Volatility"

    if spot > put_wall and not pd.isna(rvol) and rvol >= 1.2:
        return "Long Call"

    if spot < call_wall and not pd.isna(rvol) and rvol >= 1.2:
        return "Long Put"

    return "Watch Only"


def build_reason(row):
    reasons = []

    hv20 = row.get("hv20", np.nan)
    hv60 = row.get("hv60", np.nan)
    atm_iv = row.get("atm_iv", np.nan)
    rvol = row.get("relative_volume", np.nan)
    breakeven = row.get("breakeven_pct", np.nan)
    spot = row.get("spot", np.nan)
    call_wall = row.get("max_call_oi_strike", np.nan)
    put_wall = row.get("max_put_oi_strike", np.nan)

    if not pd.isna(hv20) and not pd.isna(hv60):
        if hv20 > hv60:
            reasons.append("HV20 above HV60")
        else:
            reasons.append("HV20 below HV60")

    if not pd.isna(atm_iv) and not pd.isna(hv20):
        if atm_iv <= hv20:
            reasons.append("ATM IV below/equal HV20")
        elif atm_iv <= hv20 * 1.25:
            reasons.append("ATM IV reasonable vs HV20")
        else:
            reasons.append("ATM IV expensive vs HV20")

    if not pd.isna(rvol):
        if rvol >= 2:
            reasons.append("Very strong relative volume")
        elif rvol >= 1.2:
            reasons.append("Strong relative volume")
        else:
            reasons.append("Weak relative volume")

    if not pd.isna(breakeven):
        if breakeven <= 3:
            reasons.append("Cheap straddle")
        elif breakeven <= 5:
            reasons.append("Moderate straddle cost")
        elif breakeven <= 7:
            reasons.append("Slightly expensive straddle")
        else:
            reasons.append("Expensive straddle")

    if not pd.isna(spot) and not pd.isna(put_wall) and spot > put_wall:
        reasons.append("Spot above Put OI support")

    if not pd.isna(spot) and not pd.isna(call_wall) and spot < call_wall:
        reasons.append("Spot below Call OI resistance")

    return " | ".join(reasons)


def suggest_rough_strike(row):
    spot = row.get("spot", np.nan)
    atm = row.get("atm_strike", np.nan)

    if pd.isna(spot):
        return np.nan

    if pd.isna(atm):
        return spot

    return atm


def suggest_tradable_option(row, details):
    symbol = row.get("symbol", "")
    bias = row.get("bias", "")
    rough_strike = row.get("rough_suggested_strike", np.nan)

    if pd.isna(rough_strike):
        return pd.Series(["Watch", np.nan, np.nan])

    chain = details[details["symbol"] == symbol].copy()

    if chain.empty:
        return pd.Series(["Watch", np.nan, np.nan])

    chain["strike_distance"] = (chain["strike"] - rough_strike).abs()
    best = chain.sort_values("strike_distance").iloc[0]

    if bias == "Long Call":
        action = "Buy CE"
        premium = best.get("ce_ltp", np.nan)

    elif bias == "Long Put":
        action = "Buy PE"
        premium = best.get("pe_ltp", np.nan)

    elif bias == "Long Volatility":
        action = "Buy ATM Straddle"
        ce = best.get("ce_ltp", 0)
        pe = best.get("pe_ltp", 0)
        premium = (0 if pd.isna(ce) else ce) + (0 if pd.isna(pe) else pe)

    else:
        action = "Watch"
        premium = np.nan

    return pd.Series([action, best["strike"], premium])


def main():
    vol = pd.read_csv(VOLATILITY_FILE)
    opt = pd.read_csv(OPTION_CHAIN_FILE)
    details = pd.read_csv(OPTION_CHAIN_DETAILS_FILE)

    vol = rename_common_columns(normalize_input_columns(vol))
    opt = rename_common_columns(normalize_input_columns(opt))
    details = rename_common_columns(normalize_input_columns(details))

    lot_lookup = build_lot_size_lookup()

    if "symbol" not in vol.columns:
        raise Exception(f"{VOLATILITY_FILE} missing required column: symbol")

    if "symbol" not in opt.columns:
        raise Exception(f"{OPTION_CHAIN_FILE} missing required column: symbol")

    if "symbol" not in details.columns:
        raise Exception(f"{OPTION_CHAIN_DETAILS_FILE} missing required column: symbol")

    vol["symbol"] = vol["symbol"].apply(clean_symbol)
    opt["symbol"] = opt["symbol"].apply(clean_symbol)
    details["symbol"] = details["symbol"].apply(clean_symbol)

    df = pd.merge(vol, opt, on="symbol", how="inner")

    for col in [
        "hv20",
        "hv60",
        "relative_volume",
        "atm_iv",
        "straddle_cost",
        "breakeven_pct",
        "spot",
        "atm_strike",
        "max_call_oi_strike",
        "max_put_oi_strike",
        "max_call_oi",
        "max_put_oi",
    ]:
        ensure_col(df, col)
        df[col] = df[col].apply(safe_float)

    for col in ["strike", "ce_ltp", "pe_ltp", "ce_iv", "pe_iv", "ce_oi", "pe_oi"]:
        ensure_col(details, col)
        details[col] = details[col].apply(safe_float)

    df["hv_expansion"] = df["hv20"] - df["hv60"]
    df["hv_iv_gap"] = df["hv20"] - df["atm_iv"]

    df["call_wall_distance_pct"] = ((df["max_call_oi_strike"] - df["spot"]) / df["spot"]) * 100
    df["put_wall_distance_pct"] = ((df["spot"] - df["max_put_oi_strike"]) / df["spot"]) * 100

    df["hv20_score"] = normalize_0_100(df["hv20"])
    df["rvol_score"] = normalize_0_100(df["relative_volume"])
    df["hv_expansion_score"] = normalize_0_100(df["hv_expansion"])
    df["hv_iv_gap_score"] = normalize_0_100(df["hv_iv_gap"])
    df["cheap_option_score"] = 100 - normalize_0_100(df["breakeven_pct"])
    df["call_wall_score"] = normalize_0_100(df["call_wall_distance_pct"])
    df["put_wall_score"] = normalize_0_100(df["put_wall_distance_pct"])

    df["trade_score"] = (
        df["hv20_score"] * 0.20
        + df["rvol_score"] * 0.20
        + df["hv_expansion_score"] * 0.20
        + df["hv_iv_gap_score"] * 0.20
        + df["cheap_option_score"] * 0.10
        + df["call_wall_score"] * 0.05
        + df["put_wall_score"] * 0.05
    )

    df["trade_score"] = df["trade_score"].round(2)
    df["bias"] = df.apply(classify_bias, axis=1)
    df["reason"] = df.apply(build_reason, axis=1)
    df["rough_suggested_strike"] = df.apply(suggest_rough_strike, axis=1)

    df[["suggested_action", "tradable_strike", "estimated_premium"]] = df.apply(
        lambda row: suggest_tradable_option(row, details),
        axis=1,
    )

    df["lot_size"] = df["symbol"].map(lot_lookup)
    df["estimated_max_loss"] = df["estimated_premium"] * df["lot_size"]

    df["capital_fit"] = np.where(
        df["estimated_max_loss"] <= MAX_LOSS_LIMIT,
        "YES",
        "NO",
    )

    df["candidate_quality"] = np.select(
        [
            df["breakeven_pct"] <= 5.0,
            df["breakeven_pct"] <= 7.0,
        ],
        [
            "A - Clean",
            "B - Slightly Expensive",
        ],
        default="C - Too Expensive",
    )

    output_cols = [
        "symbol",
        "trade_score",
        "candidate_quality",
        "capital_fit",
        "bias",
        "suggested_action",
        "tradable_strike",
        "estimated_premium",
        "lot_size",
        "estimated_max_loss",
        "spot",
        "expiry",
        "atm_strike",
        "atm_ce_ltp",
        "atm_pe_ltp",
        "atm_iv",
        "hv20",
        "hv60",
        "relative_volume",
        "straddle_cost",
        "breakeven_pct",
        "max_call_oi_strike",
        "max_put_oi_strike",
        "call_wall_distance_pct",
        "put_wall_distance_pct",
        "reason",
    ]

    output_cols = [c for c in output_cols if c in df.columns]

    df = df.sort_values("trade_score", ascending=False).reset_index(drop=True)
    df[output_cols].to_csv(OUTPUT_FILE, index=False)

    candidates = df[
        (df["bias"].isin(["Long Call", "Long Put", "Long Volatility"]))
        & (df["breakeven_pct"] <= 7.0)
        & (df["relative_volume"] >= 1.2)
        & (df["estimated_premium"].notna())
        & (df["lot_size"].notna())
        & (df["estimated_max_loss"] <= MAX_LOSS_LIMIT)
    ].copy()

    candidates = candidates.sort_values("trade_score", ascending=False).head(25)
    candidates[output_cols].to_csv(TOP_OUTPUT_FILE, index=False)

    print("Done")
    print(f"Total scanned: {len(df)}")
    print(f"Trade candidates: {len(candidates)}")
    print(f"Max loss limit: {MAX_LOSS_LIMIT}")
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Saved: {TOP_OUTPUT_FILE}")

    print("")
    print("Top candidates:")

    preview_cols = [
        "symbol",
        "trade_score",
        "candidate_quality",
        "capital_fit",
        "suggested_action",
        "tradable_strike",
        "estimated_premium",
        "lot_size",
        "estimated_max_loss",
        "spot",
        "breakeven_pct",
    ]

    print(candidates[preview_cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()