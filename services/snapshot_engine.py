import pandas as pd


def load_snapshot(path):

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def save_snapshot(df, path):

    df.to_csv(path, index=False)