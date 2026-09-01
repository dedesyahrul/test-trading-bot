# MemeX Database Analysis

Analysis date: 2026-08-30

## Scope

Read-only analysis of the active PostgreSQL database. No trading data was modified.

## Inventory

| Area | Rows |
| --- | ---: |
| Users | 2 |
| Chains | 1 |
| Tokens | 32 |
| Pairs | 31 |
| Watched pairs | 7 |
| Market snapshots | 5,231 |
| Features | 1,191 |
| Risk assessments | 971 |
| Predictions | 971 |
| Signals | 1,942 |
| Trade decisions | 808 |
| Positions | 25 |
| Trades | 47 |
| Audit logs | 12 |

Migration head is `006_decision_score`.

## Current Runtime

```text
bot state       RUNNING
trading mode    PAPER
circuit state   SAFE_MODE
daily loss      -549.68 USD
```

The combination `RUNNING + SAFE_MODE` is intentional only if the state fields have different meanings. The UI and API should expose this distinction clearly. Otherwise, it is a state-model inconsistency that can confuse operators.

## Performance Findings

- Closed positions: 21.
- Closed PnL: `+357.16 USD`.
- Open positions: 4, current unrealized PnL: `-9.15 USD`.
- Wins/losses among closed positions: 10/11.
- Profit factor: approximately `1.48`.
- Average winning position: `+110.11 USD`.
- Average losing position: `-67.63 USD`.
- Three large losses contributed approximately `-449.93 USD`.
- Maximum observed closed loss: approximately `-180.71 USD`.

The positive aggregate PnL should not be treated as proof of profitability. The sample is small, time coverage is short, and the largest losses are concentrated.

## Strategy Findings

| Strategy | Closed positions | PnL | Wins | Losses |
| --- | ---: | ---: | ---: | ---: |
| `ml_sniper_v1` | 18 | `+504.01` | 10 | 8 |
| `momentum_v1` | 3 | `-146.85` | 0 | 3 |

`momentum_v1` should not receive equal allocation until it passes a paper validation sample. Strategy-level capital allocation and automatic quarantine are higher-value upgrades than adding another strategy.

## Signal Funnel

- BUY signals: 270.
- BUY signals from `ml_sniper_v1`: 247.
- BUY signals from `momentum_v1`: 23.
- Decisions with `ALLOW` or `REDUCE_SIZE`: 85.
- Positions created: 25.

The funnel is not yet fully traceable because position records do not reliably contain the originating decision ID/thesis. Add a direct relationship or immutable correlation ID before training from trade outcomes.

## Data Quality Findings

- Snapshots with missing liquidity: 772 of 5,231, approximately 14.8%.
- Snapshots with missing price: 0.
- Snapshots with missing 24h volume: 0.
- Duplicate pair/timestamp groups: 0.
- Extreme 5-minute changes above the current plausibility threshold: 1.
- Snapshot coverage: approximately 3.5 hours across 31 pairs.

Missing liquidity must be a `WAIT` or reduced-confidence condition for new entries, not an implicit pass. Three hours is not enough for robust regime, calibration, or strategy conclusions.

## Prediction Findings

- Predictions: 971.
- Probability below 0.5: 502 records.
- Probability from 0.8 to 1.0: 403 records.
- Average confidence for probability below 0.5 was approximately 0.886.
- Average confidence for probability at or above 0.8 was approximately 0.938.

This suggests `probability` and `confidence` are measuring different things or confidence is not calibrated. The bot must not use confidence as a substitute for probability. Add out-of-sample labels, Brier score, calibration curves, and walk-forward evaluation before allowing the model to increase position size.

## Concentration Findings

- `STACY/SOL` represented 18 of 25 positions and contributed `+504.01 USD`.
- Other pairs had isolated losses including approximately `-99.75 USD` and `-48.95 USD`.

Aggregate performance is therefore highly dependent on one pair. Add pair concentration, token concentration, chain concentration, and correlated-exposure limits.

## Highest-Value Upgrade Ideas

### P0: Fix measurement and safety

1. Reconcile `daily_loss_usd` with closed PnL, timezone, and reset behavior. Store the calculation window and source rows.
2. Add `decision_id` to positions and trades so every execution maps to one exact decision.
3. Make missing liquidity block or downgrade entries explicitly.
4. Add maximum loss per position and maximum portfolio heat, not only maximum position count.
5. Add a safe-mode recovery policy requiring a deliberate reset and a cooldown period.

The implementation now exposes portfolio and cooldown settings through the existing trading settings schema. Missing liquidity remains an exit-pressure emergency signal, while exits are still allowed so the system does not trap an existing position.

### P1: Improve entry quality

1. Quarantine `momentum_v1` while it has zero wins in the current sample.
2. Require agreement between risk, strategy, and decision score; do not allow a high model probability to override risk.
3. Add minimum sample/history requirements before using a new token or model output.
4. Penalize thin liquidity, missing liquidity, extreme price changes, and abnormal sell pressure in the decision score.
5. Add pair concentration and correlated exposure caps.

### P1: Improve exits

1. Record exit reason categories: stop, target, trailing, thesis invalidation, liquidity shock, and emergency.
2. Measure MAE/MFE per position to determine whether stops are too wide or profits are given back.
3. Use staged exits only when liquidity supports them; otherwise reduce order size and wait for execution quality.
4. Add a thesis-invalidated exit when momentum and buy pressure reverse, independent of fixed TP/SL.
5. Add cooldown after a loss on the same pair to avoid immediate re-entry.

### P2: Make the system learn safely

1. Build a labeled outcome table from entry-time features only.
2. Evaluate predictions by probability bucket and market regime.
3. Track strategy performance by pair, liquidity bucket, volatility bucket, and risk bucket.
4. Use walk-forward validation; do not randomly shuffle time-series data.
5. Promote model versions only through candidate, backtest, paper, approval, and rollback stages.

## Deferred Until Data Exists

Whale intelligence, holder growth, wallet clustering, contract authority analysis, market breadth, and LLM analysis should remain `DEFERRED` until reliable sources and labels are available. Creating values for these fields from existing pair snapshots would produce fake intelligence.

## Recommended Next Implementation Order

1. Reconcile circuit-breaker and daily-loss accounting.
2. Add decision-to-position correlation and execution outcome fields.
3. Add portfolio heat, pair concentration, and cooldown controls.
4. Add MAE/MFE and exit-reason analytics.
5. Calibrate prediction probability and confidence out of sample.
6. Add market regime only after more historical coverage is collected.
