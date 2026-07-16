import os,unittest
from datetime import datetime,timedelta
from uuid import uuid4
from services.database import get_connection
from services.v3_scale_models import BackfillSpec,ScalePolicy
from services.v3_scale_repository import V3ScaleRepository
from services.v3_scale_service import V3ScaleService,stable_id


@unittest.skipUnless(os.getenv('RUN_DB_INTEGRATION_TESTS')=='1','Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.')
class V3ScaleRepositoryIntegrationTest(unittest.TestCase):
    TABLES=('v3_incremental_checkpoints','v3_backfill_attempts','v3_retention_policies','v3_backfill_jobs')
    def setUp(self): self.now=datetime(2026,7,16);self.repo=V3ScaleRepository();self.service=V3ScaleService(self.repo,ScalePolicy(batch_size=2,lease_seconds=10),clock=lambda:self.now)
    def tearDown(self):
        with get_connection() as c:
            with c.cursor() as q:
                for table in self.TABLES:q.execute(f'ALTER TABLE {table} DISABLE TRIGGER ALL');q.execute(f'DELETE FROM {table}');q.execute(f'ALTER TABLE {table} ENABLE TRIGGER ALL')
            c.commit()
    def spec(self,symbol='NIFTY'):return BackfillSpec('CANONICAL','LOCAL_FIXTURE',(symbol,),self.now,self.now,'1m')
    def test_idempotent_schedule_concurrent_claim_checkpoint_and_immutability(self):
        job=self.service.schedule(self.spec());self.assertEqual(job,self.service.schedule(self.spec()));first=self.repo.claim('worker-a',1,self.now,10);second=self.repo.claim('worker-b',1,self.now,10);self.assertEqual(len(first),1);self.assertEqual(second,[])
        attempt=stable_id('attempt',(job,1));self.repo.checkpoint(job,attempt,1,None,'2',2,'0'*64,'RETRYING',self.now)
        with get_connection() as c:
            with c.cursor() as q:q.execute('SELECT checkpoint,status FROM v3_backfill_jobs WHERE job_id=%s',(job,));self.assertEqual(q.fetchone(),('2','RETRYING'))
        with self.assertRaises(Exception):
            with get_connection() as c:
                with c.cursor() as q:q.execute('DELETE FROM v3_backfill_attempts WHERE attempt_id=%s',(attempt,))
    def test_pause_resume_stale_recovery_retention_and_health(self):
        job=self.service.schedule(self.spec());self.assertTrue(self.repo.pause(job,self.now));self.assertTrue(self.repo.resume(job,self.now));self.repo.claim('worker',1,self.now,1);self.assertEqual(self.repo.recover_stale(self.now+timedelta(seconds=2)),[job])
        self.repo.persist_retention(self.service.retention_policies(self.now));health=self.repo.health(self.now);self.assertIn('database_size_bytes',health);self.assertGreaterEqual(health['retry_backlog'],1)

if __name__=='__main__':unittest.main()
