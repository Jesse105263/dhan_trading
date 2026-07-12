from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class OptionSignalRequest:
    risk_run_id: UUID
    as_of: datetime
    minimum_confidence: Decimal = Decimal("0")

    def normalized(self) -> "OptionSignalRequest":
        if not Decimal("0") <= self.minimum_confidence <= Decimal("1"):
            raise ValueError("minimum_confidence must be between zero and one.")
        return self


@dataclass(frozen=True)
class ApprovedRiskCandidate:
    assessment_id: UUID
    risk_run_id: UUID
    selection_id: UUID
    ranking_id: UUID
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    approved_lots: int
    approved_quantity: int
    premium_per_lot: Decimal
    approved_exposure: Decimal
    maximum_loss: Decimal
    lot_size: int
    contract_score: Decimal
    ranking_score: Decimal
    liquidity_score: Decimal
    activity_score: Decimal
    volatility_score: Decimal
    directional_score: Decimal


@dataclass(frozen=True)
class OptionSignal:
    signal_id: UUID
    signal_run_id: UUID
    risk_run_id: UUID
    assessment_id: UUID
    selection_id: UUID
    ranking_id: UUID
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    action: str
    direction: str
    strategy_context: str
    approved_lots: int
    approved_quantity: int
    entry_price: Decimal
    premium_per_lot: Decimal
    approved_exposure: Decimal
    maximum_loss: Decimal
    confidence_score: Decimal
    rationale: dict[str, str]


@dataclass(frozen=True)
class OptionSignalResult:
    signal_run_id: UUID
    risk_run_id: UUID
    as_of: datetime
    calculated_at: datetime
    approved_input_count: int
    methodology_version: str
    signals: tuple[OptionSignal, ...]
