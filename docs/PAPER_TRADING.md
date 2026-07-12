# Isolated Paper Trading

## Purpose

Paper trading creates simulated orders, fills and positions from persisted approved option signals. All prices come from completed persisted option-chain snapshots. No paper-trading component imports a Dhan client, sends a broker request or modifies source signal and market-data records.

## Apply the schema

```bash
python -m services.migration_runner
```

Migration `017_paper_trading.sql` creates isolated paper orders, positions, fills and ordered position events.

## Commands

Open a simulated position from a persisted signal:

```bash
python -m scripts.paper_trade open <signal_id>
```

Mark an open position to the newest later persisted price:

```bash
python -m scripts.paper_trade mark <position_id>
```

Close an open position using the newest persisted exit mark:

```bash
python -m scripts.paper_trade close <position_id>
```

List position state and P&L:

```bash
python -m scripts.paper_trade status --status OPEN --limit 20
```

All transition commands accept an ISO `--as-of` time. Open and close commands also accept `--slippage-bps` and `--transaction-cost-bps`.

## State and attribution

- A signal can produce at most one filled BUY entry and one paper position.
- Missing entry prices persist a rejected order with `NO_PERSISTED_MARK` and no position.
- A filled entry creates a BUY fill, OPEN position and `OPENED` audit event atomically.
- Marks update unrealized P&L and append a `MARKED` event.
- A close creates a SELL order and fill, realizes P&L and appends a `CLOSED` event atomically.
- Invalid transitions and unavailable later prices leave the existing position unchanged.
- Every position retains signal, risk run, assessment, selection, ranking, analytics and source option-chain lineage.
- Every fill retains the exact persisted reference-run ID and price.

Rejected entry orders may be retried when a persisted price later becomes available. Filled entries and exits are database-deduplicated.

## Safety boundary

Paper orders exist only in `paper_trade_*` tables. They are not broker orders and cannot be promoted or submitted to Dhan. The service contains no Dhan dependency, order endpoint or live-execution adapter.
