from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable

from services.database import get_connection


_ALLOWED_INSTRUMENT_TYPES = {"FUTSTK", "OPTSTK"}
_ALLOWED_OPTION_TYPES = {"CE", "PE"}


@dataclass(frozen=True)
class DerivativeContract:
    exchange: str
    segment: str
    security_id: str
    trading_symbol: str
    underlying_symbol: str
    instrument_type: str
    expiry: date
    lot_size: int
    tick_size: Decimal
    strike: Decimal | None = None
    option_type: str | None = None
    is_active: bool = True
    source_updated_at: datetime | None = None

    def normalized(self) -> DerivativeContract:
        exchange = self.exchange.strip().upper()
        segment = self.segment.strip().upper()
        security_id = self.security_id.strip()
        trading_symbol = self.trading_symbol.strip().upper()
        underlying_symbol = self.underlying_symbol.strip().upper()
        instrument_type = self.instrument_type.strip().upper()
        option_type = (
            self.option_type.strip().upper()
            if self.option_type is not None
            else None
        )
        strike = (
            Decimal(str(self.strike))
            if self.strike is not None
            else None
        )
        tick_size = Decimal(str(self.tick_size))

        if not exchange:
            raise ValueError("exchange is required.")
        if not segment:
            raise ValueError("segment is required.")
        if not security_id:
            raise ValueError("security_id is required.")
        if not trading_symbol:
            raise ValueError("trading_symbol is required.")
        if not underlying_symbol:
            raise ValueError("underlying_symbol is required.")
        if instrument_type not in _ALLOWED_INSTRUMENT_TYPES:
            raise ValueError(
                "instrument_type must be FUTSTK or OPTSTK."
            )
        if self.lot_size <= 0:
            raise ValueError("lot_size must be greater than zero.")
        if tick_size <= 0:
            raise ValueError("tick_size must be greater than zero.")

        if instrument_type == "FUTSTK":
            if strike is not None or option_type is not None:
                raise ValueError(
                    "FUTSTK contracts cannot have strike or option_type."
                )
        else:
            if strike is None:
                raise ValueError("OPTSTK contracts require strike.")
            if strike < 0:
                raise ValueError("strike cannot be negative.")
            if option_type not in _ALLOWED_OPTION_TYPES:
                raise ValueError(
                    "OPTSTK option_type must be CE or PE."
                )

        return DerivativeContract(
            exchange=exchange,
            segment=segment,
            security_id=security_id,
            trading_symbol=trading_symbol,
            underlying_symbol=underlying_symbol,
            instrument_type=instrument_type,
            expiry=self.expiry,
            lot_size=int(self.lot_size),
            tick_size=tick_size,
            strike=strike,
            option_type=option_type,
            is_active=bool(self.is_active),
            source_updated_at=self.source_updated_at,
        )


class DerivativeContractRepository:
    def bulk_upsert(
        self,
        contracts: Iterable[DerivativeContract],
    ) -> int:
        normalized = [contract.normalized() for contract in contracts]

        if not normalized:
            return 0

        identities = [
            (contract.exchange, contract.segment, contract.security_id)
            for contract in normalized
        ]

        if len(identities) != len(set(identities)):
            raise ValueError(
                "Duplicate derivative contract identity in input batch."
            )

        records = [
            (
                contract.exchange,
                contract.segment,
                contract.security_id,
                contract.trading_symbol,
                contract.underlying_symbol,
                contract.instrument_type,
                contract.expiry,
                contract.strike,
                contract.option_type,
                contract.lot_size,
                contract.tick_size,
                contract.is_active,
                contract.source_updated_at,
            )
            for contract in normalized
        ]

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO derivative_contracts
                    (
                        exchange,
                        segment,
                        security_id,
                        trading_symbol,
                        underlying_symbol,
                        instrument_type,
                        expiry,
                        strike,
                        option_type,
                        lot_size,
                        tick_size,
                        is_active,
                        source_updated_at,
                        updated_at
                    )
                    VALUES
                    (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (exchange, segment, security_id)
                    DO UPDATE SET
                        trading_symbol = EXCLUDED.trading_symbol,
                        underlying_symbol = EXCLUDED.underlying_symbol,
                        instrument_type = EXCLUDED.instrument_type,
                        expiry = EXCLUDED.expiry,
                        strike = EXCLUDED.strike,
                        option_type = EXCLUDED.option_type,
                        lot_size = EXCLUDED.lot_size,
                        tick_size = EXCLUDED.tick_size,
                        is_active = EXCLUDED.is_active,
                        source_updated_at = EXCLUDED.source_updated_at,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    records,
                )

            connection.commit()

        return len(records)

    def get_by_identity(
        self,
        exchange: str,
        segment: str,
        security_id: str,
    ) -> DerivativeContract | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        exchange,
                        segment,
                        security_id,
                        trading_symbol,
                        underlying_symbol,
                        instrument_type,
                        expiry,
                        lot_size,
                        tick_size,
                        strike,
                        option_type,
                        is_active,
                        source_updated_at
                    FROM derivative_contracts
                    WHERE exchange = %s
                      AND segment = %s
                      AND security_id = %s;
                    """,
                    (
                        exchange.strip().upper(),
                        segment.strip().upper(),
                        security_id.strip(),
                    ),
                )
                row = cursor.fetchone()

        return self._from_row(row) if row is not None else None

    def list_active_by_underlying(
        self,
        underlying_symbol: str,
        expiry: date | None = None,
        instrument_type: str | None = None,
    ) -> list[DerivativeContract]:
        filters = [
            "is_active = TRUE",
            "underlying_symbol = %s",
        ]
        parameters: list[object] = [
            underlying_symbol.strip().upper()
        ]

        if expiry is not None:
            filters.append("expiry = %s")
            parameters.append(expiry)

        if instrument_type is not None:
            normalized_type = instrument_type.strip().upper()
            if normalized_type not in _ALLOWED_INSTRUMENT_TYPES:
                raise ValueError(
                    "instrument_type must be FUTSTK or OPTSTK."
                )
            filters.append("instrument_type = %s")
            parameters.append(normalized_type)

        query = f"""
            SELECT
                exchange,
                segment,
                security_id,
                trading_symbol,
                underlying_symbol,
                instrument_type,
                expiry,
                lot_size,
                tick_size,
                strike,
                option_type,
                is_active,
                source_updated_at
            FROM derivative_contracts
            WHERE {' AND '.join(filters)}
            ORDER BY
                expiry,
                instrument_type,
                strike NULLS FIRST,
                option_type,
                trading_symbol;
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                rows = cursor.fetchall()

        return [self._from_row(row) for row in rows]

    def list_active_expiries(
        self,
        underlying_symbol: str,
        instrument_type: str | None = None,
    ) -> list[date]:
        filters = [
            "is_active = TRUE",
            "underlying_symbol = %s",
        ]
        parameters: list[object] = [
            underlying_symbol.strip().upper()
        ]

        if instrument_type is not None:
            normalized_type = instrument_type.strip().upper()
            if normalized_type not in _ALLOWED_INSTRUMENT_TYPES:
                raise ValueError(
                    "instrument_type must be FUTSTK or OPTSTK."
                )
            filters.append("instrument_type = %s")
            parameters.append(normalized_type)

        query = f"""
            SELECT DISTINCT expiry
            FROM derivative_contracts
            WHERE {' AND '.join(filters)}
            ORDER BY expiry;
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                rows = cursor.fetchall()

        return [row[0] for row in rows]

    def deactivate_missing(
        self,
        exchange: str,
        segment: str,
        active_security_ids: Iterable[str],
    ) -> int:
        normalized_ids = sorted(
            {
                security_id.strip()
                for security_id in active_security_ids
                if security_id.strip()
            }
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                if normalized_ids:
                    cursor.execute(
                        """
                        UPDATE derivative_contracts
                        SET
                            is_active = FALSE,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE exchange = %s
                          AND segment = %s
                          AND is_active = TRUE
                          AND NOT (security_id = ANY(%s));
                        """,
                        (
                            exchange.strip().upper(),
                            segment.strip().upper(),
                            normalized_ids,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE derivative_contracts
                        SET
                            is_active = FALSE,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE exchange = %s
                          AND segment = %s
                          AND is_active = TRUE;
                        """,
                        (
                            exchange.strip().upper(),
                            segment.strip().upper(),
                        ),
                    )

                updated_count = cursor.rowcount

            connection.commit()

        return updated_count

    def count(self, active_only: bool = False) -> int:
        query = "SELECT COUNT(*) FROM derivative_contracts"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += ";"

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()

        if result is None:
            raise RuntimeError("Unable to count derivative contracts.")

        return int(result[0])

    @staticmethod
    def _from_row(row: tuple[object, ...]) -> DerivativeContract:
        return DerivativeContract(
            exchange=str(row[0]),
            segment=str(row[1]),
            security_id=str(row[2]),
            trading_symbol=str(row[3]),
            underlying_symbol=str(row[4]),
            instrument_type=str(row[5]),
            expiry=row[6],
            lot_size=int(row[7]),
            tick_size=Decimal(str(row[8])),
            strike=(
                Decimal(str(row[9]))
                if row[9] is not None
                else None
            ),
            option_type=(
                str(row[10])
                if row[10] is not None
                else None
            ),
            is_active=bool(row[11]),
            source_updated_at=row[12],
        )
