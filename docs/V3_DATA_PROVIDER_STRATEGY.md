# Version 3 Data Provider & Licensing Strategy

## Status and decision

This document is the procurement and architecture gate for V3.1 Historical Data
Foundation. Research was completed on 15 July 2026 from public, official provider,
exchange and regulator material. Public product descriptions are not a data
licence. No subscription may be purchased and no provider integration may begin
until the provider confirms the required rights in writing.

The selected, smallest practical provider set is:

| Role | Selection | Status |
|---|---|---|
| Primary historical market data | DhanHQ | Selected subject to coverage trial and written licensing confirmation |
| Primary continuous/live market data | TrueData | Selected subject to quote, coverage trial and written licensing confirmation |
| Backup market data | DhanHQ | Selected for live failover; the existing integration does not establish research-storage rights |
| Corporate actions | NSE and BSE official products/announcements | Authoritative specialist sources; commercial feed terms require confirmation |
| Exchange announcements | NSE and BSE official announcements | Authoritative specialist sources |
| Current and historical news | TrueData Corporate Data API initially; LSEG Machine Readable News is the enterprise upgrade | Neither is activated; archive and model-use rights require confirmation |
| RBI and macro events | RBI press releases, DBIE and its release calendar; official MoSPI releases for CPI, IIP and national accounts | Public authoritative specialist sources; automated-use terms must be reviewed |
| IV, Greeks, HV, technical features and breadth | Internally derived from licensed canonical observations and official reference inputs | Permitted only after source licences expressly allow derived data and model research |

This selection uses two market-data vendors in normal operation. Dhan supplies the
deepest publicly documented broker-API backfill relevant to the existing platform;
TrueData supplies an exchange-authorized, broker-independent continuous feed and a
corporate/news option. NSE, BSE and RBI remain authoritative sources rather than a
third normalized market-data vendor. Upstox is the procurement fallback if either
selected vendor cannot grant the required rights.

No provider integration has been implemented by this milestone. No credentials
have been created, no provider has been contacted, no paid service has been
activated and no paid API has been called.

## Non-negotiable licensing requirement

Before acquisition, the owner must obtain a written order form, licence or email
from each paid provider that answers all of the following for a private,
single-user, India-focused research system:

- long-term local retention of raw and normalized observations;
- retention after subscription termination;
- creation and indefinite retention of derived bars, IV, Greeks, labels, features,
  embeddings, outcomes and aggregate statistics;
- use of source and derived data for statistical modelling and model training;
- encrypted local and off-site backups and disaster-recovery copies;
- internal display, research and paper-decision use without redistribution;
- permitted users, devices, environments and concurrent connections;
- exchange pass-through fees and whether separate exchange agreements are needed;
- historical backfill, expired-contract and full-chain entitlements;
- audit, deletion, attribution and termination obligations.

Unless an official source below states otherwise, every right is classified as
**UNKNOWN — PROVIDER CONFIRMATION REQUIRED**. Absence of a published prohibition
does not constitute permission. Redistributing raw or derived market data, exposing
it through SaaS, or permitting third-party access is outside this strategy.

## Dataset fitness criteria

The target evidence base needs stable point-in-time identities and revisions for
Indian cash equities, indices, futures and options. It includes daily and intraday
OHLCV; futures and options OI; basis and rollover inputs; option chains; bid/ask;
expiry, strike and lot-size histories; inactive contracts; corporate actions;
India VIX, sector indices and breadth constituents; earnings, announcements,
RBI/macro releases; and current and archived news. Vendor-supplied IV and Greeks
are useful reconciliation fields, not the canonical research calculation.

“Full option-chain history” means time-stamped observations for all eligible
strikes and expiries, not merely the current chain or contract candles queried one
contract at a time. “Historical depth” below is the maximum explicitly documented
publicly and does not guarantee entitlement for every segment or instrument.

## Comparison matrix

Legend: `Yes` means the cited public product documentation explicitly advertises
the capability; `Limited` identifies a documented constraint; `Quote` means no
public price was relied upon. All unconfirmed licence rights use the required
unknown classification.

| Provider | Publicly documented depth/resolution | Derivatives, OI, IV, Greeks and depth | Actions/news/events and delivery | Limits, latency and reliability | Licensing, retention and price | Fit and major gaps |
|---|---|---|---|---|---|---|
| **DhanHQ** | Intraday 1/5/15/25/60-minute candles, documented up to five years for active instruments; requests bounded to 90 days; daily history also available | Futures/options candles and OI; expired-options capability appears in releases; live full option chain has OI, volume, IV, Greeks and top bid/ask; 20/200-level NSE depth product | REST, WebSocket and instrument master; no complete corporate-actions, macro or historical-news product documented | Data APIs 5/s and 100,000/day; quote 1/s; option chain one unique request/3s; live broker dependency | Private/internal, storage, post-termination retention, derivatives, training and backup rights: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED**. Subscription pricing is published in-account/product pages and must be captured at procurement | **Primary historical and live backup.** Best documented broker backfill and already bounded by the platform. Gaps: historical full-chain snapshots, inactive-master completeness, revision semantics, licensing and SLA |
| **NSE Data & Analytics** | Official real-time, snapshot, delayed, EOD and historical products; segment-specific files and SFTP products | Authoritative cash/F&O/CD/commodity records; analytical products include option analytics; depth and exact historical chain availability are product-specific | Official corporate data, actions, announcements, circulars and reference files; API/bulk/SFTP vary by product | Exchange-grade source; latency, delivery recovery and service levels are contractual | Published domestic pricing schedules exist. Storage, derived use, training, backup and private-use scope are product-contract specific: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | **Authoritative specialist.** Highest provenance, but multiple products, exchange agreements and integration complexity make it impractical as the only source |
| **BSE** | Official real-time, snapshot/delayed, EOD, bhavcopy and historical stock/corporate products | Cash, indices and BSE derivatives products; chain/depth/history scope is product-specific | Official corporate announcements/actions and reference data; feed/bulk products available | Exchange-grade source; SLA and recovery are contractual | Public information-products tariff exists. Retention, derived use, training and backups: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | **Authoritative specialist** for BSE instruments/actions/announcements; not a single-source solution |
| **TrueData** | Live tick, OHLC and documented historical access; exact segment-by-segment depth is not published in one definitive table | NSE/BSE/MCX equities, indices and derivatives; OI, L1/depth where available; live complete option chain, IV and Greeks; bid/ask history advertised in API guidance | Streaming/API/SDK; Corporate Data API advertises announcements, actions, financial results, shareholding and news | Advertises millisecond delivery and 99.995% uptime; historical calls are symbol-scoped; contracted SLA must govern | Public pages permit personal/internal analysis and prohibit redistribution without approval. Long-term raw retention, post-term use, derived features, training and backups: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED**. Quote plus exchange fees | **Primary continuous/live.** Broker-independent and broad. Gaps: published historical depth, historical full-chain entitlement, exact quotas and research rights |
| **Global Datafeeds (GFDL/GDFL)** | NSE cash minute history generally 3–6 months by interval and EOD from 2010; NFO tick about one week, minute 3–6 months; futures daily continuous from 2010; contractwise futures daily about three months; options daily about one month | One-second live NSE/BSE/MCX; L1 bid/ask; live chain/Greeks and historical Greeks advertised | APIs/SDK; corporate announcements, actions, results, shareholding and sector data advertised | Advertises 99.995% uptime; breadth and limits depend on subscription | Support policy places accumulated-data backup responsibility on user. Retention, post-term use, derived use and training: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED**. Quote | Credible **specialist/alternate live** source. Historical derivative depth is insufficient for V3.1 by itself. “GDFL” and “Global Datafeeds” refer to Global Financial Datafeeds LLP, not two independent backups |
| **Upstox** | V3 candles: minute/hour from January 2022 and daily from January 2000; expired-instrument history is a Plus product | Current option chain includes OI, bid/ask, IV and Greeks; expired futures/options master and candles advertised | REST/WebSocket; market information and fundamentals/news endpoints are advertised | Plan and endpoint-specific quotas; broker dependency; no public institutional SLA relied upon | Local retention, derived use, training, backup and post-term rights: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED**. Some expired data requires Plus | **Procurement fallback/secondary backup.** Strong documented depth and expired contracts; historical chain snapshots and research rights unresolved |
| **FYERS API** | Live and historical equity/F&O data; public product page does not establish the required segment-by-segment depth | Quotes, depth and derivatives are advertised; expired contract, historical OI/IV/Greeks and chain archive not established | REST/WebSocket; no complete actions/news archive established | Advertises up to 100,000 requests/day; broker dependency; SLA unknown | API marketed without separate subscription fee for clients. All retention/model/backup rights: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Backup candidate only; historical evidence and licensing detail are inadequate for selection |
| **Zerodha Kite Connect** | Several years of candles at minute through daily intervals | Historical OHLCV and OI; continuous futures only for daily candles; expired option tokens are unavailable unless the client saved the master | REST/WebSocket and daily instrument dump; not a corporate/news source | Broker API; quotas and reliability governed by Kite terms | Paid API plans are public. Long-term research retention, derived use, training and backup rights: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Operational backup candidate, but expired-option and full-chain history gaps disqualify it as V3.1 primary |
| **ICICI Direct Breeze** | Advertises three years of second-level and F&O history; API supports 1m/5m/30m/1d intervals | Contract queries include OHLCV/OI; option-chain archive, Greeks and expired-master completeness not established | REST/streaming; no complete news/events archive established | 100 requests/minute and 5,000/day documented; broker dependency | API marketed free to ICICI Direct clients. Storage, derived use, training, backups and segment consistency: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Useful validation source; daily quota makes massive backfill difficult and published coverage needs confirmation |
| **Angel One SmartAPI** | Historical candles at minute through daily intervals; required total depth is not published | NSE/NFO/BSE/BFO/MCX instrument coverage; candle examples show OHLCV, while historical OI, chain archive, IV and Greeks are not established | REST/WebSocket and instrument master | Candle quota documented as 3/s, 180/min and 5,000/day; broker dependency | API access/pricing depends on account/product. All research-storage rights: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Tactical backup only; depth, expired derivatives, chain evidence and licensing are unresolved |
| **Definedge Securities** | Daily history advertised to 20 years, intraday about six months and tick about two sessions | NSE/BSE/NFO/BFO and other masters; option tooling exists, but required two-year intraday option evidence is not established | CSV/API; no comprehensive licensed news archive established | Broker/tool dependency; service level and bulk quotas unknown | Product pricing is public for some tools. Retention, derived use, training and backups: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Research-tool specialist; documented intraday depth is insufficient for V3.1 |
| **Accelpix** | API guidance advertises EOD, intraday and tick data; exact historical depth is not public | Authorized real-time equities/futures/options/index feed; L1, symbol master/lot size and Greeks advertised | Streaming/API in multiple SDKs | Low-latency positioning; exact quota, SLA and recovery terms require quote | Price and all retention/derived/training/backup rights: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Credible live alternate; cannot be selected until history, licence and commercials are documented |
| **Bloomberg Enterprise Data** | Global real-time, bulk and historical data; Data License advertises 20+ years for some datasets | Broad derivatives/reference/pricing capabilities; exact India exchange/chain/depth entitlement is contractual | REST/SFTP/cloud, corporate actions, events and news | Enterprise delivery and support; product-specific SLA | Quote. Contract-specific exchange entitlements, local retention, derived use, training and backups: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Enterprise specialist, excessive cost/complexity for current single-user scope; future reference/news candidate |
| **LSEG Data & Analytics** | Real-time/intraday/EOD products and Tick History from 1996 for covered venues | Broad derivatives and pricing; precise NSE/BSE option-chain/depth coverage must be confirmed | APIs/SFTP/bulk/cloud; Reuters Machine Readable News has real-time and archive coverage from 1996 | Enterprise feeds and support; SLA contractual | Quote. India entitlements, retention, derived use, training and backup rights: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | **Enterprise news upgrade** and possible validation source; cost and contract complexity prevent primary selection now |
| **FactSet** | Global prices include India composite EOD, active/inactive listings and unadjusted daily data from 2006; tick products exist | Global real-time/tick products cover derivatives, but precise Indian F&O/chain coverage is not public | APIs/feeds/cloud; corporate actions from 2006; News API and StreetAccount products | Enterprise service; India venue coverage and SLA contractual | Quote. Retention, derived use, training and backups: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Corporate/reference/news specialist, not selected for India intraday derivatives without a coverage proof |
| **GlobalData** | Public offerings focus on proprietary company, industry, deals and news intelligence rather than exchange-grade Indian intraday feeds | Required Indian option/futures chain history, OI, IV, Greeks and depth are not established | APIs/feeds are product-specific; company/news/event intelligence available | Enterprise research vendor; exchange-feed reliability not applicable/unknown | Quote. All retention, derived, training and backup rights: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** | Possible thematic/news specialist only; major market-data gaps |
| **Polygon.io** | Official market coverage is centered on US stocks, options, futures, indices, forex and crypto | No official NSE/BSE cash or derivatives coverage identified | REST/WebSocket/flat files for supported markets | Strong developer delivery for supported venues, irrelevant to Indian coverage | Public tier pricing exists for supported markets; Indian rights/coverage absent | **Not suitable** for this India-focused evidence base |

## Official sources reviewed

### Selected and India-focused providers

- DhanHQ: [historical data](https://dhanhq.co/docs/v2/historical-data/),
  [option chain](https://dhanhq.co/docs/v2/option-chain/),
  [market quote](https://dhanhq.co/docs/v2/market-quote/),
  [full market depth](https://dhanhq.co/docs/v2/full-market-depth/),
  [instruments](https://dhanhq.co/docs/v2/instruments/), and
  [release notes](https://dhanhq.co/docs/v2/releases/).
- NSE: [data vending](https://www.nseindia.com/static/nse-data-and-analytics/data-information-vending),
  [data usage policy](https://www.nseindia.com/static/market-data/nse-data-policy),
  [EOD/historical subscriptions](https://www.nseindia.com/static/market-data/eod-historical-data-subscription),
  [analytical products](https://www.nseindia.com/static/market-data/analytical-products), and
  [domestic pricing](https://nsearchives.nseindia.com/web/mediaattachment/2026-04/Download_Pricing_file_-_Domestic_clients_20260424122229.pdf).
- BSE: [information-products pricing](https://www.bseindia.com/downloads1/Information_Products_Pricing_Sheet.pdf)
  and the [SEBI exchange-data directory](https://www.sebi.gov.in/curation/equity_derivatives.html).
- TrueData: [market-data APIs](https://www.truedata.in/market-data-apis),
  [getting started](https://feedback.truedata.in/knowledge-base/article/getting-started-with-truedata-market-data-api),
  [API FAQ](https://feedback.truedata.in/knowledge-base/faqs/market-data-api), and
  [NSE authorized-vendor list](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/List%20of%20Authoized%20Vendors_3.pdf).
- Global Datafeeds: [data available](https://globaldatafeeds.in/global-datafeeds-apis/global-datafeeds-apis/introduction/type-of-data-available/),
  [API introduction](https://globaldatafeeds.in/global-datafeeds-apis/global-datafeeds-apis/introduction/introduction-to-apis/),
  [support policy](https://globaldatafeeds.in/support-policy/), and
  [release notes](https://globaldatafeeds.in/release-notes/).
- Upstox: [developer API](https://upstox.com/developer/api-documentation),
  [V3 history announcement](https://upstox.com/developer/api-documentation/announcements/enhanced-historical-candle-data-apis-v3/),
  [option chain](https://upstox.com/developer/api-documentation/get-pc-option-chain/), and
  [expired instruments](https://upstox.com/developer/api-documentation/announcements/expired-instruments-api/).
- FYERS: [Trading API](https://fyers.in/products/api) and
  [API fee statement](https://support.fyers.in/portal/en/kb/articles/does-fyers-charge-any-subscription-fees-for-trading-api).
- Zerodha: [historical candles](https://kite.trade/docs/connect/v3/historical/),
  [market data and instruments](https://kite.trade/docs/connect/v3/market-data-and-instruments/), and
  [WebSocket](https://kite.trade/docs/connect/v3/websocket/).
- ICICI Direct: [Breeze API documentation](https://api.icicidirect.com/breezeapi/documents/index.html)
  and [product overview](https://api.icicidirect.com/apiuser/home).
- Angel One: [SmartAPI guide](https://smartapi.angelone.in/docs/User) and
  [rate limits](https://smartapi.angelone.in/docs/Instruments).
- Definedge: [API documentation](https://www.definedgesecurities.com/api-documentation/)
  and [Optest pricing](https://optest.definedgesecurities.com/pricing).
- Accelpix: [official site](https://accelpix.com/) and
  [real-time/historical API guide](https://support.accelpix.com/portal/en/kb/articles/pix-apis-realtime-and-historical-data-in-python).

### Enterprise and international providers

- Bloomberg: [Data License](https://professional.bloomberg.com/products/data/data-management/data-license/)
  and [enterprise data](https://professional.bloomberg.com/products/data/).
- LSEG: [instrument pricing data](https://www.lseg.com/en/data-analytics/financial-data/pricing-and-market-data/instrument-pricing-data),
  [Tick History](https://www.lseg.com/en/data-analytics/market-data/data-feeds/tick-history), and
  [Machine Readable News](https://www.lseg.com/en/data-analytics/financial-news-service/machine-readable-news).
- FactSet: [Global Prices API](https://developer.factset.com/api-catalog/factset-global-prices-api),
  [real-time data](https://developer.factset.com/solutions/real-time-data), and
  [News API](https://www.factset.com/marketplace/catalog/product/factset-news-api).
- GlobalData: [official data and intelligence products](https://www.globaldata.com/our-products/).
- Polygon.io: [market data APIs](https://polygon.io/).

### Official event and macro sources

- RBI: [press releases](https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx),
  [Database on Indian Economy](https://dbieold.rbi.org.in/DBIE/), and
  [DBIE release calendar](https://dbieold.rbi.org.in/DBIE/doc/Release_Calender.pdf).
- MoSPI: [release calendar](https://www.mospi.gov.in/release-calendar) and
  [official publications](https://www.mospi.gov.in/publication).

Links record the evidence reviewed, not approval of click-wrap terms or permission
to automate a public website. Procurement must retain dated copies of the precise
contract, product schedule, exchange entitlement and pricing accepted.

## Detailed recommendation

### Primary historical: DhanHQ

Dhan is the fastest route to recommendation-quality evidence because its official
documentation advertises up to five years of intraday candles across segments,
OI, current chains and expanded expired-option access, and the repository already
has a constrained Dhan boundary. V3.1 must nevertheless prove exact active and
expired option coverage, inactive instrument identity, corporate-action behavior,
revision behavior and request-budget feasibility on a representative sample.

Dhan is not approved for acquisition until it grants the rights listed above.
If it does not, Upstox becomes the first backfill trial and an NSE/TrueData or
NSE/Global Datafeeds commercial package must be quoted.

### Primary continuous/live: TrueData

TrueData is selected for broker-independent continuous collection because its
official material advertises exchange authorization, broad Indian segment
coverage, ticks/OHLC/OI, bid/ask/depth where available, complete live chains,
IV/Greeks and corporate/news APIs. It also publicly distinguishes internal use
from redistribution. A paid proof must establish completeness, timestamps,
reconnect/replay behavior, late corrections and entitlement before V3.2.

### Backup: DhanHQ

Dhan is the live backup because it avoids a third active vendor and already has a
tested operational boundary. Backup collection must remain independently
identifiable and cannot silently mix Dhan observations with TrueData observations.
Upstox is the unactivated procurement fallback if Dhan cannot grant storage and
research rights or does not meet expired-contract coverage.

### Specialist sources

- NSE and BSE are canonical for their own instruments, contract/reference files,
  corporate actions and exchange announcements. Cross-listed actions are retained
  per exchange and reconciled; neither exchange silently overrides the other.
- TrueData Corporate Data API is the initial normalized current-news/event source
  only if it licenses archive retention and research/model use. Official exchange
  announcements remain separate primary evidence. LSEG Machine Readable News is
  the preferred future enterprise archive when cost and rights are justified.
- RBI/DBIE and MoSPI supply official macro release times and values. The collector
  must use documented downloads/feeds, respect site terms, and preserve release
  and revision timestamps. Scraping is not implicitly approved.
- Canonical IV and Greeks are calculated internally from licensed point-in-time
  option quotes, underlying/futures inputs, time to expiry, official corporate
  actions and an explicitly versioned rate/dividend policy. Vendor values are
  comparison inputs. HV, technical features, futures basis/rollover and breadth
  are internally derived with point-in-time constituent membership.

## Provider-neutral abstraction

The abstraction is a documented V3.1 contract, not executable code in V3.0.5.
Provider payloads enter immutable raw storage and adapters emit canonical records;
collectors, Feature Store V2, Historical Outcome Engine V2, Similarity Engine V2
and research jobs consume only canonical records and lineage.

### Canonical interfaces

| Interface | Required canonical content |
|---|---|
| `instrument_master` | canonical instrument ID, provider ID/symbol, exchange, segment, instrument type, underlying ID, ISIN where applicable, strike, option type, expiry, lot/tick size, validity interval, first/last trade dates and source revision |
| `underlying_bars` | instrument ID, interval, event/open/close times, OHLCV, trade count when available, session, adjustment state, availability time and source lineage |
| `futures_bars` | contract and underlying IDs, interval, OHLCV, OI, bid/ask when licensed, expiry/lot metadata, availability and lineage; basis/rollover remain derived |
| `option_contract_bars` | option contract/underlying IDs, interval, OHLCV, OI, bid/ask when licensed, strike/expiry/type, availability and lineage |
| `option_chain_snapshots` | chain/run ID, underlying, spot/future reference, expiry, capture and provider times, every returned strike/side quote, OI/volume/bid/ask, vendor IV/Greeks, completeness and lineage |
| `quote_depth_snapshots` | instrument, event/receive times, last trade, cumulative volume/OI, sequenced depth levels, feed state and lineage |
| `corporate_actions` | issuer/instrument, action type, announcement/ex/record/pay dates, original terms, normalized terms, status, revision and availability lineage |
| `events` | issuer/macro scope, event type, scheduled/released times, period, expected/actual/previous values when licensed, revision and source document lineage |
| `news` | source story ID, publisher, headline/body or licensed reference, subjects/instruments, publish/update/receive times, language, revision/retraction and entitlement metadata |

All time values use UTC plus the source exchange/session timezone. Every record
separates `event_time`, `provider_time`, `received_at`, `available_at` and
`ingested_at` where supplied or derivable. Missing values stay missing; adapters
must never synthesize observations.

### Identifiers and symbol mapping

The provider-neutral instrument identity is an immutable internal UUID (or
equivalent stable key), never a mutable ticker or broker security ID. It links to
exchange, venue segment, instrument class, underlying, ISIN for cash instruments,
and contract terms for derivatives. A temporal mapping table relates each
provider’s symbol/security ID to the canonical identity with `valid_from`,
`valid_to`, discovery source and revision. Renames, mergers, delistings, expired
contracts and reused provider IDs create new validity records, not overwritten
history.

### Source priority and failover

1. Exchange-origin reference/actions/announcements win for their own venue.
2. Dhan is primary for historical observations; TrueData is primary for live.
3. Dhan is the live backup; provider failover is explicit, session-bounded and
   recorded as a collection incident.
4. Vendor IV/Greeks never replace versioned internal calculations.
5. A lower-priority source fills a documented gap; it does not overwrite an
   accepted higher-priority observation.

Failover triggers require freshness/completeness thresholds, bounded retries and
a persisted decision. Return to primary starts a new source interval. Mixed-source
bars are prohibited unless a separately versioned reconciliation process emits a
new derived record with all contributors.

### Deduplication, revisions and conflicts

- The raw identity is `(provider, product, entitlement, request/stream session,
  provider message ID or deterministic payload position, capture time)`.
- The canonical natural key is interface-specific, such as `(instrument_id,
  interval, bar_open_time, adjustment_state)` or `(chain_id, contract_id)`.
- Identical payload checksums are idempotent duplicates. Non-identical records for
  one natural key are revisions, never in-place updates.
- Each revision has `observed_at`, `supersedes`, reason, source priority and a
  deterministic acceptance decision. Backtests see only revisions available at
  their point in time.
- Conflicts outside declared tolerances quarantine the observation, produce a
  quality incident and retain both sources. No averaging or last-write-wins policy
  is allowed for prices, OI, actions or event timestamps.

### Checksums, manifests and entitlement metadata

Each raw object has a SHA-256 checksum over the exact received bytes. A signed or
otherwise immutable raw-source manifest records provider/product, request or
stream boundaries, retrieval time, coverage interval, item/byte counts, schema
fingerprint, checksum, collector version, retry/page sequence and parent manifest.
Canonical batches record input manifest checksums, adapter version, row counts and
output checksum.

Every raw and canonical record inherits a licensing envelope containing agreement
ID/version, product/venue entitlement, use class, permitted user/environment,
retention deadline or indefinite flag, raw/derived/model-training/backup flags,
redistribution prohibition, attribution, deletion obligations and effective
dates. `UNKNOWN` is fail-closed. Retention jobs quarantine or delete only under an
approved, auditable policy; immutable lineage records the tombstone without
retaining prohibited payload content.

## Storage forecast

These are capacity-planning estimates, not provider claims. Assumptions are about
500 trading sessions over two years, 75 five-minute bars per full NSE session,
compressed columnar raw/canonical storage, indexes and metadata, point-in-time
versions, and one independent backup. The low case limits option chains to liquid
underlyings/strikes; expected covers the supported F&O universe; high retains
broader strikes/expiries, revisions and denser snapshots. Tick/full-depth history
is outside the estimate.

| Dataset | Low | Expected | High |
|---|---:|---:|---:|
| Five years daily cash/index/futures/options and reference history | 2 GB | 8 GB | 25 GB |
| Two years five-minute underlying and futures bars | 8 GB | 25 GB | 80 GB |
| Two years five-minute option-contract bars | 70 GB | 350 GB | 1.5 TB |
| Periodic full option-chain snapshots | 25 GB | 300 GB | 2.5 TB |
| Immutable raw payloads/manifests and revisions | 60 GB | 400 GB | 2.5 TB |
| Canonical tables, indexes and quality metadata | 45 GB | 250 GB | 1.2 TB |
| Derived Feature Store | 35 GB | 220 GB | 1.0 TB |
| Historical Outcomes, experiments and reports | 15 GB | 100 GB | 500 GB |
| Primary retained footprint | **260 GB** | **1.65 TB** | **9.3 TB** |
| One encrypted independent backup plus operational headroom | 260–390 GB | 1.65–2.5 TB | 9.3–14 TB |
| Total planned capacity | **0.5–0.7 TB** | **3.3–4.2 TB** | **18.6–23.3 TB** |

V3.1 should provision the expected case in stages, measure actual bytes per
instrument-session, and revise the forecast after a representative one-month
sample. Denser than five-minute full-chain or depth collection requires a new
capacity and licensing decision.

## Cost forecast

Provider prices and exchange entitlements change and several selected products
are quote-only. The figures below are owner planning envelopes in July 2026 INR,
not vendor quotes and not authorization to buy. Tax, brokerage accounts, exchange
pass-through fees, implementation labor and enterprise legal review may be extra.

| Category | Low first-year plan | Expected first-year plan | High/future plan |
|---|---:|---:|---:|
| Historical acquisition/backfill | ₹0–₹50,000 | ₹50,000–₹3 lakh | Quote required; exchange/enterprise packages can exceed ₹10 lakh |
| Continuous market subscription and exchange fees | ₹25,000–₹1 lakh | ₹1–₹4 lakh | ₹5–₹20+ lakh |
| News/events | Official sources only: ₹0–₹25,000 | TrueData/India-focused quote: ₹50,000–₹3 lakh | LSEG/Bloomberg/FactSet: **UNKNOWN — PROVIDER CONFIRMATION REQUIRED** |
| 4 TB class primary storage/compute | ₹40,000–₹1 lakh | ₹1–₹3 lakh | ₹5–₹15+ lakh for larger redundant systems |
| Encrypted independent backups | ₹10,000–₹40,000 | ₹30,000–₹1.5 lakh/year | ₹2–₹8+ lakh/year |
| Future scale/headroom | ₹25,000–₹1 lakh | ₹1–₹4 lakh | Quote based on measured chain/depth volume |
| **Total planning envelope** | **₹1–₹3 lakh** | **₹4–₹15 lakh** | **₹25 lakh+; enterprise quote required** |

The V3.1 procurement cap must be set only after written quotations and licence
answers. The preferred decision minimizes recurring vendors; it does not choose a
cheaper feed over legally retainable, complete and reproducible evidence.

## Reliability and validation requirements

Marketing uptime claims are not acceptance evidence. Trials must measure session
coverage, timestamp monotonicity, duplicates, gaps, corrections, reconnect replay,
late arrivals, contract-master changes, corporate-action adjustments and agreement
between vendor and exchange totals. Provider health is reported separately from
market closure and instrument inactivity. A provider outage never authorizes
fabricated candles, forward-filled OI or silently reconstructed chains.

## Unresolved provider questions

The following block procurement and V3.1 ingestion:

1. Dhan: exact five-year coverage by segment; expired option/future availability
   dates; full-chain historical availability; inactive security-ID retention;
   corporate-action adjustment policy; corrections; bulk limits; SLA; raw/local,
   post-termination, derived, training and backup rights.
2. TrueData: historical depth per segment/interval; historical full-chain and
   bid/ask entitlement; expired-contract master; quotas; replay/corrections; SLA;
   exact exchange fees; archive, derived, model-training, backup and termination
   rights; India news archive depth and article-text rights.
3. NSE/BSE: exact products required for historical F&O/options, security masters,
   actions and announcements; automated download/API method; exchange agreements;
   internal research, derived/model, backup and retention terms; current quote.
4. Dhan/TrueData cross-source semantics: timestamp definitions, session calendars,
   adjustment state, volume/OI units and revision identifiers.
5. Upstox fallback: Plus price, complete expired-contract coverage, quotas and all
   research retention rights.
6. RBI/MoSPI: permitted automated retrieval mechanism, revision identifiers and
   historical release-time availability.
7. News: licensed archive depth, headline/body retention, embeddings/model use,
   citations, deletion/retraction duties and cost for TrueData versus LSEG.

Every unanswered commercial or legal item remains **UNKNOWN — PROVIDER
CONFIRMATION REQUIRED**.

## V3.1 entry requirements

V3.1 may start only after repository-owner approval of this strategy and all of
the following evidence is recorded without secrets:

- written Dhan and TrueData licence answers covering local raw retention,
  post-termination use, derived data, model training, backups and private internal
  use, or an approved fallback selection;
- dated provider quotes, exchange pass-through fees, approved first-year budget
  and confirmation that no redistribution/SaaS rights are being purchased;
- representative coverage samples or vendor-generated inventories proving the
  required historical depth, expired contracts, OI, timestamps and symbol history;
- approved NSE/BSE corporate-action, announcement and reference acquisition terms;
- approved news scope, or an explicit decision to defer licensed news while using
  only permitted official events;
- a data protection and deletion/termination procedure tied to licensing metadata;
- a measured storage pilot and approved expected capacity with independent backup;
- canonical schema/interface review, temporal identifier policy, source priority,
  conflict tolerances, checksums, manifests and fail-closed entitlement fields;
- a V3.1 acquisition plan that is idempotent, restartable, rate-limit aware,
  deterministic, survivorship-safe and leakage-tested.

Until those gates pass, V3.1 historical ingestion remains blocked. Version 2 APIs,
collectors, repositories and behavior remain unchanged.
