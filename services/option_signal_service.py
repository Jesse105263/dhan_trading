from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable
from uuid import uuid4

from services.option_signal_models import (
    ApprovedRiskCandidate,
    OptionSignal,
    OptionSignalRequest,
    OptionSignalResult,
)


class OptionSignalEligibilityError(ValueError):
    pass


class OptionSignalService:
    METHODOLOGY_VERSION = "long-option-signal-v1"
    SCORE_QUANTUM = Decimal("0.00000001")
    PRICE_QUANTUM = Decimal("0.000001")

    def __init__(self, repository, clock: Callable[[], datetime] = datetime.now) -> None:
        self.repository = repository
        self.clock = clock

    def generate_and_persist(self, request: OptionSignalRequest) -> OptionSignalResult:
        normalized = request.normalized()
        candidates = self.repository.list_approved_candidates(normalized.risk_run_id)
        if not candidates:
            raise OptionSignalEligibilityError("Risk run has no approved contracts.")

        signal_run_id = uuid4()
        side_sets: dict[tuple[str, object], set[str]] = defaultdict(set)
        for candidate in candidates:
            side_sets[(candidate.underlying_symbol, candidate.expiry)].add(candidate.option_type)

        signals: list[OptionSignal] = []
        for candidate in candidates:
            self._validate_candidate(candidate, normalized.as_of)
            confidence = self._confidence(candidate)
            if confidence < normalized.minimum_confidence:
                continue
            sides = side_sets[(candidate.underlying_symbol, candidate.expiry)]
            strategy_context = "LONG_STRADDLE_LEG" if sides == {"CE", "PE"} else (
                "LONG_CALL" if candidate.option_type == "CE" else "LONG_PUT"
            )
            direction = "BULLISH" if candidate.option_type == "CE" else "BEARISH"
            entry_price = (candidate.premium_per_lot / Decimal(candidate.lot_size)).quantize(
                self.PRICE_QUANTUM, rounding=ROUND_HALF_UP
            )
            signals.append(
                OptionSignal(
                    signal_id=uuid4(), signal_run_id=signal_run_id,
                    risk_run_id=candidate.risk_run_id,
                    assessment_id=candidate.assessment_id,
                    selection_id=candidate.selection_id,
                    ranking_id=candidate.ranking_id,
                    analytics_id=candidate.analytics_id,
                    source_run_id=candidate.source_run_id,
                    underlying_symbol=candidate.underlying_symbol,
                    expiry=candidate.expiry, option_type=candidate.option_type,
                    security_id=candidate.security_id,
                    trading_symbol=candidate.trading_symbol,
                    action="BUY_TO_OPEN", direction=direction,
                    strategy_context=strategy_context,
                    approved_lots=candidate.approved_lots,
                    approved_quantity=candidate.approved_quantity,
                    entry_price=entry_price,
                    premium_per_lot=candidate.premium_per_lot,
                    approved_exposure=candidate.approved_exposure,
                    maximum_loss=candidate.maximum_loss,
                    confidence_score=confidence,
                    rationale={
                        "methodology": self.METHODOLOGY_VERSION,
                        "action": "risk-approved long option; no order execution",
                        "direction": f"{candidate.option_type} maps deterministically to {direction}",
                        "strategy_context": strategy_context,
                        "confidence": "40% ranking, 30% contract, 15% liquidity, 10% activity, 5% volatility",
                        "lineage": "risk -> selection -> ranking -> analytics -> option-chain source run",
                    },
                )
            )

        if not signals:
            raise OptionSignalEligibilityError("No approved contracts met signal eligibility.")
        result = OptionSignalResult(
            signal_run_id=signal_run_id,
            risk_run_id=normalized.risk_run_id,
            as_of=normalized.as_of,
            calculated_at=self.clock(),
            approved_input_count=len(candidates),
            methodology_version=self.METHODOLOGY_VERSION,
            signals=tuple(signals),
        )
        return self.repository.persist(result)

    @classmethod
    def _confidence(cls, candidate: ApprovedRiskCandidate) -> Decimal:
        score = (
            candidate.ranking_score * Decimal("0.40")
            + candidate.contract_score * Decimal("0.30")
            + candidate.liquidity_score * Decimal("0.15")
            + candidate.activity_score * Decimal("0.10")
            + candidate.volatility_score * Decimal("0.05")
        )
        return max(Decimal("0"), min(Decimal("1"), score)).quantize(
            cls.SCORE_QUANTUM, rounding=ROUND_HALF_UP
        )

    @staticmethod
    def _validate_candidate(candidate: ApprovedRiskCandidate, as_of: datetime) -> None:
        if candidate.option_type not in {"CE", "PE"}:
            raise OptionSignalEligibilityError("Approved candidate has invalid option type.")
        if candidate.expiry < as_of.date():
            raise OptionSignalEligibilityError("Approved candidate is expired.")
        if candidate.approved_lots <= 0 or candidate.approved_quantity <= 0:
            raise OptionSignalEligibilityError("Approved candidate has invalid position size.")
        if candidate.lot_size <= 0 or candidate.premium_per_lot <= 0:
            raise OptionSignalEligibilityError("Approved candidate has invalid pricing data.")
