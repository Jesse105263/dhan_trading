# Architectural Decisions

Decision 001

Docker manages all infrastructure.

Reason

Portable development.

---

Decision 002

PostgreSQL is the primary database.

Reason

Scalability.

---

Decision 003

Redis stores only real-time data.

Reason

Performance.

---

Decision 004

CSV files are temporary.

Reason

Database-first architecture.

---

Decision 005

LLMs never execute trades.

Reason

Trading must remain deterministic.

---

Decision 006

One milestone per session.

Reason

Maintain documentation quality.

---

Decision 007

Every command must specify:

- Application
- Folder
- Terminal
- Virtual Environment

Reason

Remove ambiguity.

---

Decision 008

No versioned filenames.

Use Git history instead.

Reason

Cleaner project.
---

Decision 009

Available expiries are derived from active `derivative_contracts` rows rather than stored in a separate table.

Reason

Derivative contracts are already the normalized source of truth. Duplicating expiry state would create avoidable consistency and lifecycle risks.

---

Decision 010

All expiry-selection policy belongs to `ExpiryService`; repositories provide data only.

Reason

Collectors, strategies and future contract-selection components must use one deterministic implementation for eligibility, nearest-expiry, next-expiry and monthly-expiry behavior.

## ADR — Persist option-chain runs separately from legacy option quotes

The production collector writes to normalized `option_chain_runs` and `option_chain_quotes` tables rather than the legacy `option_quotes` table. A run ID provides transactional lineage, request metrics, failure state and replayability while preserving the old table for backward compatibility.

## Option analytics are deterministic and source-run scoped

Option analytics are calculated only from persisted `option_chain_quotes`. The analytics layer cannot call market-data APIs or perform expiry selection. ATM ties resolve to the lower strike. Nearby metrics use an explicit count of strikes on each side of ATM. A source run is rejected when stale, incomplete or internally inconsistent. Reprocessing is idempotent by `source_run_id`.

## ADR — Dedicated option data pipeline

The option data workflow remains separate from the production equity pipeline. This preserves backward compatibility and allows option-specific retry, throttling, symbol configuration, failure isolation, and scheduler locking without changing stable equity behavior. Partial per-underlying failure is recorded but does not fail the operational run when other configured underlyings succeed.

## ADR — Consecutive Analytics Comparison

Option changes are calculated only between a snapshot and its immediately preceding persisted analytics snapshot for the same normalized underlying and expiry. Comparisons across expiries, underlyings, duplicate snapshots or non-increasing capture times are rejected. This prevents downstream ranking and signals from silently comparing incompatible market states.

## Ranking methodology

Ranking v1 uses deterministic min-max normalization across the eligible universe with fixed weights: liquidity 35%, activity 30%, volatility 20%, directional structure 15%.

## Contract selection policy

Contract selection consumes persisted ranking runs and the exact option-chain source run linked through analytics. It selects at most one CE and one PE per ranked underlying using deterministic distance, spread, open-interest, volume, strike and security-id ordering. Downstream components must not reimplement contract eligibility.

## Long-option risk model

For Version 1, contract selection produces long-option candidates only. Maximum loss is therefore defined as premium paid. Position size is the largest whole-lot quantity that satisfies the configured available-capital, single-trade loss, total exposure and per-underlying concentration constraints. Both approvals and rejections are persisted for auditability.

## Deterministic long-option signal policy

Version 1 signals are generated only from approved risk assessments. A CE approval maps to a bullish buy-to-open signal and a PE approval maps to a bearish buy-to-open signal. When both sides exist for the same underlying and expiry, each is explicitly marked as a leg of a long-straddle context. Confidence is a fixed weighted combination of ranking, contract, liquidity, activity and volatility scores. Signal generation never sends orders.

## Persisted-lineage replay

Market replay consumes only committed database state. Live APIs and recomputation are excluded so identical source lineage produces the same ordered event types and payload semantics.

### Backtesting uses persisted marks only
Backtests use signal entry references and subsequent persisted `option_chain_quotes`. Missing future marks are recorded as skipped trades rather than fabricated prices.

## Decision: Standard-library, read-only API boundary

The first product API uses WSGI from the Python standard library and adds no web-framework dependency. All routes are GET-only, versioned under `/api/v1`, bounded to 100 rows per list request and backed by a dedicated read repository. This keeps the production dependency surface small while establishing a stable HTTP contract.

## Decision: Separate HTTP-only dashboard boundary

The private dashboard is a standard-library WSGI application and a separate process from the read API. It uses a small HTTP GET client rather than importing the API repository or database layer. Server-side rendering keeps the dashboard dependency-free and same-origin browser behavior simple, while the explicit API base URL preserves the `/api/v1` boundary. Both processes bind to loopback by default.

## Decision: Persist alerts before isolated delivery

Alert events are derived only from committed signal, risk and pipeline records. The unique `(source_type, source_id)` identity makes generation idempotent. Delivery is a separate adapter step, with every attempt persisted and sanitized. A successfully delivered alert/channel pair is never delivered again; failed channels can retry without duplicating the alert event. Delivery cannot mutate source data or invoke broker execution.

## Decision: Application-grounded Copilot with provider isolation

Copilot evidence retrieval is deterministic and occurs only through `/api/v1` before any model call. The application, not the model, selects resources, filters symbols and appends verified run/item citations. Providers receive evidence text but no tools or credentials for PostgreSQL, Dhan or execution. Local synthesis is always available, and provider failures fall back without losing evidence or exposing secrets.
