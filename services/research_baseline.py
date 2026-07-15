from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Protocol

from services.database import get_connection


@dataclass(frozen=True)
class ResearchPeriod:
    name: str
    start: date
    end: date


@dataclass(frozen=True)
class ResearchContract:
    version: str
    decision_boundary: str
    outcome_model: str
    purge_days: int
    embargo_days: int
    minimum_effective_sample_size: int
    periods: tuple[ResearchPeriod, ...]
    baseline_names: tuple[str, ...]

    def manifest(self) -> dict[str, Any]:
        value = asdict(self)
        value["periods"] = [
            {**period, "start": period["start"].isoformat(), "end": period["end"].isoformat()}
            for period in value["periods"]
        ]
        return value

    def checksum(self) -> str:
        payload = json.dumps(self.manifest(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


RESEARCH_CONTRACT = ResearchContract(
    version="v3-research-contract-v1",
    decision_boundary="Only values available at or before observed_at may be predictive inputs.",
    outcome_model="underlying-through-expiry-v1",
    purge_days=45,
    embargo_days=7,
    minimum_effective_sample_size=30,
    periods=(
        ResearchPeriod("TRAIN", date(2020, 1, 1), date(2023, 12, 31)),
        ResearchPeriod("VALIDATION", date(2024, 1, 1), date(2024, 12, 31)),
        ResearchPeriod("CALIBRATION", date(2025, 1, 1), date(2025, 6, 30)),
        ResearchPeriod("TEST", date(2025, 7, 1), date(2026, 12, 31)),
    ),
    baseline_names=(
        "always_long",
        "deterministic_random_half",
        "momentum_positive",
        "mean_reversion_negative",
        "v2_ranked",
        "v2_opportunity",
    ),
)


class ResearchBaselineRepositoryProtocol(Protocol):
    def observations(
        self, start: date, end: date, outcome_model: str
    ) -> list[dict[str, Any]]: ...


class ResearchBaselineRepository:
    """SELECT-only access to immutable Version 2 evidence for benchmarking."""

    @staticmethod
    def observations(
        start: date, end: date, outcome_model: str
    ) -> list[dict[str, Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT v.vector_id, v.observed_at, v.ranking_id,
                              change.numeric_value AS spot_price_change,
                              o.outcome_type, o.closing_return, o.won,
                              opportunity.state AS opportunity_state,
                              opportunity.historical_win_rate AS predicted_win_rate,
                              opportunity.expected_value AS predicted_expected_value
                       FROM feature_store_vectors v
                       LEFT JOIN feature_store_values change
                         ON change.vector_id=v.vector_id
                        AND change.feature_name='spot_price_change'
                       LEFT JOIN historical_outcomes o
                         ON o.vector_id=v.vector_id
                        AND o.model_version=%s
                       LEFT JOIN LATERAL (
                         SELECT candidate.state, candidate.historical_win_rate,
                                candidate.expected_value
                         FROM trade_opportunities candidate
                         WHERE candidate.query_vector_id=v.vector_id
                         ORDER BY candidate.observed_at DESC,
                                  candidate.opportunity_id DESC
                         LIMIT 1
                       ) opportunity ON TRUE
                       WHERE v.observed_at::date BETWEEN %s AND %s
                       ORDER BY v.observed_at, v.vector_id""",
                    (outcome_model, start, end),
                )
                columns = [column.name for column in cursor.description or ()]
                return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


class ResearchBaselineService:
    """Builds deterministic, non-predictive benchmarks from persisted evidence."""

    def __init__(
        self,
        repository: ResearchBaselineRepositoryProtocol | None = None,
        contract: ResearchContract = RESEARCH_CONTRACT,
    ) -> None:
        self.repository = repository or ResearchBaselineRepository()
        self.contract = contract
        self._validate_contract()

    def report(self) -> dict[str, Any]:
        first, last = self.contract.periods[0], self.contract.periods[-1]
        observations = self.repository.observations(
            first.start, last.end, self.contract.outcome_model
        )
        periods = []
        for period in self.contract.periods:
            rows = [
                row for row in observations
                if period.start <= row["observed_at"].date() <= period.end
            ]
            periods.append({
                "name": period.name,
                "start": period.start.isoformat(),
                "end": period.end.isoformat(),
                "population_count": len(rows),
                "baselines": [self._evaluate(name, rows) for name in self.contract.baseline_names],
            })
        return {
            "contract": self.contract.manifest(),
            "contract_checksum": self.contract.checksum(),
            "periods": periods,
            "limitations": [
                "Version 2 outcomes measure underlying spot through expiry, not option-premium returns.",
                "Transaction costs, slippage, turnover, capacity and calibrated intervals are unavailable in Version 2 evidence.",
                "Metrics remain null when no classified observations satisfy a baseline.",
            ],
        }

    def _evaluate(self, name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        selected = [row for row in rows if self._selected(name, row)]
        evaluated = [
            row for row in selected
            if row.get("outcome_type") == "EXPIRY_COMPLETE"
            and row.get("won") is not None
            and row.get("closing_return") is not None
        ]
        returns = [Decimal(row["closing_return"]) for row in evaluated]
        wins = [Decimal(1 if row["won"] else 0) for row in evaluated]
        probabilities = [
            (Decimal(row["predicted_win_rate"]), Decimal(1 if row["won"] else 0))
            for row in evaluated if row.get("predicted_win_rate") is not None
        ]
        win_rate = self._mean(wins)
        average_return = self._mean(returns)
        average_probability = self._mean([probability for probability, _ in probabilities])
        predicted_outcome_rate = self._mean([outcome for _, outcome in probabilities])
        return {
            "name": name,
            "selected_count": len(selected),
            "evaluated_count": len(evaluated),
            "coverage": self._ratio(len(selected), len(rows)),
            "abstention_rate": self._ratio(len(rows) - len(selected), len(rows)),
            "precision": win_rate,
            "win_rate": win_rate,
            "expected_value": average_return,
            "average_realized_return": average_return,
            "worst_realized_return": min(returns) if returns else None,
            "tail_loss": min(returns) if returns else None,
            "maximum_drawdown": self._maximum_drawdown(returns),
            "brier_score": self._mean([(probability - outcome) ** 2 for probability, outcome in probabilities]),
            "calibration_error": (
                abs(average_probability - predicted_outcome_rate)
                if average_probability is not None and predicted_outcome_rate is not None else None
            ),
            "cost_adjusted_return": None,
            "turnover": None,
            "prediction_interval_coverage": None,
            "prediction_count": len(probabilities),
            "evidence_state": (
                "SUFFICIENT" if len(evaluated) >= self.contract.minimum_effective_sample_size
                else "INSUFFICIENT"
            ),
        }

    @staticmethod
    def _selected(name: str, row: dict[str, Any]) -> bool:
        if name == "always_long":
            return True
        if name == "deterministic_random_half":
            digest = hashlib.sha256(f"v3-baseline-seed-1:{row['vector_id']}".encode()).digest()
            return digest[0] < 128
        if name == "momentum_positive":
            return row.get("spot_price_change") is not None and Decimal(row["spot_price_change"]) > 0
        if name == "mean_reversion_negative":
            return row.get("spot_price_change") is not None and Decimal(row["spot_price_change"]) < 0
        if name == "v2_ranked":
            return row.get("ranking_id") is not None
        if name == "v2_opportunity":
            return row.get("opportunity_state") == "ELIGIBLE"
        raise ValueError(f"Unsupported baseline: {name}")

    def _validate_contract(self) -> None:
        if not self.contract.version or self.contract.minimum_effective_sample_size < 1:
            raise ValueError("Research contract version and sample size are required.")
        if not self.contract.periods or not self.contract.baseline_names:
            raise ValueError("Research periods and baselines are required.")
        previous_end = None
        for period in self.contract.periods:
            if period.start > period.end:
                raise ValueError(f"Research period {period.name} has an invalid range.")
            if previous_end is not None and period.start <= previous_end:
                raise ValueError("Research periods must be ordered and non-overlapping.")
            previous_end = period.end

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> Decimal | None:
        return Decimal(numerator) / Decimal(denominator) if denominator else None

    @staticmethod
    def _mean(values: list[Decimal]) -> Decimal | None:
        return sum(values, Decimal(0)) / Decimal(len(values)) if values else None

    @staticmethod
    def _maximum_drawdown(returns: list[Decimal]) -> Decimal | None:
        if not returns:
            return None
        wealth = peak = Decimal(1)
        drawdown = Decimal(0)
        for value in returns:
            wealth *= Decimal(1) + value / Decimal(100)
            peak = max(peak, wealth)
            drawdown = min(drawdown, wealth / peak - Decimal(1))
        return drawdown * Decimal(100)
