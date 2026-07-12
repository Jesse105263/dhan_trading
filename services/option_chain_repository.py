from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Iterable
from uuid import UUID

from services.database import get_connection
from services.option_chain_models import (
    OptionQuoteSnapshot,
    UnderlyingIdentity,
)


class UnderlyingNotFoundError(LookupError):
    pass


class OptionChainRepository:
    def resolve_underlying(
        self,
        underlying_symbol: str,
    ) -> UnderlyingIdentity:
        symbol = underlying_symbol.strip().upper()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT symbol, security_id, exchange
                    FROM instruments
                    WHERE UPPER(symbol) = %s
                      AND security_id IS NOT NULL
                    ORDER BY id
                    LIMIT 1;
                    """,
                    (symbol,),
                )
                row = cursor.fetchone()

        if row is None:
            raise UnderlyingNotFoundError(
                f"No active underlying instrument found for {symbol}."
            )

        segment = str(row[2] or "NSE_EQ").strip().upper()
        if segment == "NSE":
            segment = "NSE_EQ"
        return UnderlyingIdentity(
            symbol=str(row[0]).strip().upper(),
            security_id=str(row[1]).strip(),
            segment=segment,
        )

    def start_run(
        self,
        run_id: UUID,
        identity: UnderlyingIdentity,
        expiry: date,
        requested_at: datetime,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO option_chain_runs
                    (
                        run_id,
                        underlying_symbol,
                        underlying_security_id,
                        underlying_segment,
                        expiry,
                        status,
                        requested_at
                    )
                    VALUES (%s, %s, %s, %s, %s, 'RUNNING', %s);
                    """,
                    (
                        run_id,
                        identity.symbol,
                        identity.security_id,
                        identity.segment,
                        expiry,
                        requested_at,
                    ),
                )
            connection.commit()

    def complete_run_with_quotes(
        self,
        run_id: UUID,
        completed_at: datetime,
        spot_price: Decimal | None,
        quotes: Iterable[OptionQuoteSnapshot],
    ) -> int:
        quote_list = list(quotes)
        rows = [
            (
                run_id,
                quote.underlying_symbol,
                quote.expiry,
                quote.strike,
                quote.option_type,
                quote.security_id,
                quote.last_price,
                quote.implied_volatility,
                quote.open_interest,
                quote.volume,
                quote.bid_price,
                quote.ask_price,
                quote.captured_at,
            )
            for quote in quote_list
        ]
        strike_count = len({quote.strike for quote in quote_list})

        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    if rows:
                        cursor.executemany(
                            """
                            INSERT INTO option_chain_quotes
                            (
                                run_id,
                                underlying_symbol,
                                expiry,
                                strike,
                                option_type,
                                security_id,
                                last_price,
                                implied_volatility,
                                open_interest,
                                volume,
                                bid_price,
                                ask_price,
                                captured_at
                            )
                            VALUES
                            (
                                %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s
                            );
                            """,
                            rows,
                        )
                    cursor.execute(
                        """
                        UPDATE option_chain_runs
                        SET status = 'COMPLETED',
                            completed_at = %s,
                            spot_price = %s,
                            strikes_received = %s,
                            quotes_received = %s,
                            quotes_inserted = %s,
                            error_message = NULL
                        WHERE run_id = %s;
                        """,
                        (
                            completed_at,
                            spot_price,
                            strike_count,
                            len(quote_list),
                            len(quote_list),
                            run_id,
                        ),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return len(quote_list)

    def fail_run(
        self,
        run_id: UUID,
        completed_at: datetime,
        error_message: str,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE option_chain_runs
                    SET status = 'FAILED',
                        completed_at = %s,
                        error_message = %s
                    WHERE run_id = %s;
                    """,
                    (completed_at, error_message, run_id),
                )
            connection.commit()
