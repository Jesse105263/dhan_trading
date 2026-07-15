import inspect,unittest
from datetime import datetime,timedelta
from decimal import Decimal
from uuid import UUID
from scripts.register_research_experiment import FixtureGovernanceRepository,fixture_definition
from scripts.run_offline_research import observations
from services.research_governance_models import GovernancePolicy
from services.research_governance_service import ResearchGovernanceService


class ResearchGovernanceTest(unittest.TestCase):
    def setUp(self):self.now=datetime(2026,7,16);self.repo=FixtureGovernanceRepository();self.policy=GovernancePolicy('test-governance',minimum_test_sample=10,bootstrap_samples=100);self.service=ResearchGovernanceService(self.repo,clock=lambda:self.now);self.experiment=self.service.register(fixture_definition(),self.policy)
    def test_registry_is_deterministic_and_preserves_dataset_model_roles_and_audit(self):
        again=self.service.register(fixture_definition(),self.policy);self.assertEqual(self.experiment,again);prepared=self.repo.registry;self.assertEqual(len(prepared['models']),2);self.assertEqual({x['role'] for x in prepared['roles']},{'CHAMPION','CHALLENGER'});self.assertEqual(len(prepared['dataset']['dataset_checksum']),64);self.assertEqual({x['event_type'] for x in prepared['audits']},{'REGISTERED'})
    def test_offline_replay_statistical_comparison_and_reproducibility(self):
        a=self.service.evaluate(self.experiment,observations(),self.now,self.policy,comparison_count=2);b=self.service.evaluate(self.experiment,observations(),self.now,self.policy,comparison_count=2);self.assertEqual(a.run_id,b.run_id);self.assertEqual(a.state,'PASS');run,replay,comparison,report,_=self.repo.evaluations[a.run_id];self.assertEqual(len(replay),12);self.assertEqual(comparison['superiority_state'],'SUPERIOR');self.assertEqual(comparison['adjusted_alpha'],self.policy.alpha/2);self.assertTrue(report['promotion_eligible']);self.assertTrue(report['reproducibility']['dependency_free'])
    def test_leakage_future_non_test_overlap_and_unsupported_are_excluded(self):
        rows=observations();rows.extend([{**rows[0],'observation_id':'future','episode_id':'future','terminal_at':self.now+timedelta(days=1)},{**rows[0],'observation_id':'train','episode_id':'train','period':'TRAIN'},{**rows[0],'observation_id':'leak','episode_id':'leak','leakage_flag':True},{**rows[0],'observation_id':'overlap'},{**rows[0],'observation_id':'missing','episode_id':'missing','challenger_return':None}]);result=self.service.evaluate(self.experiment,rows,self.now,self.policy);run,replay,_,report,_=self.repo.evaluations[result.run_id];reasons={x['exclusion_reason'] for x in replay if not x['included']};self.assertEqual(reasons,{'FUTURE_OR_UNMATURE_OUTCOME','NON_TEST_PARTITION','AUDIT_EXCLUSION','OVERLAPPING_EPISODE','UNSUPPORTED_OUTCOME'});self.assertFalse(report['audits']['leakage_passed']);self.assertFalse(report['promotion_eligible']);self.assertEqual(run['excluded_count'],5)
    def test_insufficient_evidence_keeps_statistics_null_and_blocks_promotion(self):
        result=self.service.evaluate(self.experiment,observations(2),self.now,self.policy);self.assertEqual(result.state,'INSUFFICIENT_EVIDENCE');comparison=self.repo.evaluations[result.run_id][2];self.assertIsNone(comparison['p_value']);self.assertIsNone(comparison['confidence_low']);self.assertFalse(self.repo.reports[result.report_id]['promotion_eligible'])
    def test_promotion_fails_closed_without_shadow_sessions_and_approvals(self):
        report=self.service.evaluate(self.experiment,observations(),self.now,self.policy).report_id;proposal=self.service.propose(report,0,self.policy);result=self.service.decide(proposal,self.policy);self.assertEqual(result.state,'REJECTED');decision,assignments,rollback,_=self.repo.decisions[-1];self.assertEqual(assignments,[]);self.assertIsNone(rollback);self.assertEqual(decision['approval_count'],0)
    def test_explicit_three_role_approval_creates_offline_assignment_and_rollback_plan(self):
        report=self.service.evaluate(self.experiment,observations(),self.now,self.policy).report_id;proposal=self.service.propose(report,60,self.policy)
        for role in self.policy.required_approval_roles:self.service.approve(proposal,role,f'{role.lower()}-1','APPROVE','Reviewed frozen offline evidence.')
        result=self.service.decide(proposal,self.policy);self.assertEqual(result.state,'APPROVED');_,assignments,rollback,audit=self.repo.decisions[-1];self.assertEqual({x['role'] for x in assignments},{'CHAMPION','RETIRED'});self.assertEqual(rollback['state'],'PLANNED');self.assertFalse(rollback['rollback_procedure']['automatic']);self.assertEqual(audit['actor_type'],'OFFLINE_SERVICE')
    def test_rejection_or_readiness_failure_blocks_promotion(self):
        report=self.service.evaluate(self.experiment,observations(),self.now,self.policy).report_id;proposal=self.service.propose(report,60,self.policy)
        for role in self.policy.required_approval_roles:self.service.approve(proposal,role,role,'APPROVE','reviewed')
        self.repo.release_ready=lambda:False;self.assertEqual(self.service.decide(proposal,self.policy).state,'REJECTED')
    def test_approval_and_policy_validation(self):
        with self.assertRaises(ValueError):self.service.approve(UUID(int=1),'UNKNOWN','x','APPROVE','x')
        with self.assertRaises(ValueError):GovernancePolicy('',minimum_test_sample=1)
    def test_no_execution_retraining_or_model_mutation_surface(self):
        source=inspect.getsource(ResearchGovernanceService).lower();self.assertNotIn('dhan',source);self.assertNotIn('order(',source);self.assertNotIn('retrain',source);self.assertNotIn('update ',source);self.assertNotIn('paper_trade',source)


if __name__=='__main__':unittest.main()
