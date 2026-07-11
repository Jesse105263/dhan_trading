from dataclasses import dataclass
from typing import Iterable

from services.database import get_connection


@dataclass(frozen=True)
class Instrument:
    symbol: str
    exchange: str
    security_id: str
    instrument_type: str
    lot_size: int | None = None
    tick_size: float | None = None


class InstrumentRepository:
    def list_active_quote_instruments(self) -> list[Instrument]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        symbol,
                        exchange,
                        security_id,
                        instrument_type,
                        lot_size,
                        tick_size
                    FROM instruments
                    WHERE symbol IS NOT NULL
                      AND exchange IS NOT NULL
                      AND security_id IS NOT NULL
                    ORDER BY symbol;
                    """
                )

                rows = cursor.fetchall()

        return [
            Instrument(
                symbol=str(row[0]).strip().upper(),
                exchange=str(row[1]).strip().upper(),
                security_id=str(row[2]).strip(),
                instrument_type=str(row[3] or "").strip().upper(),
                lot_size=int(row[4]) if row[4] is not None else None,
                tick_size=float(row[5]) if row[5] is not None else None,
            )
            for row in rows
        ]

    def count(self) -> int:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM instruments;
                    """
                )

                result = cursor.fetchone()

        return int(result[0])

    def delete_all(self) -> int:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM instruments;
                    """
                )

                deleted_count = cursor.rowcount

            connection.commit()

        return deleted_count

    def bulk_upsert(
        self,
        instruments: Iterable[Instrument],
    ) -> int:
        records = [
            (
                instrument.symbol.strip().upper(),
                instrument.exchange.strip().upper(),
                instrument.security_id.strip(),
                instrument.instrument_type.strip().upper(),
                instrument.lot_size,
                instrument.tick_size,
            )
            for instrument in instruments
        ]

        if not records:
            return 0

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO instruments
                    (
                        symbol,
                        exchange,
                        security_id,
                        instrument_type,
                        lot_size,
                        tick_size
                    )
                    VALUES
                    (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol)
                    DO UPDATE SET
                        exchange = EXCLUDED.exchange,
                        security_id = EXCLUDED.security_id,
                        instrument_type = EXCLUDED.instrument_type,
                        lot_size = EXCLUDED.lot_size,
                        tick_size = EXCLUDED.tick_size;
                    """,
                    records,
                )

            connection.commit()

        return len(records)