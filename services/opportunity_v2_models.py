from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OpportunityPolicyV2:
    policy_version: str
    strategy_code: str
    direction: str
    holding_horizon: str
    training_period_end: object
    minimum_sample: int = 5
    minimum_effective_sample: Decimal = Decimal("3")
    minimum_evidence_quality: Decimal = Decimal("0.5")
    maximum_symbol_concentration: Decimal = Decimal("0.5")
    maximum_expiry_concentration: Decimal = Decimal("0.5")
    maximum_regime_concentration: Decimal = Decimal("0.75")
    maximum_episode_concentration: Decimal = Decimal("0.5")
    maximum_spread_pct: Decimal = Decimal("2")
    minimum_volume: Decimal = Decimal("1")
    minimum_open_interest: Decimal = Decimal("1")
    minimum_days_to_expiry: int = 1
    maximum_days_to_expiry: int = 60
    minimum_moneyness_pct: Decimal = Decimal("-20")
    maximum_moneyness_pct: Decimal = Decimal("20")
    entry_slippage_bps: Decimal = Decimal("10")
    fee_bps: Decimal = Decimal("5")
    rejected_fill_return_pct: Decimal = Decimal("-0.15")
    stop_quantile: Decimal = Decimal("0.20")
    target_quantiles: tuple[Decimal,...] = (Decimal("0.50"),Decimal("0.75"))
    out_of_distribution_distance: Decimal = Decimal("0.75")

    def __post_init__(self):
        if not self.policy_version or not self.strategy_code or self.direction not in {"LONG_CALL","LONG_PUT"} or not self.holding_horizon:
            raise ValueError("Opportunity policy identity is invalid.")
        if self.minimum_sample<1 or self.minimum_effective_sample<=0 or not self.target_quantiles:
            raise ValueError("Opportunity evidence policy is invalid.")
        ratios=(self.minimum_evidence_quality,self.maximum_symbol_concentration,self.maximum_expiry_concentration,
            self.maximum_regime_concentration,self.maximum_episode_concentration,self.stop_quantile,*self.target_quantiles)
        if any(value<0 or value>1 for value in ratios): raise ValueError("Opportunity ratios must be between zero and one.")
        if self.entry_slippage_bps<0 or self.fee_bps<0 or self.minimum_days_to_expiry>self.maximum_days_to_expiry:
            raise ValueError("Opportunity execution policy is invalid.")


@dataclass(frozen=True)
class OpportunityResultV2:
    run_id: object
    candidate_id: object
    state: str
