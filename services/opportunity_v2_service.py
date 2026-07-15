from dataclasses import asdict
from datetime import date,datetime
from decimal import Decimal
import hashlib,json
from uuid import UUID,uuid5
from services.opportunity_v2_models import OpportunityPolicyV2,OpportunityResultV2
from services.opportunity_v2_repository import OpportunityV2Repository


class OpportunityV2Service:
    NAMESPACE=UUID('840d6912-a86a-4c43-a970-d0361aa43a83')
    def __init__(self,repository=None,clock=datetime.now):self.repository=repository or OpportunityV2Repository();self.clock=clock
    def materialize(self,similarity_run_id,policy):
        source,matches=self.repository.evidence(similarity_run_id)
        if source is None:raise ValueError('Similarity V2 run was not found.')
        doc=json.loads(json.dumps(asdict(policy),default=str)); checksum=self._hash(doc); now=self.clock()
        run_id=uuid5(self.NAMESPACE,f"{similarity_run_id}:{checksum}"); candidate_id=uuid5(self.NAMESPACE,f"candidate:{run_id}:{source['instrument_id']}")
        training_end=date.fromisoformat(str(policy.training_period_end)) if not isinstance(policy.training_period_end,date) else policy.training_period_end
        included=[m for m in matches if m['subject_type']=='OPTION' and m['outcome_state']=='COMPLETE' and m['net_return_pct'] is not None and m['observed_at'].date()<=training_end]
        weights=[Decimal(m['similarity_score'])*Decimal(m['evidence_quality_score']) for m in included]
        ess=(sum(weights,Decimal(0))**2/sum((w*w for w in weights),Decimal(0))) if weights and sum((w*w for w in weights),Decimal(0)) else Decimal(0)
        concentration=self._concentration(included); quality=sum((Decimal(m['evidence_quality_score']) for m in included),Decimal(0))/len(included) if included else Decimal(0)
        rejected=len(matches)-len(included); fill={"accepted":len(included),"rejected":rejected,"fee_bps":str(policy.fee_bps),"slippage_bps":str(policy.entry_slippage_bps)}
        state,reasons_against=self._state(source,included,ess,quality,concentration,policy)
        reasons_for=[]; values={"entry_zone_low":None,"entry_zone_high":None,"stop_price":None,"target_prices":[],"historical_win_rate":None,"net_expected_value_pct":None}
        if state=='PROVISIONAL':
            premium=Decimal(source['close_price']); slip=policy.entry_slippage_bps/Decimal(10000)
            returns=[Decimal(m['net_return_pct']) for m in included]+[policy.rejected_fill_return_pct]*rejected
            mfe=[Decimal(m['maximum_favourable_excursion_pct']) for m in included]; mae=[Decimal(m['maximum_adverse_excursion_pct']) for m in included]
            values={"entry_zone_low":premium,"entry_zone_high":premium*(1+slip),"stop_price":premium*(1+self._quantile(mae,policy.stop_quantile)/100),
                "target_prices":[premium*(1+self._quantile(mfe,q)/100) for q in policy.target_quantiles],
                "historical_win_rate":Decimal(sum(x>0 for x in returns))/len(returns),
                "net_expected_value_pct":sum(returns,Decimal(0))/len(returns)-policy.fee_bps/Decimal(100)}
            if not(values['stop_price']<values['entry_zone_low']<=values['entry_zone_high']<values['target_prices'][0]):
                state='CONTRADICTORY'; reasons_against=['Historical option-premium paths do not produce ordered entry, stop, and target levels.']; values={k:([] if k=='target_prices' else None) for k in values}
            else:reasons_for=[f"{len(included)} complete option-contract outcomes support the provisional levels.","Net outcomes include persisted costs, wins, losses and timeouts."]
        candidate={"candidate_id":candidate_id,"run_id":run_id,"similarity_run_id":similarity_run_id,"query_vector_id":source['query_vector_id'],
          "instrument_id":source['instrument_id'],"instrument_revision_id":source['instrument_revision_id'],"state":state,"strategy_code":policy.strategy_code,
          "direction":policy.direction,"holding_horizon":policy.holding_horizon,"observed_at":source['observed_at'],"expiry":source['expiry'],"strike":source['strike'],"option_type":source['option_type'],
          **values,"similar_setup_count":len(included),"effective_sample_size":ess,"evidence_quality":quality,"concentration_metrics":concentration,
          "fill_metrics":fill,"reasons_for":reasons_for,"reasons_against":reasons_against,"feature_lineage_checksum":source['feature_lineage_checksum'],
          "similarity_lineage_checksum":source['lineage_checksum'],"contract_lineage_checksum":self._hash({"revision":str(source['instrument_revision_id'])}),
          "lineage_checksum":self._hash({"run":str(run_id),"matches":[str(m['match_id']) for m in matches]}),"materialized_at":now}
        evidence=[{"candidate_id":candidate_id,"match_id":m['match_id'],"matched_vector_id":m['matched_vector_id'],"matched_outcome_id":m['matched_outcome_id'],
          "included":m in included,"exclusion_reason":None if m in included else 'NO_COMPLETE_OPTION_OUTCOME',"episode_key":m['observed_at'].date().isoformat(),
          "evidence_weight":Decimal(m['similarity_score'])*Decimal(m['evidence_quality_score'])} for m in matches]
        run={"run_id":run_id,"policy_version":policy.policy_version,"similarity_run_id":similarity_run_id,"as_of":source['query_observed_at'],"policy_checksum":checksum,
          "candidate_count":1,"provisional_count":int(state=='PROVISIONAL'),"abstained_count":int(state!='PROVISIONAL'),"lineage_checksum":self._hash({"candidate":str(candidate_id),"policy":checksum}),"started_at":now,"completed_at":self.clock()}
        self.repository.persist({"policy_version":policy.policy_version,"policy_checksum":checksum,"strategy_code":policy.strategy_code,"policy":doc,"started_at":now,"run":run,"candidate":candidate,"evidence":evidence})
        return OpportunityResultV2(run_id,candidate_id,state)

    def _state(self,s,e,ess,q,c,p):
        if s['subject_type']!='OPTION' or s['option_type'] not in {'CE','PE'} or s['close_price'] is None:return 'INSUFFICIENT_EVIDENCE',['An exact option contract and option-premium feature are required.']
        if (p.direction=='LONG_CALL')!=(s['option_type']=='CE'):return 'INSUFFICIENT_EVIDENCE',['Strategy direction does not match the exact option contract.']
        if s['spread_pct'] is None or Decimal(s['spread_pct'])>p.maximum_spread_pct or s['volume'] is None or Decimal(s['volume'])<p.minimum_volume or s['open_interest'] is None or Decimal(s['open_interest'])<p.minimum_open_interest:return 'ILLIQUID',['Spread, volume, or open-interest policy failed.']
        if s['days_to_expiry'] is None or not p.minimum_days_to_expiry<=Decimal(s['days_to_expiry'])<=p.maximum_days_to_expiry:return 'FILL_REJECTED',['Expiry or fill-feasibility policy failed.']
        if s['underlying_price'] in (None,0):return 'INSUFFICIENT_EVIDENCE',['Point-in-time underlying evidence is required only for moneyness validation.']
        money=(Decimal(s['strike'])-Decimal(s['underlying_price']))/Decimal(s['underlying_price'])*100
        if not p.minimum_moneyness_pct<=money<=p.maximum_moneyness_pct:return 'FILL_REJECTED',['Strike moneyness is outside policy.']
        if matches_distance:=any(Decimal(x['distance'])>p.out_of_distribution_distance for x in e):return 'OUT_OF_DISTRIBUTION',['Historical analogues exceed the distance boundary.']
        if len(e)<p.minimum_sample or ess<p.minimum_effective_sample or q<p.minimum_evidence_quality:return 'INSUFFICIENT_EVIDENCE',['Sample size, effective sample size, or evidence quality is insufficient.']
        limits=(('symbol',p.maximum_symbol_concentration),('expiry',p.maximum_expiry_concentration),('regime',p.maximum_regime_concentration),('episode',p.maximum_episode_concentration))
        if any(c[k]>v for k,v in limits):return 'UNSTABLE',['Evidence is concentrated by contract, expiry, regime, or market episode.']
        return 'PROVISIONAL',[]
    @staticmethod
    def _concentration(rows):
        def peak(key):
            if not rows:return Decimal(0)
            counts={};
            for r in rows:counts[str(key(r))]=counts.get(str(key(r)),0)+1
            return Decimal(max(counts.values()))/len(rows)
        return {'symbol':peak(lambda r:r['instrument_id']),'expiry':peak(lambda r:r['expiry']),'regime':peak(lambda r:r['regime']),'episode':peak(lambda r:r['observed_at'].date())}
    @staticmethod
    def _quantile(values,q):ordered=sorted(values);return ordered[int((len(ordered)-1)*q)]
    @staticmethod
    def _hash(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
