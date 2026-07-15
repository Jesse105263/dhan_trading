import argparse
from datetime import datetime,timedelta
from decimal import Decimal
from uuid import UUID
from scripts.register_research_experiment import FixtureGovernanceRepository,fixture_definition
from services.research_governance_models import GovernancePolicy
from services.research_governance_service import ResearchGovernanceService


def observations(count=12):
    base=datetime(2025,8,1)
    return [{'observation_id':f'fixture-{i}','episode_id':f'episode-{i}','period':'TEST','terminal_at':base+timedelta(days=i),'champion_return':Decimal('-0.2')+Decimal(i%2)/10,'challenger_return':Decimal('0.8')+Decimal(i%2)/10,'source_lineage':{'fixture_observation':i}} for i in range(count)]


def main():
    p=argparse.ArgumentParser(description='Run a deterministic offline governed replay.');p.add_argument('--experiment-id',type=UUID);p.add_argument('--fixture',action='store_true');a=p.parse_args()
    if not a.fixture and a.experiment_id is None:p.error('--experiment-id is required unless --fixture is used')
    policy=GovernancePolicy('governance-v1',minimum_test_sample=10);repo=FixtureGovernanceRepository() if a.fixture else None;service=ResearchGovernanceService(repo,clock=lambda:datetime(2026,7,16))
    experiment=service.register(fixture_definition(),policy) if a.fixture else a.experiment_id;result=service.evaluate(experiment,observations() if a.fixture else [],datetime(2026,7,16),policy)
    print(f'Offline research completed | experiment={result.experiment_id} run={result.run_id} report={result.report_id} state={result.state} execution=false trusted=false');return 0


if __name__=='__main__':raise SystemExit(main())
