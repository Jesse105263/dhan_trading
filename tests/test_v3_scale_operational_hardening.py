import io,json,unittest
from contextlib import redirect_stdout
from datetime import datetime
from services.v3_scale_models import BackfillSpec,ScalePolicy
from services.v3_scale_service import V3ScaleService
from scripts import benchmark_v3_workloads,v3_backfill


class V3ScaleTest(unittest.TestCase):
    def setUp(self): self.now=datetime(2026,7,16);self.service=V3ScaleService(policy=ScalePolicy(batch_size=2,max_attempts=2),clock=lambda:self.now);self.spec=BackfillSpec("CANONICAL","LOCAL_FIXTURE",("B","A"),self.now,self.now,"1m")
    def test_dependency_affected_selection(self): self.assertEqual(self.service.affected_stages({"FEATURE"}),("FEATURE","SIMILARITY","OPPORTUNITY","CALIBRATION","VALIDATION","GOVERNANCE"))
    def test_deterministic_job_and_no_live_provider(self): self.assertEqual(self.service.job(self.spec)["job_id"],self.service.job(self.spec)["job_id"]);self.assertEqual(self.service.job(self.spec)["provider_code"],"LOCAL_FIXTURE")
    def test_bounded_restartable_batch(self):
        job=self.service.job(self.spec);rows=[{"record_id":str(i)} for i in range(5)];first=self.service.execute_fixture(job,rows);self.assertEqual((first.processed,first.checkpoint),(2,"2"));job["checkpoint"]=first.checkpoint;second=self.service.execute_fixture(job,rows);self.assertEqual((second.processed,second.checkpoint),(2,"4"))
    def test_partial_failure_checkpoint_is_retryable(self):
        result=self.service.execute_fixture(self.service.job(self.spec),[{"record_id":"1"},{"record_id":"2"}],1);self.assertFalse(result.complete);self.assertEqual(result.checkpoint,"1")
    def test_retry_is_bounded(self): self.assertEqual(self.service.retry_state(2),("FAILED",None));self.assertEqual(self.service.retry_state(1)[0],"RETRYING")
    def test_bulk_order_and_boundaries(self): self.assertEqual([[r['record_id'] for r in b] for b in self.service.bulk_batches([{"record_id":"b"},{"record_id":"a"},{"record_id":"c"}],2)],[['a','b'],['c']])
    def test_retention_is_metadata_only(self):
        rows=self.service.retention_policies(self.now);self.assertTrue(rows);self.assertTrue(all(not r['destructive_action_enabled'] and not r['archive_eligible'] for r in rows))
    def test_fixture_command_is_idempotent_and_shadow_only(self):
        with redirect_stdout(io.StringIO()) as out:self.assertEqual(v3_backfill.main(["verify-idempotency","--fixture"]),0)
        payload=json.loads(out.getvalue());self.assertTrue(payload['idempotent']);self.assertTrue(payload['shadow_only']);self.assertEqual(payload['external_calls'],0)
    def test_benchmark_labels_tiny_fixture_honestly(self):
        with redirect_stdout(io.StringIO()) as out:self.assertEqual(benchmark_v3_workloads.main(["--fixture"]),0)
        payload=json.loads(out.getvalue());self.assertEqual(payload['row_count'],2000);self.assertFalse(payload['claims']['million_record_performance'])

if __name__=='__main__':unittest.main()
