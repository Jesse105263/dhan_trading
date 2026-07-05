import pandas as pd
import numpy as np

VOLATILITY_FILE = "volatility_ranking.csv"
OPTION_CHAIN_FILE = "option_chain_scanner.csv"
OPTION_CHAIN_DETAILS_FILE = "option_chain_details.csv"

OUTPUT_FILE = "daily_scanner.csv"
TOP_OUTPUT_FILE = "trade_candidates.csv"


def safe_float(x):
    try:
        if pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def normalize_0_100(series):
    series = pd.to_numeric(series, errors="coerce")
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series([50] * len(series), index=series.index)

    return ((series - min_val) / (max_val - min_val)) * 100


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

    rvol = row.get("relative_volume", np.nan)
    breakeven = row.get("breakeven_pct", np.nan)
    spot = row.get("spot", np.nan)
    call_wall = row.get("max_call_oi_strike", np.nan)
    put_wall = row.get("max_put_oi_strike", np.nan)

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

    vol.columns = [c.strip().lower() for c in vol.columns]
    opt.columns = [c.strip().lower() for c in opt.columns]
    details.columns = [c.strip().lower() for c in details.columns]

    df = pd.merge(vol, opt, on="symbol", how="inner")

    numeric_cols = [
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
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(safe_float)

    for col in ["strike", "ce_ltp", "pe_ltp", "ce_iv", "pe_iv", "ce_oi", "pe_oi"]:
        if col in details.columns:
            details[col] = details[col].apply(safe_float)

    df["hv_expansion"] = df["hv20"] - df["hv60"]
    df["hv_iv_gap"] = df["hv20"] - df["atm_iv"]

    df["call_wall_distance_pct"] = (
        (df["max_call_oi_strike"] - df["spot"]) / df["spot"]
    ) * 100

    df["put_wall_distance_pct"] = (
        (df["spot"] - df["max_put_oi_strike"]) / df["spot"]
    ) * 100

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

    df["candidate_quality"] = np.where(
        df["breakeven_pct"] <= 5.0,
        "A - Clean",
        "B - Slightly Expensive",
    )

    output_cols = [
        "symbol",
        "trade_score",
        "candidate_quality",
        "bias",
        "suggested_action",
        "tradable_strike",
        "estimated_premium",
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
    ].copy()

    candidates = candidates.sort_values("trade_score", ascending=False).head(25)
    candidates[output_cols].to_csv(TOP_OUTPUT_FILE, index=False)

    print("Done")
    print(f"Total scanned: {len(df)}")
    print(f"Trade candidates: {len(candidates)}")
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Saved: {TOP_OUTPUT_FILE}")

    print("")
    print("Top candidates:")
    preview_cols = [
        "symbol",
        "trade_score",
        "candidate_quality",
        "bias",
        "suggested_action",
        "tradable_strike",
        "estimated_premium",
        "spot",
        "breakeven_pct",
    ]

    print(candidates[preview_cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()

    