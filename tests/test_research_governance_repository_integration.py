import os,unittest
from datetime import datetime
from services.database import get_connection
from services.research_governance_models import GovernancePolicy
from services.research_governance_repository import ResearchGovernanceRepository
from services.research_governance_service import ResearchGovernanceService
from scripts.register_research_experiment import fixture_definition
from scripts.run_offline_research import observations


@unittest.skipUnless(os.getenv('RUN_DB_INTEGRATION_TESTS')=='1','Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.')
class ResearchGovernanceRepositoryIntegrationTest(unittest.TestCase):
    TABLES=('governance_audit_history_v3','model_rollback_metadata_v3','model_role_assignments_v3','model_promotion_decisions_v3','governance_approvals_v3','model_promotion_proposals_v3','research_evaluation_reports_v3','model_comparisons_v3','research_replay_observations_v3','research_experiment_runs_v3','research_experiments_v3','governed_models_v3','research_datasets_v3','governance_policies_v3')
    def tearDown(self):
        with get_connection() as c:
            with c.cursor() as q:
                for table in self.TABLES:q.execute(f'ALTER TABLE {table} DISABLE TRIGGER ALL')
                for table in self.TABLES:q.execute(f'DELETE FROM {table}')
                for table in reversed(self.TABLES):q.execute(f'ALTER TABLE {table} ENABLE TRIGGER ALL')
            c.commit()
    def test_registry_replay_report_promotion_audit_idempotency_and_immutability(self):
        now=datetime(2026,7,16);policy=GovernancePolicy('v39-integration',minimum_test_sample=10,bootstrap_samples=100);repository=ResearchGovernanceRepository();service=ResearchGovernanceService(repository,clock=lambda:now)
        experiment=service.register(fixture_definition(),policy);self.assertEqual(experiment,service.register(fixture_definition(),policy));result=service.evaluate(experiment,observations(),now,policy);rerun=service.evaluate(experiment,observations(),now,policy);self.assertEqual(result.run_id,rerun.run_id);self.assertEqual(result.state,'PASS')
        proposal=service.propose(result.report_id,0,policy);decision=service.decide(proposal,policy);self.assertEqual(decision.state,'REJECTED')
        with get_connection() as c:
            with c.cursor() as q:
                q.execute('SELECT COUNT(*),COUNT(*) FILTER(WHERE included) FROM research_replay_observations_v3 WHERE run_id=%s',(result.run_id,));self.assertEqual(q.fetchone(),(12,12));q.execute('SELECT promotion_eligible,report_checksum FROM research_evaluation_reports_v3 WHERE report_id=%s',(result.report_id,));eligible,checksum=q.fetchone();self.assertTrue(eligible);self.assertEqual(len(checksum),64);q.execute('SELECT COUNT(*) FROM governance_audit_history_v3');self.assertGreaterEqual(q.fetchone()[0],4)
        with self.assertRaises(Exception):
            with get_connection() as c:
                with c.cursor() as q:q.execute('UPDATE research_experiments_v3 SET hypothesis=%s WHERE experiment_id=%s',('changed',experiment))


if __name__=='__main__':unittest.main()
