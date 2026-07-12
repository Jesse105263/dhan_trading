from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from services.database import get_connection


_ALLOWED_INSTRUMENT_TYPES = {"FUTSTK", "OPTSTK"}


@dataclass(frozen=True)
class ExpiryAvailability:
    underlying_symbol: str
    instrument_type: str
    expiry: date
    contract_count: int


class ExpiryRepository:
    def list_available(
        self,
        underlying_symbol: str,
        instrument_type: str = "OPTSTK",
        on_or_after: date | None = None,
    ) -> list[ExpiryAvailability]:
        symbol = self._normalize_symbol(underlying_symbol)
        normalized_type = self._normalize_instrument_type(
            instrument_type
        )

        filters = [
            "is_active = TRUE",
            "underlying_symbol = %s",
            "instrument_type = %s",
        ]
        parameters: list[object] = [symbol, normalized_type]

        if on_or_after is not None:
            filters.append("expiry >= %s")
            parameters.append(on_or_after)

        query = f"""
            SELECT
                underlying_symbol,
                instrument_type,
                expiry,
                COUNT(*)
            FROM derivative_contracts
            WHERE {' AND '.join(filters)}
            GROUP BY
                underlying_symbol,
                instrument_type,
                expiry
            ORDER BY expiry;
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                rows = cursor.fetchall()

        return [
            ExpiryAvailability(
                underlying_symbol=str(row[0]),
                instrument_type=str(row[1]),
                expiry=row[2],
                contract_count=int(row[3]),
            )
            for row in rows
        ]

    def is_available(
        self,
        underlying_symbol: str,
        expiry: date,
        instrument_type: str = "OPTSTK",
    ) -> bool:
        symbol = self._normalize_symbol(underlying_symbol)
        normalized_type = self._normalize_instrument_type(
            instrument_type
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT EXISTS
                    (
                        SELECT 1
                        FROM derivative_contracts
                        WHERE is_active = TRUE
                          AND underlying_symbol = %s
                          AND instrument_type = %s
                          AND expiry = %s
                    );
                    """,
                    (symbol, normalized_type, expiry),
                )
                row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                "Unable to determine expiry availability."
            )

        return bool(row[0])

    def count_underlyings(
        self,
        instrument_type: str = "OPTSTK",
        on_or_after: date | None = None,
    ) -> int:
        normalized_type = self._normalize_instrument_type(
            instrument_type
        )
        filters = [
            "is_active = TRUE",
            "instrument_type = %s",
        ]
        parameters: list[object] = [normalized_type]

        if on_or_after is not None:
            filters.append("expiry >= %s")
            parameters.append(on_or_after)

        query = f"""
            SELECT COUNT(DISTINCT underlying_symbol)
            FROM derivative_contracts
            WHERE {' AND '.join(filters)};
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                row = cursor.fetchone()

        if row is None:
            raise RuntimeError("Unable to count expiry underlyings.")

        return int(row[0])

    @staticmethod
    def _normalize_symbol(underlying_symbol: str) -> str:
        symbol = underlying_symbol.strip().upper()
        if not symbol:
            raise ValueError("underlying_symbol is required.")
        return symbol

    @staticmethod
    def _normalize_instrument_type(
        instrument_type: str,
    ) -> str:
        normalized_type = instrument_type.strip().upper()
        if normalized_type not in _ALLOWED_INSTRUMENT_TYPES:
            raise ValueError(
                "instrument_type must be FUTSTK or OPTSTK."
            )
        return normalized_type
