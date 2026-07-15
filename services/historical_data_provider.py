from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from services.historical_data_models import (
    CanonicalHistoricalDataset,
    CanonicalInstrument,
    CorporateAction,
    HistoricalBar,
    InstrumentMapping,
    RawPayloadEnvelope,
)


class HistoricalDataAdapter(Protocol):
    adapter_version: str

    def normalize(
        self,
        envelope: RawPayloadEnvelope,
    ) -> CanonicalHistoricalDataset:
        ...


class LocalJsonHistoricalDataAdapter:
    """Strict local-fixture adapter. It performs no network or credential access."""

    adapter_version = "local-historical-json-v1"

    def normalize(
        self,
        envelope: RawPayloadEnvelope,
    ) -> CanonicalHistoricalDataset:
        try:
            value = json.loads(envelope.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Historical payload must be valid UTF-8 JSON.") from exc
        if not isinstance(value, dict):
            raise ValueError("Historical payload must contain a JSON object.")
        allowed = {"instruments", "mappings", "bars", "corporate_actions"}
        if set(value) - allowed:
            raise ValueError("Historical payload contains unsupported top-level fields.")
        return CanonicalHistoricalDataset(
            instruments=tuple(
                self._instrument(item) for item in self._records(value, "instruments")
            ),
            mappings=tuple(
                self._mapping(item) for item in self._records(value, "mappings")
            ),
            bars=tuple(self._bar(item) for item in self._records(value, "bars")),
            corporate_actions=tuple(
                self._action(item)
                for item in self._records(value, "corporate_actions")
            ),
        )

    @staticmethod
    def _records(value: dict[str, Any], key: str) -> list[dict[str, Any]]:
        records = value.get(key, [])
        if not isinstance(records, list) or len(records) > 10_000:
            raise ValueError(f"{key} must be an array with at most 10000 records.")
        if any(not isinstance(item, dict) for item in records):
            raise ValueError(f"Every {key} record must be an object.")
        return records

    def _instrument(self, item: dict[str, Any]) -> CanonicalInstrument:
        return CanonicalInstrument(
            instrument_id=self._uuid(item, "instrument_id"),
            identity_key=self._text(item, "identity_key"),
            instrument_class=self._text(item, "instrument_class"),
            exchange=self._text(item, "exchange"),
            segment=self._text(item, "segment"),
            trading_symbol=self._text(item, "trading_symbol"),
            valid_from=self._datetime(item, "valid_from"),
            available_at=self._datetime(item, "available_at"),
            underlying_instrument_id=self._optional_uuid(item.get("underlying_instrument_id")),
            isin=self._optional_text(item.get("isin")),
            expiry=self._optional_date(item.get("expiry")),
            strike=self._optional_decimal(item.get("strike")),
            option_type=self._optional_text(item.get("option_type")),
            lot_size=self._optional_int(item.get("lot_size")),
            tick_size=self._optional_decimal(item.get("tick_size")),
            valid_to=self._optional_datetime(item.get("valid_to")),
        )

    def _mapping(self, item: dict[str, Any]) -> InstrumentMapping:
        return InstrumentMapping(
            instrument_id=self._uuid(item, "instrument_id"),
            provider_security_id=self._text(item, "provider_security_id"),
            provider_symbol=self._text(item, "provider_symbol"),
            provider_exchange=self._text(item, "provider_exchange"),
            provider_segment=self._text(item, "provider_segment"),
            valid_from=self._datetime(item, "valid_from"),
            discovered_at=self._datetime(item, "discovered_at"),
            valid_to=self._optional_datetime(item.get("valid_to")),
        )

    def _bar(self, item: dict[str, Any]) -> HistoricalBar:
        return HistoricalBar(
            instrument_id=self._uuid(item, "instrument_id"),
            interval_code=self._text(item, "interval_code"),
            bar_open_at=self._datetime(item, "bar_open_at"),
            bar_close_at=self._datetime(item, "bar_close_at"),
            session_date=self._date(item, "session_date"),
            adjustment_state=self._text(item, "adjustment_state"),
            open_price=self._decimal(item, "open_price"),
            high_price=self._decimal(item, "high_price"),
            low_price=self._decimal(item, "low_price"),
            close_price=self._decimal(item, "close_price"),
            event_at=self._datetime(item, "event_at"),
            available_at=self._datetime(item, "available_at"),
            provider_at=self._optional_datetime(item.get("provider_at")),
            volume=self._optional_decimal(item.get("volume")),
            open_interest=self._optional_decimal(item.get("open_interest")),
            trade_count=self._optional_int(item.get("trade_count")),
            bid_price=self._optional_decimal(item.get("bid_price")),
            ask_price=self._optional_decimal(item.get("ask_price")),
        )

    def _action(self, item: dict[str, Any]) -> CorporateAction:
        original = item.get("original_terms", {})
        normalized = item.get("normalized_terms", {})
        if not isinstance(original, dict) or not isinstance(normalized, dict):
            raise ValueError("Corporate-action terms must be objects.")
        return CorporateAction(
            action_identity=self._text(item, "action_identity"),
            instrument_id=self._uuid(item, "instrument_id"),
            action_type=self._text(item, "action_type"),
            status=self._text(item, "status"),
            original_terms=original,
            normalized_terms=normalized,
            available_at=self._datetime(item, "available_at"),
            announcement_at=self._optional_datetime(item.get("announcement_at")),
            ex_date=self._optional_date(item.get("ex_date")),
            record_date=self._optional_date(item.get("record_date")),
            pay_date=self._optional_date(item.get("pay_date")),
        )

    @staticmethod
    def _text(item: dict[str, Any], key: str) -> str:
        value = str(item.get(key, "")).strip()
        if not value or len(value) > 500:
            raise ValueError(f"{key} must contain 1 to 500 characters.")
        return value

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value in (None, ""):
            return None
        text = str(value).strip()
        if not text or len(text) > 500:
            raise ValueError("Optional text must contain at most 500 characters.")
        return text

    @staticmethod
    def _uuid(item: dict[str, Any], key: str) -> UUID:
        try:
            return UUID(str(item[key]))
        except (KeyError, ValueError) as exc:
            raise ValueError(f"{key} must be a valid UUID.") from exc

    @staticmethod
    def _optional_uuid(value: Any) -> UUID | None:
        if value in (None, ""):
            return None
        try:
            return UUID(str(value))
        except ValueError as exc:
            raise ValueError("Optional instrument identifier must be a UUID.") from exc

    @staticmethod
    def _datetime(item: dict[str, Any], key: str) -> datetime:
        value = LocalJsonHistoricalDataAdapter._optional_datetime(item.get(key))
        if value is None:
            raise ValueError(f"{key} is required.")
        return value

    @staticmethod
    def _optional_datetime(value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        try:
            result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Timestamp must use ISO format.") from exc
        return result.replace(tzinfo=None)

    @staticmethod
    def _date(item: dict[str, Any], key: str) -> date:
        value = LocalJsonHistoricalDataAdapter._optional_date(item.get(key))
        if value is None:
            raise ValueError(f"{key} is required.")
        return value

    @staticmethod
    def _optional_date(value: Any) -> date | None:
        if value in (None, ""):
            return None
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError("Date must use ISO format.") from exc

    @staticmethod
    def _decimal(item: dict[str, Any], key: str) -> Decimal:
        value = LocalJsonHistoricalDataAdapter._optional_decimal(item.get(key))
        if value is None:
            raise ValueError(f"{key} is required.")
        return value

    @staticmethod
    def _optional_decimal(value: Any) -> Decimal | None:
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except Exception as exc:
            raise ValueError("Numeric value is invalid.") from exc

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value in (None, ""):
            return None
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Integer value is invalid.") from exc
        return result
