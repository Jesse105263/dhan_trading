from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from psycopg.types.json import Jsonb

from services.database import get_connection
from services.option_backtest_models import BacktestMarketMark, BacktestSignal, OptionBacktestResult


class OptionBacktestRepository:
    def list_signals(self, signal_run_id: UUID) -> list[BacktestSignal]:
        query = """
            SELECT
                s.signal_id, s.signal_run_id, s.source_run_id,
                s.underlying_symbol, s.expiry, s.option_type,
                s.security_id, s.trading_symbol, s.approved_quantity,
                s.entry_price, a.source_captured_at, sr.calculated_at
            FROM option_signals s
            JOIN option_signal_runs sr ON sr.signal_run_id = s.signal_run_id
            JOIN option_chain_analytics a ON a.analytics_id = s.analytics_id
            WHERE s.signal_run_id = %s
            ORDER BY s.underlying_symbol, s.expiry, s.option_type, s.security_id
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (signal_run_id,))
                rows = cursor.fetchall()
        return [
            BacktestSignal(
                row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7],
                int(row[8]), Decimal(row[9]), row[10], row[11]
            )
            for row in rows
        ]

    def list_future_marks(
        self,
        signal: BacktestSignal,
        as_of: datetime,
    ) -> list[BacktestMarketMark]:
        query = """
            SELECT q.run_id, q.captured_at, q.last_price
            FROM option_chain_quotes q
            JOIN option_chain_runs r ON r.run_id = q.run_id
            WHERE q.underlying_symbol = %s
              AND q.expiry = %s
              AND q.security_id = %s
              AND q.option_type = %s
              AND q.captured_at > %s
              AND q.captured_at <= %s
              AND q.last_price IS NOT NULL
              AND q.last_price > 0
              AND r.status = 'COMPLETED'
            ORDER BY q.captured_at, q.run_id
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        signal.underlying_symbol, signal.expiry, signal.security_id,
                        signal.option_type, signal.source_captured_at, as_of,
                    ),
                )
                rows = cursor.fetchall()
        return [BacktestMarketMark(row[0], row[1], Decimal(row[2])) for row in rows]

    def persist(self, result: OptionBacktestResult) -> OptionBacktestResult:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO option_backtest_runs (
                        backtest_run_id, signal_run_id, requested_as_of, calculated_at,
                        signal_count, completed_trade_count, skipped_trade_count,
                        gross_pnl, transaction_costs, net_pnl, return_on_exposure,
                        win_rate, profit_factor, maximum_drawdown,
                        methodology_version, parameters
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        result.backtest_run_id, result.signal_run_id,
                        result.requested_as_of, result.calculated_at,
                        result.signal_count, result.completed_trade_count,
                        result.skipped_trade_count, result.gross_pnl,
                        result.transaction_costs, result.net_pnl,
                        result.return_on_exposure, result.win_rate,
                        result.profit_factor, result.maximum_drawdown,
                        result.methodology_version, Jsonb(result.parameters),
                    ),
                )
                for trade in result.trades:
                    cursor.execute(
                        """
                        INSERT INTO option_backtest_trades (
                            backtest_trade_id, backtest_run_id, signal_id, source_run_id,
                            exit_run_id, underlying_symbol, expiry, option_type,
                            security_id, trading_symbol, quantity, entry_time, exit_time,
                            entry_reference_price, entry_execution_price,
                            exit_reference_price, exit_execution_price, exit_reason,
                            gross_pnl, transaction_costs, net_pnl, return_rate
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            trade.backtest_trade_id, trade.backtest_run_id,
                            trade.signal_id, trade.source_run_id, trade.exit_run_id,
                            trade.underlying_symbol, trade.expiry, trade.option_type,
                            trade.security_id, trade.trading_symbol, trade.quantity,
                            trade.entry_time, trade.exit_time,
                            trade.entry_reference_price, trade.entry_execution_price,
                            trade.exit_reference_price, trade.exit_execution_price,
                            trade.exit_reason, trade.gross_pnl,
                            trade.transaction_costs, trade.net_pnl, trade.return_rate,
                        ),
                    )
            connection.commit()
        return result
