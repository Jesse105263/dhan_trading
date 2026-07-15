import hashlib
import json
import unittest
from datetime import datetime
from uuid import UUID

from services.historical_data_models import (
    HistoricalDataSource,
    HistoricalImportResult,
    RawPayloadEnvelope,
    RetentionPolicy,
)
from services.historical_data_provider import LocalJsonHistoricalDataAdapter
from services.historical_data_service import HistoricalDataService


UNDERLYING = UUID("11111111-1111-4111-8111-111111111111")
OPTION = UUID("22222222-2222-4222-8222-222222222222")
NOW = datetime(2026, 7, 15, 10, 0)


def fixture(close_price="101.5", action_status="CONFIRMED"):
    return {
        "instruments": [
            {
                "instrument_id": str(UNDERLYING),
                "identity_key": "NSE|EQUITY|INE000000001",
                "instrument_class": "EQUITY",
                "exchange": "NSE",
                "segment": "NSE_EQ",
                "trading_symbol": "TESTCO",
                "isin": "INE000000001",
                "valid_from": "2020-01-01T00:00:00",
                "available_at": "2020-01-01T00:00:00",
            },
            {
                "instrument_id": str(OPTION),
                "identity_key": "NSE|OPTION|TESTCO|2026-07-30|100|CE",
                "instrument_class": "OPTION",
                "exchange": "NSE",
                "segment": "NSE_FNO",
                "trading_symbol": "TESTCO-20260730-100-CE",
                "underlying_instrument_id": str(UNDERLYING),
                "expiry": "2026-07-30",
                "strike": "100",
                "option_type": "CE",
                "lot_size": 50,
                "tick_size": "0.05",
                "valid_from": "2026-01-01T00:00:00",
                "available_at": "2026-01-01T00:00:00",
            },
        ],
        "mappings": [
            {
                "instrument_id": str(OPTION),
                "provider_security_id": "9001",
                "provider_symbol": "TESTCO OPT",
                "provider_exchange": "NSE",
                "provider_segment": "NSE_FNO",
                "valid_from": "2026-01-01T00:00:00",
                "discovered_at": "2026-01-01T00:00:00",
            }
        ],
        "bars": [
            {
                "instrument_id": str(OPTION),
                "interval_code": "1D",
                "bar_open_at": "2026-07-14T03:45:00",
                "bar_close_at": "2026-07-14T10:00:00",
                "session_date": "2026-07-14",
                "adjustment_state": "RAW",
                "open_price": "100",
                "high_price": "103",
                "low_price": "99",
                "close_price": close_price,
                "volume": "1000",
                "open_interest": "5000",
                "event_at": "2026-07-14T10:00:00",
                "available_at": "2026-07-14T10:01:00",
            }
        ],
        "corporate_actions": [
            {
                "action_identity": "NSE:TESTCO:SPLIT:2026-07-10",
                "instrument_id": str(UNDERLYING),
                "action_type": "SPLIT",
                "status": action_status,
                "original_terms": {"ratio": "2:1"},
                "normalized_terms": {"new_shares": 2, "old_shares": 1},
                "announcement_at": "2026-07-01T10:00:00",
                "ex_date": "2026-07-10",
                "available_at": "2026-07-01T10:01:00",
            }
        ],
    }


class MemoryRepository:
    def __init__(self):
        self.prepared = []
        self.payloads = set()
        self.instruments = {}
        self.bars = {}
        self.actions = {}
        self.mappings = set()

    def persist_import(self, prepared):
        self.prepared.append(prepared)
        checksum = prepared["payload_checksum"]
        duplicate = checksum in self.payloads
        self.payloads.add(checksum)
        records = prepared["records"]
        incoming_ids = {
            record["value"].instrument_id for record in records["instruments"]
        }
        known_ids = set(self.instruments) | incoming_ids
        referenced_ids = {
            record["value"].instrument_id
            for group in ("mappings", "bars", "actions")
            for record in records[group]
        }
        referenced_ids.update(
            record["value"].underlying_instrument_id
            for record in records["instruments"]
            if record["value"].underlying_instrument_id is not None
        )
        if referenced_ids - known_ids:
            raise ValueError("Canonical record references an unknown instrument.")
        new_instruments = revised_instruments = 0
        for record in records["instruments"]:
            key = record["value"].instrument_id
            old = self.instruments.get(key)
            if old is None:
                new_instruments += 1
            elif old != record["checksum"]:
                revised_instruments += 1
            self.instruments[key] = record["checksum"]
        new_bars = revised_bars = 0
        for record in records["bars"]:
            key = record["natural_key"]
            old = self.bars.get(key)
            if old is None:
                new_bars += 1
            elif old != record["checksum"]:
                revised_bars += 1
            self.bars[key] = record["checksum"]
        new_actions = revised_actions = 0
        for record in records["actions"]:
            key = record["value"].action_identity
            old = self.actions.get(key)
            if old is None:
                new_actions += 1
            elif old != record["checksum"]:
                revised_actions += 1
            self.actions[key] = record["checksum"]
        mappings = 0
        for record in records["mappings"]:
            if record["checksum"] not in self.mappings:
                mappings += 1
                self.mappings.add(record["checksum"])
        return HistoricalImportResult(
            manifest_id=prepared["manifest_id"],
            payload_id=prepared["payload_id"],
            payload_checksum=checksum,
            manifest_checksum=prepared["manifest_checksum"],
            canonical_checksum=prepared["canonical_checksum"],
            raw_duplicate=duplicate,
            instruments_inserted=new_instruments,
            instrument_revisions_inserted=revised_instruments,
            mappings_inserted=mappings,
            bars_inserted=new_bars,
            bar_revisions_inserted=revised_bars,
            actions_inserted=new_actions,
            action_revisions_inserted=revised_actions,
        )


def source():
    return HistoricalDataSource(
        "local", "fixture", "historical-foundation", "LOCAL_FIXTURE", "unit-test"
    )


def policy(raw="ALLOWED", normalized="ALLOWED"):
    return RetentionPolicy(
        agreement_id="local-test",
        agreement_version="1",
        use_class="TEST_ONLY",
        raw_retention=raw,
        normalized_retention=normalized,
        derived_data="DENIED",
        model_training="DENIED",
        backup_copy="DENIED",
        post_termination="DENIED",
        redistribution="DENIED",
        effective_from=NOW,
    )


def envelope(data, batch="batch-1"):
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return RawPayloadEnvelope(
        external_batch_id=batch,
        provider_schema_version="fixture-v1",
        content_type="application/json",
        payload=payload,
        captured_at=NOW,
        received_at=NOW,
        coverage_start=datetime(2026, 7, 14),
        coverage_end=datetime(2026, 7, 14, 23, 59),
    )


class HistoricalDataFoundationTest(unittest.TestCase):
    def setUp(self):
        self.repository = MemoryRepository()
        self.service = HistoricalDataService(self.repository, clock=lambda: NOW)
        self.adapter = LocalJsonHistoricalDataAdapter()

    def test_exact_raw_checksum_manifest_and_ids_are_deterministic(self):
        item = envelope(fixture())
        first = self.service.import_payload(source(), policy(), item, self.adapter)
        second = self.service.import_payload(source(), policy(), item, self.adapter)
        self.assertEqual(first.payload_checksum, hashlib.sha256(item.payload).hexdigest())
        self.assertEqual(first.manifest_id, second.manifest_id)
        self.assertEqual(first.manifest_checksum, second.manifest_checksum)
        self.assertFalse(first.raw_duplicate)
        self.assertTrue(second.raw_duplicate)
        self.assertEqual(second.bars_inserted, 0)
        self.assertEqual(second.bar_revisions_inserted, 0)

    def test_normalizes_instruments_mappings_bars_and_actions(self):
        result = self.service.import_payload(
            source(), policy(), envelope(fixture()), self.adapter
        )
        self.assertEqual(result.instruments_inserted, 2)
        self.assertEqual(result.mappings_inserted, 1)
        self.assertEqual(result.bars_inserted, 1)
        self.assertEqual(result.actions_inserted, 1)
        prepared = self.repository.prepared[0]
        option = prepared["dataset"].instruments[1]
        self.assertEqual(option.underlying_instrument_id, UNDERLYING)
        self.assertEqual(str(option.strike), "100")
        self.assertIsNone(prepared["dataset"].bars[0].trade_count)

    def test_changed_canonical_content_is_a_revision_not_duplicate(self):
        first = self.service.import_payload(
            source(), policy(), envelope(fixture(), "batch-1"), self.adapter
        )
        second = self.service.import_payload(
            source(), policy(), envelope(fixture(close_price="102"), "batch-2"), self.adapter
        )
        self.assertEqual(first.bars_inserted, 1)
        self.assertEqual(second.bars_inserted, 0)
        self.assertEqual(second.bar_revisions_inserted, 1)
        self.assertNotEqual(first.payload_checksum, second.payload_checksum)

    def test_incremental_bar_page_can_reference_persisted_instrument(self):
        self.service.import_payload(
            source(), policy(), envelope(fixture(), "master-and-bars"), self.adapter
        )
        page = fixture(close_price="102")
        page["instruments"] = []
        page["mappings"] = []
        page["corporate_actions"] = []
        result = self.service.import_payload(
            source(), policy(), envelope(page, "bars-page-2"), self.adapter
        )
        self.assertEqual(result.instruments_inserted, 0)
        self.assertEqual(result.bar_revisions_inserted, 1)

    def test_unknown_or_denied_retention_fails_closed_before_adapter(self):
        class Adapter:
            adapter_version = "should-not-run"

            def normalize(self, value):
                raise AssertionError("adapter must not be invoked")

        for raw, normalized in (("UNKNOWN", "ALLOWED"), ("ALLOWED", "DENIED")):
            with self.assertRaises(PermissionError):
                self.service.import_payload(
                    source(), policy(raw, normalized), envelope(fixture()), Adapter()
                )

    def test_invalid_derivative_and_bar_values_are_rejected(self):
        invalid_option = fixture()
        invalid_option["instruments"][1]["option_type"] = "XX"
        with self.assertRaisesRegex(ValueError, "Options require"):
            self.service.import_payload(
                source(), policy(), envelope(invalid_option), self.adapter
            )
        invalid_bar = fixture()
        invalid_bar["bars"][0]["high_price"] = "105"
        invalid_bar["bars"][0]["low_price"] = "104"
        with self.assertRaisesRegex(ValueError, "low_price"):
            self.service.import_payload(
                source(), policy(), envelope(invalid_bar), self.adapter
            )

    def test_mapping_overlaps_and_unknown_instruments_are_rejected(self):
        overlapping = fixture()
        overlapping["mappings"].append(
            {
                **overlapping["mappings"][0],
                "instrument_id": str(UNDERLYING),
                "valid_from": "2026-06-01T00:00:00",
            }
        )
        with self.assertRaisesRegex(ValueError, "cannot overlap"):
            self.service.import_payload(
                source(), policy(), envelope(overlapping), self.adapter
            )
        unknown = fixture()
        unknown["bars"][0]["instrument_id"] = "33333333-3333-4333-8333-333333333333"
        with self.assertRaisesRegex(ValueError, "unknown instrument"):
            self.service.import_payload(
                source(), policy(), envelope(unknown), self.adapter
            )

    def test_adapter_is_bounded_strict_and_local_only(self):
        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.adapter.normalize(envelope({"unknown": []}))
        with self.assertRaisesRegex(ValueError, "UTF-8 JSON"):
            self.adapter.normalize(
                RawPayloadEnvelope(
                    "bad", "v1", "application/json", b"not-json", NOW, NOW
                )
            )

    def test_no_provider_client_or_credentials_are_imported(self):
        import services.historical_data_provider as provider_module
        import services.historical_data_service as service_module

        combined = provider_module.__dict__.keys() | service_module.__dict__.keys()
        self.assertNotIn("requests", combined)
        self.assertNotIn("DHAN_SETTINGS", combined)
        self.assertNotIn("DhanOptionChainClient", combined)


if __name__ == "__main__":
    unittest.main()
