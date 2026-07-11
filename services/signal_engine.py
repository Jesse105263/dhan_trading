def select_trade_candidates(df):

    return (
        df[df["trade_status"] == "TRADE_READY"]
        .sort_values("rank_score", ascending=False)
        .head(25)
    )