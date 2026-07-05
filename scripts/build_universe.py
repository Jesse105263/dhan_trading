import pandas as pd

SECURITY_MASTER_FILE = "security_id_list.csv"
OUTPUT_FILE = "fno_universe.csv"


def find_col(df, possible_names):
    lower_map = {c.lower().strip(): c for c in df.columns}
    for name in possible_names:
        if name.lower().strip() in lower_map:
            return lower_map[name.lower().strip()]
    return None


def clean_symbol(x):
    return str(x).strip().upper().replace("-EQ", "")


def extract_underlying_symbol(row, trading_col, custom_col):
    trading_symbol = clean_symbol(row[trading_col]) if trading_col else ""
    custom_symbol = clean_symbol(row[custom_col]) if custom_col else ""

    raw = trading_symbol if trading_symbol else custom_symbol

    if "-" in raw:
        return raw.split("-")[0].strip().upper()

    parts = raw.split()
    if len(parts) > 0:
        return parts[0].strip().upper()

    return raw.strip().upper()


def main():
    master = pd.read_csv(SECURITY_MASTER_FILE, low_memory=False)
    master.columns = [c.strip() for c in master.columns]

    exch_col = find_col(master, ["SEM_EXM_EXCH_ID", "exchange", "exch_id"])
    seg_col = find_col(master, ["SEM_SEGMENT", "segment"])
    inst_col = find_col(master, ["SEM_INSTRUMENT_NAME", "instrument", "instrument_name"])
    trading_col = find_col(master, ["SEM_TRADING_SYMBOL", "trading_symbol", "symbol"])
    custom_col = find_col(master, ["SEM_CUSTOM_SYMBOL", "custom_symbol", "name"])
    sec_col = find_col(master, ["SEM_SMST_SECURITY_ID", "security_id", "securityId"])

    if not inst_col:
        raise Exception("Instrument column not found in security master")

    if not trading_col and not custom_col:
        raise Exception("No symbol column found in security master")

    df = master.copy()

    if exch_col:
        df = df[df[exch_col].astype(str).str.upper().eq("NSE")]

    if seg_col:
        df = df[df[seg_col].astype(str).str.upper().isin(["D", "NSE_FNO", "FNO"])]

    df = df[df[inst_col].astype(str).str.upper().isin(["OPTSTK", "FUTSTK"])]

    df["symbol"] = df.apply(
        lambda row: extract_underlying_symbol(row, trading_col, custom_col),
        axis=1,
    )
    
    df = df[~df["symbol"].str.contains("NSETEST", na=False)]
    df = df[~df["symbol"].str.contains("TEST", na=False)]
    df = df[df["symbol"].notna()]
    df = df[df["symbol"].astype(str).str.len() > 0]

    universe = (
        df[["symbol"]]
        .drop_duplicates()
        .sort_values("symbol")
        .reset_index(drop=True)
    )

    universe.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {OUTPUT_FILE}")
    print(f"F&O underlying symbols: {len(universe)}")
    print(universe.head(30).to_string(index=False))


if __name__ == "__main__":
    main()