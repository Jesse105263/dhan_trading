import json
from psycopg.types.json import Jsonb
from services.database import get_connection


class LiveValidationRepository:
    def recommendation_source(self,evaluation_id):
        rows=self._dicts("""SELECT c.*,e.evaluation_id,e.policy_id,e.calibration_run_id,e.state evaluation_state,e.eligible,
          e.calibrated_win_probability,e.win_probability_low,e.win_probability_high,e.conservative_expected_value,
          e.uncertainty_tier,e.effective_sample_size evaluation_effective_sample_size,e.gates,e.reasons evaluation_reasons,e.evaluated_at,
          r.dataset_checksum,p.policy_version calibration_policy_version,
          oru.policy_version opportunity_policy_version,s.model_version similarity_model_version,
          v.schema_version feature_version,v.quality_metrics feature_contributions,
          (SELECT o.model_version FROM historical_outcomes_v2 o WHERE o.anchor_bar_revision_id=v.anchor_bar_revision_id ORDER BY o.materialized_at DESC LIMIT 1) outcome_model_version
          FROM recommendation_evaluations_v2 e JOIN calibration_runs_v2 r ON r.run_id=e.calibration_run_id
          JOIN calibration_policies_v2 p ON p.policy_id=e.policy_id JOIN opportunity_candidates_v2 c ON c.candidate_id=e.candidate_id
          JOIN opportunity_runs_v2 oru ON oru.run_id=c.run_id JOIN similarity_runs_v2 s ON s.run_id=c.similarity_run_id
          JOIN feature_vectors_v2 v ON v.vector_id=c.query_vector_id WHERE e.evaluation_id=%s""",(evaluation_id,))
        return rows[0] if rows else None

    def snapshot(self,recommendation_id):
        rows=self._dicts('SELECT * FROM recommendation_snapshots_v2 WHERE recommendation_id=%s',(recommendation_id,));return rows[0] if rows else None

    def path(self,snapshot,as_of):
        return self._dicts("""SELECT b.bar_revision_id,b.manifest_id,b.bar_open_at,b.bar_close_at observed_at,b.available_at,b.open_price,b.high_price,b.low_price,b.close_price
          FROM historical_bar_revisions b WHERE b.instrument_id=%s AND b.acceptance_state='ACCEPTED' AND b.adjustment_state='RAW'
          AND b.bar_close_at>%s AND b.available_at<=%s AND NOT EXISTS(SELECT 1 FROM historical_bar_revisions b2 WHERE b2.instrument_id=b.instrument_id
          AND b2.interval_code=b.interval_code AND b2.bar_open_at=b.bar_open_at AND b2.adjustment_state=b.adjustment_state AND b2.acceptance_state='ACCEPTED'
          AND b2.available_at<=%s AND (b2.revision_number,b2.bar_revision_id)>(b.revision_number,b.bar_revision_id)) ORDER BY b.bar_close_at,b.bar_revision_id""",
          (snapshot['instrument_id'],snapshot['recommendation_at'],as_of,as_of))

    def user_fill(self,recommendation_id,as_of):
        rows=self._dicts("SELECT * FROM recommendation_fills_v2 WHERE recommendation_id=%s AND fill_type='USER_RECORDED' AND fill_at<=%s ORDER BY fill_at LIMIT 1",(recommendation_id,as_of));return rows[0] if rows else None

    def persist_fill(self,fill):
        with get_connection() as c:
            with c.cursor() as q:self._insert(q,'recommendation_fills_v2',fill,set())
            c.commit()

    def metric_records(self,window_start,window_end):
        return self._dicts("""SELECT s.*,o.state outcome_state,o.terminal_reason,o.mfe_pct,o.mae_pct,o.net_return_pct,o.failure_classification,
          o.fill_id,f.fill_quality,f.slippage_pct FROM recommendation_snapshots_v2 s LEFT JOIN LATERAL(SELECT * FROM recommendation_outcomes_v2 x
          WHERE x.recommendation_id=s.recommendation_id AND x.as_of<=%s ORDER BY x.as_of DESC LIMIT 1)o ON TRUE
          LEFT JOIN recommendation_fills_v2 f ON f.fill_id=o.fill_id WHERE s.recommendation_at BETWEEN %s AND %s ORDER BY s.recommendation_at,s.recommendation_id""",
          (window_end,window_start,window_end))

    def persist_snapshot(self,policy,prepared):
        with get_connection() as c:
            try:
                with c.cursor() as q:
                    q.execute('INSERT INTO live_validation_policies(policy_version,policy_checksum,policy,created_at) VALUES(%s,%s,%s,%s) ON CONFLICT(policy_version) DO NOTHING',(policy['policy_version'],policy['policy_checksum'],Jsonb(policy['policy']),prepared['snapshotted_at']))
                    q.execute('SELECT policy_checksum FROM live_validation_policies WHERE policy_version=%s',(policy['policy_version'],))
                    if q.fetchone()[0]!=policy['policy_checksum']:raise ValueError('Live-validation policy is immutable.')
                    self._insert(q,'recommendation_snapshots_v2',prepared,{'target_prices','reasons_for','reasons_against','feature_contributions','lineage'})
                c.commit()
            except Exception:c.rollback();raise

    def persist_validation(self,observations,fill,outcome,classification):
        with get_connection() as c:
            try:
                with c.cursor() as q:
                    for row in observations:self._insert(q,'recommendation_validation_observations_v2',row,set())
                    if fill:self._insert(q,'recommendation_fills_v2',fill,set())
                    self._insert(q,'recommendation_outcomes_v2',outcome,set())
                    self._insert(q,'recommendation_failure_classifications_v2',classification,{'evidence'})
                c.commit()
            except Exception:c.rollback();raise

    def persist_metrics(self,policy,run,segments):
        with get_connection() as c:
            with c.cursor() as q:
                q.execute('INSERT INTO live_validation_policies(policy_version,policy_checksum,policy,created_at) VALUES(%s,%s,%s,%s) ON CONFLICT(policy_version) DO NOTHING',(policy['policy_version'],policy['policy_checksum'],Jsonb(policy['policy']),run['created_at']))
                q.execute('SELECT policy_checksum FROM live_validation_policies WHERE policy_version=%s',(policy['policy_version'],))
                if q.fetchone()[0]!=policy['policy_checksum']:raise ValueError('Live-validation policy is immutable.')
                self._insert(q,'validation_metric_runs_v2',run,set())
                for row in segments:self._insert(q,'validation_metrics_v2',row,{'metrics'})
            c.commit()

    def persist_drift(self,policy,evaluation,suspension):
        with get_connection() as c:
            with c.cursor() as q:
                q.execute('INSERT INTO live_validation_policies(policy_version,policy_checksum,policy,created_at) VALUES(%s,%s,%s,%s) ON CONFLICT(policy_version) DO NOTHING',(policy['policy_version'],policy['policy_checksum'],Jsonb(policy['policy']),evaluation['created_at']))
                q.execute('SELECT policy_checksum FROM live_validation_policies WHERE policy_version=%s',(policy['policy_version'],))
                if q.fetchone()[0]!=policy['policy_checksum']:raise ValueError('Live-validation policy is immutable.')
                self._insert(q,'validation_drift_evaluations_v2',evaluation,{'drift_metrics','reasons'})
                if suspension:self._insert(q,'validation_policy_suspensions_v2',suspension,set())
            c.commit()

    @staticmethod
    def _insert(q,table,row,json_keys):
        keys=tuple(row);values=tuple(Jsonb(json.loads(json.dumps(v,default=str))) if k in json_keys else v for k,v in row.items())
        q.execute(f"INSERT INTO {table}({','.join(keys)}) VALUES({','.join(['%s']*len(keys))}) ON CONFLICT DO NOTHING",values)

    @staticmethod
    def _dicts(sql,params):
        with get_connection() as c:
            with c.cursor() as q:q.execute(sql,params);names=[x.name for x in q.description or ()];return [dict(zip(names,row,strict=True)) for row in q.fetchall()]
