from collections import defaultdict
from datetime import datetime
from typing import Any

import requests

from services.config import DHAN_SETTINGS
from services.database import get_connection
from services.stage import Stage


DHAN_QUOTE_URL = "https://api.dhan.co/v2/marketfeed/quote"
REQUEST_TIMEOUT_SECONDS = 30
MAX_INSTRUMENTS_PER_REQUEST = 1000


class CollectorStage(Stage):
    def __init__(self) -> None:
        super().__init__("Collector")

    def run(self, context: dict[str, Any]) -> None:
        instruments = self._load_instruments()

        if not instruments:
            raise RuntimeError(
                "No instruments found in PostgreSQL table: instruments"
            )

        if len(instruments) > MAX_INSTRUMENTS_PER_REQUEST:
            raise RuntimeError(
                "Collector currently supports a maximum of "
                f"{MAX_INSTRUMENTS_PER_REQUEST} instruments per run."
            )

        payload = self._build_payload(instruments)
        response_data = self._fetch_quotes(payload)
        quotes = self._parse_quotes(instruments, response_data)

        if not quotes:
            raise RuntimeError(
                "Dhan returned no usable quotes for configured instruments."
            )

        inserted_count = self._save_quotes(quotes)

        context["collector_complete"] = True
        context["instruments_requested"] = len(instruments)
        context["quotes_received"] = len(quotes)
        context["quotes_inserted"] = inserted_count
        context["collection_time"] = datetime.now()

        print(f"Instruments requested: {len(instruments)}")
        print(f"Quotes received: {len(quotes)}")
        print(f"Quotes inserted: {inserted_count}")

    @staticmethod
    def _load_instruments() -> list[dict[str, str]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        symbol,
                        exchange,
                        security_id
                    FROM instruments
                    WHERE symbol IS NOT NULL
                      AND exchange IS NOT NULL
                      AND security_id IS NOT NULL
                    ORDER BY symbol;
                    """
                )

                rows = cursor.fetchall()

        return [
            {
                "symbol": str(row[0]).strip().upper(),
                "exchange": str(row[1]).strip().upper(),
                "security_id": str(row[2]).strip(),
            }
            for row in rows
        ]

    @staticmethod
    def _build_payload(
        instruments: list[dict[str, str]],
    ) -> dict[str, list[int]]:
        grouped: defaultdict[str, list[int]] = defaultdict(list)

        for instrument in instruments:
            exchange = instrument["exchange"]
            security_id = instrument["security_id"]

            try:
                grouped[exchange].append(int(security_id))
            except ValueError as error:
                raise RuntimeError(
                    f"Invalid security ID for "
                    f"{instrument['symbol']}: {security_id}"
                ) from error

        return dict(grouped)

    @staticmethod
    def _fetch_quotes(
        payload: dict[str, list[int]],
    ) -> dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "access-token": DHAN_SETTINGS.access_token,
            "client-id": DHAN_SETTINGS.client_id,
        }

        try:
            response = requests.post(
                DHAN_QUOTE_URL,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as error:
            raise RuntimeError(
                f"Unable to connect to Dhan Market Quote API: {error}"
            ) from error

        if not response.ok:
            raise RuntimeError(
                "Dhan Market Quote API request failed. "
                f"HTTP {response.status_code}: {response.text}"
            )

        try:
            response_data = response.json()
        except ValueError as error:
            raise RuntimeError(
                "Dhan Market Quote API returned invalid JSON."
            ) from error

        if response_data.get("status") != "success":
            raise RuntimeError(
                "Dhan Market Quote API returned an unsuccessful response: "
                f"{response_data}"
            )

        data = response_data.get("data")

        if not isinstance(data, dict):
            raise RuntimeError(
                "Dhan Market Quote API response is missing quote data."
            )

        return data

    @staticmethod
    def _parse_quotes(
        instruments: list[dict[str, str]],
        response_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        instrument_lookup = {
            (
                instrument["exchange"],
                instrument["security_id"],
            ): instrument
            for instrument in instruments
        }

        collected_at = datetime.now()
        quotes: list[dict[str, Any]] = []

        for exchange, exchange_quotes in response_data.items():
            if not isinstance(exchange_quotes, dict):
                continue

            for security_id, quote in exchange_quotes.items():
                if not isinstance(quote, dict):
                    continue

                instrument = instrument_lookup.get(
                    (str(exchange).upper(), str(security_id))
                )

                if instrument is None:
                    continue

                last_price = quote.get("last_price")

                if last_price is None:
                    continue

                quotes.append(
                    {
                        "symbol": instrument["symbol"],
                        "spot_price": float(last_price),
                        "volume": CollectorStage._safe_integer(
                            quote.get("volume")
                        ),
                        "oi": CollectorStage._safe_integer(
                            quote.get("open_interest")
                        ),
                        "timestamp": collected_at,
                    }
                )

        return quotes

    @staticmethod
    def _safe_integer(value: Any) -> int | None:
        if value is None:
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _save_quotes(
        quotes: list[dict[str, Any]],
    ) -> int:
        records = [
            (
                quote["symbol"],
                quote["spot_price"],
                quote["volume"],
                quote["oi"],
                quote["timestamp"],
            )
            for quote in quotes
        ]

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO underlying_quotes
                    (
                        symbol,
                        spot_price,
                        volume,
                        oi,
                        timestamp
                    )
                    VALUES
                    (%s, %s, %s, %s, %s);
                    """,
                    records,
                )

            connection.commit()

        return len(records)