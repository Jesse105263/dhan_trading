# AI Trading Analyst

V2.1.4 release verification confirms grounded local synthesis, exact citations,
explicit insufficient evidence and refusal before evidence/provider access.

## Purpose

V2.1.3 explains and compares persisted deterministic Trade Opportunity Engine
records. It does not discover, calculate, modify or execute opportunities.

## Evidence model and grounding

`trading-analyst-evidence-v1` is assembled by the application before synthesis. It
contains opportunity facts and underlying reference levels, evidence state,
ranking score, win rate, expected value, risk/reward, evidence quality, sample
size, Feature Store values, Market Memory, Similarity diagnostics, persisted
Historical Outcomes, event context, limitations and exact lineage.

The provider receives sanitized application evidence and identifiers only. It has
no PostgreSQL, Dhan, broker, alert or execution access. Citations are attached by
the application, never trusted from generated prose.

## Outputs and insufficient evidence

Responses separate Facts, Historical evidence, Interpretation, Reasons for,
Reasons against and Limitations. Ranking score is never called confidence.
Levels are explicitly underlying reference levels, not option-premium prices.
For a non-eligible opportunity the analyst states `INSUFFICIENT_EVIDENCE` and
does not emit entry, stop, targets, win rate or expected value.

## Providers, refusals and failure behavior

Deterministic local synthesis is the default. The existing isolated OpenAI
Responses provider may be selected explicitly by the CLI when credentials are
configured. It receives no tools. Provider failure is sanitized and falls back to
local synthesis. Verification never invokes an external model.

Order placement, execution, Dhan submission, auto-trading, bypassing risk
controls, paper-to-live conversion and profit guarantees are refused before
evidence retrieval and before provider invocation.

## API and CLI

- `POST /api/v2/analyst/questions`
- `POST /api/v2/analyst/opportunities/{opportunity_id}/explain`
- `POST /api/v2/analyst/compare`
- `python -m scripts.ask_trading_analyst --opportunity-id UUID --question "..."`

Questions are bounded to 2,000 characters and comparisons to five unique
opportunities. These are research commands, not trading commands. No response or
conversation persistence is added: evidence packets are reproducible from
immutable lineage, while storing generated prose would retain unnecessary
history and duplicate derived output.

## Limitations

The analyst is limited by persisted features, classified outcomes, similarity
coverage and explicitly linked events. Historical behavior is not a guarantee.
It cannot fill missing evidence, infer news sentiment, calculate option-premium
levels, or create confidence values.
