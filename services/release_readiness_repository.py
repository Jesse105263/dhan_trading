from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from services.database import get_connection
from services.release_readiness_models import AppliedMigration, AuditMetric


class ReleaseReadinessRepository:
    """SELECT-only database evidence for platform release checks."""

    def database_identity(self) -> tuple[str, str, bool]:
        row = self._fetch_one(
            "SELECT current_database(), current_user, pg_is_in_recovery()",
        )
        return str(row[0]), str(row[1]), bool(row[2])

    def applied_migrations(self) -> tuple[AppliedMigration, ...]:
        rows = self._fetch_all(
            """
            SELECT version, filename, checksum
            FROM schema_migrations
            ORDER BY version
            """
        )
        return tuple(
            AppliedMigration(str(row[0]), str(row[1]), str(row[2]))
            for row in rows
        )

    def audit_metrics(self) -> Mapping[str, AuditMetric]:
        return {
            "option_chain_lineage": self._option_chain_lineage(),
            "decision_lineage": self._decision_lineage(),
            "evaluation_lineage": self._evaluation_lineage(),
            "alert_lineage": self._alert_lineage(),
            "paper_lineage": self._paper_lineage(),
            "operational_state": self._operational_state(),
            "feature_store_lineage": self._feature_store_lineage(),
            "historical_outcome_lineage": self._historical_outcome_lineage(),
            "similarity_lineage_and_leakage": self._similarity_lineage_and_leakage(),
            "trade_opportunity_lineage": self._trade_opportunity_lineage(),
            "news_event_lineage_and_leakage": self._news_event_lineage_and_leakage(),
            "analyst_evidence_grounding": self._analyst_evidence_grounding(),
            "historical_data_foundation_lineage": self._historical_data_foundation_lineage(),
            "continuous_collection_lineage": self._continuous_collection_lineage(),
            "outcome_v2_lineage_and_leakage": self._outcome_v2_lineage_and_leakage(),
            "feature_store_v2_lineage_and_leakage": self._feature_store_v2_lineage_and_leakage(),
            "similarity_v2_lineage_and_leakage": self._similarity_v2_lineage_and_leakage(),
            "opportunity_v2_lineage_and_leakage": self._opportunity_v2_lineage_and_leakage(),
            "calibration_v2_lineage_and_leakage": self._calibration_v2_lineage_and_leakage(),
            "execution_schema_boundary": self._execution_schema_boundary(),
        }

    def _feature_store_lineage(self) -> AuditMetric:
        row = self._fetch_one("""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE
                v.analytics_id <> a.analytics_id OR v.underlying_symbol <> a.underlying_symbol
                OR v.expiry <> a.expiry OR v.observed_at <> a.source_captured_at
                OR counts.actual_count <> v.feature_count
                OR counts.missing_count <> v.missing_feature_count
                OR (v.change_id IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM option_analytics_changes c
                    WHERE c.change_id=v.change_id AND c.current_analytics_id=v.analytics_id))
                OR (v.ranking_id IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM option_rankings r
                    WHERE r.ranking_id=v.ranking_id AND r.analytics_id=v.analytics_id)))
            FROM feature_store_vectors v
            JOIN option_chain_analytics a ON a.analytics_id=v.analytics_id
            JOIN LATERAL (SELECT COUNT(*) actual_count,
                COUNT(*) FILTER (WHERE numeric_value IS NULL) missing_count
                FROM feature_store_values fv WHERE fv.vector_id=v.vector_id) counts ON TRUE
        """)
        return self._metric("feature_store_lineage", row)

    def _historical_outcome_lineage(self) -> AuditMetric:
        row = self._fetch_one("""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE
                o.analytics_id <> v.analytics_id OR o.underlying_symbol <> v.underlying_symbol
                OR o.expiry <> v.expiry OR o.observed_at <> v.observed_at
                OR (o.ranking_id IS DISTINCT FROM v.ranking_id)
                OR (o.terminal_vector_id IS NOT NULL AND (
                    t.observed_at <= o.observed_at OR t.observed_at <> o.terminal_observed_at
                    OR t.underlying_symbol <> o.underlying_symbol OR t.expiry <> o.expiry))
                OR (o.outcome_type='EXPIRY_COMPLETE' AND (o.won IS NULL OR o.closing_return IS NULL))
                OR (o.outcome_type<>'EXPIRY_COMPLETE' AND o.won IS NOT NULL))
            FROM historical_outcomes o
            JOIN feature_store_vectors v ON v.vector_id=o.vector_id
            LEFT JOIN feature_store_vectors t ON t.vector_id=o.terminal_vector_id
        """)
        return self._metric("historical_outcome_lineage", row)

    def _similarity_lineage_and_leakage(self) -> AuditMetric:
        row = self._fetch_one("""
            WITH audited AS (
                SELECT r.run_id::text entity_id, (
                    r.query_analytics_id <> q.analytics_id
                    OR r.query_ranking_id IS DISTINCT FROM q.ranking_id
                    OR COALESCE((r.configuration->>'outcomes_used_as_inputs')::boolean, TRUE)
                    OR r.match_count <> (SELECT COUNT(*) FROM similarity_matches m WHERE m.run_id=r.run_id)
                ) violation FROM similarity_runs r
                JOIN feature_store_vectors q ON q.vector_id=r.query_vector_id
                UNION ALL
                SELECT m.match_id::text, (
                    m.matched_vector_id=r.query_vector_id OR v.observed_at >= q.observed_at
                    OR (m.matched_outcome_id IS NOT NULL AND o.vector_id <> m.matched_vector_id)
                ) FROM similarity_matches m JOIN similarity_runs r ON r.run_id=m.run_id
                JOIN feature_store_vectors q ON q.vector_id=r.query_vector_id
                JOIN feature_store_vectors v ON v.vector_id=m.matched_vector_id
                LEFT JOIN historical_outcomes o ON o.outcome_id=m.matched_outcome_id
            ) SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
        """)
        return self._metric("similarity_lineage_and_leakage", row)

    def _trade_opportunity_lineage(self) -> AuditMetric:
        row = self._fetch_one("""
            WITH audited AS (
                SELECT o.opportunity_id::text entity_id, (
                    o.query_vector_id <> s.query_vector_id OR o.query_analytics_id <> s.query_analytics_id
                    OR o.query_ranking_id IS DISTINCT FROM s.query_ranking_id
                    OR o.underlying_symbol <> v.underlying_symbol OR o.expiry <> v.expiry
                    OR o.observed_at <> v.observed_at
                    OR (o.state<>'ELIGIBLE' AND (o.entry_zone_low IS NOT NULL OR o.entry_zone_high IS NOT NULL
                        OR o.stop_zone IS NOT NULL OR jsonb_array_length(o.target_zones)>0
                        OR o.expected_value IS NOT NULL OR o.historical_win_rate IS NOT NULL OR o.risk_reward IS NOT NULL))
                ) violation FROM trade_opportunities o JOIN similarity_runs s ON s.run_id=o.similarity_run_id
                JOIN feature_store_vectors v ON v.vector_id=o.query_vector_id
                UNION ALL
                SELECT e.similarity_match_id::text, (
                    e.opportunity_id <> o.opportunity_id OR e.matched_vector_id <> m.matched_vector_id
                    OR e.matched_outcome_id IS DISTINCT FROM m.matched_outcome_id
                    OR h.vector_id <> e.matched_vector_id
                ) FROM trade_opportunity_evidence e JOIN trade_opportunities o ON o.opportunity_id=e.opportunity_id
                JOIN similarity_matches m ON m.match_id=e.similarity_match_id AND m.run_id=o.similarity_run_id
                JOIN historical_outcomes h ON h.outcome_id=e.matched_outcome_id
            ) SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
        """)
        return self._metric("trade_opportunity_lineage", row)

    def _news_event_lineage_and_leakage(self) -> AuditMetric:
        row = self._fetch_one("""
            WITH audited AS (
                SELECT c.event_id::text || ':' || c.vector_id::text entity_id, (
                    (c.predictive_eligible AND (e.published_at IS NULL OR e.published_at > v.observed_at))
                    OR (c.outcome_id IS NOT NULL AND o.vector_id <> c.vector_id)
                ) violation FROM market_event_vector_context c JOIN market_events e ON e.event_id=c.event_id
                JOIN feature_store_vectors v ON v.vector_id=c.vector_id
                LEFT JOIN historical_outcomes o ON o.outcome_id=c.outcome_id
                UNION ALL
                SELECT c.event_id::text || ':' || c.opportunity_id::text, (
                    e.published_at IS NULL OR e.published_at > o.observed_at
                ) FROM market_event_opportunity_context c JOIN market_events e ON e.event_id=c.event_id
                JOIN trade_opportunities o ON o.opportunity_id=c.opportunity_id
                UNION ALL
                SELECT c.event_id::text || ':' || c.similarity_run_id::text, (
                    c.query_vector_id <> r.query_vector_id OR NOT EXISTS (
                        SELECT 1 FROM market_event_vector_context v
                        WHERE v.event_id=c.event_id AND v.vector_id=c.query_vector_id AND v.predictive_eligible)
                ) FROM market_event_similarity_context c JOIN similarity_runs r ON r.run_id=c.similarity_run_id
            ) SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
        """)
        return self._metric("news_event_lineage_and_leakage", row)

    def _analyst_evidence_grounding(self) -> AuditMetric:
        row = self._fetch_one("""
            SELECT COUNT(*), COUNT(*) FILTER (WHERE
                NOT EXISTS (SELECT 1 FROM feature_store_vectors v WHERE v.vector_id=o.query_vector_id)
                OR NOT EXISTS (SELECT 1 FROM option_chain_analytics a WHERE a.analytics_id=o.query_analytics_id)
                OR NOT EXISTS (SELECT 1 FROM similarity_runs s WHERE s.run_id=o.similarity_run_id))
            FROM trade_opportunities o
        """)
        return self._metric("analyst_evidence_grounding", row)

    def _historical_data_foundation_lineage(self) -> AuditMetric:
        row = self._fetch_one("""
            WITH audited AS (
                SELECT m.manifest_id::text entity_id, (
                    m.source_id <> p.source_id OR m.source_id <> raw.source_id
                    OR m.policy_id <> raw.policy_id
                    OR m.payload_checksum <> raw.payload_checksum
                    OR raw.byte_count <> octet_length(raw.payload_bytes)
                    OR p.raw_retention <> 'ALLOWED'
                    OR p.normalized_retention <> 'ALLOWED'
                ) violation
                FROM historical_raw_manifests m
                JOIN historical_raw_payloads raw ON raw.payload_id=m.payload_id
                JOIN historical_retention_policies p ON p.policy_id=m.policy_id
                UNION ALL
                SELECT b.bar_revision_id::text, (
                    b.available_at < b.event_at
                    OR (b.supersedes_revision_id IS NOT NULL AND NOT EXISTS (
                        SELECT 1 FROM historical_bar_revisions previous
                        WHERE previous.bar_revision_id=b.supersedes_revision_id
                          AND previous.instrument_id=b.instrument_id
                          AND previous.interval_code=b.interval_code
                          AND previous.bar_open_at=b.bar_open_at
                          AND previous.adjustment_state=b.adjustment_state
                          AND previous.revision_number < b.revision_number))
                ) FROM historical_bar_revisions b
                UNION ALL
                SELECT r.revision_id::text, (
                    r.supersedes_revision_id IS NOT NULL AND NOT EXISTS (
                        SELECT 1 FROM canonical_instrument_revisions previous
                        WHERE previous.revision_id=r.supersedes_revision_id
                          AND previous.instrument_id=r.instrument_id
                          AND previous.revision_number < r.revision_number)
                ) FROM canonical_instrument_revisions r
                UNION ALL
                SELECT a.action_revision_id::text, (
                    a.supersedes_revision_id IS NOT NULL AND NOT EXISTS (
                        SELECT 1 FROM corporate_action_revisions previous
                        WHERE previous.action_revision_id=a.supersedes_revision_id
                          AND previous.action_identity=a.action_identity
                          AND previous.revision_number < a.revision_number)
                ) FROM corporate_action_revisions a
            ) SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
        """)
        return self._metric("historical_data_foundation_lineage", row)

    def _continuous_collection_lineage(self) -> AuditMetric:
        row = self._fetch_one("""
            WITH audited AS (
                SELECT w.work_id::text entity_id, (
                    w.attempt_count <> (SELECT COUNT(*) FROM continuous_collection_attempts a WHERE a.work_id=w.work_id)
                    OR (w.status IN ('COMPLETED','PARTIAL') AND NOT EXISTS (
                        SELECT 1 FROM continuous_collection_attempts a
                        WHERE a.work_id=w.work_id AND a.payload_manifest_id IS NOT NULL))
                    OR (w.status IN ('FAILED','UNAVAILABLE') AND w.terminal_failure_state IS NULL)
                ) violation FROM continuous_collection_work_items w
                UNION ALL
                SELECT a.attempt_id::text, (
                    a.payload_manifest_id IS NOT NULL AND NOT EXISTS (
                        SELECT 1 FROM historical_raw_manifests m WHERE m.manifest_id=a.payload_manifest_id)
                ) FROM continuous_collection_attempts a
                UNION ALL
                SELECT r.repair_job_id::text, (
                    g.gap_id IS NULL OR (r.work_id IS NOT NULL AND NOT EXISTS (
                        SELECT 1 FROM continuous_collection_work_items w WHERE w.work_id=r.work_id))
                ) FROM continuous_repair_jobs r
                LEFT JOIN continuous_coverage_gaps g ON g.gap_id=r.gap_id
            ) SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
        """)
        return self._metric("continuous_collection_lineage", row)

    def _outcome_v2_lineage_and_leakage(self) -> AuditMetric:
        row=self._fetch_one("""
            WITH audited AS (
                SELECT o.outcome_id::text entity_id, (
                    o.policy_checksum<>m.policy_checksum OR o.policy_checksum<>r.policy_checksum
                    OR o.instrument_id<>b.instrument_id OR o.entry_manifest_id<>b.manifest_id
                    OR o.observed_at<>b.bar_close_at OR o.available_at<>b.available_at
                    OR o.available_at>r.as_of OR (o.terminal_at IS NOT NULL AND o.terminal_at<=o.observed_at)
                    OR (o.terminal_bar_revision_id IS NOT NULL AND (t.bar_revision_id IS NULL OR t.available_at>r.as_of))
                    OR o.path_observation_count<>(SELECT COUNT(*) FROM historical_outcome_path_v2 p WHERE p.outcome_id=o.outcome_id)
                    OR (o.outcome_state='COMPLETE' AND (o.net_return_pct IS NULL OR o.maximum_favourable_excursion_pct IS NULL OR o.maximum_adverse_excursion_pct IS NULL))
                    OR (o.outcome_state<>'COMPLETE' AND (o.gross_return_pct IS NOT NULL OR o.net_return_pct IS NOT NULL))
                ) AS violation FROM historical_outcomes_v2 o JOIN outcome_model_versions_v2 m ON m.model_version=o.model_version
                JOIN outcome_materialization_runs_v2 r ON r.run_id=o.run_id
                JOIN historical_bar_revisions b ON b.bar_revision_id=o.anchor_bar_revision_id
                LEFT JOIN historical_bar_revisions t ON t.bar_revision_id=o.terminal_bar_revision_id
                UNION ALL
                SELECT p.outcome_id::text||':'||p.sequence_number::text, (
                    p.bar_revision_id<>b.bar_revision_id OR p.manifest_id<>b.manifest_id
                    OR p.bar_close_at<=o.observed_at OR p.available_at>r.as_of
                ) FROM historical_outcome_path_v2 p JOIN historical_outcomes_v2 o ON o.outcome_id=p.outcome_id
                JOIN outcome_materialization_runs_v2 r ON r.run_id=o.run_id
                JOIN historical_bar_revisions b ON b.bar_revision_id=p.bar_revision_id
            ) SELECT COUNT(*),COUNT(*) FILTER(WHERE violation) FROM audited
        """)
        return self._metric("outcome_v2_lineage_and_leakage",row)

    def _feature_store_v2_lineage_and_leakage(self) -> AuditMetric:
        row=self._fetch_one("""
            WITH audited AS (
                SELECT v.vector_id::text entity_id, (
                    v.definition_checksum<>s.definition_checksum OR v.definition_checksum<>r.definition_checksum
                    OR v.schema_version<>r.schema_version OR v.instrument_id<>b.instrument_id
                    OR v.anchor_manifest_id<>b.manifest_id OR v.observed_at<>b.bar_close_at
                    OR v.available_at<>b.available_at OR v.available_at>r.as_of
                    OR v.feature_count<>(SELECT COUNT(*) FROM feature_values_v2 x WHERE x.vector_id=v.vector_id)
                    OR v.present_feature_count<>(SELECT COUNT(*) FROM feature_values_v2 x WHERE x.vector_id=v.vector_id AND x.numeric_value IS NOT NULL)
                    OR v.missing_feature_count<>(SELECT COUNT(*) FROM feature_values_v2 x WHERE x.vector_id=v.vector_id AND x.numeric_value IS NULL)
                ) violation FROM feature_vectors_v2 v JOIN feature_schema_versions_v2 s ON s.schema_version=v.schema_version
                JOIN feature_materialization_runs_v2 r ON r.run_id=v.run_id
                JOIN historical_bar_revisions b ON b.bar_revision_id=v.anchor_bar_revision_id
                UNION ALL
                SELECT x.vector_id::text||':'||x.feature_name, (
                    x.feature_name<>d.feature_name OR d.schema_version<>v.schema_version
                    OR (x.numeric_value IS NULL)<>(x.missing_reason IS NOT NULL)
                    OR EXISTS(SELECT 1 FROM jsonb_array_elements_text(x.source_revision_ids) source_id
                        LEFT JOIN historical_bar_revisions b ON b.bar_revision_id=source_id::uuid
                        WHERE b.bar_revision_id IS NULL OR b.bar_close_at>v.observed_at OR b.available_at>v.available_at)
                ) FROM feature_values_v2 x JOIN feature_vectors_v2 v ON v.vector_id=x.vector_id
                JOIN feature_definitions_v2 d ON d.definition_id=x.definition_id
            ) SELECT COUNT(*),COUNT(*) FILTER(WHERE violation) FROM audited
        """)
        return self._metric("feature_store_v2_lineage_and_leakage",row)

    def _similarity_v2_lineage_and_leakage(self) -> AuditMetric:
        row=self._fetch_one("""
            WITH audited AS (
                SELECT r.run_id::text entity_id, (
                    r.policy_checksum<>m.policy_checksum OR r.query_observed_at<>q.observed_at
                    OR r.cutoff_at>q.observed_at OR r.match_count<>(SELECT COUNT(*) FROM similarity_matches_v2 x WHERE x.run_id=r.run_id)
                ) violation FROM similarity_runs_v2 r JOIN similarity_models_v2 m ON m.model_version=r.model_version
                JOIN feature_vectors_v2 q ON q.vector_id=r.query_vector_id
                UNION ALL
                SELECT x.match_id::text, (
                    v.observed_at>=r.cutoff_at OR v.available_at>r.cutoff_at OR v.schema_version<>q.schema_version
                    OR (x.matched_outcome_id IS NOT NULL AND (o.anchor_bar_revision_id<>v.anchor_bar_revision_id OR o.terminal_at>r.query_observed_at))
                ) FROM similarity_matches_v2 x JOIN similarity_runs_v2 r ON r.run_id=x.run_id
                JOIN feature_vectors_v2 q ON q.vector_id=r.query_vector_id JOIN feature_vectors_v2 v ON v.vector_id=x.matched_vector_id
                LEFT JOIN historical_outcomes_v2 o ON o.outcome_id=x.matched_outcome_id
            ) SELECT COUNT(*),COUNT(*) FILTER(WHERE violation) FROM audited
        """)
        return self._metric("similarity_v2_lineage_and_leakage",row)

    def _opportunity_v2_lineage_and_leakage(self) -> AuditMetric:
        row=self._fetch_one("""WITH audited AS (
          SELECT o.candidate_id::text entity_id,(o.query_vector_id<>s.query_vector_id OR o.instrument_id<>v.instrument_id
            OR o.observed_at<>v.observed_at OR r.policy_checksum<>p.policy_checksum OR r.similarity_run_id<>o.similarity_run_id
            OR (o.state='PROVISIONAL' AND (o.option_type IS NULL OR o.entry_zone_low IS NULL OR o.net_expected_value_pct IS NULL))
            OR (o.state<>'PROVISIONAL' AND (o.entry_zone_low IS NOT NULL OR o.historical_win_rate IS NOT NULL OR o.net_expected_value_pct IS NOT NULL))) violation
          FROM opportunity_candidates_v2 o JOIN opportunity_runs_v2 r ON r.run_id=o.run_id JOIN opportunity_policies_v2 p ON p.policy_version=r.policy_version
          JOIN similarity_runs_v2 s ON s.run_id=o.similarity_run_id JOIN feature_vectors_v2 v ON v.vector_id=o.query_vector_id
          UNION ALL SELECT e.candidate_id::text||':'||e.match_id::text,(m.run_id<>o.similarity_run_id OR e.matched_vector_id<>m.matched_vector_id
            OR e.matched_outcome_id IS DISTINCT FROM m.matched_outcome_id OR v.observed_at>=s.cutoff_at
            OR (h.outcome_id IS NOT NULL AND h.terminal_at>s.query_observed_at))
          FROM opportunity_evidence_v2 e JOIN opportunity_candidates_v2 o ON o.candidate_id=e.candidate_id
          JOIN similarity_matches_v2 m ON m.match_id=e.match_id JOIN similarity_runs_v2 s ON s.run_id=m.run_id
          JOIN feature_vectors_v2 v ON v.vector_id=e.matched_vector_id LEFT JOIN historical_outcomes_v2 h ON h.outcome_id=e.matched_outcome_id)
          SELECT COUNT(*),COUNT(*) FILTER(WHERE violation) FROM audited""")
        return self._metric("opportunity_v2_lineage_and_leakage",row)

    def _calibration_v2_lineage_and_leakage(self) -> AuditMetric:
        row=self._fetch_one("""WITH audited AS (
          SELECT r.run_id::text entity_id,(r.policy_id<>p.policy_id OR r.calibration_sample_size<>(
            SELECT COUNT(*) FROM calibration_dataset_lineage_v2 l WHERE l.run_id=r.run_id AND l.included AND l.period_name='CALIBRATION')
            OR EXISTS(SELECT 1 FROM calibration_dataset_lineage_v2 l WHERE l.run_id=r.run_id AND l.included AND l.period_name NOT IN ('CALIBRATION','TEST'))
            OR EXISTS(SELECT 1 FROM calibration_dataset_lineage_v2 l WHERE l.run_id=r.run_id AND l.included AND l.terminal_at>r.cutoff_at)) violation
          FROM calibration_runs_v2 r JOIN calibration_policies_v2 p ON p.policy_id=r.policy_id
          UNION ALL SELECT e.evaluation_id::text,(e.policy_id<>r.policy_id OR e.dataset_lineage_checksum<>r.dataset_checksum
            OR e.eligible<>(e.state='ELIGIBLE') OR (e.eligible AND (e.calibrated_win_probability IS NULL OR e.conservative_expected_value IS NULL
              OR EXISTS(SELECT 1 FROM jsonb_each_text(e.gates) g WHERE g.value<>'true'))))
          FROM recommendation_evaluations_v2 e JOIN calibration_runs_v2 r ON r.run_id=e.calibration_run_id
          JOIN opportunity_candidates_v2 c ON c.candidate_id=e.candidate_id)
          SELECT COUNT(*),COUNT(*) FILTER(WHERE violation) FROM audited""")
        return self._metric("calibration_v2_lineage_and_leakage",row)

    def _option_chain_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH audited AS (
                SELECT
                    a.analytics_id::text AS entity_id,
                    (
                        r.status <> 'COMPLETED'
                        OR a.source_run_id <> r.run_id
                        OR a.underlying_symbol <> r.underlying_symbol
                        OR a.expiry <> r.expiry
                    ) AS violation
                FROM option_chain_analytics a
                JOIN option_chain_runs r ON r.run_id = a.source_run_id
                UNION ALL
                SELECT
                    c.change_id::text,
                    (
                        c.previous_source_run_id <> previous.source_run_id
                        OR c.current_source_run_id <> current.source_run_id
                        OR c.underlying_symbol <> previous.underlying_symbol
                        OR c.underlying_symbol <> current.underlying_symbol
                        OR c.expiry <> previous.expiry
                        OR c.expiry <> current.expiry
                        OR c.previous_captured_at <> previous.source_captured_at
                        OR c.current_captured_at <> current.source_captured_at
                        OR c.previous_captured_at >= c.current_captured_at
                    )
                FROM option_analytics_changes c
                JOIN option_chain_analytics previous
                  ON previous.analytics_id = c.previous_analytics_id
                JOIN option_chain_analytics current
                  ON current.analytics_id = c.current_analytics_id
            )
            SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
            """
        )
        return self._metric("option_chain_lineage", row)

    def _decision_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH audited AS (
                SELECT r.ranking_id::text AS entity_id,
                    (
                        r.analytics_id <> c.current_analytics_id
                        OR r.underlying_symbol <> a.underlying_symbol
                        OR r.expiry <> a.expiry
                        OR r.source_captured_at <> a.source_captured_at
                    ) AS violation
                FROM option_rankings r
                JOIN option_chain_analytics a ON a.analytics_id = r.analytics_id
                JOIN option_analytics_changes c ON c.change_id = r.change_id
                UNION ALL
                SELECT s.selection_id::text,
                    (
                        s.analytics_id <> r.analytics_id
                        OR s.source_run_id <> a.source_run_id
                        OR s.underlying_symbol <> r.underlying_symbol
                        OR s.expiry <> r.expiry
                    )
                FROM option_contract_selections s
                JOIN option_rankings r ON r.ranking_id = s.ranking_id
                JOIN option_chain_analytics a ON a.analytics_id = s.analytics_id
                UNION ALL
                SELECT ra.assessment_id::text,
                    (
                        ra.selection_run_id <> s.selection_run_id
                        OR ra.ranking_id <> s.ranking_id
                        OR ra.analytics_id <> s.analytics_id
                        OR ra.source_run_id <> s.source_run_id
                        OR ra.underlying_symbol <> s.underlying_symbol
                        OR ra.expiry <> s.expiry
                        OR ra.option_type <> s.option_type
                        OR ra.security_id <> s.security_id
                    )
                FROM option_risk_assessments ra
                JOIN option_contract_selections s ON s.selection_id = ra.selection_id
                UNION ALL
                SELECT sig.signal_id::text,
                    (
                        sig.risk_run_id <> sr.risk_run_id
                        OR sig.risk_run_id <> ra.risk_run_id
                        OR sig.selection_id <> ra.selection_id
                        OR sig.ranking_id <> ra.ranking_id
                        OR sig.analytics_id <> ra.analytics_id
                        OR sig.source_run_id <> ra.source_run_id
                        OR sig.underlying_symbol <> ra.underlying_symbol
                        OR sig.expiry <> ra.expiry
                        OR sig.option_type <> ra.option_type
                        OR sig.security_id <> ra.security_id
                        OR ra.approved IS NOT TRUE
                    )
                FROM option_signals sig
                JOIN option_signal_runs sr ON sr.signal_run_id = sig.signal_run_id
                JOIN option_risk_assessments ra
                  ON ra.assessment_id = sig.assessment_id
            )
            SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
            """
        )
        return self._metric("decision_lineage", row)

    def _evaluation_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH replay_counts AS (
                SELECT rr.replay_run_id, rr.event_count,
                       COUNT(e.replay_event_id) AS actual_events,
                       COUNT(e.replay_event_id) FILTER (
                           WHERE e.sequence_number <= 0
                       ) AS invalid_events
                FROM market_replay_runs rr
                LEFT JOIN market_replay_events e
                  ON e.replay_run_id = rr.replay_run_id
                GROUP BY rr.replay_run_id, rr.event_count
            ), backtest_counts AS (
                SELECT br.backtest_run_id, br.signal_run_id, br.signal_count,
                       br.completed_trade_count, br.skipped_trade_count,
                       COUNT(bt.backtest_trade_id) AS actual_trades,
                       COUNT(bt.backtest_trade_id) FILTER (
                           WHERE bt.signal_id IS NOT NULL
                             AND sig.signal_run_id <> br.signal_run_id
                       ) AS lineage_errors
                FROM option_backtest_runs br
                LEFT JOIN option_backtest_trades bt
                  ON bt.backtest_run_id = br.backtest_run_id
                LEFT JOIN option_signals sig ON sig.signal_id = bt.signal_id
                GROUP BY br.backtest_run_id, br.signal_run_id, br.signal_count,
                         br.completed_trade_count, br.skipped_trade_count
            ), audited AS (
                SELECT replay_run_id::text AS entity_id,
                       (event_count <> actual_events OR invalid_events > 0) AS violation
                FROM replay_counts
                UNION ALL
                SELECT backtest_run_id::text,
                       (
                           signal_count <> actual_trades
                           OR completed_trade_count + skipped_trade_count <> actual_trades
                           OR lineage_errors > 0
                       )
                FROM backtest_counts
            )
            SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
            """
        )
        return self._metric("evaluation_lineage", row)

    def _alert_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            SELECT COUNT(*), COUNT(*) FILTER (
                WHERE
                    (a.source_type = 'SIGNAL' AND NOT EXISTS (
                        SELECT 1 FROM option_signals s
                        WHERE s.signal_id::text = a.source_id
                          AND s.signal_run_id::text = a.source_run_id
                    ))
                    OR (a.source_type = 'RISK_DECISION' AND NOT EXISTS (
                        SELECT 1 FROM option_risk_assessments r
                        WHERE r.assessment_id::text = a.source_id
                          AND r.risk_run_id::text = a.source_run_id
                    ))
                    OR (a.source_type = 'PIPELINE_HEALTH' AND NOT EXISTS (
                        SELECT 1 FROM pipeline_runs p
                        WHERE p.run_id = a.source_id
                          AND p.run_id = a.source_run_id
                    ))
            )
            FROM alert_events a
            """
        )
        return self._metric("alert_lineage", row)

    def _paper_lineage(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH event_counts AS (
                SELECT position_id, COUNT(*) AS event_count,
                       MIN(sequence_number) AS first_sequence,
                       MAX(sequence_number) AS last_sequence
                FROM paper_position_events
                GROUP BY position_id
            ), fill_counts AS (
                SELECT position_id,
                       COUNT(*) FILTER (WHERE side = 'BUY') AS buy_fills,
                       COUNT(*) FILTER (WHERE side = 'SELL') AS sell_fills
                FROM paper_trade_fills
                GROUP BY position_id
            )
            SELECT COUNT(*), COUNT(*) FILTER (
                WHERE
                    p.signal_run_id <> s.signal_run_id
                    OR p.risk_run_id <> s.risk_run_id
                    OR p.assessment_id <> s.assessment_id
                    OR p.selection_id <> s.selection_id
                    OR p.ranking_id <> s.ranking_id
                    OR p.analytics_id <> s.analytics_id
                    OR p.source_run_id <> s.source_run_id
                    OR p.underlying_symbol <> s.underlying_symbol
                    OR p.expiry <> s.expiry
                    OR p.option_type <> s.option_type
                    OR p.security_id <> s.security_id
                    OR entry_order.signal_id <> p.signal_id
                    OR entry_order.side <> 'BUY'
                    OR entry_order.status <> 'FILLED'
                    OR COALESCE(f.buy_fills, 0) <> 1
                    OR COALESCE(e.first_sequence, 0) <> 1
                    OR e.last_sequence <> e.event_count
                    OR (
                        p.status = 'OPEN'
                        AND (COALESCE(f.sell_fills, 0) <> 0 OR p.exit_order_id IS NOT NULL)
                    )
                    OR (
                        p.status = 'CLOSED'
                        AND (COALESCE(f.sell_fills, 0) <> 1 OR p.exit_order_id IS NULL)
                    )
            )
            FROM paper_positions p
            JOIN option_signals s ON s.signal_id = p.signal_id
            JOIN paper_trade_orders entry_order
              ON entry_order.order_id = p.entry_order_id
            LEFT JOIN event_counts e ON e.position_id = p.position_id
            LEFT JOIN fill_counts f ON f.position_id = p.position_id
            """
        )
        return self._metric("paper_lineage", row)

    def _operational_state(self) -> AuditMetric:
        row = self._fetch_one(
            """
            WITH audited AS (
                SELECT run_id::text AS entity_id,
                    (
                        (status IN ('COMPLETED', 'FAILED') AND completed_at IS NULL)
                        OR (status = 'COMPLETED' AND error_message IS NOT NULL)
                        OR (status = 'FAILED' AND error_message IS NULL)
                    ) AS violation
                FROM option_chain_runs
                UNION ALL
                SELECT run_id,
                    (
                        (status IN ('COMPLETED', 'FAILED') AND completed_at IS NULL)
                        OR (status = 'RUNNING' AND completed_at IS NOT NULL)
                    )
                FROM pipeline_runs
            )
            SELECT COUNT(*), COUNT(*) FILTER (WHERE violation) FROM audited
            """
        )
        return self._metric("operational_state", row)

    def _execution_schema_boundary(self) -> AuditMetric:
        row = self._fetch_one(
            """
            SELECT COUNT(*), COUNT(*) FILTER (
                WHERE table_name NOT IN ('paper_trade_orders')
            )
            FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_type = 'BASE TABLE'
              AND (
                  table_name LIKE '%broker%'
                  OR table_name LIKE '%live_order%'
                  OR table_name LIKE '%trade_order%'
              )
            """
        )
        audited = max(int(row[0]), 1)
        return AuditMetric("execution_schema_boundary", audited, int(row[1]))

    @staticmethod
    def _metric(name: str, row: tuple[Any, ...]) -> AuditMetric:
        return AuditMetric(name, int(row[0]), int(row[1]))

    @staticmethod
    def _fetch_one(query: str) -> tuple[Any, ...]:
        rows = ReleaseReadinessRepository._fetch_all(query)
        if len(rows) != 1:
            raise RuntimeError("Release audit query did not return exactly one row.")
        return rows[0]

    @staticmethod
    def _fetch_all(query: str) -> list[tuple[Any, ...]]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
