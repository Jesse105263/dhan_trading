from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


MISSING_POLICIES={"PRESERVE_NULL","REQUIRED","NOT_APPLICABLE"}
NORMALIZATION_POLICIES={"NONE","ZSCORE_TRAIN_WINDOW","MINMAX_TRAIN_WINDOW","LOG1P"}


@dataclass(frozen=True)
class FeatureDefinitionV2:
    name: str
    family: str
    formula: str
    missing_policy: str
    normalization_policy: str
    minimum_history: int
    description: str

    def __post_init__(self):
        if not self.name or not self.family or not self.formula:
            raise ValueError("Feature definitions require name, family and formula.")
        if self.missing_policy not in MISSING_POLICIES or self.normalization_policy not in NORMALIZATION_POLICIES:
            raise ValueError("Unsupported feature missing/normalization policy.")
        if self.minimum_history<1: raise ValueError("minimum_history must be positive.")


@dataclass(frozen=True)
class FeatureSchemaV2:
    schema_version: str
    definitions: tuple[FeatureDefinitionV2,...]
    compatible_schema_versions: tuple[str,...]=()
    compatible_outcome_models: tuple[str,...]=("canonical-path-outcome-v2",)

    def __post_init__(self):
        if not self.schema_version or not self.definitions: raise ValueError("Feature schema requires a version and definitions.")
        if len({item.name for item in self.definitions})!=len(self.definitions): raise ValueError("Feature names must be unique.")


@dataclass(frozen=True)
class FeatureAnchorV2:
    bar_revision_id: UUID
    manifest_id: UUID
    instrument_id: UUID
    instrument_class: str
    underlying_instrument_id: UUID|None
    interval_code: str
    session_date: object
    bar_open_at: datetime
    bar_close_at: datetime
    available_at: datetime
    expiry: object|None
    open_price: object
    high_price: object
    low_price: object
    close_price: object
    volume: object|None
    open_interest: object|None
    bid_price: object|None
    ask_price: object|None


@dataclass(frozen=True)
class FeatureValueV2:
    name: str
    value: object|None
    missing_reason: str|None
    source_revision_ids: tuple[UUID,...]


@dataclass(frozen=True)
class FeatureMaterializationResultV2:
    run_id: UUID
    anchor_count: int
    vector_count: int
    complete_count: int
    partial_count: int
    insufficient_count: int
