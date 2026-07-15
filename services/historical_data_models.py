from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


PERMISSION_VALUES = {"ALLOWED", "DENIED", "UNKNOWN"}
INSTRUMENT_CLASSES = {"EQUITY", "INDEX", "FUTURE", "OPTION"}
ADJUSTMENT_STATES = {"RAW", "SPLIT_ADJUSTED", "TOTAL_RETURN_ADJUSTED"}
ACTION_TYPES = {
    "BONUS", "DIVIDEND", "MERGER", "RIGHTS", "SPINOFF", "SPLIT",
    "SYMBOL_CHANGE", "DELISTING", "OTHER",
}


@dataclass(frozen=True)
class HistoricalDataSource:
    provider_code: str
    product_code: str
    dataset_code: str
    source_kind: str
    source_reference: str | None = None


@dataclass(frozen=True)
class RetentionPolicy:
    agreement_id: str
    agreement_version: str
    use_class: str
    raw_retention: str
    normalized_retention: str
    derived_data: str
    model_training: str
    backup_copy: str
    post_termination: str
    redistribution: str
    effective_from: datetime
    effective_to: datetime | None = None
    retention_until: datetime | None = None
    deletion_obligation: str | None = None

    def permits_foundation_import(self) -> bool:
        return (
            self.raw_retention == "ALLOWED"
            and self.normalized_retention == "ALLOWED"
        )


@dataclass(frozen=True)
class RawPayloadEnvelope:
    external_batch_id: str
    provider_schema_version: str
    content_type: str
    payload: bytes
    captured_at: datetime
    received_at: datetime
    coverage_start: datetime | None = None
    coverage_end: datetime | None = None
    parent_manifest_id: UUID | None = None
    request_metadata: dict[str, Any] | None = None
    page_number: int = 1
    retry_number: int = 0


@dataclass(frozen=True)
class CanonicalInstrument:
    instrument_id: UUID
    identity_key: str
    instrument_class: str
    exchange: str
    segment: str
    trading_symbol: str
    valid_from: datetime
    available_at: datetime
    underlying_instrument_id: UUID | None = None
    isin: str | None = None
    expiry: date | None = None
    strike: Decimal | None = None
    option_type: str | None = None
    lot_size: int | None = None
    tick_size: Decimal | None = None
    valid_to: datetime | None = None


@dataclass(frozen=True)
class InstrumentMapping:
    instrument_id: UUID
    provider_security_id: str
    provider_symbol: str
    provider_exchange: str
    provider_segment: str
    valid_from: datetime
    discovered_at: datetime
    valid_to: datetime | None = None


@dataclass(frozen=True)
class HistoricalBar:
    instrument_id: UUID
    interval_code: str
    bar_open_at: datetime
    bar_close_at: datetime
    session_date: date
    adjustment_state: str
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    event_at: datetime
    available_at: datetime
    provider_at: datetime | None = None
    volume: Decimal | None = None
    open_interest: Decimal | None = None
    trade_count: int | None = None
    bid_price: Decimal | None = None
    ask_price: Decimal | None = None


@dataclass(frozen=True)
class CorporateAction:
    action_identity: str
    instrument_id: UUID
    action_type: str
    status: str
    original_terms: dict[str, Any]
    normalized_terms: dict[str, Any]
    available_at: datetime
    announcement_at: datetime | None = None
    ex_date: date | None = None
    record_date: date | None = None
    pay_date: date | None = None


@dataclass(frozen=True)
class CanonicalHistoricalDataset:
    instruments: tuple[CanonicalInstrument, ...] = ()
    mappings: tuple[InstrumentMapping, ...] = ()
    bars: tuple[HistoricalBar, ...] = ()
    corporate_actions: tuple[CorporateAction, ...] = ()

    @property
    def record_count(self) -> int:
        return sum(
            len(items)
            for items in (
                self.instruments,
                self.mappings,
                self.bars,
                self.corporate_actions,
            )
        )


@dataclass(frozen=True)
class HistoricalImportResult:
    manifest_id: UUID
    payload_id: UUID
    payload_checksum: str
    manifest_checksum: str
    canonical_checksum: str
    raw_duplicate: bool
    instruments_inserted: int
    instrument_revisions_inserted: int
    mappings_inserted: int
    bars_inserted: int
    bar_revisions_inserted: int
    actions_inserted: int
    action_revisions_inserted: int
