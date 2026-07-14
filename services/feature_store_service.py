from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid5

import psycopg

from services.feature_store_repository import FeatureStoreRepository
from services.market_workspace_service import WorkspaceQueryError, WorkspaceUnavailable


class FeatureStoreService:
    SCHEMA_VERSION = "option-observation-v1"
    NAMESPACE = UUID("4918286e-04df-4aee-89c0-d64e559db629")
    ANALYTICS = (
        "spot_price", "atm_strike", "atm_distance", "atm_distance_pct",
        "atm_call_price", "atm_put_price", "atm_straddle_cost", "total_call_oi",
        "total_put_oi", "total_pcr", "nearby_call_oi", "nearby_put_oi", "nearby_pcr",
        "atm_call_iv", "atm_put_iv", "atm_mean_iv", "nearby_call_mean_iv",
        "nearby_put_mean_iv", "nearby_mean_iv", "call_oi_wall_strike",
        "call_oi_wall_value", "put_oi_wall_strike", "put_oi_wall_value",
        "minimum_strike", "maximum_strike", "strike_count", "nearby_strike_count",
        "quote_count", "priced_quote_count", "liquid_quote_count", "price_coverage",
        "liquidity_coverage",
    )
    CHANGES = (
        "elapsed_seconds", "spot_price_change", "atm_straddle_change",
        "total_call_oi_change", "total_put_oi_change", "total_pcr_change",
        "nearby_call_oi_change", "nearby_put_oi_change", "nearby_pcr_change",
        "atm_mean_iv_change", "nearby_mean_iv_change", "call_oi_wall_strike_change",
        "put_oi_wall_strike_change", "call_oi_wall_value_change",
        "put_oi_wall_value_change", "liquidity_coverage_change", "price_coverage_change",
    )
    RANKING = (
        "rank_position", "total_score", "liquidity_score", "activity_score",
        "volatility_score", "directional_score",
    )

    def __init__(self, repository: FeatureStoreRepository | None = None, clock=datetime.now) -> None:
        self.repository = repository or FeatureStoreRepository()
        self.clock = clock

    @classmethod
    def definitions(cls) -> list[dict[str, Any]]:
        definitions = []
        for group, relation, fields in (
            ("analytics", "option_chain_analytics", cls.ANALYTICS),
            ("change", "option_analytics_changes", cls.CHANGES),
            ("ranking", "option_rankings", cls.RANKING),
        ):
            definitions.extend({"name": field, "group": group, "source_relation": relation,
                                "source_field": field, "nullable": group != "analytics"}
                               for field in fields)
        definitions.append({"name": "time_to_expiry_days", "group": "temporal",
                            "source_relation": "option_chain_analytics",
                            "source_field": "expiry-source_captured_at", "nullable": False})
        return definitions

    def materialize(self, limit: int | None = None, batch_size: int = 500) -> dict[str, int]:
        if limit is not None and limit < 1:
            raise ValueError("limit must be greater than zero.")
        if not 1 <= batch_size <= 1000:
            raise ValueError("batch_size must be between 1 and 1000.")
        total, after_at, after_id = 0, None, None
        while limit is None or total < limit:
            request_size = min(batch_size, limit - total) if limit is not None else batch_size
            sources = self.repository.source_observations(request_size, after_at, after_id)
            if not sources: break
            for source in sources:
                vector, values = self._build(source)
                self.repository.upsert_vector(vector, values)
            total += len(sources)
            last = sources[-1]["analytics"]
            after_at, after_id = last["source_captured_at"], last["analytics_id"]
            if len(sources) < request_size: break
        return {"source_count": total, "materialized_count": total}

    def list(self, query: dict[str, str]) -> dict[str, Any]:
        symbol = (query.get("symbol") or "").strip().upper()
        if not symbol or len(symbol) > 30:
            raise WorkspaceQueryError("symbol must contain 1 to 30 characters.")
        expiry = query.get("expiry") or None
        if expiry:
            try: date.fromisoformat(expiry)
            except ValueError as exc: raise WorkspaceQueryError("expiry must be an ISO date.") from exc
        try: limit = int(query.get("limit", "50"))
        except ValueError as exc: raise WorkspaceQueryError("limit must be an integer.") from exc
        if not 1 <= limit <= 200: raise WorkspaceQueryError("limit must be between 1 and 200.")
        try: rows = self.repository.list_vectors(symbol, expiry, limit)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Persisted features are unavailable.") from exc
        return {"data": rows, "count": len(rows), "limit": limit, "schema_version": self.SCHEMA_VERSION}

    def detail(self, vector_id: UUID) -> dict[str, Any] | None:
        try: return self.repository.get_vector(vector_id)
        except psycopg.Error as exc: raise WorkspaceUnavailable("Persisted features are unavailable.") from exc

    def _build(self, source: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        analytics, changes, ranking = source["analytics"], source.get("changes") or {}, source.get("ranking") or {}
        values = []
        for group, relation, record, fields in (
            ("analytics", "option_chain_analytics", analytics, self.ANALYTICS),
            ("change", "option_analytics_changes", changes, self.CHANGES),
            ("ranking", "option_rankings", ranking, self.RANKING),
        ):
            values.extend({"name": field, "group": group, "value": record.get(field),
                           "relation": relation, "field": field} for field in fields)
        captured_value, expiry_value = analytics["source_captured_at"], analytics["expiry"]
        captured = captured_value if isinstance(captured_value, datetime) else datetime.fromisoformat(captured_value)
        expiry = expiry_value if isinstance(expiry_value, date) else date.fromisoformat(expiry_value)
        values.append({"name": "time_to_expiry_days", "group": "temporal",
                       "value": Decimal((expiry - captured.date()).days),
                       "relation": "option_chain_analytics", "field": "expiry-source_captured_at"})
        missing = sum(value["value"] is None for value in values)
        analytics_id = UUID(str(analytics["analytics_id"]))
        vector = {
            "vector_id": uuid5(self.NAMESPACE, f"{self.SCHEMA_VERSION}:{analytics_id}"),
            "analytics_id": analytics_id, "change_id": changes.get("change_id"),
            "ranking_id": ranking.get("ranking_id"),
            "underlying_symbol": analytics["underlying_symbol"], "expiry": expiry,
            "observed_at": captured, "schema_version": self.SCHEMA_VERSION,
            "quality_state": "COMPLETE" if missing == 0 else "PARTIAL",
            "feature_count": len(values), "missing_feature_count": missing,
            "materialized_at": self.clock(),
        }
        return vector, values
