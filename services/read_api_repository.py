from __future__ import annotations

from typing import Any
from uuid import UUID

from services.database import get_connection


class ReadApiRepository:
    """Read-only query boundary for the application API."""

    _RESOURCES = {
        "rankings": {
            "run_table": "option_ranking_runs",
            "run_id": "ranking_run_id",
            "run_order": "calculated_at",
            "item_table": "option_rankings",
            "item_order": "rank_position",
        },
        "selections": {
            "run_table": "option_contract_selection_runs",
            "run_id": "selection_run_id",
            "run_order": "calculated_at",
            "item_table": "option_contract_selections",
            "item_order": "underlying_symbol, expiry, option_type",
        },
        "risk": {
            "run_table": "option_risk_assessment_runs",
            "run_id": "risk_run_id",
            "run_order": "calculated_at",
            "item_table": "option_risk_assessments",
            "item_order": "underlying_symbol, expiry, option_type",
        },
        "signals": {
            "run_table": "option_signal_runs",
            "run_id": "signal_run_id",
            "run_order": "calculated_at",
            "item_table": "option_signals",
            "item_order": "underlying_symbol, expiry, option_type",
        },
        "replays": {
            "run_table": "market_replay_runs",
            "run_id": "replay_run_id",
            "run_order": "replayed_at",
            "item_table": "market_replay_events",
            "item_order": "sequence_number",
        },
        "backtests": {
            "run_table": "option_backtest_runs",
            "run_id": "backtest_run_id",
            "run_order": "calculated_at",
            "item_table": "option_backtest_trades",
            "item_order": "underlying_symbol, expiry, option_type",
        },
    }

    def list_latest(self, resource: str, limit: int) -> list[dict[str, Any]]:
        config = self._config(resource)
        query = (
            f"SELECT * FROM {config['run_table']} "
            f"ORDER BY {config['run_order']} DESC, {config['run_id']} DESC LIMIT %s"
        )
        return self._fetch_all(query, (limit,))

    def get_run(self, resource: str, run_id: UUID) -> dict[str, Any] | None:
        config = self._config(resource)
        query = f"SELECT * FROM {config['run_table']} WHERE {config['run_id']} = %s"
        rows = self._fetch_all(query, (run_id,))
        if not rows:
            return None
        run = rows[0]
        item_query = (
            f"SELECT * FROM {config['item_table']} WHERE {config['run_id']} = %s "
            f"ORDER BY {config['item_order']}"
        )
        run["items"] = self._fetch_all(item_query, (run_id,))
        return run

    def health(self) -> dict[str, Any]:
        rows = self._fetch_all("SELECT 1 AS database_ready", ())
        return {"status": "ok", "database_ready": bool(rows[0]["database_ready"])}

    @classmethod
    def resources(cls) -> tuple[str, ...]:
        return tuple(cls._RESOURCES)

    @classmethod
    def _config(cls, resource: str) -> dict[str, str]:
        try:
            return cls._RESOURCES[resource]
        except KeyError as exc:
            raise ValueError(f"Unsupported API resource: {resource}") from exc

    @staticmethod
    def _fetch_all(query: str, parameters: tuple[Any, ...]) -> list[dict[str, Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                columns = [column.name for column in cursor.description or ()]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
