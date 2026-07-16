from __future__ import annotations

import json
from datetime import datetime, timedelta
from psycopg.types.json import Jsonb
from services.database import get_connection


class V3ScaleRepository:
    def schedule(self, row: dict) -> bool:
        with get_connection() as c:
            with c.cursor() as q:
                q.execute("""INSERT INTO v3_backfill_jobs(job_id,dataset_type,provider_code,scope,partition_start,partition_end,resolution,priority,dependency_job_id,status,checkpoint,attempt_count,max_attempts,created_at,updated_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(job_id) DO NOTHING RETURNING job_id""",
                (row['job_id'],row['dataset_type'],row['provider_code'],Jsonb(row['scope']),row['partition_start'],row['partition_end'],row['resolution'],row['priority'],row['dependency_job_id'],row['status'],row['checkpoint'],row['attempt_count'],row['max_attempts'],row['created_at'],row['updated_at']))
                inserted=q.fetchone() is not None
            c.commit()
        return inserted

    def claim(self, worker: str, limit: int, now: datetime, lease_seconds: int) -> list[dict]:
        with get_connection() as c:
            with c.cursor() as q:
                q.execute("""WITH claimable AS (SELECT j.job_id FROM v3_backfill_jobs j
                  WHERE j.status IN ('PENDING','RETRYING') AND (j.next_retry_at IS NULL OR j.next_retry_at<=%s)
                  AND (j.dependency_job_id IS NULL OR EXISTS(SELECT 1 FROM v3_backfill_jobs d WHERE d.job_id=j.dependency_job_id AND d.status='COMPLETED'))
                  ORDER BY j.priority,j.created_at,j.job_id FOR UPDATE SKIP LOCKED LIMIT %s)
                UPDATE v3_backfill_jobs j SET status='RUNNING',worker_id=%s,claimed_at=%s,lease_expires_at=%s,updated_at=%s
                FROM claimable c WHERE j.job_id=c.job_id RETURNING j.*""",
                (now,limit,worker,now,now+timedelta(seconds=lease_seconds),now))
                names=[x.name for x in q.description]; rows=[dict(zip(names,r,strict=True)) for r in q.fetchall()]
            c.commit()
        return rows

    def checkpoint(self, job_id, attempt_id, attempt_number, previous, current, processed, batch_checksum, state, now):
        with get_connection() as c:
            try:
                with c.cursor() as q:
                    q.execute("""INSERT INTO v3_backfill_attempts(attempt_id,job_id,attempt_number,state,previous_checkpoint,result_checkpoint,processed_count,batch_checksum,started_at,completed_at)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(attempt_id) DO NOTHING""",(attempt_id,job_id,attempt_number,state,previous,current,processed,batch_checksum,now,now))
                    q.execute("""INSERT INTO v3_incremental_checkpoints(checkpoint_id,job_id,stage,previous_checkpoint,current_checkpoint,processed_count,batch_checksum,state,created_at)
                    SELECT %s,job_id,dataset_type,%s,%s,%s,%s,%s,%s FROM v3_backfill_jobs WHERE job_id=%s ON CONFLICT(checkpoint_id) DO NOTHING""",(attempt_id,previous,current,processed,batch_checksum,state,now,job_id))
                    q.execute("UPDATE v3_backfill_jobs SET checkpoint=%s,status=%s,attempt_count=%s,worker_id=NULL,claimed_at=NULL,lease_expires_at=NULL,updated_at=%s WHERE job_id=%s",(current,state,attempt_number,now,job_id))
                c.commit()
            except Exception: c.rollback(); raise

    def pause(self, job_id, now): return self._transition(job_id,"PAUSED",now,("PENDING","RETRYING"))
    def resume(self, job_id, now): return self._transition(job_id,"PENDING",now,("PAUSED",))
    def _transition(self, job_id, state, now, allowed):
        with get_connection() as c:
            with c.cursor() as q:q.execute("UPDATE v3_backfill_jobs SET status=%s,updated_at=%s WHERE job_id=%s AND status=ANY(%s) RETURNING job_id",(state,now,job_id,list(allowed))); changed=q.fetchone() is not None
            c.commit()
        return changed

    def recover_stale(self, now):
        with get_connection() as c:
            with c.cursor() as q:q.execute("UPDATE v3_backfill_jobs SET status='RETRYING',worker_id=NULL,claimed_at=NULL,lease_expires_at=NULL,next_retry_at=%s,updated_at=%s WHERE status='RUNNING' AND lease_expires_at<%s RETURNING job_id",(now,now,now)); rows=[r[0] for r in q.fetchall()]
            c.commit()
        return rows

    def persist_retention(self, rows):
        with get_connection() as c:
            with c.cursor() as q:
                q.executemany("""INSERT INTO v3_retention_policies(policy_id,record_class,policy_version,minimum_days,archive_eligible,destructive_action_enabled,owner_approval_required,created_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(policy_id) DO NOTHING""",[(r['policy_id'],r['record_class'],r['policy_version'],r['minimum_days'],r['archive_eligible'],r['destructive_action_enabled'],r['owner_approval_required'],r['created_at']) for r in rows])
            c.commit()

    def health(self, now):
        with get_connection() as c:
            with c.cursor() as q:
                q.execute("""SELECT COUNT(*) FILTER(WHERE status IN ('PENDING','RETRYING')),COUNT(*) FILTER(WHERE status='FAILED'),COUNT(*) FILTER(WHERE status='RUNNING' AND lease_expires_at<%s),MAX(updated_at) FILTER(WHERE status='COMPLETED') FROM v3_backfill_jobs""",(now,)); backlog,failed,stale,latest=q.fetchone()
                q.execute("SELECT pg_database_size(current_database())"); size=q.fetchone()[0]
                q.execute("SELECT COUNT(*) FROM continuous_coverage_gaps WHERE status IN ('OPEN','REPAIR_SCHEDULED')"); gaps=q.fetchone()[0]
                q.execute("SELECT COUNT(*) FROM historical_quality_incidents"); quarantines=q.fetchone()[0]
        return {"incremental_backlog":backlog,"failed_partitions":failed,"stale_checkpoints":stale,"retry_backlog":backlog,
                "collection_gaps":gaps,"unresolved_quarantines":quarantines,"database_size_bytes":size,
                "latest_successful_materialization":latest,"backup_age_seconds":None}

    def benchmark_plan(self):
        with get_connection() as c:
            with c.cursor() as q:
                q.execute("EXPLAIN (FORMAT JSON) SELECT vector_id FROM feature_vectors_v2 WHERE instrument_id=%s ORDER BY observed_at DESC LIMIT 100",('00000000-0000-0000-0000-000000000000',)); return q.fetchone()[0]
