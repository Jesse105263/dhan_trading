import json
import unittest
from datetime import date, datetime, timedelta
from uuid import UUID

from services.continuous_collection_models import CoverageExpectation, CoverageSnapshot, ProviderBatch, RetryPolicy
from services.continuous_collection_policy import ContinuousCollectionPolicy
from services.continuous_collection_provider import LocalFixtureCollectionProvider, ProviderQuotaExhaustedError
from services.continuous_collection_service import ContinuousCollectionService
from tests.test_historical_data_foundation import MemoryRepository, policy, source
from services.historical_data_service import HistoricalDataService


NOW=datetime(2026,7,15,10,0)


class QueueMemory:
    def __init__(self): self.items={}; self.attempts=[]; self.gaps={}; self.quota={}; self.observed=set()
    def schedule(self,work):
        if work.work_id in self.items:return False
        self.items[work.work_id]=work; return True
    def claim_pending(self,owner,now,limit):
        result=[]
        for key,work in list(self.items.items()):
            if len(result)>=limit:break
            if work.status in {"PENDING","RETRYING"} and (work.next_retry_at is None or work.next_retry_at<=now):
                updated=work.__class__(**{**work.__dict__,"status":"RUNNING","attempt_count":work.attempt_count+1})
                self.items[key]=updated; result.append(updated)
        return result
    def finish_attempt(self,work,**kwargs):
        status=kwargs["status"]; delay=work.retry_policy.delay(work.attempt_count) if status=="RETRYING" else None
        self.items[work.work_id]=work.__class__(**{**work.__dict__,"status":status,"next_retry_at":NOW+timedelta(seconds=delay) if delay else None})
        self.attempts.append((work,kwargs))
    def set_quota(self,provider,remaining,exhausted,resets_at,now,throttled_until=None): self.quota[provider]=(remaining,exhausted)
    def observed_bar_times(self,*args): return set(self.observed)
    def insert_gap(self,gap):
        if gap["gap_id"] in self.gaps:return False
        self.gaps[gap["gap_id"]]=gap; return True
    def open_gaps(self,limit=100): return []
    def health(self,now): return {"scheduled_jobs":len(self.items)}


def batch(failed=(),quota=None):
    payload=json.dumps({"instruments":[],"mappings":[],"bars":[],"corporate_actions":[]}).encode()
    return ProviderBatch(payload,"application/json","fixture-v1",NOW,NOW,("A",),failed,quota)


class ContinuousCollectionTest(unittest.TestCase):
    def setUp(self):
        self.queue=QueueMemory(); self.foundation=MemoryRepository()
        self.provider=LocalFixtureCollectionProvider({"*":batch()})
        self.service=ContinuousCollectionService(self.queue,HistoricalDataService(self.foundation,clock=lambda:NOW),{"LOCAL_FIXTURE":self.provider},clock=lambda:NOW)

    def work(self,retry=RetryPolicy()):
        return self.service.make_work(provider_code="LOCAL_FIXTURE",dataset_type="UNDERLYING_BARS",scope=("B","A","A"),
            requested_start=NOW,requested_end=NOW,resolution="1m",session="REGULAR",retry_policy=retry)

    def test_work_id_and_scheduling_are_deterministic_and_idempotent(self):
        first=self.work(); second=self.work()
        self.assertEqual(first.work_id,second.work_id); self.assertEqual(first.scope,("A","B"))
        self.assertTrue(self.service.schedule(first)); self.assertFalse(self.service.schedule(second))

    def test_success_and_exact_payload_replay_are_preserved(self):
        work=self.work(); self.service.schedule(work)
        result=self.service.execute_pending(owner="one",limit=1,source=source(),policy=policy())
        self.assertEqual(result.completed,1); self.assertEqual(len(self.foundation.payloads),1)
        self.queue.items[work.work_id]=work
        replay=self.service.execute_pending(owner="restart",limit=1,source=source(),policy=policy())
        self.assertEqual(replay.completed,1); self.assertEqual(len(self.foundation.payloads),1)
        self.assertTrue(self.queue.attempts[-1][1]["provider_metadata"]["raw_duplicate"])

    def test_partial_symbol_success_is_terminal_and_preserves_manifest(self):
        self.service.providers["LOCAL_FIXTURE"]=LocalFixtureCollectionProvider({"*":batch(("B",))})
        self.service.schedule(self.work()); result=self.service.execute_pending(owner="x",limit=1,source=source(),policy=policy())
        self.assertEqual(result.partial,1); self.assertEqual(self.queue.attempts[0][1]["failed_scope"],("B",))

    def test_failure_retries_then_becomes_terminal(self):
        self.service.providers["LOCAL_FIXTURE"]=LocalFixtureCollectionProvider({"*":RuntimeError("fixture failure")})
        work=self.work(RetryPolicy(max_attempts=2,initial_delay_seconds=0)); self.service.schedule(work)
        first=self.service.execute_pending(owner="x",limit=1,source=source(),policy=policy()); self.assertEqual(first.retrying,1)
        second=self.service.execute_pending(owner="x",limit=1,source=source(),policy=policy()); self.assertEqual(second.failed,1)

    def test_quota_exhaustion_is_explicit(self):
        self.service.providers["LOCAL_FIXTURE"]=LocalFixtureCollectionProvider({"*":ProviderQuotaExhaustedError("quota exhausted")})
        self.service.schedule(self.work(RetryPolicy(max_attempts=1)))
        result=self.service.execute_pending(owner="x",limit=1,source=source(),policy=policy())
        self.assertEqual(result.failed,1); self.assertEqual(self.queue.quota["LOCAL_FIXTURE"],(0,True))

    def test_unavailable_provider_is_terminal(self):
        work=self.service.make_work(provider_code="NOT_ACTIVATED",dataset_type="INDEX_BARS",scope=("X",),requested_start=NOW,requested_end=NOW,resolution="1m",session="REGULAR")
        self.service.schedule(work); result=self.service.execute_pending(owner="x",limit=1,source=source(),policy=policy())
        self.assertEqual(result.unavailable,1)

    def test_gap_detection_is_deterministic(self):
        instrument=UUID("11111111-1111-4111-8111-111111111111"); expected=(NOW,NOW+timedelta(minutes=1)); self.queue.observed={NOW}
        request=CoverageExpectation("LOCAL_FIXTURE","UNDERLYING_BARS",instrument,date(2026,7,15),"1m",expected)
        first=self.service.detect_gaps(request); second=self.service.detect_gaps(request)
        self.assertEqual(len(first),1); self.assertEqual(second,())

    def test_session_holiday_and_expiry_policy(self):
        policy_service=ContinuousCollectionPolicy(frozenset({date(2026,7,16)}))
        regular=policy_service.classify(NOW,frozenset({date(2026,7,15)})); self.assertTrue(regular.expiry_day)
        self.assertTrue(policy_service.permits_dataset(regular,"OPTION_CHAIN_SNAPSHOTS"))
        holiday=policy_service.classify(datetime(2026,7,16,10)); self.assertFalse(holiday.trading_day)
        weekend=policy_service.classify(datetime(2026,7,18,10)); self.assertEqual(weekend.reason,"weekend")

    def test_all_declared_gap_categories_are_deterministic(self):
        snapshot=CoverageSnapshot(expected_sessions=(date(2026,7,14),date(2026,7,15)),observed_sessions=(date(2026,7,14),),
            expected_intervals=("09:15","09:16"),observed_intervals=("09:15",),expected_symbols=("A","B"),observed_symbols=("A",),
            expected_expiries=(date(2026,7,30),),expected_contracts=("CE100","PE100"),observed_contracts=("CE100",),
            expected_revision="revision-2",observed_revision="revision-1")
        self.assertEqual({kind for kind,_ in self.service.compare_coverage(snapshot)},
            {"MISSING_SESSION","MISSING_INTERVAL","INCOMPLETE_SYMBOL_COVERAGE","MISSING_EXPIRY","MISSING_OPTION_CONTRACT","STALE_SOURCE_REVISION"})


if __name__ == "__main__": unittest.main()
