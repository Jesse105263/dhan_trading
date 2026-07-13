from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from services.database import get_connection
from services.release_readiness_models import AppliedMigration, AuditMetric


class ReleaseReadinessRepository:
    """SELECT-only database evidence for Version 1.0 release checks."""

    def database_identity(self) -> tuple[str, str, bool]:
        row = self._fetch_one(
            "SELECT current_database(), current_user, pg_is_in_recovery()",
        )
        return str(row[0]), str(row[1]), bool(row[2])

    def applied_migrations(self) -> tuple[AppliedMigration, ...]:
        rows = self._fetch_all(
            """
            SELECT version, filename, checksum
            FROM schema_migrations
            ORDER BY version
            """
        )
        return tuple(
            AppliedMigration(str(row[0]), str(row[1]), str(row[2]))
            for row in rows
        )

    def audit_metrics(self) -> Mapping[str, AuditMetric]:
        return {
            "option_chain_lineage": self._option_chain_lineage(),
            "decision_lineage": self._decision_lineage(),
            "evaluation_lineage": self._evaluation_lineage(),
            "alert_lineage": self._alert_lineage(),
            "paper_lineage": self._paper_lineage(),
            "operational_state": self._operational_state(),
            "execution_schema_boundary": self._execution_schema_boundary(),
        }

    def _option_chain_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH audited AS (
                SELECT
                    a.analytics_id::text AS entity_id,
                    (
                        r.status <> 'COMPLETED'
                        OR a.source_run_id <> r.run_id
                        OR a.underlying_symbol <> r.underlying_symbol
                        OR a.expiry <> r.expiry
                    ) AS violation
                FROM option_chain_analytics a
                JOIN option_chain_runs r ON r.run_id = a.source_run_id
                UNION ALL
                SELECT
                    c.change_id::text,
                    (
                        c.previous_source_run_id <> previous.source_run_id
                        OR c.current_source_run_id <> current.source_run_id
                        OR c.underlying_symbol <> previous.underlying_symbol
                        OR c.underlying_symbol <> current.underlying_symbol
                        OR c.expiry <> previous.expiry
                        OR c.expiry <> current.expiry
                        OR c.previous_captured_at <> previous.source_captured_at
                        OR c.current_captured_at <> current.source_captured_at
                        OR c.previous_captured_at >= c.current_captured_at
                    )
                FROM option_analytics_changes c
                JOIN option_chain_analytics previous
                  ON previous.analytics_id = c.previous_analytics_id
                JOIN option_chain_analytics current
                  ON current.analytics_id = c.current_analytics_id
            )
            SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
            """
        )
        return self._metric("option_chain_lineage", row)

    def _decision_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH audited AS (
                SELECT r.ranking_id::text AS entity_id,
                    (
                        r.analytics_id <> c.current_analytics_id
                        OR r.underlying_symbol <> a.underlying_symbol
                        OR r.expiry <> a.expiry
                        OR r.source_captured_at <> a.source_captured_at
                    ) AS violation
                FROM option_rankings r
                JOIN option_chain_analytics a ON a.analytics_id = r.analytics_id
                JOIN option_analytics_changes c ON c.change_id = r.change_id
                UNION ALL
                SELECT s.selection_id::text,
                    (
                        s.analytics_id <> r.analytics_id
                        OR s.source_run_id <> a.source_run_id
                        OR s.underlying_symbol <> r.underlying_symbol
                        OR s.expiry <> r.expiry
                    )
                FROM option_contract_selections s
                JOIN option_rankings r ON r.ranking_id = s.ranking_id
                JOIN option_chain_analytics a ON a.analytics_id = s.analytics_id
                UNION ALL
                SELECT ra.assessment_id::text,
                    (
                        ra.selection_run_id <> s.selection_run_id
                        OR ra.ranking_id <> s.ranking_id
                        OR ra.analytics_id <> s.analytics_id
                        OR ra.source_run_id <> s.source_run_id
                        OR ra.underlying_symbol <> s.underlying_symbol
                        OR ra.expiry <> s.expiry
                        OR ra.option_type <> s.option_type
                        OR ra.security_id <> s.security_id
                    )
                FROM option_risk_assessments ra
                JOIN option_contract_selections s ON s.selection_id = ra.selection_id
                UNION ALL
                SELECT sig.signal_id::text,
                    (
                        sig.risk_run_id <> sr.risk_run_id
                        OR sig.risk_run_id <> ra.risk_run_id
                        OR sig.selection_id <> ra.selection_id
                        OR sig.ranking_id <> ra.ranking_id
                        OR sig.analytics_id <> ra.analytics_id
                        OR sig.source_run_id <> ra.source_run_id
                        OR sig.underlying_symbol <> ra.underlying_symbol
                        OR sig.expiry <> ra.expiry
                        OR sig.option_type <> ra.option_type
                        OR sig.security_id <> ra.security_id
                        OR ra.approved IS NOT TRUE
                    )
                FROM option_signals sig
                JOIN option_signal_runs sr ON sr.signal_run_id = sig.signal_run_id
                JOIN option_risk_assessments ra
                  ON ra.assessment_id = sig.assessment_id
            )
            SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
            """
        )
        return self._metric("decision_lineage", row)

    def _evaluation_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH replay_counts AS (
                SELECT rr.replay_run_id, rr.event_count,
                       COUNT(e.replay_event_id) AS actual_events,
                       COUNT(e.replay_event_id) FILTER (
                           WHERE e.sequence_number <= 0
                       ) AS invalid_events
                FROM market_replay_runs rr
                LEFT JOIN market_replay_events e
                  ON e.replay_run_id = rr.replay_run_id
                GROUP BY rr.replay_run_id, rr.event_count
            ), backtest_counts AS (
                SELECT br.backtest_run_id, br.signal_run_id, br.signal_count,
                       br.completed_trade_count, br.skipped_trade_count,
                       COUNT(bt.backtest_trade_id) AS actual_trades,
                       COUNT(bt.backtest_trade_id) FILTER (
                           WHERE bt.signal_id IS NOT NULL
                             AND sig.signal_run_id <> br.signal_run_id
                       ) AS lineage_errors
                FROM option_backtest_runs br
                LEFT JOIN option_backtest_trades bt
                  ON bt.backtest_run_id = br.backtest_run_id
                LEFT JOIN option_signals sig ON sig.signal_id = bt.signal_id
                GROUP BY br.backtest_run_id, br.signal_run_id, br.signal_count,
                         br.completed_trade_count, br.skipped_trade_count
            ), audited AS (
                SELECT replay_run_id::text AS entity_id,
                       (event_count <> actual_events OR invalid_events > 0) AS violation
                FROM replay_counts
                UNION ALL
                SELECT backtest_run_id::text,
                       (
                           signal_count <> actual_trades
                           OR completed_trade_count + skipped_trade_count <> actual_trades
                           OR lineage_errors > 0
                       )
                FROM backtest_counts
            )
            SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
            """
        )
        return self._metric("evaluation_lineage", row)

    def _alert_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            SELECT COUNT(*), COUNT(*) FILTER (
                WHERE
                    (a.source_type = 'SIGNAL' AND NOT EXISTS (
                        SELECT 1 FROM option_signals s
                        WHERE s.signal_id::text = a.source_id
                          AND s.signal_run_id::text = a.source_run_id
                    ))
                    OR (a.source_type = 'RISK_DECISION' AND NOT EXISTS (
                        SELECT 1 FROM option_risk_assessments r
                        WHERE r.assessment_id::text = a.source_id
                          AND r.risk_run_id::text = a.source_run_id
                    ))
                    OR (a.source_type = 'PIPELINE_HEALTH' AND NOT EXISTS (
                        SELECT 1 FROM pipeline_runs p
                        WHERE p.run_id = a.source_id
                          AND p.run_id = a.source_run_id
                    ))
            )
            FROM alert_events a
            """
        )
        return self._metric("alert_lineage", row)

    def _paper_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH event_counts AS (
                SELECT position_id, COUNT(*) AS event_count,
                       MIN(sequence_number) AS first_sequence,
                       MAX(sequence_number) AS last_sequence
                FROM paper_position_events
                GROUP BY position_id
            ), fill_counts AS (
                SELECT position_id,
                       COUNT(*) FILTER (WHERE side = 'BUY') AS buy_fills,
                       COUNT(*) FILTER (WHERE side = 'SELL') AS sell_fills
                FROM paper_trade_fills
                GROUP BY position_id
            )
            SELECT COUNT(*), COUNT(*) FILTER (
                WHERE
                    p.signal_run_id <> s.signal_run_id
                    OR p.risk_run_id <> s.risk_run_id
                    OR p.assessment_id <> s.assessment_id
                    OR p.selection_id <> s.selection_id
                    OR p.ranking_id <> s.ranking_id
                    OR p.analytics_id <> s.analytics_id
                    OR p.source_run_id <> s.source_run_id
                    OR p.underlying_symbol <> s.underlying_symbol
                    OR p.expiry <> s.expiry
                    OR p.option_type <> s.option_type
                    OR p.security_id <> s.security_id
                    OR entry_order.signal_id <> p.signal_id
                    OR entry_order.side <> 'BUY'
                    OR entry_order.status <> 'FILLED'
                    OR COALESCE(f.buy_fills, 0) <> 1
                    OR COALESCE(e.first_sequence, 0) <> 1
                    OR e.last_sequence <> e.event_count
                    OR (
                        p.status = 'OPEN'
                        AND (COALESCE(f.sell_fills, 0) <> 0 OR p.exit_order_id IS NOT NULL)
                    )
                    OR (
                        p.status = 'CLOSED'
                        AND (COALESCE(f.sell_fills, 0) <> 1 OR p.exit_order_id IS NULL)
                    )
            )
            FROM paper_positions p
            JOIN option_signals s ON s.signal_id = p.signal_id
            JOIN paper_trade_orders entry_order
              ON entry_order.order_id = p.entry_order_id
            LEFT JOIN event_counts e ON e.position_id = p.position_id
            LEFT JOIN fill_counts f ON f.position_id = p.position_id
            """
        )
        return self._metric("paper_lineage", row)

    def _operational_state(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH audited AS (
                SELECT run_id::text AS entity_id,
                    (
                        (status IN ('COMPLETED', 'FAILED') AND completed_at IS NULL)
                        OR (status = 'COMPLETED' AND error_message IS NOT NULL)
                        OR (status = 'FAILED' AND error_message IS NULL)
                    ) AS violation
                FROM option_chain_runs
                UNION ALL
                SELECT run_id,
                    (
                        (status IN ('COMPLETED', 'FAILED') AND completed_at IS NULL)
                        OR (status = 'RUNNING' AND completed_at IS NOT NULL)
                    )
                FROM pipeline_runs
            )
            SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
            """
        )
        return self._metric("operational_state", row)

    def _execution_schema_boundary(self) -> AuditMetric:
        row = self._fetch_one(
            """
            SELECT COUNT(*), COUNT(*) FILTER (
                WHERE table_name NOT IN ('paper_trade_orders')
            )
            FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_type = 'BASE TABLE'
              AND (
                  table_name LIKE '%broker%'
                  OR table_name LIKE '%live_order%'
                  OR table_name LIKE '%trade_order%'
              )
            """
        )
        audited = max(int(row[0]), 1)
        return AuditMetric("execution_schema_boundary", audited, int(row[1]))

    @staticmethod
    def _metric(name: str, row: tuple[Any, ...]) -> AuditMetric:
        return AuditMetric(name, int(row[0]), int(row[1]))

    @staticmethod
    def _fetch_one(query: str) -> tuple[Any, ...]:
        rows = ReleaseReadinessRepository._fetch_all(query)
        if len(rows) != 1:
            raise RuntimeError("Release audit query did not return exactly one row.")
        return rows[0]

    @staticmethod
    def _fetch_all(query: str) -> list[tuple[Any, ...]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
