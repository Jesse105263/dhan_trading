from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from services.database import get_connection
from services.feature_store_v2_models import FeatureAnchorV2


class FeatureStoreV2Repository:
    def anchors(self,as_of,limit:int,after_at=None,after_id=None)->list[FeatureAnchorV2]:
        rows=self._fetch("""SELECT b.bar_revision_id,b.manifest_id,b.instrument_id,i.instrument_class,r.underlying_instrument_id,
            b.interval_code,b.session_date,b.bar_open_at,b.bar_close_at,b.available_at,r.expiry,
            b.open_price,b.high_price,b.low_price,b.close_price,b.volume,b.open_interest,b.bid_price,b.ask_price
            FROM historical_bar_revisions b JOIN canonical_instruments i ON i.instrument_id=b.instrument_id
            JOIN canonical_instrument_revisions r ON r.instrument_id=i.instrument_id AND r.available_at<=b.available_at
              AND NOT EXISTS(SELECT 1 FROM canonical_instrument_revisions r2 WHERE r2.instrument_id=r.instrument_id
                AND r2.available_at<=b.available_at AND (r2.revision_number,r2.revision_id)>(r.revision_number,r.revision_id))
            WHERE b.adjustment_state='RAW' AND b.acceptance_state='ACCEPTED' AND b.available_at<=%s
              AND i.instrument_class IN ('EQUITY','INDEX','FUTURE','OPTION')
              AND NOT EXISTS(SELECT 1 FROM historical_bar_revisions b2 WHERE b2.instrument_id=b.instrument_id
                AND b2.interval_code=b.interval_code AND b2.bar_open_at=b.bar_open_at AND b2.adjustment_state=b.adjustment_state
                AND b2.acceptance_state='ACCEPTED' AND b2.available_at<=%s
                AND (b2.revision_number,b2.bar_revision_id)>(b.revision_number,b.bar_revision_id))
              AND (%s::timestamp IS NULL OR (b.available_at,b.bar_revision_id)>(%s,%s))
            ORDER BY b.available_at,b.bar_revision_id LIMIT %s""",(as_of,as_of,after_at,after_at,after_id,limit))
        return [FeatureAnchorV2(*row) for row in rows]

    def history(self,anchor:FeatureAnchorV2,limit:int=64)->list[FeatureAnchorV2]:
        rows=self._fetch("""SELECT b.bar_revision_id,b.manifest_id,b.instrument_id,i.instrument_class,r.underlying_instrument_id,
            b.interval_code,b.session_date,b.bar_open_at,b.bar_close_at,b.available_at,r.expiry,
            b.open_price,b.high_price,b.low_price,b.close_price,b.volume,b.open_interest,b.bid_price,b.ask_price
            FROM historical_bar_revisions b JOIN canonical_instruments i ON i.instrument_id=b.instrument_id
            JOIN canonical_instrument_revisions r ON r.instrument_id=i.instrument_id AND r.available_at<=%s
              AND NOT EXISTS(SELECT 1 FROM canonical_instrument_revisions r2 WHERE r2.instrument_id=r.instrument_id
                AND r2.available_at<=%s AND (r2.revision_number,r2.revision_id)>(r.revision_number,r.revision_id))
            WHERE b.instrument_id=%s AND b.interval_code=%s AND b.adjustment_state='RAW'
              AND b.acceptance_state='ACCEPTED' AND b.bar_close_at<=%s AND b.available_at<=%s
              AND NOT EXISTS(SELECT 1 FROM historical_bar_revisions b2 WHERE b2.instrument_id=b.instrument_id
                AND b2.interval_code=b.interval_code AND b2.bar_open_at=b.bar_open_at AND b2.adjustment_state=b.adjustment_state
                AND b2.acceptance_state='ACCEPTED' AND b2.available_at<=%s
                AND (b2.revision_number,b2.bar_revision_id)>(b.revision_number,b.bar_revision_id))
            ORDER BY b.bar_close_at DESC,b.bar_revision_id DESC LIMIT %s""",
            (anchor.available_at,anchor.available_at,anchor.instrument_id,anchor.interval_code,anchor.bar_close_at,anchor.available_at,anchor.available_at,limit))
        return [FeatureAnchorV2(*row) for row in reversed(rows)]

    def persist(self,prepared:dict[str,Any])->None:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""INSERT INTO feature_schema_versions_v2(schema_version,definition_checksum,compatible_schema_versions,compatible_outcome_models,created_at)
                        VALUES(%s,%s,%s,%s,%s) ON CONFLICT(schema_version) DO NOTHING""",
                        (prepared['schema_version'],prepared['definition_checksum'],Jsonb(prepared['compatible_schema_versions']),Jsonb(prepared['compatible_outcome_models']),prepared['started_at']))
                    cursor.execute("SELECT definition_checksum FROM feature_schema_versions_v2 WHERE schema_version=%s",(prepared['schema_version'],))
                    if cursor.fetchone()[0]!=prepared['definition_checksum']: raise ValueError("Feature schema version is immutable.")
                    for definition in prepared['definitions']:
                        cursor.execute("""INSERT INTO feature_definitions_v2(definition_id,schema_version,feature_name,feature_family,formula,missing_policy,
                            normalization_policy,minimum_history,description,definition_checksum) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT(definition_id) DO NOTHING""",tuple(definition.values()))
                    counts=prepared['counts']
                    cursor.execute("""INSERT INTO feature_materialization_runs_v2(run_id,schema_version,as_of,definition_checksum,anchor_count,vector_count,
                        complete_count,partial_count,insufficient_count,started_at,completed_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(run_id) DO NOTHING""",(prepared['run_id'],prepared['schema_version'],prepared['as_of'],prepared['definition_checksum'],
                        prepared['anchor_count'],counts['vector_count'],counts['complete_count'],counts['partial_count'],counts['insufficient_count'],prepared['started_at'],prepared['completed_at']))
                    for vector,values in prepared['vectors']:
                        keys=tuple(vector)
                        vector_values=tuple(Jsonb(value) if key=='quality_metrics' else value for key,value in vector.items())
                        cursor.execute(f"INSERT INTO feature_vectors_v2({','.join(keys)}) VALUES({','.join(['%s']*len(keys))}) ON CONFLICT(vector_id) DO NOTHING",vector_values)
                        for value in values:
                            cursor.execute("""INSERT INTO feature_values_v2(vector_id,definition_id,feature_name,numeric_value,missing_reason,source_revision_ids,value_checksum)
                                VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(vector_id,definition_id) DO NOTHING""",
                                (vector['vector_id'],value['definition_id'],value['feature_name'],value['numeric_value'],value['missing_reason'],Jsonb(value['source_revision_ids']),value['value_checksum']))
                connection.commit()
            except Exception: connection.rollback(); raise

    @staticmethod
    def _fetch(query:str,parameters:tuple[Any,...])->list[tuple[Any,...]]:
        with get_connection() as connection:
            with connection.cursor() as cursor: cursor.execute(query,parameters); return cursor.fetchall()
