import json
from psycopg.types.json import Jsonb
from services.database import get_connection


class OpportunityV2Repository:
    def evidence(self,run_id):
        runs=self._dicts("""SELECT r.*,v.instrument_id,v.subject_type,v.observed_at,v.available_at,v.lineage_checksum feature_lineage_checksum,
          v.anchor_bar_revision_id,v.quality_state,v.coverage_percentage,i.revision_id instrument_revision_id,i.expiry,i.strike,i.option_type,
          q.numeric_value close_price,vol.numeric_value volume,oi.numeric_value open_interest,spread.numeric_value spread_pct,
          dte.numeric_value days_to_expiry,reg.numeric_value regime,
          (SELECT x.numeric_value FROM feature_vectors_v2 uv JOIN feature_values_v2 x ON x.vector_id=uv.vector_id AND x.feature_name='close_price'
           WHERE uv.instrument_id=v.underlying_instrument_id AND uv.observed_at<=v.observed_at AND uv.available_at<=v.available_at ORDER BY uv.observed_at DESC LIMIT 1) underlying_price
          FROM similarity_runs_v2 r JOIN feature_vectors_v2 v ON v.vector_id=r.query_vector_id
          JOIN canonical_instrument_revisions i ON i.instrument_id=v.instrument_id AND i.available_at<=v.available_at
            AND NOT EXISTS(SELECT 1 FROM canonical_instrument_revisions i2 WHERE i2.instrument_id=i.instrument_id AND i2.available_at<=v.available_at AND (i2.revision_number,i2.revision_id)>(i.revision_number,i.revision_id))
          LEFT JOIN feature_values_v2 q ON q.vector_id=v.vector_id AND q.feature_name='close_price'
          LEFT JOIN feature_values_v2 vol ON vol.vector_id=v.vector_id AND vol.feature_name='volume'
          LEFT JOIN feature_values_v2 oi ON oi.vector_id=v.vector_id AND oi.feature_name='open_interest'
          LEFT JOIN feature_values_v2 spread ON spread.vector_id=v.vector_id AND spread.feature_name='bid_ask_spread_pct'
          LEFT JOIN feature_values_v2 dte ON dte.vector_id=v.vector_id AND dte.feature_name='days_to_expiry'
          LEFT JOIN feature_values_v2 reg ON reg.vector_id=v.vector_id AND reg.feature_name='trend_regime_3'
          WHERE r.run_id=%s""",(run_id,))
        if not runs:return None,[]
        matches=self._dicts("""SELECT m.*,v.instrument_id,v.observed_at,v.available_at,v.subject_type,i.expiry,
          reg.numeric_value regime,o.outcome_state,o.terminal_reason,o.net_return_pct,o.maximum_favourable_excursion_pct,
          o.maximum_adverse_excursion_pct,o.holding_duration_seconds,o.lineage_checksum outcome_lineage_checksum
          FROM similarity_matches_v2 m JOIN feature_vectors_v2 v ON v.vector_id=m.matched_vector_id
          LEFT JOIN canonical_instrument_revisions i ON i.instrument_id=v.instrument_id AND i.available_at<=v.available_at
            AND NOT EXISTS(SELECT 1 FROM canonical_instrument_revisions i2 WHERE i2.instrument_id=i.instrument_id AND i2.available_at<=v.available_at AND (i2.revision_number,i2.revision_id)>(i.revision_number,i.revision_id))
          LEFT JOIN feature_values_v2 reg ON reg.vector_id=v.vector_id AND reg.feature_name='trend_regime_3'
          LEFT JOIN historical_outcomes_v2 o ON o.outcome_id=m.matched_outcome_id WHERE m.run_id=%s ORDER BY m.rank_position""",(run_id,))
        return runs[0],matches

    def persist(self,p):
        with get_connection() as c:
            try:
                with c.cursor() as q:
                    q.execute("INSERT INTO opportunity_policies_v2(policy_version,policy_checksum,strategy_code,policy,created_at) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(policy_version) DO NOTHING",(p['policy_version'],p['policy_checksum'],p['strategy_code'],Jsonb(p['policy']),p['started_at']))
                    q.execute("SELECT policy_checksum FROM opportunity_policies_v2 WHERE policy_version=%s",(p['policy_version'],))
                    if q.fetchone()[0]!=p['policy_checksum']:raise ValueError('Opportunity policy version is immutable.')
                    r=p['run']; q.execute("""INSERT INTO opportunity_runs_v2(run_id,policy_version,similarity_run_id,as_of,policy_checksum,candidate_count,
                      provisional_count,abstained_count,lineage_checksum,started_at,completed_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(run_id) DO NOTHING""",tuple(r.values()))
                    o=p['candidate']; keys=tuple(o); vals=tuple(Jsonb(json.loads(json.dumps(v,default=str))) if k in {'target_prices','concentration_metrics','fill_metrics','reasons_for','reasons_against'} else v for k,v in o.items())
                    q.execute(f"INSERT INTO opportunity_candidates_v2({','.join(keys)}) VALUES({','.join(['%s']*len(keys))}) ON CONFLICT(candidate_id) DO NOTHING",vals)
                    for e in p['evidence']:
                        q.execute("INSERT INTO opportunity_evidence_v2(candidate_id,match_id,matched_vector_id,matched_outcome_id,included,exclusion_reason,episode_key,evidence_weight) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(candidate_id,match_id) DO NOTHING",tuple(e.values()))
                c.commit()
            except Exception:c.rollback();raise

    @staticmethod
    def _dicts(query,params):
        with get_connection() as c:
            with c.cursor() as q:q.execute(query,params); names=[x.name for x in q.description or ()];return [dict(zip(names,row,strict=True)) for row in q.fetchall()]
