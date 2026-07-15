from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from services.database import get_connection
from services.outcome_v2_models import OutcomeAnchor, OutcomePathBar


class OutcomeV2Repository:
    def anchors(self, as_of, limit: int, after_at=None, after_id=None) -> list[OutcomeAnchor]:
        rows=self._fetch("""SELECT b.bar_revision_id,b.instrument_id,i.instrument_class,r.underlying_instrument_id,
            b.interval_code,b.session_date,b.bar_close_at,b.available_at,r.expiry,b.close_price,b.manifest_id,b.adjustment_state
            FROM historical_bar_revisions b JOIN canonical_instruments i ON i.instrument_id=b.instrument_id
            JOIN canonical_instrument_revisions r ON r.instrument_id=i.instrument_id
              AND r.available_at<=%s AND NOT EXISTS(SELECT 1 FROM canonical_instrument_revisions r2
                WHERE r2.instrument_id=r.instrument_id AND r2.available_at<=%s AND (r2.revision_number,r2.revision_id)>(r.revision_number,r.revision_id))
            WHERE b.acceptance_state='ACCEPTED' AND b.adjustment_state='RAW' AND b.available_at<=%s
              AND i.instrument_class IN ('EQUITY','INDEX','OPTION')
              AND NOT EXISTS(SELECT 1 FROM historical_bar_revisions b2 WHERE b2.instrument_id=b.instrument_id
                AND b2.interval_code=b.interval_code AND b2.bar_open_at=b.bar_open_at AND b2.adjustment_state=b.adjustment_state
                AND b2.acceptance_state='ACCEPTED' AND b2.available_at<=%s
                AND (b2.revision_number,b2.bar_revision_id)>(b.revision_number,b.bar_revision_id))
              AND (%s::timestamp IS NULL OR (b.available_at,b.bar_revision_id)>(%s,%s))
            ORDER BY b.available_at,b.bar_revision_id LIMIT %s""",(as_of,as_of,as_of,as_of,after_at,after_at,after_id,limit))
        return [OutcomeAnchor(*row[:11]) for row in rows]

    def path(self, anchor: OutcomeAnchor, as_of) -> list[OutcomePathBar]:
        rows=self._fetch("""SELECT b.bar_revision_id,b.manifest_id,b.session_date,b.bar_open_at,b.bar_close_at,b.available_at,
            b.open_price,b.high_price,b.low_price,b.close_price FROM historical_bar_revisions b
            WHERE b.instrument_id=%s AND b.interval_code=%s AND b.adjustment_state='RAW' AND b.acceptance_state='ACCEPTED'
              AND b.bar_close_at>%s AND b.available_at<=%s
              AND NOT EXISTS(SELECT 1 FROM historical_bar_revisions b2 WHERE b2.instrument_id=b.instrument_id
                AND b2.interval_code=b.interval_code AND b2.bar_open_at=b.bar_open_at AND b2.adjustment_state=b.adjustment_state
                AND b2.acceptance_state='ACCEPTED' AND b2.available_at<=%s
                AND (b2.revision_number,b2.bar_revision_id)>(b.revision_number,b.bar_revision_id))
            ORDER BY b.bar_close_at,b.bar_revision_id LIMIT 10000""",(anchor.instrument_id,anchor.interval_code,anchor.bar_close_at,as_of,as_of))
        return [OutcomePathBar(*row) for row in rows]

    def corporate_actions(self, instrument_id, start_at, end_at, as_of) -> list[dict[str,Any]]:
        return self._dicts("""SELECT a.action_revision_id,a.action_type,a.status,a.ex_date,a.normalized_terms,a.available_at,a.manifest_id
            FROM corporate_action_revisions a WHERE a.instrument_id=%s
              AND a.available_at<=%s AND a.ex_date BETWEEN %s::date AND %s::date
              AND NOT EXISTS(SELECT 1 FROM corporate_action_revisions a2
                WHERE a2.action_identity=a.action_identity AND a2.available_at<=%s
                  AND (a2.revision_number,a2.action_revision_id)>(a.revision_number,a.action_revision_id))
              AND a.status IN ('CONFIRMED','REVISED') ORDER BY a.ex_date,a.action_revision_id""",
            (instrument_id,as_of,start_at,end_at,as_of))

    def persist(self, prepared: dict[str,Any]) -> None:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""INSERT INTO outcome_model_versions_v2(model_version,policy_checksum,policy,created_at)
                        VALUES(%s,%s,%s,%s) ON CONFLICT(model_version) DO NOTHING""",
                        (prepared['model_version'],prepared['policy_checksum'],Jsonb(prepared['policy']),prepared['started_at']))
                    cursor.execute("SELECT policy_checksum FROM outcome_model_versions_v2 WHERE model_version=%s",(prepared['model_version'],))
                    if cursor.fetchone()[0] != prepared['policy_checksum']: raise ValueError("Outcome model version policy is immutable.")
                    counts=prepared['counts']
                    cursor.execute("""INSERT INTO outcome_materialization_runs_v2(run_id,model_version,as_of,policy_checksum,
                        anchor_count,outcome_count,complete_count,unknown_count,insufficient_count,ambiguous_count,started_at,completed_at)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(run_id) DO NOTHING""",
                        (prepared['run_id'],prepared['model_version'],prepared['as_of'],prepared['policy_checksum'],prepared['anchor_count'],
                         counts['outcome_count'],counts['complete_count'],counts['unknown_count'],counts['insufficient_count'],counts['ambiguous_count'],
                         prepared['started_at'],prepared['completed_at']))
                    for outcome,path in prepared['outcomes']:
                        keys=tuple(outcome)
                        cursor.execute(f"INSERT INTO historical_outcomes_v2({','.join(keys)}) VALUES({','.join(['%s']*len(keys))}) ON CONFLICT(outcome_id) DO NOTHING",tuple(outcome.values()))
                        for sequence,bar in enumerate(path,1):
                            cursor.execute("""INSERT INTO historical_outcome_path_v2(outcome_id,sequence_number,bar_revision_id,manifest_id,bar_open_at,bar_close_at,available_at)
                                VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(outcome_id,sequence_number) DO NOTHING""",
                                (outcome['outcome_id'],sequence,bar.bar_revision_id,bar.manifest_id,bar.bar_open_at,bar.bar_close_at,bar.available_at))
                connection.commit()
            except Exception:
                connection.rollback(); raise

    def statistics(self, model_version: str, horizon_code: str) -> dict[str,Any]:
        rows=self._dicts("""WITH population AS (SELECT net_return_pct FROM historical_outcomes_v2
            WHERE model_version=%s AND horizon_code=%s AND outcome_state='COMPLETE' AND net_return_pct IS NOT NULL)
            SELECT COUNT(*) outcome_count,AVG(net_return_pct) expectancy,
              AVG(net_return_pct) FILTER(WHERE net_return_pct>0) average_win,
              ABS(AVG(net_return_pct) FILTER(WHERE net_return_pct<0)) average_loss,
              CASE WHEN AVG(net_return_pct) FILTER(WHERE net_return_pct<0)<0 THEN
                AVG(net_return_pct) FILTER(WHERE net_return_pct>0)/ABS(AVG(net_return_pct) FILTER(WHERE net_return_pct<0)) END payoff_ratio
            FROM population""",(model_version,horizon_code))
        return rows[0]

    @staticmethod
    def _fetch(query: str, parameters: tuple[Any,...]) -> list[tuple[Any,...]]:
        with get_connection() as connection:
            with connection.cursor() as cursor: cursor.execute(query,parameters); return cursor.fetchall()

    @staticmethod
    def _dicts(query: str, parameters: tuple[Any,...]) -> list[dict[str,Any]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query,parameters); names=[column.name for column in cursor.description or ()]
                return [dict(zip(names,row,strict=True)) for row in cursor.fetchall()]
