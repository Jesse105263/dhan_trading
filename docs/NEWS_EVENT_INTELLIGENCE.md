# News & Event Intelligence

V2.1.2 persists source-attributed market context and deterministically links it to
Feature Store observations, Historical Outcomes, Similarity runs and Trade
Opportunities. Events never generate opportunities, alter eligibility or scores,
or invoke AI, sentiment, alerts, Dhan, paper trading or execution.

## Event Model and Sources

`market-event-v1` supports corporate earnings/actions, exchange announcements,
macroeconomic, RBI, sector, market-wide and company-news events, each explicitly
scheduled or unscheduled. Records preserve deterministic identity, source event
identity, sanitized text, supplied timestamps, explicit symbols/sectors, scope,
source reference, sanitized metadata, ingestion time, checksum and deduplication
identity. At least one source timestamp is required; none is fabricated.

`EventProvider` is the provider interface. `LocalJsonEventProvider` is the only
implemented adapter and reads bounded local JSON without network access. Unique
constraints and upserts make imports idempotent. Sensitive metadata keys are
discarded; raw payloads are not stored, only SHA-256 checksums.

Future adapters require separate approval. Candidates include NSE/BSE
announcements, exchange earnings/corporate-action calendars, RBI's calendar,
authoritative macro calendars, and licensed market/sector news. V2.1.2 calls none.

## Relevance and Leakage Prevention

An event is relevant only through an exact explicit symbol or `market_wide=true`.
Explicit sectors are persisted and filterable, but no symbol-sector relationship
is inferred because the repository has no authoritative mapping.

- `BEFORE_OBSERVATION`: within seven days before observation and published by the
  observation; predictive eligible.
- `DURING_HOLDING`: after observation through persisted terminal time; outcome
  context only.
- `NEAR_EXPIRY`: within two days of expiry; predictive only when already published.

Scheduled future events are inputs only when their publication timestamp proves
they were known. Similarity context derives only from predictive query-vector
links. Later events can only describe outcomes.

## Opportunity Context

Only events published by opportunity observation time attach. `RECENT_CONTEXT`
covers seven prior days; `UPCOMING_RISK` covers the earlier of 14 days or expiry.
Upcoming scheduled events may produce deterministic reasons-against text. Events
produce no reason-for and cannot change opportunity calculations or eligibility.

## Persistence, Commands and API

Migration `022_news_event_intelligence.sql` adds canonical events, normalized
symbol/sector relationships, vector/outcome, similarity and opportunity links.

```bash
python -m scripts.import_news_events --file fixtures/news_events.json
python -m scripts.link_historical_events
python -m scripts.materialize_opportunity_events
```

Commands are bounded, deterministic, idempotent, restartable and local-only.

- `GET /api/v2/events`
- `GET /api/v2/events/{event_id}`
- `GET /api/v2/events/context?symbol=...`
- `GET /api/v2/events/context?vector_id=...`
- `GET /api/v2/trade-opportunities/{opportunity_id}/events`

Filters cover symbol, sector, type, date range, scheduled/market-wide state and a
1–200 limit. Reads never fetch externally.

## Frontend and Limitations

`/events` provides a timeline, filters, timestamps, scope and source references.
Opportunity detail shows recent/upcoming context, scheduled risk, reasons and
empty/unavailable states. No sentiment, inferred relationships, AI summaries,
bullish/bearish labels or completeness claim is provided. Fixture data verifies
architecture and behavior only.
