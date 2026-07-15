import argparse
from datetime import date,datetime
from services.research_governance_models import GovernancePolicy
from services.research_governance_service import ResearchGovernanceService


def fixture_definition():
    return {'dataset_version':'fixture-dataset-v1','source_versions':{'features':'fixture-feature-v2','outcomes':'fixture-outcome-v2','validation':'fixture-shadow-v1'},'periods':{'TRAIN':[date(2020,1,1),date(2023,12,31)],'VALIDATION':[date(2024,1,1),date(2024,12,31)],'CALIBRATION':[date(2025,1,1),date(2025,6,30)],'TEST':[date(2025,7,1),date(2026,12,31)]},'dataset_lineage':{'fixture':True,'fabricated_market_data':False},'champion_model':{'model_version':'champion-v1','model_type':'RULE_POLICY','configuration':{'frozen':True}},'challenger_model':{'model_version':'challenger-v1','model_type':'RULE_POLICY','configuration':{'frozen':True}},'experiment_version':'fixture-experiment-v1','hypothesis':'The frozen challenger has higher paired net return on untouched test evidence.','evaluation_plan':{'method':'PAIRED_RETURN_COMPARISON','offline_replay':True}}


class FixtureGovernanceRepository:
    def __init__(self):self.registry=None;self.evaluations={};self.reports={};self.proposals={};self.approval_rows=[];self.decisions=[]
    def persist_registry(self,p):self.registry=p
    def experiment(self,experiment_id):
        if not self.registry:return None
        e=dict(self.registry['experiment']);d=self.registry['dataset'];e.update({'dataset_version':d['dataset_version'],'dataset_checksum':d['dataset_checksum'],'test_start':d['test_start'],'test_end':d['test_end']});return e
    def persist_evaluation(self,run,observations,comparison,report,audit):self.evaluations[run['run_id']]=(run,observations,comparison,report,audit);self.reports[report['report_id']]={**report,'experiment_id':run['experiment_id'],'champion_model_id':comparison['champion_model_id'],'challenger_model_id':comparison['challenger_model_id']}
    def report(self,report_id):return self.reports.get(report_id)
    def persist_proposal(self,policy,proposal,audit):self.proposals[proposal['proposal_id']]={**proposal,'promotion_eligible':self.reports[proposal['report_id']]['promotion_eligible']}
    def proposal(self,proposal_id):return self.proposals.get(proposal_id)
    def approvals(self,proposal_id):return [x for x in self.approval_rows if x['proposal_id']==proposal_id]
    def persist_approval(self,approval,audit):self.approval_rows.append(approval)
    def release_ready(self):return True
    def persist_decision(self,decision,assignments,rollback,audit):self.decisions.append((decision,assignments,rollback,audit))


def main():
    p=argparse.ArgumentParser(description='Register an immutable offline research experiment.');p.add_argument('--fixture',action='store_true');p.add_argument('--dataset-version');p.add_argument('--champion');p.add_argument('--challenger');a=p.parse_args()
    if not a.fixture and not all((a.dataset_version,a.champion,a.challenger)):p.error('use --fixture or provide --dataset-version, --champion and --challenger')
    definition=fixture_definition()
    if not a.fixture:definition={**definition,'dataset_version':a.dataset_version,'experiment_version':f'{a.champion}-vs-{a.challenger}','champion_model':{**definition['champion_model'],'model_version':a.champion},'challenger_model':{**definition['challenger_model'],'model_version':a.challenger}}
    repo=FixtureGovernanceRepository() if a.fixture else None;service=ResearchGovernanceService(repo,clock=lambda:datetime(2026,7,16));experiment=service.register(definition,GovernancePolicy('governance-v1'))
    print(f'Research experiment registered | experiment={experiment} offline=true execution=false trusted=false');return 0


if __name__=='__main__':raise SystemExit(main())
