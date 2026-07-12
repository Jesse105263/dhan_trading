from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable
from uuid import uuid4

from services.option_contract_selection_models import (
    ContractCandidate,
    OptionContractSelection,
    OptionContractSelectionRequest,
    OptionContractSelectionResult,
)


class OptionContractSelectionEligibilityError(ValueError):
    pass


class OptionContractSelectionService:
    METHODOLOGY_VERSION = "contract-selection-v1"
    Q = Decimal("0.00000001")

    def __init__(
        self,
        repository,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.repository = repository
        self.clock = clock

    def select_and_persist(
        self,
        request: OptionContractSelectionRequest,
    ) -> OptionContractSelectionResult:
        normalized = request.normalized()
        ranked_underlyings = self.repository.list_ranked_underlyings(
            normalized.ranking_run_id,
            normalized.top_underlyings,
        )
        if not ranked_underlyings:
            raise OptionContractSelectionEligibilityError(
                "Ranking run has no underlyings."
            )

        selections: list[OptionContractSelection] = []
        selection_run_id = uuid4()

        for ranked in ranked_underlyings:
            source_age = normalized.as_of - ranked.source_captured_at
            if (
                source_age.total_seconds() < 0
                or source_age > normalized.maximum_source_age
            ):
                continue

            candidates = self.repository.list_contract_candidates(ranked)
            for option_type in ("CE", "PE"):
                eligible = [
                    candidate
                    for candidate in candidates
                    if candidate.option_type == option_type
                    and self._eligible(candidate, normalized)
                ]
                if eligible:
                    selections.append(
                        self._choose(selection_run_id, eligible)
                    )

        if not selections:
            raise OptionContractSelectionEligibilityError(
                "No tradeable option contracts."
            )

        result = OptionContractSelectionResult(
            selection_run_id=selection_run_id,
            ranking_run_id=normalized.ranking_run_id,
            as_of=normalized.as_of,
            calculated_at=self.clock(),
            methodology_version=self.METHODOLOGY_VERSION,
            requested_underlying_count=len(ranked_underlyings),
            selections=tuple(selections),
        )
        return self.repository.persist(result)

    @classmethod
    def _eligible(
        cls,
        candidate: ContractCandidate,
        request: OptionContractSelectionRequest,
    ) -> bool:
        if candidate.last_price is None or candidate.last_price <= 0:
            return False
        if candidate.lot_size <= 0:
            return False
        if candidate.spot_price <= 0:
            return False

        distance = (
            abs(candidate.strike - candidate.spot_price)
            / candidate.spot_price
        )
        spread = cls._spread(candidate)
        premium = candidate.last_price * candidate.lot_size

        return (
            candidate.open_interest >= request.minimum_open_interest
            and candidate.volume >= request.minimum_volume
            and distance <= request.maximum_distance_pct
            and (
                spread is None
                or spread <= request.maximum_spread_pct
            )
            and (
                request.maximum_premium_per_lot is None
                or premium <= request.maximum_premium_per_lot
            )
        )

    @classmethod
    def _choose(
        cls,
        selection_run_id,
        candidates: list[ContractCandidate],
    ) -> OptionContractSelection:
        def sort_key(candidate: ContractCandidate):
            distance = (
                abs(candidate.strike - candidate.spot_price)
                / candidate.spot_price
            )
            spread = cls._spread(candidate) or Decimal(0)
            return (
                distance,
                spread,
                -candidate.open_interest,
                -candidate.volume,
                candidate.strike,
                candidate.security_id,
            )

        candidate = sorted(candidates, key=sort_key)[0]
        if candidate.last_price is None:
            raise OptionContractSelectionEligibilityError(
                "Selected contract is missing last price."
            )

        distance = (
            abs(candidate.strike - candidate.spot_price)
            / candidate.spot_price
        ).quantize(cls.Q, rounding=ROUND_HALF_UP)
        spread = cls._spread(candidate)
        premium = (candidate.last_price * candidate.lot_size).quantize(
            Decimal("0.000001")
        )
        score = max(
            Decimal(0),
            Decimal(1) - distance - (spread or Decimal(0)),
        ).quantize(cls.Q, rounding=ROUND_HALF_UP)

        return OptionContractSelection(
            selection_id=uuid4(),
            selection_run_id=selection_run_id,
            ranking_id=candidate.ranking_id,
            analytics_id=candidate.analytics_id,
            source_run_id=candidate.source_run_id,
            underlying_symbol=candidate.underlying_symbol,
            expiry=candidate.expiry,
            option_type=candidate.option_type,
            security_id=candidate.security_id,
            trading_symbol=candidate.trading_symbol,
            strike=candidate.strike,
            spot_price=candidate.spot_price,
            last_price=candidate.last_price,
            bid_price=candidate.bid_price,
            ask_price=candidate.ask_price,
            open_interest=candidate.open_interest,
            volume=candidate.volume,
            lot_size=candidate.lot_size,
            distance_pct=distance,
            spread_pct=spread,
            premium_per_lot=premium,
            contract_score=score,
            explanation={
                "methodology": cls.METHODOLOGY_VERSION,
                "selection": (
                    "minimum distance, then spread, OI, volume, "
                    "strike and security id"
                ),
            },
        )

    @classmethod
    def _spread(
        cls,
        candidate: ContractCandidate,
    ) -> Decimal | None:
        if (
            candidate.bid_price is None
            or candidate.ask_price is None
            or candidate.ask_price < candidate.bid_price
        ):
            return None

        midpoint = (candidate.bid_price + candidate.ask_price) / 2
        if midpoint <= 0:
            return None

        return (
            (candidate.ask_price - candidate.bid_price) / midpoint
        ).quantize(cls.Q, rounding=ROUND_HALF_UP)
