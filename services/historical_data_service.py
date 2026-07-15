from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID, uuid5

from services.historical_data_models import (
    ACTION_TYPES,
    ADJUSTMENT_STATES,
    INSTRUMENT_CLASSES,
    PERMISSION_VALUES,
    CanonicalHistoricalDataset,
    HistoricalDataSource,
    HistoricalImportResult,
    RawPayloadEnvelope,
    RetentionPolicy,
)
from services.historical_data_provider import HistoricalDataAdapter


class HistoricalDataRepositoryProtocol(Protocol):
    def persist_import(self, prepared: dict[str, Any]) -> HistoricalImportResult:
        ...


class HistoricalDataService:
    SCHEMA_VERSION = "historical-data-foundation-v1"
    NAMESPACE = UUID("9064694e-35e9-4fb7-9ae3-2fc4110b17b4")

    def __init__(
        self,
        repository: HistoricalDataRepositoryProtocol,
        clock=datetime.now,
    ) -> None:
        self.repository = repository
        self.clock = clock

    def import_payload(
        self,
        source: HistoricalDataSource,
        policy: RetentionPolicy,
        envelope: RawPayloadEnvelope,
        adapter: HistoricalDataAdapter,
    ) -> HistoricalImportResult:
        normalized_source = self._source(source)
        normalized_policy = self._policy(policy)
        normalized_envelope = self._envelope(envelope)
        if not normalized_policy.permits_foundation_import():
            raise PermissionError(
                "Historical import requires ALLOWED raw and normalized retention."
            )

        dataset = adapter.normalize(normalized_envelope)
        self._validate_dataset(dataset)
        payload_checksum = hashlib.sha256(normalized_envelope.payload).hexdigest()
        source_key = "|".join(
            (
                normalized_source.provider_code,
                normalized_source.product_code,
                normalized_source.dataset_code,
            )
        )
        source_id = uuid5(self.NAMESPACE, f"source:{source_key}")
        policy_manifest = self._canonical(asdict(normalized_policy))
        policy_id = uuid5(
            self.NAMESPACE,
            f"policy:{source_id}:{hashlib.sha256(policy_manifest).hexdigest()}",
        )
        payload_id = uuid5(
            self.NAMESPACE,
            f"payload:{source_id}:{payload_checksum}",
        )
        manifest_data = {
            "schema_version": self.SCHEMA_VERSION,
            "source_id": str(source_id),
            "policy_id": str(policy_id),
            "payload_id": str(payload_id),
            "payload_checksum": payload_checksum,
            "external_batch_id": normalized_envelope.external_batch_id,
            "provider_schema_version": normalized_envelope.provider_schema_version,
            "adapter_version": adapter.adapter_version,
            "request_metadata": normalized_envelope.request_metadata or {},
            "page_number": normalized_envelope.page_number,
            "retry_number": normalized_envelope.retry_number,
            "coverage_start": normalized_envelope.coverage_start,
            "coverage_end": normalized_envelope.coverage_end,
            "record_count": dataset.record_count,
            "captured_at": normalized_envelope.captured_at,
            "parent_manifest_id": normalized_envelope.parent_manifest_id,
        }
        canonical_checksum = hashlib.sha256(
            self._canonical(asdict(dataset))
        ).hexdigest()
        manifest_data["canonical_checksum"] = canonical_checksum
        manifest_checksum = hashlib.sha256(
            self._canonical(manifest_data)
        ).hexdigest()
        manifest_id = uuid5(
            self.NAMESPACE,
            f"manifest:{source_id}:{normalized_envelope.external_batch_id}:"
            f"{payload_checksum}:{manifest_checksum}",
        )
        ingested_at = self.clock()
        prepared = {
            "source_id": source_id,
            "source": normalized_source,
            "policy_id": policy_id,
            "policy": normalized_policy,
            "payload_id": payload_id,
            "payload_checksum": payload_checksum,
            "manifest_id": manifest_id,
            "manifest_checksum": manifest_checksum,
            "canonical_checksum": canonical_checksum,
            "adapter_version": adapter.adapter_version,
            "envelope": normalized_envelope,
            "dataset": dataset,
            "ingested_at": ingested_at,
            "records": self._prepare_records(dataset, manifest_id),
        }
        return self.repository.persist_import(prepared)

    def _prepare_records(
        self,
        dataset: CanonicalHistoricalDataset,
        manifest_id: UUID,
    ) -> dict[str, list[dict[str, Any]]]:
        instruments = []
        for item in sorted(
            dataset.instruments,
            key=lambda value: (value.underlying_instrument_id is not None, value.identity_key),
        ):
            content = asdict(item)
            checksum = hashlib.sha256(self._canonical(content)).hexdigest()
            instruments.append(
                {
                    "value": item,
                    "checksum": checksum,
                    "revision_id": uuid5(
                        self.NAMESPACE,
                        f"instrument-revision:{manifest_id}:{item.instrument_id}:{checksum}",
                    ),
                }
            )
        mappings = []
        for item in dataset.mappings:
            content = asdict(item)
            checksum = hashlib.sha256(self._canonical(content)).hexdigest()
            mappings.append(
                {
                    "value": item,
                    "checksum": checksum,
                    "mapping_id": uuid5(
                        self.NAMESPACE,
                        f"mapping:{manifest_id}:{checksum}",
                    ),
                }
            )
        bars = []
        for item in dataset.bars:
            content = asdict(item)
            checksum = hashlib.sha256(self._canonical(content)).hexdigest()
            natural_key = (
                f"{item.instrument_id}|{item.interval_code}|"
                f"{item.bar_open_at.isoformat()}|{item.adjustment_state}"
            )
            bars.append(
                {
                    "value": item,
                    "checksum": checksum,
                    "natural_key": natural_key,
                    "revision_id": uuid5(
                        self.NAMESPACE,
                        f"bar-revision:{manifest_id}:{natural_key}:{checksum}",
                    ),
                }
            )
        actions = []
        for item in dataset.corporate_actions:
            content = asdict(item)
            checksum = hashlib.sha256(self._canonical(content)).hexdigest()
            actions.append(
                {
                    "value": item,
                    "checksum": checksum,
                    "revision_id": uuid5(
                        self.NAMESPACE,
                        f"action-revision:{manifest_id}:{item.action_identity}:{checksum}",
                    ),
                }
            )
        return {
            "instruments": instruments,
            "mappings": mappings,
            "bars": bars,
            "actions": actions,
        }

    @staticmethod
    def _source(source: HistoricalDataSource) -> HistoricalDataSource:
        provider = source.provider_code.strip().upper()
        product = source.product_code.strip().upper()
        dataset = source.dataset_code.strip().upper()
        kind = source.source_kind.strip().upper()
        if any(not value or len(value) > 100 for value in (provider, product, dataset)):
            raise ValueError("Source codes must contain 1 to 100 characters.")
        if kind not in {"PROVIDER", "EXCHANGE", "REGULATOR", "LOCAL_FIXTURE"}:
            raise ValueError("Unsupported historical source kind.")
        reference = source.source_reference.strip() if source.source_reference else None
        return HistoricalDataSource(provider, product, dataset, kind, reference)

    @staticmethod
    def _policy(policy: RetentionPolicy) -> RetentionPolicy:
        values = (
            policy.raw_retention,
            policy.normalized_retention,
            policy.derived_data,
            policy.model_training,
            policy.backup_copy,
            policy.post_termination,
            policy.redistribution,
        )
        normalized = tuple(value.strip().upper() for value in values)
        if any(value not in PERMISSION_VALUES for value in normalized):
            raise ValueError("Retention permissions must be ALLOWED, DENIED, or UNKNOWN.")
        if not policy.agreement_id.strip() or not policy.agreement_version.strip():
            raise ValueError("Agreement identity and version are required.")
        if policy.effective_to is not None and policy.effective_to <= policy.effective_from:
            raise ValueError("Policy effective_to must be after effective_from.")
        return RetentionPolicy(
            agreement_id=policy.agreement_id.strip(),
            agreement_version=policy.agreement_version.strip(),
            use_class=policy.use_class.strip().upper(),
            raw_retention=normalized[0],
            normalized_retention=normalized[1],
            derived_data=normalized[2],
            model_training=normalized[3],
            backup_copy=normalized[4],
            post_termination=normalized[5],
            redistribution=normalized[6],
            effective_from=policy.effective_from,
            effective_to=policy.effective_to,
            retention_until=policy.retention_until,
            deletion_obligation=(
                policy.deletion_obligation.strip()
                if policy.deletion_obligation
                else None
            ),
        )

    @staticmethod
    def _envelope(envelope: RawPayloadEnvelope) -> RawPayloadEnvelope:
        if not envelope.external_batch_id.strip():
            raise ValueError("external_batch_id is required.")
        if not envelope.provider_schema_version.strip():
            raise ValueError("provider_schema_version is required.")
        if not envelope.content_type.strip():
            raise ValueError("content_type is required.")
        if not isinstance(envelope.payload, bytes) or not envelope.payload:
            raise ValueError("payload must contain exact non-empty bytes.")
        if len(envelope.payload) > 50_000_000:
            raise ValueError("Local historical payload exceeds the 50 MB safety limit.")
        if envelope.page_number < 1 or envelope.retry_number < 0:
            raise ValueError("page_number must be positive and retry_number non-negative.")
        if envelope.request_metadata is not None and not isinstance(
            envelope.request_metadata, dict
        ):
            raise ValueError("request_metadata must be an object.")
        if (
            envelope.coverage_start is not None
            and envelope.coverage_end is not None
            and envelope.coverage_end < envelope.coverage_start
        ):
            raise ValueError("coverage_end cannot precede coverage_start.")
        return envelope

    def _validate_dataset(self, dataset: CanonicalHistoricalDataset) -> None:
        instrument_ids = {item.instrument_id for item in dataset.instruments}
        if len(instrument_ids) != len(dataset.instruments):
            raise ValueError("Instrument IDs must be unique within a payload.")
        identity_keys = {item.identity_key for item in dataset.instruments}
        if len(identity_keys) != len(dataset.instruments):
            raise ValueError("Instrument identity keys must be unique within a payload.")
        for item in dataset.instruments:
            self._validate_instrument(item)
            if (
                item.underlying_instrument_id is not None
                and item.underlying_instrument_id == item.instrument_id
            ):
                raise ValueError("An instrument cannot be its own underlying.")
        self._validate_mapping_overlaps(dataset)
        for bar in dataset.bars:
            if bar.adjustment_state not in ADJUSTMENT_STATES:
                raise ValueError("Unsupported bar adjustment state.")
            if bar.bar_close_at <= bar.bar_open_at:
                raise ValueError("bar_close_at must be after bar_open_at.")
            if min(bar.open_price, bar.high_price, bar.low_price, bar.close_price) < 0:
                raise ValueError("OHLC prices cannot be negative.")
            if bar.high_price < max(bar.open_price, bar.close_price, bar.low_price):
                raise ValueError("high_price is inconsistent with OHLC values.")
            if bar.low_price > min(bar.open_price, bar.close_price, bar.high_price):
                raise ValueError("low_price is inconsistent with OHLC values.")
            for value in (bar.volume, bar.open_interest, bar.trade_count, bar.bid_price, bar.ask_price):
                if value is not None and value < 0:
                    raise ValueError("Bar quantities and quotes cannot be negative.")
            if bar.bid_price is not None and bar.ask_price is not None and bar.ask_price < bar.bid_price:
                raise ValueError("ask_price cannot be below bid_price.")
        for action in dataset.corporate_actions:
            if action.action_type not in ACTION_TYPES:
                raise ValueError("Unsupported corporate action type.")
            if action.status not in {"ANNOUNCED", "CONFIRMED", "CANCELLED", "REVISED"}:
                raise ValueError("Unsupported corporate action status.")

    @staticmethod
    def _validate_instrument(item: Any) -> None:
        if item.instrument_class not in INSTRUMENT_CLASSES:
            raise ValueError("Unsupported instrument class.")
        if not all((item.identity_key.strip(), item.exchange.strip(), item.segment.strip(), item.trading_symbol.strip())):
            raise ValueError("Instrument identity, venue, and symbol are required.")
        if item.valid_to is not None and item.valid_to <= item.valid_from:
            raise ValueError("Instrument valid_to must be after valid_from.")
        if item.lot_size is not None and item.lot_size <= 0:
            raise ValueError("lot_size must be greater than zero.")
        if item.tick_size is not None and item.tick_size <= 0:
            raise ValueError("tick_size must be greater than zero.")
        if item.instrument_class == "OPTION":
            if item.expiry is None or item.strike is None or item.option_type not in {"CE", "PE"}:
                raise ValueError("Options require expiry, strike, and CE/PE type.")
            if item.underlying_instrument_id is None:
                raise ValueError("Options require a canonical underlying.")
        elif item.instrument_class == "FUTURE":
            if item.expiry is None or item.underlying_instrument_id is None:
                raise ValueError("Futures require expiry and a canonical underlying.")
            if item.strike is not None or item.option_type is not None:
                raise ValueError("Futures cannot contain option fields.")
        elif any(value is not None for value in (item.expiry, item.strike, item.option_type)):
            raise ValueError("Cash instruments cannot contain derivative terms.")

    @staticmethod
    def _validate_mapping_overlaps(dataset: CanonicalHistoricalDataset) -> None:
        mappings = sorted(
            dataset.mappings,
            key=lambda item: (
                item.provider_exchange,
                item.provider_segment,
                item.provider_security_id,
                item.valid_from,
            ),
        )
        previous: dict[tuple[str, str, str], Any] = {}
        for item in mappings:
            if item.valid_to is not None and item.valid_to <= item.valid_from:
                raise ValueError("Mapping valid_to must be after valid_from.")
            key = (
                item.provider_exchange,
                item.provider_segment,
                item.provider_security_id,
            )
            prior = previous.get(key)
            if prior is not None and (
                prior.valid_to is None or item.valid_from < prior.valid_to
            ):
                raise ValueError("Provider security-ID mappings cannot overlap.")
            previous[key] = item

    @staticmethod
    def _canonical(value: Any) -> bytes:
        def default(item: Any) -> str:
            if isinstance(item, (UUID, date, datetime, Decimal)):
                return str(item)
            raise TypeError(f"Unsupported canonical value: {type(item).__name__}")

        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=default,
        ).encode("utf-8")
