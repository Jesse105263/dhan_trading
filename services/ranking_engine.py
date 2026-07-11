def calculate_trade_score(df):

    df = df.copy()

    df["trade_score"] = (
        df["hv20_score"] * 0.15
        + df["rvol_score"] * 0.20
        + df["hv_expansion_score"] * 0.15
        + df["hv_iv_gap_score"] * 0.15
        + df["cheap_option_score"] * 0.15
        + df["pcr_score"] * 0.10
        + df["total_oi_score"] * 0.10
    )

    df["trade_score"] = df["trade_score"].round(2)

    return df