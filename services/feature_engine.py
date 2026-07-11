import numpy as np
import pandas as pd


def normalize_0_100(series):
    series = pd.to_numeric(series, errors="coerce")

    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
        return pd.Series([50] * len(series), index=series.index)

    return ((series - min_val) / (max_val - min_val)) * 100


def build_features(df):

    df = df.copy()

    df["hv_expansion"] = df["hv20"] - df["hv60"]
    df["hv_iv_gap"] = df["hv20"] - df["atm_iv"]

    df["call_wall_distance_pct"] = (
        (df["max_call_oi_strike"] - df["spot"])
        / df["spot"]
    ) * 100

    df["put_wall_distance_pct"] = (
        (df["spot"] - df["max_put_oi_strike"])
        / df["spot"]
    ) * 100

    df["hv20_score"] = normalize_0_100(df["hv20"])
    df["rvol_score"] = normalize_0_100(df["relative_volume"])
    df["hv_expansion_score"] = normalize_0_100(df["hv_expansion"])
    df["hv_iv_gap_score"] = normalize_0_100(df["hv_iv_gap"])
    df["cheap_option_score"] = 100 - normalize_0_100(df["breakeven_pct"])
    df["pcr_score"] = normalize_0_100(df["nearby_pcr"])
    df["total_oi_score"] = normalize_0_100(df["total_oi"])

    return df