from dataclasses import dataclass
from datetime import datetime

from services.database import get_connection


@dataclass(frozen=True)
class UnderlyingQuote:
    symbol: str
    spot_price: float
    volume: int | None
    oi: int | None
    timestamp: datetime


class UnderlyingQuoteRepository:
    def latest_batch_timestamp(
        self,
    ) -> datetime | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT MAX(timestamp)
                    FROM underlying_quotes;
                    """
                )

                result = cursor.fetchone()

        if result is None:
            return None

        return result[0]

    def list_latest_batch(
        self,
    ) -> list[UnderlyingQuote]:
        latest_timestamp = self.latest_batch_timestamp()

        if latest_timestamp is None:
            return []

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        symbol,
                        spot_price,
                        volume,
                        oi,
                        timestamp
                    FROM underlying_quotes
                    WHERE timestamp = %s
                    ORDER BY symbol;
                    """,
                    (latest_timestamp,),
                )

                rows = cursor.fetchall()

        return [
            UnderlyingQuote(
                symbol=str(row[0]).strip().upper(),
                spot_price=float(row[1]),
                volume=(
                    int(row[2])
                    if row[2] is not None
                    else None
                ),
                oi=(
                    int(row[3])
                    if row[3] is not None
                    else None
                ),
                timestamp=row[4],
            )
            for row in rows
        ]