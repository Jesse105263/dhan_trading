from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class OptionRiskRequest:
    selection_run_id: UUID
    as_of: datetime
    account_equity: Decimal
    available_capital: Decimal
    existing_total_exposure: Decimal = Decimal("0")
    existing_underlying_exposure: dict[str, Decimal] = field(default_factory=dict)
    maximum_total_exposure_pct: Decimal = Decimal("0.25")
    maximum_underlying_exposure_pct: Decimal = Decimal("0.10")
    maximum_single_trade_loss_pct: Decimal = Decimal("0.02")
    maximum_lots_per_contract: int = 10

    def normalized(self) -> "OptionRiskRequest":
        if self.account_equity <= 0:
            raise ValueError("account_equity must be positive.")
        if self.available_capital < 0:
            raise ValueError("available_capital cannot be negative.")
        if self.existing_total_exposure < 0:
            raise ValueError("existing_total_exposure cannot be negative.")
        if self.maximum_lots_per_contract <= 0:
            raise ValueError("maximum_lots_per_contract must be positive.")
        for name, value in (
            ("maximum_total_exposure_pct", self.maximum_total_exposure_pct),
            ("maximum_underlying_exposure_pct", self.maximum_underlying_exposure_pct),
            ("maximum_single_trade_loss_pct", self.maximum_single_trade_loss_pct),
        ):
            if value <= 0 or value > 1:
                raise ValueError(f"{name} must be greater than zero and at most one.")
        normalized_exposure: dict[str, Decimal] = {}
        for symbol, exposure in self.existing_underlying_exposure.items():
            normalized_symbol = symbol.strip().upper()
            if not normalized_symbol:
                raise ValueError("existing_underlying_exposure contains an empty symbol.")
            if exposure < 0:
                raise ValueError("existing_underlying_exposure cannot contain negative values.")
            normalized_exposure[normalized_symbol] = exposure
        return OptionRiskRequest(
            selection_run_id=self.selection_run_id,
            as_of=self.as_of,
            account_equity=self.account_equity,
            available_capital=self.available_capital,
            existing_total_exposure=self.existing_total_exposure,
            existing_underlying_exposure=normalized_exposure,
            maximum_total_exposure_pct=self.maximum_total_exposure_pct,
            maximum_underlying_exposure_pct=self.maximum_underlying_exposure_pct,
            maximum_single_trade_loss_pct=self.maximum_single_trade_loss_pct,
            maximum_lots_per_contract=self.maximum_lots_per_contract,
        )


@dataclass(frozen=True)
class SelectedOptionContract:
    selection_id: UUID
    selection_run_id: UUID
    ranking_id: UUID
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    premium_per_lot: Decimal
    lot_size: int
    contract_score: Decimal


@dataclass(frozen=True)
class OptionRiskAssessment:
    assessment_id: UUID
    risk_run_id: UUID
    selection_id: UUID
    selection_run_id: UUID
    ranking_id: UUID
    analytics_id: UUID
    source_run_id: UUID
    underlying_symbol: str
    expiry: date
    option_type: str
    security_id: str
    trading_symbol: str
    premium_per_lot: Decimal
    approved: bool
    approved_lots: int
    approved_quantity: int
    approved_exposure: Decimal
    maximum_loss: Decimal
    rejection_code: str | None
    explanation: dict[str, str]


@dataclass(frozen=True)
class OptionRiskResult:
    risk_run_id: UUID
    selection_run_id: UUID
    as_of: datetime
    calculated_at: datetime
    account_equity: Decimal
    available_capital: Decimal
    existing_total_exposure: Decimal
    methodology_version: str
    assessments: tuple[OptionRiskAssessment, ...]

    @property
    def approved(self) -> tuple[OptionRiskAssessment, ...]:
        return tuple(item for item in self.assessments if item.approved)

    @property
    def rejected(self) -> tuple[OptionRiskAssessment, ...]:
        return tuple(item for item in self.assessments if not item.approved)

    @property
    def approved_exposure(self) -> Decimal:
        return sum((item.approved_exposure for item in self.approved), Decimal("0"))
