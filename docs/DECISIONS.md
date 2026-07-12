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
