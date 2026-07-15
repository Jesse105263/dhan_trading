from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid5

from services.continuous_collection_models import (
    DATASET_TYPES, SESSIONS, CollectionHealth, CollectionRunSummary, CollectionWork,
    CoverageExpectation, CoverageSnapshot, RetryPolicy,
)
from services.continuous_collection_provider import (
    ContinuousCollectionProvider, ProviderQuotaExhaustedError, ProviderUnavailableError,
)
from services.historical_data_models import HistoricalDataSource, RawPayloadEnvelope, RetentionPolicy
from services.historical_data_provider import LocalJsonHistoricalDataAdapter
from services.historical_data_service import HistoricalDataService


class ContinuousCollectionService:
    NAMESPACE = UUID("744af2d7-69d8-4e1a-af09-60ee5122e143")

    def __init__(self, repository, historical_service: HistoricalDataService, providers: dict[str, ContinuousCollectionProvider], clock=datetime.now):
        self.repository=repository; self.historical_service=historical_service; self.providers=providers; self.clock=clock

    def make_work(self, *, provider_code: str, dataset_type: str, scope: tuple[str,...], requested_start: datetime|None,
                  requested_end: datetime|None, resolution: str|None, session: str, priority: int=50,
                  retry_policy: RetryPolicy=RetryPolicy(), source_lineage: dict|None=None, repair_job_id: UUID|None=None) -> CollectionWork:
        if dataset_type not in DATASET_TYPES: raise ValueError("Unsupported collection dataset type.")
        if session not in SESSIONS: raise ValueError("Unsupported collection session.")
        if not scope: raise ValueError("Collection scope cannot be empty.")
        if retry_policy.max_attempts < 1: raise ValueError("Maximum attempts must be positive.")
        key="|".join((provider_code,dataset_type,",".join(sorted(set(scope))),str(requested_start),str(requested_end),str(resolution),session,str(repair_job_id)))
        return CollectionWork(uuid5(self.NAMESPACE,"work:"+key),provider_code,dataset_type,tuple(sorted(set(scope))),requested_start,
                              requested_end,resolution,session,priority,retry_policy,source_lineage or {},self.clock(),repair_job_id=repair_job_id)

    def schedule(self, work: CollectionWork) -> bool:
        return self.repository.schedule(work)

    def execute_pending(self, *, owner: str, limit: int, source: HistoricalDataSource, policy: RetentionPolicy) -> CollectionRunSummary:
        now=self.clock(); work_items=self.repository.claim_pending(owner,now,limit)
        counts={"completed":0,"partial":0,"retrying":0,"failed":0,"unavailable":0}
        for work in work_items:
            attempt_id=uuid5(self.NAMESPACE,f"attempt:{work.work_id}:{work.attempt_count}")
            provider=self.providers.get(work.provider_code)
            if provider is None:
                self.repository.finish_attempt(work,status="UNAVAILABLE",now=self.clock(),attempt_id=attempt_id,
                    error=ProviderUnavailableError("Provider is not activated."),retryable=False)
                counts["unavailable"]+=1; continue
            try:
                batch=provider.collect(work)
                envelope=RawPayloadEnvelope(str(work.work_id),batch.provider_schema_version,batch.content_type,batch.payload,
                    batch.captured_at,batch.received_at,work.requested_start,work.requested_end,
                    request_metadata={"work_id":str(work.work_id),"dataset_type":work.dataset_type,"scope":list(work.scope)},retry_number=work.attempt_count-1)
                result=self.historical_service.import_payload(source,policy,envelope,LocalJsonHistoricalDataAdapter())
                status="PARTIAL" if batch.failed_scope else "COMPLETED"
                self.repository.finish_attempt(work,status=status,now=self.clock(),attempt_id=attempt_id,manifest_id=result.manifest_id,
                    succeeded_scope=batch.succeeded_scope,failed_scope=batch.failed_scope,
                    provider_metadata={"payload_checksum":result.payload_checksum,"raw_duplicate":result.raw_duplicate})
                if batch.quota_remaining is not None: self.repository.set_quota(work.provider_code,batch.quota_remaining,batch.quota_remaining == 0,batch.quota_resets_at,self.clock())
                counts[status.lower()]+=1
            except ProviderQuotaExhaustedError as error:
                retry=work.attempt_count < work.retry_policy.max_attempts
                status="RETRYING" if retry else "FAILED"
                self.repository.set_quota(work.provider_code,0,True,None,self.clock())
                self.repository.finish_attempt(work,status=status,now=self.clock(),attempt_id=attempt_id,error=error,retryable=retry)
                counts[status.lower()]+=1
            except ProviderUnavailableError as error:
                self.repository.finish_attempt(work,status="UNAVAILABLE",now=self.clock(),attempt_id=attempt_id,error=error,retryable=False)
                counts["unavailable"]+=1
            except Exception as error:
                retry=work.attempt_count < work.retry_policy.max_attempts
                status="RETRYING" if retry else "FAILED"
                self.repository.finish_attempt(work,status=status,now=self.clock(),attempt_id=attempt_id,error=error,retryable=retry)
                counts[status.lower()]+=1
        return CollectionRunSummary(len(work_items),**counts)

    def detect_gaps(self, expectation: CoverageExpectation) -> tuple[UUID,...]:
        observed=self.repository.observed_bar_times(expectation.instrument_id,expectation.resolution,expectation.session_date)
        found=[]
        for timestamp in expectation.expected_intervals:
            if timestamp in observed: continue
            key=timestamp.isoformat(); gap_id=uuid5(self.NAMESPACE,"gap:"+"|".join((expectation.provider_code,expectation.dataset_type,
                str(expectation.instrument_id),str(expectation.session_date),expectation.resolution,"MISSING_INTERVAL",key)))
            if self.repository.insert_gap({"gap_id":gap_id,"provider_code":expectation.provider_code,"dataset_type":expectation.dataset_type,
                    "instrument_id":expectation.instrument_id,"session_date":expectation.session_date,"resolution":expectation.resolution,
                    "gap_type":"MISSING_INTERVAL","expected_key":key,"detected_at":self.clock()}): found.append(gap_id)
        return tuple(found)

    def schedule_repairs(self, limit: int=100) -> int:
        created=0
        for gap_id,provider,dataset,instrument,session_date,resolution,gap_type,expected_key in self.repository.open_gaps(limit):
            repair_id=uuid5(self.NAMESPACE,f"repair:{gap_id}")
            point=datetime.fromisoformat(expected_key) if gap_type == "MISSING_INTERVAL" else datetime.combine(session_date,datetime.min.time())
            work=self.make_work(provider_code=provider,dataset_type=dataset,scope=(str(instrument),),requested_start=point,
                requested_end=point,resolution=resolution,session="POST_CLOSE",priority=100,source_lineage={"gap_id":str(gap_id)},repair_job_id=repair_id)
            created += int(self.repository.create_repair(repair_id,gap_id,work,self.clock()))
        return created

    def compare_coverage(self, snapshot: CoverageSnapshot) -> tuple[tuple[str,str],...]:
        """Pure deterministic comparison; callers persist returned gap keys."""
        gaps=[]
        categories=(
            ("MISSING_SESSION",snapshot.expected_sessions,snapshot.observed_sessions),
            ("MISSING_INTERVAL",snapshot.expected_intervals,snapshot.observed_intervals),
            ("INCOMPLETE_SYMBOL_COVERAGE",snapshot.expected_symbols,snapshot.observed_symbols),
            ("MISSING_EXPIRY",snapshot.expected_expiries,snapshot.observed_expiries),
            ("MISSING_OPTION_CONTRACT",snapshot.expected_contracts,snapshot.observed_contracts),
        )
        for gap_type,expected,observed in categories:
            present={str(value) for value in observed}
            gaps.extend((gap_type,str(value)) for value in sorted(expected,key=str) if str(value) not in present)
        if snapshot.expected_revision is not None and snapshot.observed_revision != snapshot.expected_revision:
            gaps.append(("STALE_SOURCE_REVISION",snapshot.expected_revision))
        return tuple(gaps)

    def health(self) -> CollectionHealth:
        now=self.clock(); return CollectionHealth(self.repository.health(now),now)

    def reconcile(self, limit: int=100) -> int:
        created=0
        for work_id,manifest_id,manifest_checksum,payload_checksum,conflict,revised in self.repository.reconciliation_candidates(limit):
            valid=manifest_checksum == payload_checksum
            result_type="CHECKSUM_FAILURE" if not valid else "CROSS_SOURCE_CONFLICT" if conflict else "SAME_SOURCE_REVISION" if revised else "EXACT_OR_NEW"
            reconciliation_id=uuid5(self.NAMESPACE,f"reconciliation:{work_id}:{manifest_id}:{result_type}")
            created += int(self.repository.insert_reconciliation(reconciliation_id,work_id,manifest_id,result_type,valid,
                {"conflict_quarantined":bool(conflict),"revision_detected":bool(revised)},self.clock()))
        return created
