# Upgrade Plan

## Completed P0 Slice

- Data quality classification before intelligence evaluation.
- Structured risk decisions: `ALLOW`, `REDUCE_SIZE`, `WAIT`, `REJECT`, `EMERGENCY`.
- Centralized circuit-breaker checks for bot state, data quality, daily loss, and execution failures.
- Adaptive paper position sizing using risk, volatility, and liquidity.
- Decision ledger records for every evaluated strategy decision.
- Transparent decision score combining momentum, volume, liquidity, prediction availability, market factor, and risk.
- Adaptive stop loss, take profit, trailing/profit-lock logic, exit pressure, and conservative partial exits.
- Entry sizing capped by a configurable maximum risk budget per trade.
- Migration-safe schema extensions.

## Next Increment

- Adaptive exit and staged exits.
- Portfolio exposure and drawdown metrics.
- Market/token regime detection from available snapshots.

## Completed P1 Slice

- Exit assessment is now evaluated from current price, high-water mark, sell pressure, liquidity, and volatility.
- Full manual close remains backward compatible; automated exits may sell a fraction and retain the remaining position.

## Deferred

Whale intelligence, holder/security authority checks, LLM analyst, and advanced model lifecycle remain deferred until data sources and evaluation protocols exist.
