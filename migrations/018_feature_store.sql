CREATE TABLE IF NOT EXISTS feature_store_vectors (
    vector_id UUID PRIMARY KEY,
    analytics_id UUID NOT NULL REFERENCES option_chain_analytics(analytics_id) ON DELETE CASCADE,
    change_id UUID REFERENCES option_analytics_changes(change_id) ON DELETE SET NULL,
    ranking_id UUID REFERENCES option_rankings(ranking_id) ON DELETE SET NULL,
    underlying_symbol VARCHAR(30) NOT NULL,
    expiry DATE NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    schema_version VARCHAR(30) NOT NULL,
    quality_state VARCHAR(20) NOT NULL,
    feature_count INTEGER NOT NULL,
    missing_feature_count INTEGER NOT NULL,
    materialized_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_feature_store_source_version UNIQUE (analytics_id, schema_version),
    CONSTRAINT ck_feature_store_quality CHECK (quality_state IN ('COMPLETE', 'PARTIAL')),
    CONSTRAINT ck_feature_store_counts CHECK (feature_count > 0 AND missing_feature_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_feature_store_symbol_expiry_time
ON feature_store_vectors (underlying_symbol, expiry, observed_at DESC, vector_id DESC);

CREATE TABLE IF NOT EXISTS feature_store_values (
    vector_id UUID NOT NULL REFERENCES feature_store_vectors(vector_id) ON DELETE CASCADE,
    feature_name VARCHAR(80) NOT NULL,
    feature_group VARCHAR(30) NOT NULL,
    numeric_value NUMERIC,
    source_relation VARCHAR(80) NOT NULL,
    source_field VARCHAR(80) NOT NULL,
    PRIMARY KEY (vector_id, feature_name)
);

CREATE INDEX IF NOT EXISTS idx_feature_store_values_feature
ON feature_store_values (feature_name, numeric_value, vector_id);
