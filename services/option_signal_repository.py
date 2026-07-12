from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from psycopg.types.json import Jsonb

from services.database import get_connection
from services.option_signal_models import ApprovedRiskCandidate, OptionSignalResult


class OptionSignalRepository:
    def list_approved_candidates(self, risk_run_id: UUID) -> list[ApprovedRiskCandidate]:
        query = """
            SELECT
                ra.assessment_id, ra.risk_run_id, ra.selection_id, ra.ranking_id,
                ra.analytics_id, ra.source_run_id, ra.underlying_symbol, ra.expiry,
                ra.option_type, ra.security_id, ra.trading_symbol, ra.approved_lots,
                ra.approved_quantity, ra.premium_per_lot, ra.approved_exposure,
                ra.maximum_loss, s.lot_size, s.contract_score, r.total_score,
                r.liquidity_score, r.activity_score, r.volatility_score,
                r.directional_score
            FROM option_risk_assessments ra
            JOIN option_contract_selections s ON s.selection_id = ra.selection_id
            JOIN option_rankings r ON r.ranking_id = ra.ranking_id
            WHERE ra.risk_run_id = %s AND ra.approved = TRUE
            ORDER BY r.rank_position, ra.underlying_symbol, ra.option_type, ra.security_id
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (risk_run_id,))
                rows = cursor.fetchall()
        output: list[ApprovedRiskCandidate] = []
        for row in rows:
            values = list(row)
            for index in range(13, 16):
                values[index] = Decimal(values[index])
            for index in range(17, 23):
                values[index] = Decimal(values[index])
            output.append(ApprovedRiskCandidate(*values))
        return output

    def persist(self, result: OptionSignalResult) -> OptionSignalResult:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO option_signal_runs (
                        signal_run_id, risk_run_id, as_of, calculated_at,
                        approved_input_count, generated_signal_count, methodology_version
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        result.signal_run_id, result.risk_run_id, result.as_of,
                        result.calculated_at, result.approved_input_count,
                        len(result.signals), result.methodology_version,
                    ),
                )
                for signal in result.signals:
                    cursor.execute(
                        """
                        INSERT INTO option_signals (
                            signal_id, signal_run_id, risk_run_id, assessment_id,
                            selection_id, ranking_id, analytics_id, source_run_id,
                            underlying_symbol, expiry, option_type, security_id,
                            trading_symbol, action, direction, strategy_context,
                            approved_lots, approved_quantity, entry_price,
                            premium_per_lot, approved_exposure, maximum_loss,
                            confidence_score, rationale
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            signal.signal_id, signal.signal_run_id, signal.risk_run_id,
                            signal.assessment_id, signal.selection_id, signal.ranking_id,
                            signal.analytics_id, signal.source_run_id,
                            signal.underlying_symbol, signal.expiry, signal.option_type,
                            signal.security_id, signal.trading_symbol, signal.action,
                            signal.direction, signal.strategy_context,
                            signal.approved_lots, signal.approved_quantity,
                            signal.entry_price, signal.premium_per_lot,
                            signal.approved_exposure, signal.maximum_loss,
                            signal.confidence_score, Jsonb(signal.rationale),
                        ),
                    )
            connection.commit()
        return result
