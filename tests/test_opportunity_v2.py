import unittest
from datetime import date,datetime,timedelta
from decimal import Decimal
from uuid import UUID
from services.opportunity_v2_models import OpportunityPolicyV2
from services.opportunity_v2_service import OpportunityV2Service

def match(i,ret=2,distance=Decimal('.1'),quality=Decimal('.9')):
 return {'match_id':UUID(int=100+i),'matched_vector_id':UUID(int=200+i),'matched_outcome_id':UUID(int=300+i),'instrument_id':UUID(int=400+i),'observed_at':datetime(2026,6,i+1),'available_at':datetime(2026,6,i+1,1),'subject_type':'OPTION','expiry':date(2026,7,30),'regime':i%2,'outcome_state':'COMPLETE','terminal_reason':'TIMEOUT','net_return_pct':Decimal(ret),'maximum_favourable_excursion_pct':Decimal(5+i),'maximum_adverse_excursion_pct':Decimal(-3-i/10),'distance':distance,'similarity_score':Decimal('.9'),'evidence_quality_score':quality}
class Repo:
 def __init__(self):
  self.source={'query_vector_id':UUID(int=1),'instrument_id':UUID(int=2),'subject_type':'OPTION','observed_at':datetime(2026,7,15),'query_observed_at':datetime(2026,7,15),'available_at':datetime(2026,7,15),'feature_lineage_checksum':'a'*64,'lineage_checksum':'b'*64,'instrument_revision_id':UUID(int=3),'expiry':date(2026,7,30),'strike':Decimal(100),'option_type':'CE','close_price':Decimal(10),'volume':Decimal(100),'open_interest':Decimal(500),'spread_pct':Decimal('.5'),'days_to_expiry':Decimal(15),'regime':1,'underlying_price':Decimal(100)}
  self.matches=[match(i,2 if i<4 else -1) for i in range(1,7)];self.saved=[]
 def evidence(self,r):return self.source,self.matches
 def persist(self,p):self.saved.append(p)
class OpportunityV2Tests(unittest.TestCase):
 def setUp(self):self.r=Repo();self.s=OpportunityV2Service(self.r,clock=lambda:datetime(2026,7,16));self.p=OpportunityPolicyV2('test','OPTION_PATH','LONG_CALL','SESSION','2026-06-30',maximum_symbol_concentration=Decimal(1),maximum_expiry_concentration=Decimal(1),maximum_regime_concentration=Decimal(1),maximum_episode_concentration=Decimal(1))
 def test_contract_levels_costs_expected_value_and_lineage(self):
  a=self.s.materialize(UUID(int=9),self.p);b=self.s.materialize(UUID(int=9),self.p);self.assertEqual(a.run_id,b.run_id);self.assertEqual(a.state,'PROVISIONAL')
  c=self.r.saved[0]['candidate'];self.assertEqual(c['instrument_id'],UUID(int=2));self.assertLess(c['stop_price'],c['entry_zone_low']);self.assertEqual(len(c['target_prices']),2);self.assertGreater(c['target_prices'][0],c['entry_zone_high']);self.assertIsNotNone(c['historical_win_rate']);self.assertIsNotNone(c['net_expected_value_pct']);self.assertGreater(c['effective_sample_size'],0);self.assertEqual(len(c['lineage_checksum']),64)
 def test_liquidity_fill_sparse_ood_and_concentration_abstain_with_nulls(self):
  cases=[]
  self.r.source['spread_pct']=Decimal(9);cases.append(('ILLIQUID',self.p));self.assert_state(*cases[-1]);self.r.source['spread_pct']=Decimal('.5')
  self.r.source['days_to_expiry']=Decimal(0);self.assert_state('FILL_REJECTED',self.p);self.r.source['days_to_expiry']=Decimal(15)
  self.r.matches=self.r.matches[:2];self.assert_state('INSUFFICIENT_EVIDENCE',self.p);self.r.matches=[match(i,distance=Decimal('.9')) for i in range(1,7)];self.assert_state('OUT_OF_DISTRIBUTION',self.p)
  self.r.matches=[{**match(i),'instrument_id':UUID(int=400)} for i in range(1,7)];p=OpportunityPolicyV2('concentrated','OPTION_PATH','LONG_CALL','SESSION','2026-06-30');self.assert_state('UNSTABLE',p)
 def assert_state(self,state,policy):
  self.assertEqual(self.s.materialize(UUID(int=9),policy).state,state);c=self.r.saved[-1]['candidate'];self.assertIsNone(c['entry_zone_low']);self.assertIsNone(c['historical_win_rate']);self.assertEqual(c['target_prices'],[])
 def test_direction_and_policy_validation(self):
  self.assert_state('INSUFFICIENT_EVIDENCE',OpportunityPolicyV2('put','OPTION_PATH','LONG_PUT','SESSION','2026-06-30'))
  with self.assertRaises(ValueError):OpportunityPolicyV2('bad','x','LONG','S','x')
if __name__=='__main__':unittest.main()
