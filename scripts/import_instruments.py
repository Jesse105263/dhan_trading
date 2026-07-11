from pathlib import Path

import pandas as pd

from services.instrument_repository import (
    Instrument,
    InstrumentRepository,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECURITY_MASTER_PATH = (
    PROJECT_ROOT
    / "data"
    / "csv"
    / "security_id_list.csv"
)


def normalize_column_name(value: object) -> str:
    return (
        str(value)
        .strip()
        .upper()
        .replace(" ", "_")
        .replace("-", "_")
    )


def find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    lookup = {
        normalize_column_name(column): column
        for column in dataframe.columns
    }

    for candidate in candidates:
        normalized_candidate = normalize_column_name(candidate)

        if normalized_candidate in lookup:
            return lookup[normalized_candidate]

    return None


def clean_symbol(value: object) -> str:
    symbol = str(value).strip().upper()

    if symbol.endswith("-EQ"):
        symbol = symbol[:-3]

    return symbol


def extract_underlying_symbol(value: object) -> str:
    symbol = clean_symbol(value)

    if "-" in symbol:
        symbol = symbol.split("-", maxsplit=1)[0]

    if " " in symbol:
        symbol = symbol.split(maxsplit=1)[0]

    return symbol.strip().upper()


def is_valid_production_symbol(symbol: str) -> bool:
    normalized = symbol.strip().upper()

    if not normalized:
        return False

    blocked_terms = {
        "NSETEST",
        "TEST",
        "DUMMY",
        "MOCK",
    }

    return not any(
        term in normalized
        for term in blocked_terms
    )


def safe_integer(value: object) -> int | None:
    try:
        if pd.isna(value):
            return None

        parsed = int(float(value))

        if parsed <= 0:
            return None

        return parsed
    except (TypeError, ValueError):
        return None


def safe_float(value: object) -> float | None:
    try:
        if pd.isna(value):
            return None

        return float(value)
    except (TypeError, ValueError):
        return None


def load_security_master() -> pd.DataFrame:
    if not SECURITY_MASTER_PATH.exists():
        raise FileNotFoundError(
            "Dhan security master not found: "
            f"{SECURITY_MASTER_PATH}"
        )

    dataframe = pd.read_csv(
        SECURITY_MASTER_PATH,
        low_memory=False,
    )

    dataframe.columns = [
        normalize_column_name(column)
        for column in dataframe.columns
    ]

    return dataframe


def build_fno_equity_instruments(
    master: pd.DataFrame,
) -> list[Instrument]:
    exchange_column = find_column(
        master,
        [
            "SEM_EXM_EXCH_ID",
            "EXCHANGE",
            "EXCH_ID",
        ],
    )

    segment_column = find_column(
        master,
        [
            "SEM_SEGMENT",
            "SEGMENT",
            "EXCHANGE_SEGMENT",
        ],
    )

    instrument_column = find_column(
        master,
        [
            "SEM_INSTRUMENT_NAME",
            "INSTRUMENT",
            "INSTRUMENT_NAME",
        ],
    )

    trading_symbol_column = find_column(
        master,
        [
            "SEM_TRADING_SYMBOL",
            "TRADING_SYMBOL",
            "SYMBOL",
        ],
    )

    custom_symbol_column = find_column(
        master,
        [
            "SEM_CUSTOM_SYMBOL",
            "CUSTOM_SYMBOL",
            "DISPLAY_NAME",
        ],
    )

    security_id_column = find_column(
        master,
        [
            "SEM_SMST_SECURITY_ID",
            "SECURITY_ID",
            "SEM_SECURITY_ID",
        ],
    )

    lot_size_column = find_column(
        master,
        [
            "SEM_LOT_UNITS",
            "SEM_LOT_SIZE",
            "LOT_SIZE",
            "LOT_UNITS",
        ],
    )

    tick_size_column = find_column(
        master,
        [
            "SEM_TICK_SIZE",
            "TICK_SIZE",
        ],
    )

    series_column = find_column(
        master,
        [
            "SEM_SERIES",
            "SERIES",
        ],
    )

    required_columns = {
        "exchange": exchange_column,
        "instrument": instrument_column,
        "trading_symbol": trading_symbol_column,
        "security_id": security_id_column,
    }

    missing_columns = [
        name
        for name, column in required_columns.items()
        if column is None
    ]

    if missing_columns:
        raise RuntimeError(
            "Security master is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    derivatives = master.copy()

    derivatives = derivatives[
        derivatives[exchange_column]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("NSE")
    ]

    derivatives = derivatives[
        derivatives[instrument_column]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(["FUTSTK", "OPTSTK"])
    ]

    underlying_symbols: set[str] = set()
    lot_size_lookup: dict[str, int] = {}

    for _, row in derivatives.iterrows():
        symbol = extract_underlying_symbol(
            row[trading_symbol_column]
        )

        if (
            not symbol
            and custom_symbol_column is not None
        ):
            symbol = extract_underlying_symbol(
                row[custom_symbol_column]
            )

        if not is_valid_production_symbol(symbol):
            continue

        underlying_symbols.add(symbol)

        lot_size = (
            safe_integer(row[lot_size_column])
            if lot_size_column is not None
            else None
        )

        if lot_size is not None:
            lot_size_lookup.setdefault(
                symbol,
                lot_size,
            )

    equities = master.copy()

    equities = equities[
        equities[exchange_column]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("NSE")
    ]

    equities = equities[
        equities[instrument_column]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(["EQUITY", "EQ"])
    ]

    if segment_column is not None:
        segment_values = (
            equities[segment_column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        valid_segment_mask = segment_values.isin(
            {
                "E",
                "NSE_EQ",
                "EQ",
                "CASH",
            }
        )

        if valid_segment_mask.any():
            equities = equities[
                valid_segment_mask
            ]

    if series_column is not None:
        series_values = (
            equities[series_column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        eq_series_mask = series_values.eq("EQ")

        if eq_series_mask.any():
            equities = equities[
                eq_series_mask
            ]

    instruments_by_symbol: dict[
        str,
        Instrument,
    ] = {}

    for _, row in equities.iterrows():
        symbol = clean_symbol(
            row[trading_symbol_column]
        )

        if not is_valid_production_symbol(symbol):
            continue

        if symbol not in underlying_symbols:
            continue

        security_id = str(
            row[security_id_column]
        ).strip()

        if (
            not security_id
            or security_id.lower() == "nan"
        ):
            continue

        tick_size = (
            safe_float(row[tick_size_column])
            if tick_size_column is not None
            else None
        )

        instruments_by_symbol[symbol] = Instrument(
            symbol=symbol,
            exchange="NSE_EQ",
            security_id=security_id,
            instrument_type="EQUITY",
            lot_size=lot_size_lookup.get(symbol),
            tick_size=tick_size,
        )

    return sorted(
        instruments_by_symbol.values(),
        key=lambda instrument: instrument.symbol,
    )


def main() -> None:
    master = load_security_master()

    instruments = build_fno_equity_instruments(
        master
    )

    if not instruments:
        raise RuntimeError(
            "No production F&O equity instruments "
            "were produced from the Dhan security master."
        )

    test_symbols = [
        instrument.symbol
        for instrument in instruments
        if not is_valid_production_symbol(
            instrument.symbol
        )
    ]

    if test_symbols:
        raise RuntimeError(
            "Test instruments survived validation: "
            + ", ".join(test_symbols[:20])
        )

    repository = InstrumentRepository()

    deleted_count = repository.delete_all()
    inserted_count = repository.bulk_upsert(
        instruments
    )
    database_count = repository.count()

    print(
        f"Existing instruments removed: {deleted_count}"
    )
    print(
        f"Production F&O equities prepared: {len(instruments)}"
    )
    print(
        f"Instruments upserted: {inserted_count}"
    )
    print(
        f"Database instrument count: {database_count}"
    )

    print("")
    print("Sample instruments:")

    for instrument in instruments[:20]:
        print(
            instrument.symbol,
            instrument.exchange,
            instrument.security_id,
            instrument.lot_size,
            instrument.tick_size,
        )


if __name__ == "__main__":
    main()