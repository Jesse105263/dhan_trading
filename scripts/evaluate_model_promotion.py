import argparse
from datetime import datetime
from uuid import UUID
from scripts.register_research_experiment import FixtureGovernanceRepository,fixture_definition
from scripts.run_offline_research import observations
from services.research_governance_models import GovernancePolicy
from services.research_governance_service import ResearchGovernanceService


def main():
    p=argparse.ArgumentParser(description='Evaluate an offline model promotion proposal.');p.add_argument('--report-id',type=UUID);p.add_argument('--fixture',action='store_true');p.add_argument('--shadow-sessions',type=int,default=0);a=p.parse_args()
    if not a.fixture and a.report_id is None:p.error('--report-id is required unless --fixture is used')
    policy=GovernancePolicy('governance-v1',minimum_test_sample=10);repo=FixtureGovernanceRepository() if a.fixture else None;service=ResearchGovernanceService(repo,clock=lambda:datetime(2026,7,16))
    if a.fixture:experiment=service.register(fixture_definition(),policy);report_id=service.evaluate(experiment,observations(),datetime(2026,7,16),policy).report_id
    else:report_id=a.report_id
    proposal=service.propose(report_id,a.shadow_sessions,policy);result=service.decide(proposal,policy)
    print(f'Model promotion evaluated | proposal={result.proposal_id} decision={result.decision_id} state={result.state} offline=true deployed=false trusted=false');return 0


if __name__=='__main__':raise SystemExit(main())
