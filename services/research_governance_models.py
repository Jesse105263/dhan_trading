from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class GovernancePolicy:
    policy_version: str
    minimum_test_sample: int = 30
    minimum_shadow_sessions: int = 60
    alpha: Decimal = Decimal("0.05")
    bootstrap_samples: int = 500
    seed: int = 39
    required_approval_roles: tuple[str,...] = ("RESEARCH_OWNER","RISK_OWNER","DATA_OWNER")

    def __post_init__(self):
        if not self.policy_version or self.minimum_test_sample<2 or self.minimum_shadow_sessions<1 or not 0<self.alpha<1 or self.bootstrap_samples<10:
            raise ValueError("Invalid governance policy.")
        if len(set(self.required_approval_roles))!=len(self.required_approval_roles):raise ValueError("Approval roles must be unique.")


@dataclass(frozen=True)
class ExperimentResult:
    experiment_id: object
    run_id: object
    report_id: object
    state: str


@dataclass(frozen=True)
class PromotionResult:
    proposal_id: object
    decision_id: object | None
    state: str
