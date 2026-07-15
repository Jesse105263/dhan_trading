import argparse
from datetime import date,datetime
from decimal import Decimal
from uuid import UUID
from services.opportunity_v2_models import OpportunityPolicyV2
from services.opportunity_v2_service import OpportunityV2Service

class FixtureRepository:
 def evidence(self,run_id):
  source={'query_vector_id':UUID(int=1),'instrument_id':UUID(int=2),'subject_type':'OPTION','observed_at':datetime(2026,7,15),'query_observed_at':datetime(2026,7,15),'available_at':datetime(2026,7,15),'feature_lineage_checksum':'a'*64,'lineage_checksum':'b'*64,'instrument_revision_id':UUID(int=3),'expiry':date(2026,7,30),'strike':Decimal(100),'option_type':'CE','close_price':Decimal(10),'volume':Decimal(100),'open_interest':Decimal(500),'spread_pct':Decimal('.5'),'days_to_expiry':Decimal(15),'regime':1,'underlying_price':Decimal(100)}
  matches=[{'match_id':UUID(int=100+i),'matched_vector_id':UUID(int=200+i),'matched_outcome_id':UUID(int=300+i),'instrument_id':UUID(int=400+i),'observed_at':datetime(2026,6,i+1),'subject_type':'OPTION','expiry':date(2026,7,30),'regime':i%2,'outcome_state':'COMPLETE','terminal_reason':'TIMEOUT','net_return_pct':Decimal(2 if i<5 else -1),'maximum_favourable_excursion_pct':Decimal(5+i),'maximum_adverse_excursion_pct':Decimal(-3),'distance':Decimal('.1'),'similarity_score':Decimal('.9'),'evidence_quality_score':Decimal('.9')} for i in range(1,7)]
  return source,matches
 def persist(self,prepared):pass

def main():
 p=argparse.ArgumentParser(description='Materialize a provisional, non-recommendational Opportunity V2 candidate.');p.add_argument('--similarity-run-id',type=UUID);p.add_argument('--fixture',action='store_true');p.add_argument('--policy-version',default='option-path-opportunity-v2');p.add_argument('--direction',choices=('LONG_CALL','LONG_PUT'),default='LONG_CALL');p.add_argument('--horizon',default='SESSION');a=p.parse_args()
 if not a.fixture and a.similarity_run_id is None:p.error('--similarity-run-id is required unless --fixture is used')
 service=OpportunityV2Service(FixtureRepository(),clock=lambda:datetime(2026,7,16)) if a.fixture else OpportunityV2Service();run_id=UUID(int=9) if a.fixture else a.similarity_run_id
 policy=OpportunityPolicyV2(a.policy_version,'OPTION_PATH',a.direction,a.horizon,'2026-06-30',maximum_symbol_concentration=Decimal(1),maximum_expiry_concentration=Decimal(1),maximum_regime_concentration=Decimal(1),maximum_episode_concentration=Decimal(1))
 r=service.materialize(run_id,policy)
 print(f'Opportunity V2 materialized | run={r.run_id} candidate={r.candidate_id} state={r.state} trusted=false recommendation=false');return 0
if __name__=='__main__':raise SystemExit(main())
