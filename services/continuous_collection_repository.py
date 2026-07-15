from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from services.continuous_collection_models import CollectionWork, RetryPolicy
from services.database import get_connection


class ContinuousCollectionRepository:
    def schedule(self, work: CollectionWork) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO continuous_collection_work_items
                    (work_id,schedule_id,repair_job_id,provider_code,dataset_type,scope,requested_start,requested_end,resolution,session,
                     priority,retry_policy,source_lineage,status,attempt_count,next_retry_at,terminal_failure_state,created_at,updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(work_id) DO NOTHING RETURNING work_id""",
                    (work.work_id,work.schedule_id,work.repair_job_id,work.provider_code,work.dataset_type,Jsonb(list(work.scope)),
                     work.requested_start,work.requested_end,work.resolution,work.session,work.priority,Jsonb(work.retry_policy.__dict__),
                     Jsonb(work.source_lineage),work.status,work.attempt_count,work.next_retry_at,work.terminal_failure_state,
                     work.created_at,work.created_at))
                inserted = cursor.fetchone() is not None
            connection.commit()
        return inserted

    def claim_pending(self, owner: str, now: datetime, limit: int, stale_after_seconds: int = 900) -> list[CollectionWork]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""UPDATE continuous_collection_work_items SET status='RETRYING',claimed_by=NULL,claimed_at=NULL,
                    next_retry_at=%s,updated_at=%s WHERE status='RUNNING' AND claimed_at < %s""",
                    (now,now,now-timedelta(seconds=stale_after_seconds)))
                cursor.execute("""SELECT work_id FROM continuous_collection_work_items
                    WHERE status IN ('PENDING','RETRYING') AND (next_retry_at IS NULL OR next_retry_at <= %s)
                    ORDER BY priority DESC,created_at,work_id FOR UPDATE SKIP LOCKED LIMIT %s""",(now,limit))
                ids=[row[0] for row in cursor.fetchall()]
                if ids:
                    cursor.execute("""UPDATE continuous_collection_work_items SET status='RUNNING',claimed_by=%s,claimed_at=%s,
                        attempt_count=attempt_count+1,updated_at=%s WHERE work_id=ANY(%s) RETURNING
                        work_id,schedule_id,repair_job_id,provider_code,dataset_type,scope,requested_start,requested_end,resolution,session,
                        priority,retry_policy,source_lineage,created_at,status,attempt_count,next_retry_at,terminal_failure_state""",
                        (owner,now,now,ids))
                    rows=cursor.fetchall()
                else: rows=[]
            connection.commit()
        return [self._work(row) for row in rows]

    @staticmethod
    def _work(row: tuple[Any,...]) -> CollectionWork:
        retry=row[11]
        return CollectionWork(row[0],row[3],row[4],tuple(row[5]),row[6],row[7],row[8],row[9],row[10],RetryPolicy(**retry),row[12],row[13],row[14],row[15],row[16],row[17],row[1],row[2])

    def finish_attempt(self, work: CollectionWork, *, status: str, now: datetime, attempt_id: UUID,
                       manifest_id: UUID | None = None, succeeded_scope: tuple[str,...]=(), failed_scope: tuple[str,...]=(),
                       error: Exception | None=None, retryable: bool=False, provider_metadata: dict[str,Any]|None=None) -> None:
        terminal = status in {"COMPLETED","PARTIAL","FAILED","UNAVAILABLE"}
        next_retry = now + timedelta(seconds=work.retry_policy.delay(work.attempt_count)) if status == "RETRYING" else None
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO continuous_collection_attempts
                    (attempt_id,work_id,attempt_number,status,started_at,completed_at,payload_manifest_id,succeeded_scope,failed_scope,
                     error_type,error_message,retryable,provider_metadata) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (attempt_id,work.work_id,work.attempt_count,status,work.created_at if work.attempt_count == 1 else now,now,manifest_id,
                     Jsonb(list(succeeded_scope)),Jsonb(list(failed_scope)),type(error).__name__ if error else None,
                     str(error)[:500] if error else None,retryable,Jsonb(provider_metadata or {})))
                cursor.execute("""UPDATE continuous_collection_work_items SET status=%s,next_retry_at=%s,terminal_failure_state=%s,
                    claimed_by=NULL,claimed_at=NULL,completed_at=%s,updated_at=%s WHERE work_id=%s""",
                    (status,next_retry,str(error)[:500] if error and terminal else None,now if terminal else None,now,work.work_id))
            connection.commit()

    def set_quota(self, provider: str, remaining: int | None, exhausted: bool, resets_at: datetime | None, now: datetime, throttled_until: datetime | None=None) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO continuous_provider_quota_state(provider_code,remaining,exhausted,resets_at,throttled_until,updated_at)
                    VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(provider_code) DO UPDATE SET remaining=EXCLUDED.remaining,
                    exhausted=EXCLUDED.exhausted,resets_at=EXCLUDED.resets_at,throttled_until=EXCLUDED.throttled_until,updated_at=EXCLUDED.updated_at""",
                    (provider,remaining,exhausted,resets_at,throttled_until,now))
            connection.commit()

    def observed_bar_times(self, instrument_id: UUID, resolution: str, session_date) -> set[datetime]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT bar_open_at FROM historical_bar_revisions WHERE instrument_id=%s AND interval_code=%s
                    AND session_date=%s AND is_current AND acceptance_state='ACCEPTED'""",(instrument_id,resolution,session_date))
                return {row[0] for row in cursor.fetchall()}

    def insert_gap(self, gap: dict[str,Any]) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO continuous_coverage_gaps(gap_id,provider_code,dataset_type,instrument_id,session_date,resolution,
                    gap_type,expected_key,observed_key,detected_at,source_revision_id,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'OPEN')
                    ON CONFLICT(provider_code,dataset_type,instrument_id,session_date,resolution,gap_type,expected_key) DO NOTHING RETURNING gap_id""",
                    (gap['gap_id'],gap['provider_code'],gap['dataset_type'],gap['instrument_id'],gap['session_date'],gap['resolution'],
                     gap['gap_type'],gap['expected_key'],gap.get('observed_key'),gap['detected_at'],gap.get('source_revision_id')))
                inserted=cursor.fetchone() is not None
            connection.commit()
        return inserted

    def open_gaps(self, limit: int=100) -> list[tuple[Any,...]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT gap_id,provider_code,dataset_type,instrument_id,session_date,resolution,gap_type,expected_key
                    FROM continuous_coverage_gaps WHERE status='OPEN' ORDER BY session_date,gap_id LIMIT %s""",(limit,))
                return cursor.fetchall()

    def create_repair(self, repair_id: UUID, gap_id: UUID, work: CollectionWork, now: datetime) -> bool:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""INSERT INTO continuous_repair_jobs(repair_job_id,gap_id,status,max_attempts,created_at)
                        VALUES(%s,%s,'PENDING',%s,%s) ON CONFLICT(gap_id) DO NOTHING RETURNING repair_job_id""",
                        (repair_id,gap_id,work.retry_policy.max_attempts,now))
                    if cursor.fetchone() is None: connection.rollback(); return False
                    cursor.execute("UPDATE continuous_coverage_gaps SET status='REPAIR_SCHEDULED' WHERE gap_id=%s",(gap_id,))
                connection.commit()
            except Exception: connection.rollback(); raise
        return self.schedule(work)

    def health(self, now: datetime) -> dict[str,int|float|None]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT status,COUNT(*) FROM continuous_collection_work_items GROUP BY status""")
                counts={str(k).lower():int(v) for k,v in cursor.fetchall()}
                cursor.execute("SELECT COUNT(*) FROM continuous_coverage_gaps WHERE status IN ('OPEN','REPAIR_SCHEDULED')")
                gaps=int(cursor.fetchone()[0]); cursor.execute("SELECT COUNT(*) FROM historical_quality_incidents WHERE reason_code='CROSS_SOURCE_CONFLICT'")
                conflicts=int(cursor.fetchone()[0]); cursor.execute("SELECT COUNT(*) FROM continuous_provider_quota_state WHERE exhausted")
                exhausted=int(cursor.fetchone()[0]); cursor.execute("SELECT COUNT(*) FROM continuous_collection_work_items WHERE status='RUNNING' AND claimed_at < %s",(now-timedelta(minutes=15),))
                stale=int(cursor.fetchone()[0])
        completed=counts.get('completed',0)+counts.get('partial',0); total=sum(counts.values())
        return {"scheduled_jobs":total,"completed_jobs":completed,"failed_jobs":counts.get('failed',0),
                "retrying_jobs":counts.get('retrying',0),"stale_jobs":stale,"provider_throttling":0,
                "quota_exhaustion":exhausted,"collection_lag_seconds":None,"missing_intervals":gaps,
                "coverage_percentage":(completed*100.0/total) if total else None,"repair_backlog":gaps,
                "unresolved_conflicts":conflicts,"abnormal_row_counts":0,"clock_drift_seconds":None,"checksum_failures":0}

    def reconciliation_candidates(self, limit: int) -> list[tuple[Any,...]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT a.work_id,a.payload_manifest_id,m.payload_checksum,raw.payload_checksum,
                    EXISTS(SELECT 1 FROM historical_quality_incidents q WHERE q.manifest_id=m.manifest_id),
                    EXISTS(SELECT 1 FROM historical_bar_revisions b WHERE b.manifest_id=m.manifest_id AND b.supersedes_revision_id IS NOT NULL)
                    FROM continuous_collection_attempts a JOIN historical_raw_manifests m ON m.manifest_id=a.payload_manifest_id
                    JOIN historical_raw_payloads raw ON raw.payload_id=m.payload_id
                    WHERE NOT EXISTS(SELECT 1 FROM continuous_reconciliation_results r
                      WHERE r.work_id=a.work_id AND r.manifest_id=a.payload_manifest_id)
                    ORDER BY a.completed_at,a.attempt_id LIMIT %s""",(limit,))
                return cursor.fetchall()

    def insert_reconciliation(self, reconciliation_id: UUID, work_id: UUID, manifest_id: UUID,
                              result_type: str, checksum_valid: bool, details: dict[str,Any], now: datetime) -> bool:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO continuous_reconciliation_results
                    (reconciliation_id,work_id,manifest_id,result_type,checksum_valid,details,reconciled_at)
                    VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(reconciliation_id)
                    DO NOTHING RETURNING reconciliation_id""",
                    (reconciliation_id,work_id,manifest_id,result_type,checksum_valid,Jsonb(details),now))
                inserted=cursor.fetchone() is not None
            connection.commit()
        return inserted
