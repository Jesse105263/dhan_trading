import json
from psycopg.types.json import Jsonb
from services.database import get_connection

class CalibrationV2Repository:
 def observations(self,policy,cutoff):
  return self._rows("""SELECT c.candidate_id,o.outcome_id,c.observed_at,o.terminal_at,c.historical_win_rate raw_score,o.net_return_pct realized_return,
   c.effective_sample_size evidence_weight,c.evidence_quality,(c.concentration_metrics->>'symbol')::numeric concentration,
   COALESCE((s.quality_metrics->>'maximum_distance')::numeric,0) distance,
   CASE WHEN c.state='PROVISIONAL' THEN 1 ELSE 0 END liquidity_ok,0::numeric drift_value,FALSE data_quality_issue
   FROM opportunity_candidates_v2 c JOIN feature_vectors_v2 v ON v.vector_id=c.query_vector_id
   JOIN historical_outcomes_v2 o ON o.anchor_bar_revision_id=v.anchor_bar_revision_id AND o.outcome_state='COMPLETE'
   JOIN similarity_runs_v2 s ON s.run_id=c.similarity_run_id WHERE c.strategy_code=%s AND c.direction=%s AND c.holding_horizon=%s
   AND c.observed_at<=%s AND o.terminal_at<=%s ORDER BY c.observed_at,c.candidate_id,o.outcome_id""",(policy.strategy,policy.direction,policy.holding_horizon,cutoff,cutoff))
 def candidate(self,candidate_id):
  rows=self._rows('SELECT * FROM opportunity_candidates_v2 WHERE candidate_id=%s',(candidate_id,));return rows[0] if rows else None
 def calibration(self,run_id):
  rows=self._rows('SELECT * FROM calibration_runs_v2 WHERE run_id=%s',(run_id,));
  if not rows:return None
  rows[0]['bins']=self._rows('SELECT * FROM calibration_reliability_bins_v2 WHERE run_id=%s ORDER BY bin_number',(run_id,));return rows[0]
 def release_ready(self):
  from scripts.verify_release import build_service
  return build_service().verify().ready
 def persist_calibration(self,p):
  with get_connection() as c:
   try:
    with c.cursor() as q:
     q.execute('INSERT INTO calibration_policies_v2(policy_id,policy_version,policy_checksum,strategy,direction,holding_horizon,policy,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(policy_id) DO NOTHING',(p['policy_id'],p['policy_version'],p['policy_checksum'],p['strategy'],p['direction'],p['holding_horizon'],Jsonb(p['policy']),p['started_at']))
     q.execute('SELECT policy_checksum FROM calibration_policies_v2 WHERE policy_id=%s',(p['policy_id'],));
     if q.fetchone()[0]!=p['policy_checksum']:raise ValueError('Calibration policy is immutable.')
     r=p['run'];q.execute("""INSERT INTO calibration_runs_v2(run_id,policy_id,cutoff_at,dataset_checksum,state,calibration_sample_size,effective_sample_size,brier_score,log_loss,expected_calibration_error,maximum_calibration_error,confidence_interval_coverage,abstention_rate,recommendation_coverage,net_expected_value,realized_outcome_rate,return_prediction_low,return_prediction_high,expected_value_low,expected_value_high,lineage_checksum,started_at,completed_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(run_id) DO NOTHING""",tuple(r.values()))
     for b in p['bins']:q.execute('INSERT INTO calibration_reliability_bins_v2(run_id,bin_number,prediction_low,prediction_high,sample_count,mean_uncalibrated_score,calibrated_probability,observed_win_rate) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(run_id,bin_number) DO NOTHING',tuple(b.values()))
     for x in p['lineage']:q.execute('INSERT INTO calibration_dataset_lineage_v2(run_id,candidate_id,outcome_id,period_name,included,exclusion_reason,observed_at,terminal_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(run_id,candidate_id,outcome_id) DO NOTHING',tuple(x.values()))
    c.commit()
   except Exception:c.rollback();raise
 def persist_evaluation(self,e):
  with get_connection() as c:
   with c.cursor() as q:
    vals=tuple(Jsonb(v) if k in {'gates','reasons'} else v for k,v in e.items());q.execute(f"INSERT INTO recommendation_evaluations_v2({','.join(e)}) VALUES({','.join(['%s']*len(e))}) ON CONFLICT(evaluation_id) DO NOTHING",vals)
   c.commit()
 @staticmethod
 def _rows(sql,p):
  with get_connection() as c:
   with c.cursor() as q:q.execute(sql,p);names=[x.name for x in q.description or ()];return [dict(zip(names,r,strict=True)) for r in q.fetchall()]
