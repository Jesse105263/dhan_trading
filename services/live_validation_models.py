from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LiveValidationPolicy:
    policy_version: str
    minimum_metric_sample: int = 30
    minimum_shadow_sessions: int = 60
    timeout_seconds: int = 23400
    cost_bps: Decimal = Decimal("15")
    watch_drift: Decimal = Decimal("0.10")
    degraded_drift: Decimal = Decimal("0.20")
    suspended_drift: Decimal = Decimal("0.30")

    def __post_init__(self):
        if not self.policy_version or self.minimum_metric_sample < 1 or self.minimum_shadow_sessions < 1:
            raise ValueError("Invalid live-validation policy.")
        if not (Decimal(0) <= self.watch_drift <= self.degraded_drift <= self.suspended_drift):
            raise ValueError("Drift thresholds must be ordered.")


@dataclass(frozen=True)
class ValidationResult:
    recommendation_id: object
    outcome_id: object | None
    state: str


@dataclass(frozen=True)
class DriftResult:
    evaluation_id: object
    state: str
    suspended: bool
