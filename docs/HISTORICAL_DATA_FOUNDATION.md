# Version 3 Historical Data Foundation

## Scope

V3.1 implements the provider-neutral persistence and normalization boundary needed
before licensed historical acquisition can begin. It does not connect to Dhan,
TrueData, an exchange, a regulator or any other external provider. It requires no
credentials and includes no downloader, backfill command, scheduler or continuous
collector.

The implemented adapter accepts bounded local JSON bytes only. It exists to prove
the contracts with deterministic test records; it is not a production data source.
No historical coverage target is claimed by this milestone checkpoint.

## Migration 023

`023_historical_data_foundation.sql` adds separate raw, licensing and canonical
layers:

- `historical_data_sources` identifies provider, product and dataset boundaries.
- `historical_retention_policies` records agreement version and fail-closed raw,
  normalized, derived, training, backup, post-termination and redistribution rights.
- `historical_raw_payloads` stores exact received bytes, SHA-256 and byte count.
- `historical_raw_manifests` records source/policy lineage, external batch,
  provider and adapter schema versions, request/page/retry metadata, coverage,
  item count, parent manifest, raw SHA-256 and canonical batch SHA-256.
- `canonical_instruments` owns immutable provider-neutral identities.
- `canonical_instrument_revisions` preserves point-in-time instrument metadata,
  derivative terms, underlying identity, validity and supersession.
- `source_instrument_mappings` stores temporal provider security-ID and symbol
  mappings without replacing expired or renamed history.
- `historical_bar_revisions` stores underlying, futures and option-contract OHLCV,
  OI, optional quote/trade fields, explicit adjustment state, all relevant times,
  revision lineage and acceptance state.
- `corporate_action_revisions` preserves original and normalized terms, lifecycle
  dates, status and supersession.
- `historical_quality_incidents` records quarantined cross-source bar conflicts.

Raw payload and manifest updates are rejected by database triggers. Retention-led
deletion is intentionally not automated; it requires a separately approved,
auditable policy. Migrations `001`–`022` are unchanged.

## Provider-neutral contracts

`HistoricalDataSource`, `RetentionPolicy`, `RawPayloadEnvelope`,
`CanonicalInstrument`, `InstrumentMapping`, `HistoricalBar`, `CorporateAction`
and `CanonicalHistoricalDataset` are frozen domain contracts.
`HistoricalDataAdapter` is the provider-neutral normalization protocol.
`HistoricalDataRepositoryProtocol` isolates persistence from normalization policy.

`LocalJsonHistoricalDataAdapter` parses exact local bytes into those contracts. It
imports no HTTP client, Dhan client or settings and reads no credential. A future
provider adapter must be separately approved and may emit only these canonical
records; downstream Feature, Outcome, Similarity and research layers must never
consume provider payloads or provider security IDs directly.

## Identity and validation

Canonical instrument UUIDs are independent of provider IDs and mutable tickers.
Cash identities may carry ISIN. Futures require an expiry and canonical
underlying and reject option fields. Options require canonical underlying,
expiry, strike and CE/PE type. Expired instruments remain addressable.

Mappings are scoped by source, venue, segment and provider security ID with
half-open validity intervals. Overlaps are rejected. Reused IDs and symbol changes
must create later mappings rather than overwrite earlier rows.

Bars require explicit interval, session date, adjustment state, open/close/event,
provider and availability timestamps where supplied. OHLC ordering, non-negative
prices/quantities and bid/ask ordering are validated. Missing volume, OI, trade
count or quote fields remain null; nothing is zero-filled or fabricated.

Corporate actions preserve the source terms separately from normalized terms.
Supported types include splits, bonuses, dividends, rights, mergers, spinoffs,
symbol changes and delistings. Raw bars are never retroactively rewritten by an
action record.

## Checksums, deduplication and revisions

SHA-256 is calculated over the exact payload bytes before decoding. A second
SHA-256 covers deterministic canonical serialization of the complete normalized
batch. The manifest checksum covers source, entitlement, payload, adapter,
request, coverage, parent and canonical-output metadata. UUIDv5 identities make
identical source, policy, payload and manifest inputs restartable and idempotent.

Exact raw payloads deduplicate by source and byte checksum. Exact canonical
records deduplicate by natural key and content checksum. Different content from
the same source appends a new revision, marks the previous accepted revision
non-current and records `supersedes_revision_id`. No canonical observation uses
last-write-wins replacement.

A differing bar from another source is appended as `QUARANTINED`, leaves the
accepted current record unchanged and creates a quality incident. Prices, OI and
timestamps are never averaged. Conflicting cross-source instrument or corporate
action revisions reject the transaction pending an explicit future source-priority
policy.

## Retention and licensing

Import fails before adapter invocation unless both raw and normalized retention
are explicitly `ALLOWED`. `UNKNOWN` and `DENIED` fail closed. Other permissions
remain recorded independently and are not inferred from storage permission.

The local-test policy used in automated tests grants only fixture raw/normalized
retention and denies derived use, model training, backups, post-termination use
and redistribution. It conveys no rights for Dhan, TrueData, NSE, BSE or any other
provider.

## Point-in-time lineage

Every canonical revision points to the raw manifest that produced it. Records
separate event time, provider time, availability time and ingestion time where
applicable. Later research must filter revisions by `available_at`; it may not use
a corrected observation before the correction became available.

The SELECT-only release verifier now audits raw/source/policy agreement, byte
counts, allowed retention and same-natural-key supersession. Empty historical
foundation tables are a valid `SKIP` until licensed acquisition is approved.

## Verification and limitations

Unit coverage verifies deterministic IDs/checksums, exact-byte raw hashing,
retention refusal before adapter use, local-only isolation, derivative validation,
mapping overlap rejection, missing-value preservation, OHLC validation,
idempotency and canonical revision behavior. PostgreSQL coverage verifies atomic
raw/canonical persistence, replay deduplication, bar supersession, byte/checksum
lineage and database-enforced raw immutability.

V3.1 has not downloaded or backfilled any dataset. Five-year daily, two-year
intraday, 95% underlying-session and 90% derivative coverage targets remain unmet
and cannot be evaluated until procurement and licensing gates in
`docs/V3_DATA_PROVIDER_STRATEGY.md` are satisfied.

## V3.2 integration

Continuous collection submits provider-neutral local fixture bytes through this
unchanged import service. Work and attempt lineage live in migration `024`; raw
immutability, replay deduplication, same-source revisions and cross-source
quarantine remain owned by V3.1. No live provider adapter was added.

## V3.3 outcome consumer

Outcome Engine V2 reads accepted canonical bars and corporate-action revisions
only through stable instrument IDs. Every label retains anchor, terminal, path and
raw-manifest lineage. Point-in-time queries use revision availability rather than
today's `is_current`, preventing late corrections from leaking into earlier runs.

## V3.4 feature consumer

Feature Store V2 reads accepted raw-adjustment canonical bars and point-in-time
instrument revisions. Each value retains exact source revision IDs; each vector
retains its anchor manifest and availability. Corrections append new vectors and
cannot destructively mutate prior feature evidence.

## V3.5 similarity consumer

Similarity V2 reaches foundation evidence only through Feature Store V2 lineage.
Candidate availability is bounded by the run cutoff, so late canonical revisions
cannot enter an earlier historical analogue population.
