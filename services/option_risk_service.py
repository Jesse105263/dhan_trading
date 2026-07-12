from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from typing import Callable
from uuid import uuid4

from services.option_risk_models import (
    OptionRiskAssessment,
    OptionRiskRequest,
    OptionRiskResult,
    SelectedOptionContract,
)


class OptionRiskEligibilityError(ValueError):
    pass


class OptionRiskService:
    METHODOLOGY_VERSION = "long-option-risk-v1"
    MONEY_QUANTUM = Decimal("0.01")

    def __init__(
        self,
        repository,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.repository = repository
        self.clock = clock

    def assess_and_persist(self, request: OptionRiskRequest) -> OptionRiskResult:
        normalized = request.normalized()
        selections = self.repository.list_selected_contracts(normalized.selection_run_id)
        if not selections:
            raise OptionRiskEligibilityError("Selection run has no contracts.")

        risk_run_id = uuid4()
        total_limit = normalized.account_equity * normalized.maximum_total_exposure_pct
        trade_loss_limit = normalized.account_equity * normalized.maximum_single_trade_loss_pct
        total_used = normalized.existing_total_exposure
        underlying_used = dict(normalized.existing_underlying_exposure)
        available_used = Decimal("0")
        assessments: list[OptionRiskAssessment] = []

        for selection in selections:
            symbol = selection.underlying_symbol.upper()
            underlying_limit = normalized.account_equity * normalized.maximum_underlying_exposure_pct
            remaining_total = max(Decimal("0"), total_limit - total_used)
            remaining_underlying = max(
                Decimal("0"),
                underlying_limit - underlying_used.get(symbol, Decimal("0")),
            )
            remaining_available = max(
                Decimal("0"),
                normalized.available_capital - available_used,
            )
            lot_budget = min(
                trade_loss_limit,
                remaining_total,
                remaining_underlying,
                remaining_available,
            )
            lots = self._maximum_lots(
                budget=lot_budget,
                premium_per_lot=selection.premium_per_lot,
                hard_limit=normalized.maximum_lots_per_contract,
            )

            if lots <= 0:
                rejection_code = self._rejection_code(
                    normalized=normalized,
                    total_limit=total_limit,
                    underlying_limit=underlying_limit,
                    trade_loss_limit=trade_loss_limit,
                    total_used=total_used,
                    underlying_used=underlying_used.get(symbol, Decimal("0")),
                    available_used=available_used,
                    premium_per_lot=selection.premium_per_lot,
                )
                assessments.append(
                    self._assessment(
                        risk_run_id=risk_run_id,
                        selection=selection,
                        approved=False,
                        lots=0,
                        exposure=Decimal("0"),
                        rejection_code=rejection_code,
                        explanation={
                            "methodology": self.METHODOLOGY_VERSION,
                            "decision": "rejected",
                            "reason": rejection_code,
                        },
                    )
                )
                continue

            exposure = self._money(selection.premium_per_lot * lots)
            total_used += exposure
            underlying_used[symbol] = underlying_used.get(symbol, Decimal("0")) + exposure
            available_used += exposure
            assessments.append(
                self._assessment(
                    risk_run_id=risk_run_id,
                    selection=selection,
                    approved=True,
                    lots=lots,
                    exposure=exposure,
                    rejection_code=None,
                    explanation={
                        "methodology": self.METHODOLOGY_VERSION,
                        "decision": "approved",
                        "sizing": "minimum of per-trade loss, total exposure, underlying concentration and available capital budgets",
                    },
                )
            )

        result = OptionRiskResult(
            risk_run_id=risk_run_id,
            selection_run_id=normalized.selection_run_id,
            as_of=normalized.as_of,
            calculated_at=self.clock(),
            account_equity=normalized.account_equity,
            available_capital=normalized.available_capital,
            existing_total_exposure=normalized.existing_total_exposure,
            methodology_version=self.METHODOLOGY_VERSION,
            assessments=tuple(assessments),
        )
        return self.repository.persist(result)

    @classmethod
    def _maximum_lots(
        cls,
        budget: Decimal,
        premium_per_lot: Decimal,
        hard_limit: int,
    ) -> int:
        if budget <= 0 or premium_per_lot <= 0:
            return 0
        affordable = int((budget / premium_per_lot).to_integral_value(rounding=ROUND_DOWN))
        return min(affordable, hard_limit)

    @classmethod
    def _assessment(
        cls,
        risk_run_id,
        selection: SelectedOptionContract,
        approved: bool,
        lots: int,
        exposure: Decimal,
        rejection_code: str | None,
        explanation: dict[str, str],
    ) -> OptionRiskAssessment:
        quantity = lots * selection.lot_size
        return OptionRiskAssessment(
            assessment_id=uuid4(),
            risk_run_id=risk_run_id,
            selection_id=selection.selection_id,
            selection_run_id=selection.selection_run_id,
            ranking_id=selection.ranking_id,
            analytics_id=selection.analytics_id,
            source_run_id=selection.source_run_id,
            underlying_symbol=selection.underlying_symbol,
            expiry=selection.expiry,
            option_type=selection.option_type,
            security_id=selection.security_id,
            trading_symbol=selection.trading_symbol,
            premium_per_lot=selection.premium_per_lot,
            approved=approved,
            approved_lots=lots,
            approved_quantity=quantity,
            approved_exposure=exposure,
            maximum_loss=exposure,
            rejection_code=rejection_code,
            explanation=explanation,
        )

    @classmethod
    def _rejection_code(
        cls,
        normalized: OptionRiskRequest,
        total_limit: Decimal,
        underlying_limit: Decimal,
        trade_loss_limit: Decimal,
        total_used: Decimal,
        underlying_used: Decimal,
        available_used: Decimal,
        premium_per_lot: Decimal,
    ) -> str:
        if premium_per_lot > trade_loss_limit:
            return "SINGLE_TRADE_LOSS_LIMIT"
        if normalized.available_capital - available_used < premium_per_lot:
            return "AVAILABLE_CAPITAL_LIMIT"
        if total_limit - total_used < premium_per_lot:
            return "TOTAL_EXPOSURE_LIMIT"
        if underlying_limit - underlying_used < premium_per_lot:
            return "UNDERLYING_CONCENTRATION_LIMIT"
        return "NO_AFFORDABLE_LOTS"

    @classmethod
    def _money(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.MONEY_QUANTUM)
