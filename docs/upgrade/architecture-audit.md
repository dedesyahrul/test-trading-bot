# Architecture Audit

## P0 Findings

1. Data quality was implicit. A malformed or stale market snapshot could reach feature and strategy evaluation.
2. Risk and strategy decisions were coupled through conventions rather than a structured risk decision.
3. Position sizing was fixed and did not account for volatility or liquidity.
4. There was no persistent decision ledger connecting snapshot, risk, signal, and execution.
5. Bot state existed as a kill switch, but daily loss, consecutive failures, and data failure did not centrally transition it to a safe mode.
6. Worker pipeline failures were previously difficult to diagnose and one schema mismatch stopped all paper trading.

## Deferred Intelligence

Holder growth, whale behavior, wallet clustering, contract authorities, market breadth, and LLM analysis are `[DEFERRED]` until reliable data sources and validation datasets are available.

## Compatibility Strategy

The upgrade extends current models and services. Existing endpoints, signal types, and execution modes remain available. New fields are nullable and new tables are additive.
