from psycopg.types.json import Jsonb

from services.database import get_connection


class SimilarityV2Repository:
    def vector(self, vector_id):
        rows = self._vectors("WHERE v.vector_id=%s", (vector_id,))
        return rows[0] if rows else None

    def candidates(self, query, cutoff, policy):
        clauses = ["v.vector_id<>%s", "v.schema_version=%s", "v.observed_at<%s", "v.available_at<=%s", "v.coverage_percentage>=%s"]
        values = [query["vector_id"], query["schema_version"], cutoff, cutoff, policy.minimum_coverage_pct]
        if policy.same_subject_type:
            clauses.append("v.subject_type=%s"); values.append(query["subject_type"])
        if policy.same_interval:
            clauses.append("v.interval_code=%s"); values.append(query["interval_code"])
        if policy.maximum_age_days is not None:
            clauses.append("v.observed_at>=%s::timestamp-(%s*INTERVAL '1 day')"); values.extend((cutoff, policy.maximum_age_days))
        return self._vectors("WHERE " + " AND ".join(clauses), tuple(values))

    def outcomes(self, vectors, query_observed_at):
        if not vectors: return {}
        ids = [item["anchor_bar_revision_id"] for item in vectors]
        rows = self._dicts("""SELECT DISTINCT ON (anchor_bar_revision_id) outcome_id,anchor_bar_revision_id,
            model_version,horizon_code,outcome_state,net_return_pct,terminal_at,lineage_checksum
            FROM historical_outcomes_v2 WHERE anchor_bar_revision_id=ANY(%s)
              AND outcome_state='COMPLETE' AND terminal_at<=%s
            ORDER BY anchor_bar_revision_id,model_version,horizon_code,outcome_id""", (ids, query_observed_at))
        return {item["anchor_bar_revision_id"]: item for item in rows}

    def persist(self, prepared):
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""INSERT INTO similarity_models_v2(model_version,policy_checksum,feature_schema_version,
                        compatible_outcome_model,policy,created_at) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(model_version) DO NOTHING""",
                        (prepared["model_version"], prepared["policy_checksum"], prepared["feature_schema_version"],
                         prepared["compatible_outcome_model"], Jsonb(prepared["policy"]), prepared["started_at"]))
                    cursor.execute("SELECT policy_checksum FROM similarity_models_v2 WHERE model_version=%s", (prepared["model_version"],))
                    if cursor.fetchone()[0] != prepared["policy_checksum"]: raise ValueError("Similarity model version is immutable.")
                    run = prepared["run"]
                    cursor.execute("""INSERT INTO similarity_runs_v2(run_id,model_version,query_vector_id,query_observed_at,cutoff_at,
                        policy_checksum,candidate_count,match_count,evidence_state,quality_metrics,lineage_checksum,started_at,completed_at)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(run_id) DO NOTHING""",
                        (run["run_id"], run["model_version"], run["query_vector_id"], run["query_observed_at"], run["cutoff_at"],
                         run["policy_checksum"], run["candidate_count"], run["match_count"], run["evidence_state"],
                         Jsonb(run["quality_metrics"]), run["lineage_checksum"], run["started_at"], run["completed_at"]))
                    for match in prepared["matches"]:
                        cursor.execute("""INSERT INTO similarity_matches_v2(match_id,run_id,rank_position,matched_vector_id,
                            matched_outcome_id,distance,similarity_score,evidence_quality_score,shared_feature_count,
                            feature_diagnostics,filter_diagnostics,lineage_checksum) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT(match_id) DO NOTHING""", (match["match_id"], match["run_id"], match["rank_position"],
                            match["matched_vector_id"], match["matched_outcome_id"], match["distance"], match["similarity_score"],
                            match["evidence_quality_score"], match["shared_feature_count"], Jsonb(match["feature_diagnostics"]),
                            Jsonb(match["filter_diagnostics"]), match["lineage_checksum"]))
                connection.commit()
            except Exception:
                connection.rollback(); raise

    def _vectors(self, where, parameters):
        return self._dicts(f"""SELECT v.*,COALESCE(jsonb_object_agg(x.feature_name,x.numeric_value)
            FILTER(WHERE x.numeric_value IS NOT NULL),'{{}}') features,
            COALESCE(jsonb_object_agg(x.feature_name,d.feature_family),'{{}}') families
            FROM feature_vectors_v2 v LEFT JOIN feature_values_v2 x ON x.vector_id=v.vector_id
            LEFT JOIN feature_definitions_v2 d ON d.definition_id=x.definition_id {where}
            GROUP BY v.vector_id ORDER BY v.observed_at,v.vector_id""", parameters)

    @staticmethod
    def _dicts(query, parameters):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters); names=[item.name for item in cursor.description or ()]
                return [dict(zip(names,row,strict=True)) for row in cursor.fetchall()]
