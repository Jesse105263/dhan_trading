from dataclasses import dataclass, field
from decimal import Decimal


MODELS = {"WEIGHTED_MANHATTAN", "WEIGHTED_EUCLIDEAN", "COSINE"}
RANKINGS = {"DISTANCE", "EVIDENCE_QUALITY", "TEMPORAL_DIVERSITY"}


@dataclass(frozen=True)
class SimilarityPolicyV2:
    model_version: str
    distance_model: str = "WEIGHTED_MANHATTAN"
    ranking_strategy: str = "DISTANCE"
    feature_weights: dict[str, Decimal] = field(default_factory=dict)
    family_weights: dict[str, Decimal] = field(default_factory=dict)
    selected_features: tuple[str, ...] = ()
    minimum_shared_features: int = 3
    minimum_coverage_pct: Decimal = Decimal("50")
    minimum_candidates: int = 3
    maximum_matches: int = 20
    maximum_age_days: int | None = None
    same_subject_type: bool = True
    same_interval: bool = True
    same_regime: bool = False
    minimum_liquidity_value: Decimal | None = None
    temporal_bucket_days: int = 1

    def __post_init__(self):
        if not self.model_version or self.distance_model not in MODELS or self.ranking_strategy not in RANKINGS:
            raise ValueError("Unsupported similarity policy.")
        if self.minimum_shared_features < 1 or self.minimum_candidates < 1 or not 1 <= self.maximum_matches <= 100:
            raise ValueError("Similarity counts are outside supported bounds.")
        if not 0 <= self.minimum_coverage_pct <= 100 or self.temporal_bucket_days < 1:
            raise ValueError("Similarity coverage/bucket policy is invalid.")
        if any(value <= 0 for value in (*self.feature_weights.values(), *self.family_weights.values())):
            raise ValueError("Similarity weights must be positive.")


@dataclass(frozen=True)
class SimilarityResultV2:
    run_id: object
    candidate_count: int
    match_count: int
    evidence_state: str
