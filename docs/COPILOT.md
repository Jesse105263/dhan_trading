# Private AI Copilot

## Purpose

The Copilot answers research questions using only persisted platform evidence obtained through the stable `/api/v1` HTTP API. It supports rankings, contract selections, risk decisions, signals and backtests.

Every evidence-backed answer includes verified citations in this form:

```text
[resource:run_id:item_id]
```

The Copilot does not query PostgreSQL, call Dhan, trigger analytics, modify platform state or place orders.

## Start locally

Start the read API in one terminal:

```bash
python -m scripts.run_read_api
```

Ask a question with deterministic local synthesis:

```bash
python -m scripts.ask_copilot \
  "Explain the latest ranking" \
  --symbol RELIANCE
```

The local provider is the default. It is useful for private operation, testing and environments without model credentials.

## Optional OpenAI provider

Set the API key in the environment and select the provider:

```bash
export OPENAI_API_KEY="your-key"
python -m scripts.ask_copilot \
  "Compare the latest opportunities" \
  --provider openai
```

The model is configurable with `--model` or `OPENAI_COPILOT_MODEL`. The adapter uses the standard-library HTTP client and the OpenAI Responses API. See the official [OpenAI text-generation guide](https://developers.openai.com/api/docs/guides/text?api-mode=responses).

## Grounding and failure behavior

- Question keywords select only relevant API resources; general questions inspect all supported research resources.
- `--symbol` restricts item evidence to one normalized underlying.
- Model input contains only the question and retrieved evidence.
- Verified platform citations are appended by the application, independent of model output.
- Missing evidence is reported explicitly rather than inferred.
- Model or network failures are sanitized and fall back to local evidence synthesis.
- Execution requests are refused before evidence retrieval or provider invocation.

## Safety boundary

The Copilot is explanatory only. It cannot submit, preview or execute an order and does not guarantee returns. The optional model provider has no tools and receives no database or broker capability.

## Version 2 analyst specialization

V2.1.3 reuses provider isolation and pre-retrieval refusal for a specialized AI
Trading Analyst over deterministic opportunity evidence. Unlike the general
Version 1 Copilot, its packet includes Feature Store, Market Memory, Historical
Outcomes, Similarity, Trade Opportunity and Event lineage. See
`docs/AI_TRADING_ANALYST.md`.
