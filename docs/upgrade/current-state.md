# Current State

## Architecture

- FastAPI backend with async SQLAlchemy and PostgreSQL.
- Vue 3 + Vite frontend with Axios, Pinia, Chart.js, and WebSocket updates.
- Redis is used for events and ARQ worker scheduling.
- DexScreener is the market-data source; Jupiter/Solana adapters support execution.

## Trading Flow

```text
DexScreener -> MarketSnapshot -> Features -> RiskAssessment -> Strategy -> Signal
-> ExecutionEngine -> Position/Trade -> Position Monitor
```

The worker processes watched pairs. PAPER mode uses virtual execution; LIVE mode uses the wallet/Jupiter adapter.

## Existing Controls

- Maximum open positions.
- Maximum daily loss based on closed losing positions.
- Minimum liquidity.
- Risk score limits in strategies.
- Stop, pause, and emergency-stop bot states.
- Paper slippage simulation.

## Known Gaps

- Incoming snapshots were not classified for stale, invalid, or impossible values.
- Risk calculations returned a score but no explicit decision or sizing recommendation.
- There was no centralized circuit breaker or auditable decision record.
- Position sizing used a fixed 2% virtual balance allocation.
- Holder, whale, contract-authority, and market-wide data are not currently available from the configured data sources.
