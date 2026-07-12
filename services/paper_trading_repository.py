from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from psycopg.types.json import Jsonb

from services.database import get_connection
from services.paper_trading_models import (
    PaperCloseResult,
    PaperFill,
    PaperMarketMark,
    PaperOpenResult,
    PaperOrder,
    PaperPosition,
    PaperSignal,
)


class PaperTradingRepository:
    def get_signal(self, signal_id: UUID) -> PaperSignal | None:
        query = """
            SELECT s.signal_id, s.signal_run_id, s.risk_run_id, s.assessment_id,
                   s.selection_id, s.ranking_id, s.analytics_id, s.source_run_id,
                   s.underlying_symbol, s.expiry, s.option_type, s.security_id,
                   s.trading_symbol, s.approved_quantity, s.entry_price,
                   a.source_captured_at, sr.calculated_at
            FROM option_signals s
            JOIN option_signal_runs sr ON sr.signal_run_id = s.signal_run_id
            JOIN option_chain_analytics a ON a.analytics_id = s.analytics_id
            WHERE s.signal_id = %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (signal_id,))
                row = cursor.fetchone()
        return self._signal(row) if row else None

    def get_position(self, position_id: UUID) -> PaperPosition | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._POSITION_QUERY + " WHERE p.position_id = %s", (position_id,))
                row = cursor.fetchone()
        return self._position(row) if row else None

    def get_position_for_signal(self, signal_id: UUID) -> PaperPosition | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._POSITION_QUERY + " WHERE p.signal_id = %s", (signal_id,))
                row = cursor.fetchone()
        return self._position(row) if row else None

    def list_positions(self, status: str | None = None, limit: int = 20) -> list[PaperPosition]:
        query = self._POSITION_QUERY
        parameters = []
        if status is not None:
            query += " WHERE p.status = %s"
            parameters.append(status)
        query += " ORDER BY p.updated_at DESC, p.position_id DESC LIMIT %s"
        parameters.append(limit)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(parameters))
                rows = cursor.fetchall()
        return [self._position(row) for row in rows]

    def latest_mark(self, signal: PaperSignal, as_of: datetime, after: datetime | None = None) -> PaperMarketMark | None:
        query = """
            SELECT q.run_id, q.captured_at, q.last_price
            FROM option_chain_quotes q
            JOIN option_chain_runs r ON r.run_id = q.run_id
            WHERE q.underlying_symbol = %s AND q.expiry = %s
              AND q.security_id = %s AND q.option_type = %s
              AND q.captured_at >= %s AND q.captured_at <= %s
              AND q.last_price IS NOT NULL AND q.last_price > 0
              AND r.status = 'COMPLETED'
        """
        parameters = [
            signal.underlying_symbol, signal.expiry, signal.security_id,
            signal.option_type, signal.source_captured_at, as_of,
        ]
        if after is not None:
            query += " AND q.captured_at > %s"
            parameters.append(after)
        query += " ORDER BY q.captured_at DESC, q.run_id DESC LIMIT 1"
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(parameters))
                row = cursor.fetchone()
        return PaperMarketMark(row[0], row[1], Decimal(row[2])) if row else None

    def persist_open(self, result: PaperOpenResult, event_payload: dict) -> PaperOpenResult:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                self._insert_order(cursor, result.order)
                if result.position is not None and result.fill is not None:
                    self._insert_position(cursor, result.position)
                    self._insert_fill(cursor, result.fill)
                    self._insert_event(cursor, result.position.position_id, 1, "OPENED", result.position.entry_time, event_payload)
            connection.commit()
        return result

    def persist_mark(self, position: PaperPosition, event_payload: dict) -> PaperPosition:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE paper_positions SET latest_mark_run_id=%s, latest_mark_time=%s,
                        latest_mark_price=%s, gross_pnl=%s, transaction_costs=%s,
                        net_pnl=%s, updated_at=%s
                    WHERE position_id=%s AND status='OPEN'
                    """,
                    (
                        position.latest_mark_run_id, position.latest_mark_time,
                        position.latest_mark_price, position.gross_pnl,
                        position.transaction_costs, position.net_pnl,
                        position.updated_at, position.position_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("Open paper position was not found during mark persistence.")
                sequence = self._next_sequence(cursor, position.position_id)
                self._insert_event(cursor, position.position_id, sequence, "MARKED", position.latest_mark_time, event_payload)
            connection.commit()
        return position

    def persist_close(self, result: PaperCloseResult, event_payload: dict) -> PaperCloseResult:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                self._insert_order(cursor, result.order)
                self._insert_fill(cursor, result.fill)
                position = result.position
                cursor.execute(
                    """
                    UPDATE paper_positions SET exit_order_id=%s, status='CLOSED',
                        latest_mark_run_id=%s, latest_mark_time=%s, latest_mark_price=%s,
                        exit_run_id=%s, exit_time=%s, exit_price=%s, gross_pnl=%s,
                        transaction_costs=%s, net_pnl=%s, updated_at=%s
                    WHERE position_id=%s AND status='OPEN'
                    """,
                    (
                        position.exit_order_id, position.latest_mark_run_id,
                        position.latest_mark_time, position.latest_mark_price,
                        position.exit_run_id, position.exit_time, position.exit_price,
                        position.gross_pnl, position.transaction_costs,
                        position.net_pnl, position.updated_at, position.position_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("Open paper position was not found during close persistence.")
                sequence = self._next_sequence(cursor, position.position_id)
                self._insert_event(cursor, position.position_id, sequence, "CLOSED", position.exit_time, event_payload)
            connection.commit()
        return result

    @staticmethod
    def _insert_order(cursor, order: PaperOrder) -> None:
        cursor.execute(
            """
            INSERT INTO paper_trade_orders (
                order_id, signal_id, source_run_id, side, quantity, status,
                requested_at, filled_at, reference_run_id, reference_price,
                fill_price, rejection_code
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                order.order_id, order.signal_id, order.source_run_id, order.side,
                order.quantity, order.status, order.requested_at, order.filled_at,
                order.reference_run_id, order.reference_price, order.fill_price,
                order.rejection_code,
            ),
        )

    @staticmethod
    def _insert_position(cursor, position: PaperPosition) -> None:
        signal = position.signal
        cursor.execute(
            """
            INSERT INTO paper_positions (
                position_id, signal_id, signal_run_id, risk_run_id, assessment_id,
                selection_id, ranking_id, analytics_id, source_run_id, entry_order_id,
                exit_order_id, underlying_symbol, expiry, option_type, security_id,
                trading_symbol, status, quantity, entry_run_id, entry_time, entry_price,
                latest_mark_run_id, latest_mark_time, latest_mark_price, exit_run_id,
                exit_time, exit_price, gross_pnl, transaction_costs, net_pnl, updated_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                position.position_id, signal.signal_id, signal.signal_run_id,
                signal.risk_run_id, signal.assessment_id, signal.selection_id,
                signal.ranking_id, signal.analytics_id, signal.source_run_id,
                position.entry_order_id, position.exit_order_id,
                signal.underlying_symbol, signal.expiry, signal.option_type,
                signal.security_id, signal.trading_symbol, position.status,
                signal.quantity, position.entry_run_id, position.entry_time,
                position.entry_price, position.latest_mark_run_id,
                position.latest_mark_time, position.latest_mark_price,
                position.exit_run_id, position.exit_time, position.exit_price,
                position.gross_pnl, position.transaction_costs,
                position.net_pnl, position.updated_at,
            ),
        )

    @staticmethod
    def _insert_fill(cursor, fill: PaperFill) -> None:
        cursor.execute(
            """
            INSERT INTO paper_trade_fills (
                fill_id, order_id, position_id, side, quantity, reference_run_id,
                reference_price, fill_price, filled_at, transaction_cost
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                fill.fill_id, fill.order_id, fill.position_id, fill.side,
                fill.quantity, fill.reference_run_id, fill.reference_price,
                fill.fill_price, fill.filled_at, fill.transaction_cost,
            ),
        )

    @staticmethod
    def _next_sequence(cursor, position_id: UUID) -> int:
        cursor.execute(
            "SELECT COALESCE(MAX(sequence_number),0)+1 FROM paper_position_events WHERE position_id=%s",
            (position_id,),
        )
        return int(cursor.fetchone()[0])

    @staticmethod
    def _insert_event(cursor, position_id, sequence, event_type, occurred_at, payload) -> None:
        from uuid import uuid4
        cursor.execute(
            """
            INSERT INTO paper_position_events (
                event_id, position_id, sequence_number, event_type, occurred_at, payload
            ) VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (uuid4(), position_id, sequence, event_type, occurred_at, Jsonb(payload)),
        )

    _POSITION_QUERY = """
        SELECT p.position_id, p.entry_order_id, p.exit_order_id, p.status,
               p.entry_run_id, p.entry_time, p.entry_price, p.latest_mark_run_id,
               p.latest_mark_time, p.latest_mark_price, p.exit_run_id, p.exit_time,
               p.exit_price, p.gross_pnl, p.transaction_costs, p.net_pnl, p.updated_at,
               s.signal_id, s.signal_run_id, s.risk_run_id, s.assessment_id,
               s.selection_id, s.ranking_id, s.analytics_id, s.source_run_id,
               s.underlying_symbol, s.expiry, s.option_type, s.security_id,
               s.trading_symbol, s.approved_quantity, s.entry_price,
               a.source_captured_at, sr.calculated_at
        FROM paper_positions p
        JOIN option_signals s ON s.signal_id=p.signal_id
        JOIN option_signal_runs sr ON sr.signal_run_id=s.signal_run_id
        JOIN option_chain_analytics a ON a.analytics_id=s.analytics_id
    """

    @staticmethod
    def _signal(row) -> PaperSignal:
        return PaperSignal(
            *row[:14], Decimal(row[14]), row[15], row[16]
        )

    @classmethod
    def _position(cls, row) -> PaperPosition:
        signal = cls._signal(row[17:])
        return PaperPosition(
            row[0], signal, row[1], row[2], row[3], row[4], row[5],
            Decimal(row[6]), row[7], row[8], Decimal(row[9]), row[10],
            row[11], Decimal(row[12]) if row[12] is not None else None,
            Decimal(row[13]), Decimal(row[14]), Decimal(row[15]), row[16],
        )
