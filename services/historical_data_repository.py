from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from services.database import get_connection
from services.historical_data_models import HistoricalImportResult


class HistoricalDataRepository:
    """Transactional persistence for immutable raw data and canonical revisions."""

    def persist_import(self, prepared: dict[str, Any]) -> HistoricalImportResult:
        counters = {
            "instruments_inserted": 0,
            "instrument_revisions_inserted": 0,
            "mappings_inserted": 0,
            "bars_inserted": 0,
            "bar_revisions_inserted": 0,
            "actions_inserted": 0,
            "action_revisions_inserted": 0,
        }
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    self._source(cursor, prepared)
                    self._policy(cursor, prepared)
                    raw_duplicate = self._raw(cursor, prepared)
                    self._manifest(cursor, prepared)
                    for record in prepared["records"]["instruments"]:
                        created, revised = self._instrument(cursor, prepared, record)
                        counters["instruments_inserted"] += created
                        counters["instrument_revisions_inserted"] += revised
                    for record in prepared["records"]["mappings"]:
                        counters["mappings_inserted"] += self._mapping(
                            cursor, prepared, record
                        )
                    for record in prepared["records"]["bars"]:
                        created, revised = self._bar(cursor, prepared, record)
                        counters["bars_inserted"] += created
                        counters["bar_revisions_inserted"] += revised
                    for record in prepared["records"]["actions"]:
                        created, revised = self._action(cursor, prepared, record)
                        counters["actions_inserted"] += created
                        counters["action_revisions_inserted"] += revised
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return HistoricalImportResult(
            manifest_id=prepared["manifest_id"],
            payload_id=prepared["payload_id"],
            payload_checksum=prepared["payload_checksum"],
            manifest_checksum=prepared["manifest_checksum"],
            canonical_checksum=prepared["canonical_checksum"],
            raw_duplicate=raw_duplicate,
            **counters,
        )

    @staticmethod
    def _source(cursor: Any, prepared: dict[str, Any]) -> None:
        source = prepared["source"]
        cursor.execute(
            """INSERT INTO historical_data_sources
               (source_id,provider_code,product_code,dataset_code,source_kind,
                source_reference,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (source_id) DO NOTHING""",
            (
                prepared["source_id"], source.provider_code, source.product_code,
                source.dataset_code, source.source_kind, source.source_reference,
                prepared["ingested_at"],
            ),
        )

    @staticmethod
    def _policy(cursor: Any, prepared: dict[str, Any]) -> None:
        policy = prepared["policy"]
        cursor.execute(
            """INSERT INTO historical_retention_policies
               (policy_id,source_id,agreement_id,agreement_version,use_class,
                raw_retention,normalized_retention,derived_data,model_training,
                backup_copy,post_termination,redistribution,retention_until,
                deletion_obligation,effective_from,effective_to,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (policy_id) DO NOTHING""",
            (
                prepared["policy_id"], prepared["source_id"], policy.agreement_id,
                policy.agreement_version, policy.use_class, policy.raw_retention,
                policy.normalized_retention, policy.derived_data,
                policy.model_training, policy.backup_copy, policy.post_termination,
                policy.redistribution, policy.retention_until,
                policy.deletion_obligation, policy.effective_from,
                policy.effective_to, prepared["ingested_at"],
            ),
        )

    @staticmethod
    def _raw(cursor: Any, prepared: dict[str, Any]) -> bool:
        envelope = prepared["envelope"]
        cursor.execute(
            """INSERT INTO historical_raw_payloads
               (payload_id,source_id,policy_id,payload_checksum,payload_bytes,
                byte_count,content_type,received_at,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (source_id,payload_checksum) DO NOTHING
               RETURNING payload_id""",
            (
                prepared["payload_id"], prepared["source_id"], prepared["policy_id"],
                prepared["payload_checksum"], envelope.payload, len(envelope.payload),
                envelope.content_type, envelope.received_at, prepared["ingested_at"],
            ),
        )
        return cursor.fetchone() is None

    @staticmethod
    def _manifest(cursor: Any, prepared: dict[str, Any]) -> None:
        envelope = prepared["envelope"]
        dataset = prepared["dataset"]
        cursor.execute(
            """INSERT INTO historical_raw_manifests
               (manifest_id,payload_id,source_id,policy_id,external_batch_id,
                provider_schema_version,adapter_version,request_metadata,page_number,
                retry_number,coverage_start,coverage_end,record_count,payload_checksum,
                canonical_checksum,manifest_checksum,parent_manifest_id,captured_at,
                ingested_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (manifest_id) DO NOTHING""",
            (
                prepared["manifest_id"], prepared["payload_id"], prepared["source_id"],
                prepared["policy_id"], envelope.external_batch_id,
                envelope.provider_schema_version, prepared["adapter_version"],
                Jsonb(envelope.request_metadata or {}), envelope.page_number,
                envelope.retry_number, envelope.coverage_start, envelope.coverage_end,
                dataset.record_count, prepared["payload_checksum"],
                prepared["canonical_checksum"], prepared["manifest_checksum"],
                envelope.parent_manifest_id, envelope.captured_at,
                prepared["ingested_at"],
            ),
        )

    @staticmethod
    def _instrument(cursor: Any, prepared: dict[str, Any], record: dict[str, Any]) -> tuple[int, int]:
        item = record["value"]
        cursor.execute(
            """INSERT INTO canonical_instruments
               (instrument_id,identity_key,instrument_class,created_at)
               VALUES (%s,%s,%s,%s) ON CONFLICT (instrument_id) DO NOTHING
               RETURNING instrument_id""",
            (item.instrument_id, item.identity_key, item.instrument_class, prepared["ingested_at"]),
        )
        created = 1 if cursor.fetchone() is not None else 0
        cursor.execute(
            "SELECT identity_key,instrument_class FROM canonical_instruments WHERE instrument_id=%s",
            (item.instrument_id,),
        )
        stable = cursor.fetchone()
        if stable != (item.identity_key, item.instrument_class):
            raise ValueError("Canonical instrument identity is immutable.")
        cursor.execute(
            """SELECT 1 FROM canonical_instrument_revisions
               WHERE instrument_id=%s AND record_checksum=%s""",
            (item.instrument_id, record["checksum"]),
        )
        if cursor.fetchone() is not None:
            return created, 0
        cursor.execute(
            """SELECT revision_id,revision_number,record_checksum,m.source_id
               FROM canonical_instrument_revisions r
               JOIN historical_raw_manifests m USING (manifest_id)
               WHERE instrument_id=%s AND is_current""",
            (item.instrument_id,),
        )
        current = cursor.fetchone()
        if current is not None and current[2] == record["checksum"]:
            return created, 0
        if current is not None and current[3] != prepared["source_id"]:
            raise ValueError("Conflicting cross-source instrument revision requires review.")
        revision_number = 1 if current is None else current[1] + 1
        if current is not None:
            cursor.execute(
                "UPDATE canonical_instrument_revisions SET is_current=FALSE WHERE revision_id=%s",
                (current[0],),
            )
        cursor.execute(
            """INSERT INTO canonical_instrument_revisions
               (revision_id,instrument_id,manifest_id,revision_number,record_checksum,
                is_current,supersedes_revision_id,exchange,segment,trading_symbol,
                underlying_instrument_id,isin,expiry,strike,option_type,lot_size,
                tick_size,valid_from,valid_to,available_at,ingested_at)
               VALUES (%s,%s,%s,%s,%s,TRUE,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                record["revision_id"], item.instrument_id, prepared["manifest_id"],
                revision_number, record["checksum"], current[0] if current else None,
                item.exchange, item.segment, item.trading_symbol,
                item.underlying_instrument_id, item.isin, item.expiry, item.strike,
                item.option_type, item.lot_size, item.tick_size, item.valid_from,
                item.valid_to, item.available_at, prepared["ingested_at"],
            ),
        )
        return created, 1

    @staticmethod
    def _mapping(cursor: Any, prepared: dict[str, Any], record: dict[str, Any]) -> int:
        item = record["value"]
        cursor.execute(
            """SELECT mapping_checksum FROM source_instrument_mappings
               WHERE source_id=%s AND provider_exchange=%s AND provider_segment=%s
                 AND provider_security_id=%s
                 AND valid_from < COALESCE(%s,'infinity'::timestamp)
                 AND COALESCE(valid_to,'infinity'::timestamp) > %s""",
            (
                prepared["source_id"], item.provider_exchange, item.provider_segment,
                item.provider_security_id, item.valid_to, item.valid_from,
            ),
        )
        overlaps = cursor.fetchall()
        if overlaps:
            if len(overlaps) == 1 and overlaps[0][0] == record["checksum"]:
                return 0
            raise ValueError("Provider security-ID mapping overlaps persisted history.")
        cursor.execute(
            """INSERT INTO source_instrument_mappings
               (mapping_id,source_id,instrument_id,manifest_id,provider_security_id,
                provider_symbol,provider_exchange,provider_segment,valid_from,
                valid_to,mapping_checksum,discovered_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (source_id,mapping_checksum) DO NOTHING RETURNING mapping_id""",
            (
                record["mapping_id"], prepared["source_id"], item.instrument_id,
                prepared["manifest_id"], item.provider_security_id,
                item.provider_symbol, item.provider_exchange, item.provider_segment,
                item.valid_from, item.valid_to, record["checksum"], item.discovered_at,
            ),
        )
        return 1 if cursor.fetchone() is not None else 0

    @staticmethod
    def _bar(cursor: Any, prepared: dict[str, Any], record: dict[str, Any]) -> tuple[int, int]:
        item = record["value"]
        cursor.execute(
            """SELECT 1 FROM historical_bar_revisions
               WHERE instrument_id=%s AND interval_code=%s AND bar_open_at=%s
                 AND adjustment_state=%s AND record_checksum=%s""",
            (
                item.instrument_id, item.interval_code, item.bar_open_at,
                item.adjustment_state, record["checksum"],
            ),
        )
        if cursor.fetchone() is not None:
            return 0, 0
        cursor.execute(
            """SELECT bar_revision_id,revision_number,record_checksum,m.source_id
               FROM historical_bar_revisions b
               JOIN historical_raw_manifests m USING (manifest_id)
               WHERE instrument_id=%s AND interval_code=%s AND bar_open_at=%s
                 AND adjustment_state=%s AND is_current AND acceptance_state='ACCEPTED'""",
            (item.instrument_id, item.interval_code, item.bar_open_at, item.adjustment_state),
        )
        current = cursor.fetchone()
        if current is not None and current[2] == record["checksum"]:
            return 0, 0
        cross_source = current is not None and current[3] != prepared["source_id"]
        cursor.execute(
            """SELECT COALESCE(MAX(revision_number),0)
               FROM historical_bar_revisions
               WHERE instrument_id=%s AND interval_code=%s AND bar_open_at=%s
                 AND adjustment_state=%s""",
            (item.instrument_id, item.interval_code, item.bar_open_at, item.adjustment_state),
        )
        revision_number = cursor.fetchone()[0] + 1
        acceptance = "QUARANTINED" if cross_source else "ACCEPTED"
        if current is not None and not cross_source:
            cursor.execute(
                "UPDATE historical_bar_revisions SET is_current=FALSE WHERE bar_revision_id=%s",
                (current[0],),
            )
        cursor.execute(
            """INSERT INTO historical_bar_revisions
               (bar_revision_id,instrument_id,manifest_id,interval_code,bar_open_at,
                bar_close_at,session_date,adjustment_state,revision_number,
                record_checksum,is_current,acceptance_state,supersedes_revision_id,
                open_price,high_price,low_price,close_price,volume,open_interest,
                trade_count,bid_price,ask_price,event_at,provider_at,available_at,ingested_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                       %s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                record["revision_id"], item.instrument_id, prepared["manifest_id"],
                item.interval_code, item.bar_open_at, item.bar_close_at,
                item.session_date, item.adjustment_state, revision_number,
                record["checksum"], acceptance == "ACCEPTED", acceptance,
                current[0] if current else None, item.open_price, item.high_price,
                item.low_price, item.close_price, item.volume, item.open_interest,
                item.trade_count, item.bid_price, item.ask_price, item.event_at,
                item.provider_at, item.available_at, prepared["ingested_at"],
            ),
        )
        if cross_source:
            incident_id = record["revision_id"]
            cursor.execute(
                """INSERT INTO historical_quality_incidents
                   (incident_id,manifest_id,record_type,natural_key,reason_code,
                    conflicting_revision_id,quarantined_revision_id,detected_at)
                   VALUES (%s,%s,'HISTORICAL_BAR',%s,'CROSS_SOURCE_CONFLICT',%s,%s,%s)
                   ON CONFLICT (incident_id) DO NOTHING""",
                (
                    incident_id, prepared["manifest_id"], record["natural_key"],
                    current[0], record["revision_id"], prepared["ingested_at"],
                ),
            )
        return (1, 0) if current is None else (0, 1)

    @staticmethod
    def _action(cursor: Any, prepared: dict[str, Any], record: dict[str, Any]) -> tuple[int, int]:
        item = record["value"]
        cursor.execute(
            """SELECT 1 FROM corporate_action_revisions
               WHERE action_identity=%s AND record_checksum=%s""",
            (item.action_identity, record["checksum"]),
        )
        if cursor.fetchone() is not None:
            return 0, 0
        cursor.execute(
            """SELECT action_revision_id,revision_number,record_checksum,m.source_id
               FROM corporate_action_revisions a
               JOIN historical_raw_manifests m USING (manifest_id)
               WHERE action_identity=%s AND is_current""",
            (item.action_identity,),
        )
        current = cursor.fetchone()
        if current is not None and current[2] == record["checksum"]:
            return 0, 0
        if current is not None and current[3] != prepared["source_id"]:
            raise ValueError("Conflicting cross-source corporate action requires review.")
        revision_number = 1 if current is None else current[1] + 1
        if current is not None:
            cursor.execute(
                "UPDATE corporate_action_revisions SET is_current=FALSE WHERE action_revision_id=%s",
                (current[0],),
            )
        cursor.execute(
            """INSERT INTO corporate_action_revisions
               (action_revision_id,action_identity,instrument_id,manifest_id,
                action_type,revision_number,record_checksum,is_current,status,
                supersedes_revision_id,announcement_at,ex_date,record_date,pay_date,
                original_terms,normalized_terms,available_at,ingested_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                record["revision_id"], item.action_identity, item.instrument_id,
                prepared["manifest_id"], item.action_type, revision_number,
                record["checksum"], item.status, current[0] if current else None,
                item.announcement_at, item.ex_date, item.record_date, item.pay_date,
                Jsonb(item.original_terms), Jsonb(item.normalized_terms),
                item.available_at, prepared["ingested_at"],
            ),
        )
        return (1, 0) if current is None else (0, 1)
