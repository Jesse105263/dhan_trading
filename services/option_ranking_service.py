from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable
from uuid import uuid4

from services.option_ranking_models import (
    OptionRanking, OptionRankingCandidate, OptionRankingRequest, OptionRankingResult,
)
from services.option_ranking_repository import OptionRankingRepository


class OptionRankingEligibilityError(ValueError):
    pass


class OptionRankingService:
    METHODOLOGY_VERSION = "ranking-v1"
    _Q = Decimal("0.00000001")

    def __init__(self, repository: OptionRankingRepository,
                 clock: Callable[[], datetime] = datetime.now) -> None:
        self.repository = repository
        self.clock = clock

    def rank_and_persist(self, request: OptionRankingRequest) -> OptionRankingResult:
        normalized = request.normalized()
        candidates = self.repository.list_latest_candidates(normalized.as_of)
        eligible = [c for c in candidates if self._eligible(c, normalized)]
        if not eligible:
            raise OptionRankingEligibilityError("No eligible ranking candidates.")
        result = self.rank(eligible, normalized.as_of, self.clock())
        return self.repository.persist(result)

    @classmethod
    def rank(cls, candidates: list[OptionRankingCandidate], as_of: datetime,
             calculated_at: datetime) -> OptionRankingResult:
        if not candidates:
            raise OptionRankingEligibilityError("No eligible ranking candidates.")
        if calculated_at < as_of:
            raise ValueError("calculated_at cannot precede as_of.")
        run_id = uuid4()
        liquidity_raw = [cls._clamp((c.liquidity_coverage + c.price_coverage) / 2) for c in candidates]
        activity_raw = [Decimal(abs(c.total_call_oi_change) + abs(c.total_put_oi_change)) for c in candidates]
        volatility_raw = [abs(c.atm_straddle_change) + abs(c.atm_mean_iv_change or Decimal(0)) for c in candidates]
        directional_raw = [cls._directional(c) for c in candidates]
        liquidity = cls._normalize(liquidity_raw)
        activity = cls._normalize(activity_raw)
        volatility = cls._normalize(volatility_raw)
        directional = cls._normalize(directional_raw)
        rows = []
        for index, candidate in enumerate(candidates):
            total = (liquidity[index] * Decimal("0.35")
                     + activity[index] * Decimal("0.30")
                     + volatility[index] * Decimal("0.20")
                     + directional[index] * Decimal("0.15"))
            rows.append((candidate, cls._quantize(total), liquidity[index], activity[index],
                         volatility[index], directional[index]))
        rows.sort(key=lambda item: (-item[1], item[0].underlying_symbol, item[0].expiry))
        rankings = []
        for position, row in enumerate(rows, 1):
            c, total, liq, act, vol, direction = row
            rankings.append(OptionRanking(
                ranking_id=uuid4(), ranking_run_id=run_id, analytics_id=c.analytics_id,
                change_id=c.change_id, underlying_symbol=c.underlying_symbol,
                expiry=c.expiry, source_captured_at=c.source_captured_at,
                rank_position=position, total_score=total, liquidity_score=liq,
                activity_score=act, volatility_score=vol, directional_score=direction,
                explanation={
                    "methodology": cls.METHODOLOGY_VERSION,
                    "liquidity": "35%: mean of price and liquidity coverage",
                    "activity": "30%: absolute call and put OI change",
                    "volatility": "20%: absolute ATM straddle and ATM IV change",
                    "directional": "15%: PCR displacement/change and OI-wall asymmetry",
                },
            ))
        return OptionRankingResult(run_id, as_of, calculated_at,
                                   cls.METHODOLOGY_VERSION, tuple(rankings))

    @staticmethod
    def _eligible(candidate: OptionRankingCandidate, request: OptionRankingRequest) -> bool:
        age = request.as_of - candidate.source_captured_at
        return (age.total_seconds() >= 0 and age <= request.maximum_age
                and candidate.liquidity_coverage >= request.minimum_liquidity_coverage
                and candidate.price_coverage > 0)

    @classmethod
    def _directional(cls, candidate: OptionRankingCandidate) -> Decimal:
        pcr = abs((candidate.total_pcr or Decimal("1")) - Decimal("1"))
        pcr_change = abs(candidate.total_pcr_change or Decimal(0))
        wall = Decimal(0)
        if candidate.call_oi_wall_strike is not None and candidate.put_oi_wall_strike is not None and candidate.spot_price:
            call_distance = abs(candidate.call_oi_wall_strike - candidate.spot_price)
            put_distance = abs(candidate.spot_price - candidate.put_oi_wall_strike)
            wall = abs(call_distance - put_distance) / candidate.spot_price
        return pcr + pcr_change + wall

    @classmethod
    def _normalize(cls, values: list[Decimal]) -> list[Decimal]:
        low, high = min(values), max(values)
        if high == low:
            return [Decimal("0.5") for _ in values]
        return [cls._quantize((value - low) / (high - low)) for value in values]

    @classmethod
    def _clamp(cls, value: Decimal) -> Decimal:
        return max(Decimal(0), min(Decimal(1), value))

    @classmethod
    def _quantize(cls, value: Decimal) -> Decimal:
        return value.quantize(cls._Q, rounding=ROUND_HALF_UP)
