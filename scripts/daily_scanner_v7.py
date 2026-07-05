import pandas as pd
import numpy as np

VOLATILITY_FILE = "volatility_ranking.csv"
OPTION_CHAIN_FILE = "option_chain_scanner.csv"
OPTION_CHAIN_DETAILS_FILE = "option_chain_details.csv"
SECURITY_MASTER_FILE = "security_id_list.csv"

OUTPUT_FILE = "daily_scanner.csv"
TOP_OUTPUT_FILE = "trade_candidates.csv"

MAX_LOSS_LIMIT = 20000

STOP_LOSS_PCT = 0.30
TARGET_1_PCT = 0.40
TARGET_2_PCT = 0.80

MIN_RVOL = 1.2
MAX_BREAKEVEN_PCT = 7.0


def safe_float(x):
    try:
        if pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def clean_symbol(x):
    return str(x).strip().upper().replace("-EQ", "")


def normalize_col_name(c):
    return str(c).strip().lower().replace(" ", "_").replace("-", "_")


def normalize_input_columns(df):
    df.columns = [normalize_col_name(c) for c in df.columns]
    return df


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


def find_col(df, possible_names):
    lookup = {c.lower().strip(): c for c in df.columns}

    for name in possible_names:
        key = name.lower().strip()
        if key in lookup:
            return lookup[key]

    return None


def extract_underlying_symbol(raw):
    raw = clean_symbol(raw)

    if "-" in raw:
        return raw.split("-")[0].strip().upper()

    parts = raw.split()

    if len(parts) > 0:
        return parts[0].strip().upper()

    return raw


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

    if spot > put_wall and not pd.isna(rvol) and rvol >= MIN_RVOL:
        return "Long Call"

    if spot < call_wall and not pd.isna(rvol) and rvol >= MIN_RVOL:
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
    max_loss = row.get("estimated_max_loss", np.nan)

    if not pd.isna(hv20) and not pd.isna(hv60):
        if hv20 > hv60:
            reasons.append("HV20 expanding vs HV60")
        else:
            reasons.append("HV20 not expanding")

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
        elif rvol >= MIN_RVOL:
            reasons.append("Strong relative volume")
        else:
            reasons.append("Weak relative volume")

    if not pd.isna(breakeven):
        if breakeven <= 3:
            reasons.append("Cheap option structure")
        elif breakeven <= 5:
            reasons.append("Moderate option cost")
        elif breakeven <= MAX_BREAKEVEN_PCT:
            reasons.append("Slightly expensive option cost")
        else:
            reasons.append("Expensive option cost")

    if not pd.isna(max_loss):
        if max_loss <= MAX_LOSS_LIMIT:
            reasons.append("Fits capital limit")
        else:
            reasons.append("Too large for capital limit")

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
        return pd.Series(["Watch", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan])

    chain = details[details["symbol"] == symbol].copy()

    if chain.empty:
        return pd.Series(["Watch", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan])

    chain["strike_distance"] = (chain["strike"] - rough_strike).abs()
    best = chain.sort_values("strike_distance").iloc[0]

    ce_ltp = best.get("ce_ltp", np.nan)
    pe_ltp = best.get("pe_ltp", np.nan)
    ce_iv = best.get("ce_iv", np.nan)
    pe_iv = best.get("pe_iv", np.nan)
    ce_oi = best.get("ce_oi", np.nan)
    pe_oi = best.get("pe_oi", np.nan)

    if bias == "Long Call":
        action = "Buy CE"
        premium = ce_ltp
        contract_iv = ce_iv
        contract_oi = ce_oi

    elif bias == "Long Put":
        action = "Buy PE"
        premium = pe_ltp
        contract_iv = pe_iv
        contract_oi = pe_oi

    elif bias == "Long Volatility":
        action = "Buy ATM Straddle"

        ce = 0 if pd.isna(ce_ltp) else ce_ltp
        pe = 0 if pd.isna(pe_ltp) else pe_ltp

        premium = ce + pe

        iv_values = []
        if not pd.isna(ce_iv):
            iv_values.append(ce_iv)
        if not pd.isna(pe_iv):
            iv_values.append(pe_iv)

        contract_iv = np.mean(iv_values) if iv_values else np.nan
        contract_oi = min(
            0 if pd.isna(ce_oi) else ce_oi,
            0 if pd.isna(pe_oi) else pe_oi,
        )

    else:
        action = "Watch"
        premium = np.nan
        contract_iv = np.nan
        contract_oi = np.nan

    return pd.Series(
        [
            action,
            best["strike"],
            premium,
            contract_iv,
            contract_oi,
            ce_ltp,
            pe_ltp,
        ]
    )


def assign_candidate_quality(row):
    breakeven = row.get("breakeven_pct", np.nan)
    max_loss = row.get("estimated_max_loss", np.nan)
    rvol = row.get("relative_volume", np.nan)

    if pd.isna(breakeven) or pd.isna(max_loss) or pd.isna(rvol):
        return "C - Incomplete"

    if breakeven <= 5 and max_loss <= MAX_LOSS_LIMIT and rvol >= 1.5:
        return "A - Clean"

    if breakeven <= MAX_BREAKEVEN_PCT and max_loss <= MAX_LOSS_LIMIT and rvol >= MIN_RVOL:
        return "B - Tradable"

    return "C - Avoid"


def assign_confidence_grade(row):
    score = row.get("trade_score", np.nan)
    quality = row.get("candidate_quality", "")
    breakeven = row.get("breakeven_pct", np.nan)
    max_loss = row.get("estimated_max_loss", np.nan)
    rvol = row.get("relative_volume", np.nan)
    contract_oi = row.get("contract_oi", np.nan)

    if pd.isna(score):
        return "C"

    if (
        quality == "A - Clean"
        and score >= 50
        and not pd.isna(contract_oi)
        and contract_oi > 0
    ):
        return "A+"

    if (
        quality == "A - Clean"
        and score >= 45
        and not pd.isna(max_loss)
        and max_loss <= MAX_LOSS_LIMIT
    ):
        return "A"

    if (
        quality in ["A - Clean", "B - Tradable"]
        and score >= 48
        and not pd.isna(breakeven)
        and breakeven <= MAX_BREAKEVEN_PCT
        and not pd.isna(rvol)
        and rvol >= MIN_RVOL
    ):
        return "B+"

    if quality == "B - Tradable":
        return "B"

    return "C"


def assign_trade_status(row):
    bias = row.get("bias", "")
    quality = row.get("candidate_quality", "")
    max_loss = row.get("estimated_max_loss", np.nan)
    premium = row.get("estimated_premium", np.nan)
    breakeven = row.get("breakeven_pct", np.nan)
    rvol = row.get("relative_volume", np.nan)

    if bias == "Watch Only":
        return "WATCH"

    if pd.isna(max_loss) or pd.isna(premium):
        return "SKIP - Missing premium or lot"

    if max_loss > MAX_LOSS_LIMIT:
        return "SKIP - Max loss too high"

    if pd.isna(breakeven) or breakeven > MAX_BREAKEVEN_PCT:
        return "SKIP - Option too expensive"

    if pd.isna(rvol) or rvol < MIN_RVOL:
        return "SKIP - Weak volume"

    if quality in ["A - Clean", "B - Tradable"]:
        return "TRADE_READY"

    return "WATCH"


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
    df["rough_suggested_strike"] = df.apply(suggest_rough_strike, axis=1)

    df[
        [
            "suggested_action",
            "tradable_strike",
            "estimated_premium",
            "contract_iv",
            "contract_oi",
            "tradable_ce_ltp",
            "tradable_pe_ltp",
        ]
    ] = df.apply(
        lambda row: suggest_tradable_option(row, details),
        axis=1,
    )

    df["lot_size"] = df["symbol"].map(lot_lookup)
    df["estimated_max_loss"] = df["estimated_premium"] * df["lot_size"]

    df["option_entry"] = df["estimated_premium"]
    df["option_stop_loss"] = (df["option_entry"] * (1 - STOP_LOSS_PCT)).round(2)
    df["option_target_1"] = (df["option_entry"] * (1 + TARGET_1_PCT)).round(2)
    df["option_target_2"] = (df["option_entry"] * (1 + TARGET_2_PCT)).round(2)

    df["risk_per_lot"] = (df["option_entry"] - df["option_stop_loss"]) * df["lot_size"]
    df["reward_1_per_lot"] = (df["option_target_1"] - df["option_entry"]) * df["lot_size"]
    df["reward_2_per_lot"] = (df["option_target_2"] - df["option_entry"]) * df["lot_size"]

    df["risk_reward_1"] = df["reward_1_per_lot"] / df["risk_per_lot"]
    df["risk_reward_2"] = df["reward_2_per_lot"] / df["risk_per_lot"]

    df["capital_fit"] = np.where(df["estimated_max_loss"] <= MAX_LOSS_LIMIT, "YES", "NO")

    df["candidate_quality"] = df.apply(assign_candidate_quality, axis=1)
    df["confidence_grade"] = df.apply(assign_confidence_grade, axis=1)
    df["trade_status"] = df.apply(assign_trade_status, axis=1)

    df["reason"] = df.apply(build_reason, axis=1)

    df["rank_score"] = df["trade_score"]

    df.loc[df["candidate_quality"] == "A - Clean", "rank_score"] += 5
    df.loc[df["capital_fit"] == "YES", "rank_score"] += 3
    df.loc[df["confidence_grade"] == "A+", "rank_score"] += 5
    df.loc[df["confidence_grade"] == "A", "rank_score"] += 3
    df.loc[df["trade_status"] == "TRADE_READY", "rank_score"] += 5

    df["rank_score"] = df["rank_score"].round(2)

    output_cols = [
        "symbol",
        "rank_score",
        "trade_score",
        "confidence_grade",
        "candidate_quality",
        "trade_status",
        "capital_fit",
        "bias",
        "suggested_action",
        "tradable_strike",
        "estimated_premium",
        "contract_iv",
        "contract_oi",
        "lot_size",
        "estimated_max_loss",
        "option_entry",
        "option_stop_loss",
        "option_target_1",
        "option_target_2",
        "risk_per_lot",
        "reward_1_per_lot",
        "reward_2_per_lot",
        "risk_reward_1",
        "risk_reward_2",
        "spot",
        "expiry",
        "atm_strike",
        "atm_ce_ltp",
        "atm_pe_ltp",
        "tradable_ce_ltp",
        "tradable_pe_ltp",
        "atm_iv",
        "hv20",
        "hv60",
        "hv_expansion",
        "hv_iv_gap",
        "relative_volume",
        "straddle_cost",
        "breakeven_pct",
        "max_call_oi_strike",
        "max_put_oi_strike",
        "max_call_oi",
        "max_put_oi",
        "call_wall_distance_pct",
        "put_wall_distance_pct",
        "reason",
    ]

    output_cols = [c for c in output_cols if c in df.columns]

    df = df.sort_values("rank_score", ascending=False).reset_index(drop=True)
    df[output_cols].to_csv(OUTPUT_FILE, index=False)

    candidates = df[df["trade_status"] == "TRADE_READY"].copy()
    candidates = candidates.sort_values("rank_score", ascending=False).head(25)
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
        "rank_score",
        "confidence_grade",
        "candidate_quality",
        "suggested_action",
        "tradable_strike",
        "estimated_premium",
        "lot_size",
        "estimated_max_loss",
        "option_stop_loss",
        "option_target_1",
        "option_target_2",
        "risk_reward_1",
        "spot",
        "breakeven_pct",
    ]

    print(candidates[preview_cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()