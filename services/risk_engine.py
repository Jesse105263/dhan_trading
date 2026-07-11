STOP_LOSS_PCT = 0.30
TARGET_1_PCT = 0.40
TARGET_2_PCT = 0.80


def calculate_option_risk(df):

    df = df.copy()

    df["option_entry"] = df["estimated_premium"]

    df["option_stop_loss"] = (
        df["option_entry"] * (1 - STOP_LOSS_PCT)
    ).round(2)

    df["option_target_1"] = (
        df["option_entry"] * (1 + TARGET_1_PCT)
    ).round(2)

    df["option_target_2"] = (
        df["option_entry"] * (1 + TARGET_2_PCT)
    ).round(2)

    return df