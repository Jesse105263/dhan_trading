# Version 2 Symbol Intelligence Workspace

V2.1.4 runtime verification confirms persisted symbol intelligence and lineage
remain available without Dhan calls or browser-side analytics.

V2.0.6 provides expiry-aware persisted research before a trading decision. Search
uses `GET /api/v2/symbols?query=...`; the workspace uses
`GET /api/v2/symbols/{symbol}?expiry=YYYY-MM-DD`. Compare mode requests the same
contract for a second symbol and performs no financial calculation.

The workspace presents historical analytics, rankings, selections, risk assessments
and signals. Its timeline merges persisted collection, analytics, ranking, selection,
risk and signal timestamps and filters by event type. Identifiers connect ranking →
selection → risk → signal. Related opportunities use persisted nearby expiries.

Available analytics include ATM/nearby IV, spot and ATM context, OI, PCR, OI changes,
coverage and persisted ranking components. IV percentile, Greeks and a standalone
risk score are explicitly unavailable because the schema does not persist them.
Sizing, exposure, maximum loss and confidence appear only when persisted.

Empty stage, history, comparison and related-expiry data remain valid explicit
states. Routes are GET-only and cannot collect data, calculate policy, call Dhan,
deliver alerts, manage paper positions or execute orders.
