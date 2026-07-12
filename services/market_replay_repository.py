from __future__ import annotations

from uuid import UUID
from psycopg.types.json import Jsonb

from services.database import get_connection
from services.market_replay_models import MarketReplayResult, ReplayLineage


class MarketReplayRepository:
    def load_lineage(self, signal_run_id: UUID) -> list[ReplayLineage]:
        query = """
            SELECT
                s.signal_id, s.signal_run_id, s.risk_run_id, s.assessment_id,
                s.selection_id, ra.selection_run_id, s.ranking_id,
                sr.ranking_run_id, s.analytics_id, r.change_id, s.source_run_id,
                s.underlying_symbol, s.expiry, s.option_type, cr.status,
                a.source_captured_at, a.calculated_at, rr.calculated_at,
                sr.calculated_at, rar.calculated_at, sgr.calculated_at,
                s.security_id, s.trading_symbol, s.action, s.direction,
                s.strategy_context, s.approved_lots, s.approved_quantity,
                s.entry_price, s.maximum_loss, s.confidence_score
            FROM option_signals s
            JOIN option_signal_runs sgr ON sgr.signal_run_id = s.signal_run_id
            JOIN option_risk_assessments ra ON ra.assessment_id = s.assessment_id
            JOIN option_risk_assessment_runs rar ON rar.risk_run_id = s.risk_run_id
            JOIN option_contract_selection_runs sr ON sr.selection_run_id = ra.selection_run_id
            JOIN option_rankings r ON r.ranking_id = s.ranking_id
            JOIN option_ranking_runs rr ON rr.ranking_run_id = r.ranking_run_id
            JOIN option_chain_analytics a ON a.analytics_id = s.analytics_id
            JOIN option_chain_runs cr ON cr.run_id = s.source_run_id
            WHERE s.signal_run_id = %s
            ORDER BY r.rank_position, s.underlying_symbol, s.expiry, s.option_type, s.security_id
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (signal_run_id,))
                return [ReplayLineage(*row) for row in cursor.fetchall()]

    def persist(self, result: MarketReplayResult) -> MarketReplayResult:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO market_replay_runs
                    (replay_run_id, signal_run_id, requested_as_of, replayed_at,
                     signal_count, event_count, methodology_version)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (result.replay_run_id, result.signal_run_id, result.requested_as_of,
                     result.replayed_at, result.signal_count, len(result.events),
                     result.methodology_version),
                )
                for event in result.events:
                    cursor.execute(
                        """INSERT INTO market_replay_events
                        (replay_event_id, replay_run_id, sequence_number, event_type,
                         event_time, underlying_symbol, expiry, option_type, entity_id, payload)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (event.replay_event_id, event.replay_run_id, event.sequence_number,
                         event.event_type, event.event_time, event.underlying_symbol,
                         event.expiry, event.option_type, event.entity_id, Jsonb(event.payload)),
                    )
            connection.commit()
        return result
