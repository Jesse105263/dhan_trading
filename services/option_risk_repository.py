from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from psycopg.types.json import Jsonb

from services.database import get_connection
from services.option_risk_models import OptionRiskResult, SelectedOptionContract


class OptionRiskRepository:
    def list_selected_contracts(self, selection_run_id: UUID) -> list[SelectedOptionContract]:
        query = """
            SELECT
                selection_id,
                selection_run_id,
                ranking_id,
                analytics_id,
                source_run_id,
                underlying_symbol,
                expiry,
                option_type,
                security_id,
                trading_symbol,
                premium_per_lot,
                lot_size,
                contract_score
            FROM option_contract_selections
            WHERE selection_run_id = %s
            ORDER BY contract_score DESC, underlying_symbol, option_type, security_id
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (selection_run_id,))
                rows = cursor.fetchall()
        output: list[SelectedOptionContract] = []
        for row in rows:
            values = list(row)
            values[10] = Decimal(values[10])
            values[12] = Decimal(values[12])
            output.append(SelectedOptionContract(*values))
        return output

    def persist(self, result: OptionRiskResult) -> OptionRiskResult:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO option_risk_assessment_runs (
                        risk_run_id,
                        selection_run_id,
                        as_of,
                        calculated_at,
                        account_equity,
                        available_capital,
                        existing_total_exposure,
                        approved_contract_count,
                        rejected_contract_count,
                        approved_exposure,
                        methodology_version
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        result.risk_run_id,
                        result.selection_run_id,
                        result.as_of,
                        result.calculated_at,
                        result.account_equity,
                        result.available_capital,
                        result.existing_total_exposure,
                        len(result.approved),
                        len(result.rejected),
                        result.approved_exposure,
                        result.methodology_version,
                    ),
                )
                for item in result.assessments:
                    cursor.execute(
                        """
                        INSERT INTO option_risk_assessments (
                            assessment_id,
                            risk_run_id,
                            selection_id,
                            selection_run_id,
                            ranking_id,
                            analytics_id,
                            source_run_id,
                            underlying_symbol,
                            expiry,
                            option_type,
                            security_id,
                            trading_symbol,
                            premium_per_lot,
                            approved,
                            approved_lots,
                            approved_quantity,
                            approved_exposure,
                            maximum_loss,
                            rejection_code,
                            explanation
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            item.assessment_id,
                            item.risk_run_id,
                            item.selection_id,
                            item.selection_run_id,
                            item.ranking_id,
                            item.analytics_id,
                            item.source_run_id,
                            item.underlying_symbol,
                            item.expiry,
                            item.option_type,
                            item.security_id,
                            item.trading_symbol,
                            item.premium_per_lot,
                            item.approved,
                            item.approved_lots,
                            item.approved_quantity,
                            item.approved_exposure,
                            item.maximum_loss,
                            item.rejection_code,
                            Jsonb(item.explanation),
                        ),
                    )
            connection.commit()
        return result
