CREATE TABLE opportunity_policies_v2 (
 policy_version TEXT PRIMARY KEY, policy_checksum TEXT NOT NULL CHECK(length(policy_checksum)=64),
 strategy_code TEXT NOT NULL, policy JSONB NOT NULL, created_at TIMESTAMP NOT NULL);
CREATE TABLE opportunity_runs_v2 (
 run_id UUID PRIMARY KEY, policy_version TEXT NOT NULL REFERENCES opportunity_policies_v2(policy_version),
 similarity_run_id UUID NOT NULL REFERENCES similarity_runs_v2(run_id), as_of TIMESTAMP NOT NULL,
 policy_checksum TEXT NOT NULL CHECK(length(policy_checksum)=64), candidate_count INTEGER NOT NULL CHECK(candidate_count>=0),
 provisional_count INTEGER NOT NULL CHECK(provisional_count>=0), abstained_count INTEGER NOT NULL CHECK(abstained_count>=0),
 lineage_checksum TEXT NOT NULL CHECK(length(lineage_checksum)=64), started_at TIMESTAMP NOT NULL, completed_at TIMESTAMP NOT NULL,
 UNIQUE(policy_version,similarity_run_id,as_of,policy_checksum));
CREATE TABLE opportunity_candidates_v2 (
 candidate_id UUID PRIMARY KEY, run_id UUID NOT NULL REFERENCES opportunity_runs_v2(run_id),
 similarity_run_id UUID NOT NULL REFERENCES similarity_runs_v2(run_id), query_vector_id UUID NOT NULL REFERENCES feature_vectors_v2(vector_id),
 instrument_id UUID NOT NULL REFERENCES canonical_instruments(instrument_id), instrument_revision_id UUID NOT NULL REFERENCES canonical_instrument_revisions(revision_id),
 state TEXT NOT NULL CHECK(state IN ('PROVISIONAL','INSUFFICIENT_EVIDENCE','ILLIQUID','FILL_REJECTED','OUT_OF_DISTRIBUTION','CONTRADICTORY','UNSTABLE')),
 strategy_code TEXT NOT NULL, direction TEXT NOT NULL CHECK(direction IN ('LONG_CALL','LONG_PUT')), holding_horizon TEXT NOT NULL,
 observed_at TIMESTAMP NOT NULL, expiry DATE, strike NUMERIC, option_type TEXT CHECK(option_type IN ('CE','PE')),
 entry_zone_low NUMERIC, entry_zone_high NUMERIC, stop_price NUMERIC, target_prices JSONB NOT NULL,
 historical_win_rate NUMERIC, net_expected_value_pct NUMERIC, similar_setup_count INTEGER NOT NULL CHECK(similar_setup_count>=0),
 effective_sample_size NUMERIC NOT NULL CHECK(effective_sample_size>=0), evidence_quality NUMERIC NOT NULL CHECK(evidence_quality>=0 AND evidence_quality<=1),
 concentration_metrics JSONB NOT NULL, fill_metrics JSONB NOT NULL, reasons_for JSONB NOT NULL, reasons_against JSONB NOT NULL,
 feature_lineage_checksum TEXT NOT NULL CHECK(length(feature_lineage_checksum)=64), similarity_lineage_checksum TEXT NOT NULL CHECK(length(similarity_lineage_checksum)=64),
 contract_lineage_checksum TEXT NOT NULL CHECK(length(contract_lineage_checksum)=64), lineage_checksum TEXT NOT NULL CHECK(length(lineage_checksum)=64), materialized_at TIMESTAMP NOT NULL,
 CHECK((state='PROVISIONAL' AND entry_zone_low IS NOT NULL AND entry_zone_high IS NOT NULL AND stop_price IS NOT NULL AND historical_win_rate IS NOT NULL AND net_expected_value_pct IS NOT NULL)
    OR (state<>'PROVISIONAL' AND entry_zone_low IS NULL AND entry_zone_high IS NULL AND stop_price IS NULL AND historical_win_rate IS NULL AND net_expected_value_pct IS NULL)));
CREATE TABLE opportunity_evidence_v2 (
 candidate_id UUID NOT NULL REFERENCES opportunity_candidates_v2(candidate_id), match_id UUID NOT NULL REFERENCES similarity_matches_v2(match_id),
 matched_vector_id UUID NOT NULL REFERENCES feature_vectors_v2(vector_id), matched_outcome_id UUID REFERENCES historical_outcomes_v2(outcome_id),
 included BOOLEAN NOT NULL, exclusion_reason TEXT, episode_key TEXT NOT NULL, evidence_weight NUMERIC NOT NULL CHECK(evidence_weight>=0),
 PRIMARY KEY(candidate_id,match_id));
CREATE FUNCTION reject_opportunity_v2_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Opportunity Engine V2 evidence is immutable'; END; $$ LANGUAGE plpgsql;
CREATE TRIGGER opportunity_runs_v2_immutable BEFORE UPDATE OR DELETE ON opportunity_runs_v2 FOR EACH ROW EXECUTE FUNCTION reject_opportunity_v2_mutation();
CREATE TRIGGER opportunity_candidates_v2_immutable BEFORE UPDATE OR DELETE ON opportunity_candidates_v2 FOR EACH ROW EXECUTE FUNCTION reject_opportunity_v2_mutation();
CREATE TRIGGER opportunity_evidence_v2_immutable BEFORE UPDATE OR DELETE ON opportunity_evidence_v2 FOR EACH ROW EXECUTE FUNCTION reject_opportunity_v2_mutation();
