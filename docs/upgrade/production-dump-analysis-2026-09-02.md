# Production Dump Analysis

Analysis source: `db_dump/dump-memex-202609020010.sql`

The dump is a PostgreSQL custom archive created by `pg_dump 17.0` from PostgreSQL `16.15`. It was restored into an isolated PostgreSQL 18 analysis container. The production database and the original dump were not modified.

## Inventory

| Area | Rows |
| --- | ---: |
| Users | 1 |
| Chains | 1 |
| Tokens | 44 |
| Pairs | 43 |
| Market snapshots | 3,053 |
| Features | 2,647 |
| Risk assessments | 2,647 |
| Predictions | 2,647 |
| Signals | 5,294 |
| Trade decisions | 5,363 |
| Positions | 12 |
| Trades | 69 |
| Audit logs | 39 |

The dump reports migration `007_position_risk_telemetry`.

## Runtime State At Dump Time

```text
Bot: RUNNING
Mode: PAPER
Circuit: RUNNING
Stored daily loss: -37.24 USD
Open positions: 2
Closed positions: 10
```

The dump is a small, short-window paper sample. It is useful for finding implementation problems, but not sufficient to claim strategy profitability.

## PnL

```text
Closed positions: 10
Wins: 1
Losses: 9
Closed PnL: -34.66 USD
Open PnL: +0.08 USD
Gross profit: +2.58 USD
Gross loss: -37.24 USD
Profit factor: 0.069
Worst closed loss: -16.14 USD
```

The system is losing because nine of ten closed positions were losses. The single profitable position does not offset the stop-loss losses.

## Strategy Performance

| Strategy | Closed positions | PnL | Wins | Losses |
| --- | ---: | ---: | ---: | ---: |
| `ml_sniper_v1` | 10 | `-31.94` | 2 | 8 |
| `momentum_v1` | 2 | `-2.64` | 0 | 2 |

Both strategies are negative in this sample. `ml_sniper_v1` is responsible for most of the loss because it produced most of the BUY decisions. It should not be allowed to use full allocation merely because its model probability is high.

## Critical Exit Finding

One `MEMECOIN/SOL` position generated:

```text
47 trades total
1 BUY
46 SELL operations
46 partial exits
```

The total sold amount is approximately equal to the entry amount, so the position was gradually liquidated through many partial sells. This indicates a logic problem, not merely market behavior:

- The same take-profit/exit condition can trigger on every monitor cycle.
- `partial_exit_count` is not being used as a hard cap per exit stage.
- The position can generate dozens of sell transactions for one signal.
- Fees and execution noise accumulate unnecessarily.
- The result can look active while masking an over-frequent exit loop.

Recommended correction:

1. Add an explicit `exit_stage` or `last_exit_reason` state.
2. Allow each partial-exit stage only once.
3. Change the target after a partial exit or mark that target as consumed.
4. Add a minimum time/price delta between partial exits.
5. Never sell more than the current remaining amount.
6. Record each exit fraction and remaining amount in the ledger.

## Entry and Decision Funnel

```text
BUY signals: 510
ALLOW/REDUCE BUY decisions: 510
Positions: 12
```

The decision layer allowed many BUY decisions, but only a small number became positions. This means execution/duplicate-position/portfolio limits are doing most of the filtering after the strategy has already called BUY. The system should expose a separate reason for:

```text
SIGNAL_BUY
RISK_ALLOW
PORTFOLIO_BLOCK
DUPLICATE_POSITION
EXECUTION_FAILED
POSITION_CREATED
```

Without this funnel, it is difficult to distinguish a strategy problem from an execution or portfolio-guard problem.

## Prediction Finding

```text
Probability < 0.5: 932 records, average confidence 0.893
Probability >= 0.8: 1,635 records, average confidence 0.911
```

Confidence is high in both low-probability and high-probability buckets. This confirms that confidence must not be used as a direct position-size multiplier until calibration is implemented.

Required before model-driven sizing:

- actual forward outcome labels;
- time-based split;
- walk-forward validation;
- probability calibration;
- Brier score;
- precision by probability bucket;
- performance by risk and liquidity bucket.

## Data Quality

```text
Missing liquidity: 439 of 3,053 snapshots, approximately 14.4%
Missing price: 0
Negative price/liquidity/volume: 0
```

Missing liquidity is material. A missing liquidity value must not be interpreted as healthy liquidity. New entries should be blocked or put into `WAIT`; exits should remain enabled.

The dump also contains 1,254 snapshots with liquidity below `$5,000`. These should not receive the same sizing as healthy pools.

## Risk and Liquidity

Risk assessments:

```text
Risk <= 50: 494 records
Risk > 50: 477 records
```

The strategy and risk layers need a hard contract: a BUY signal must not become an executable entry if risk is above the configured threshold. A high model probability must never override this veto.

## Position Sizing Finding

The dump contains position sizing values from decisions, but the largest position was approximately `$10`-equivalent while the configured PAPER balance was `$100`. This is directionally conservative, but the system must verify sizing against:

- account equity after realized PnL;
- remaining portfolio heat;
- adaptive stop distance;
- liquidity;
- current exposure;
- strategy allocation multiplier.

Using a static balance for every new trade will overstate available capital after losses.

## Highest-Priority Fixes

### P0: Fix before more paper data

1. Stop repeated partial-exit loops with one-time exit stages.
2. Add a hard maximum loss per position.
3. Use an immutable initial stop that can tighten but never widen after entry.
4. Block missing-liquidity entries explicitly.
5. Reconcile daily loss from position outcomes and expose the calculation window.
6. Add an execution outcome for every allowed BUY that did not create a position.

### P1: Improve entry quality

1. Add strategy allocation multipliers.
2. Quarantine a strategy after a configurable rolling loss sample.
3. Add pair cooldown after a loss.
4. Add portfolio heat and pair concentration limits.
5. Require minimum data history before allowing a new token entry.
6. Add provider agreement checks before entry.

### P1: Improve exit quality

1. Add `exit_stage`, `exit_fraction`, and `remaining_amount` to the exit ledger.
2. Add thesis invalidation based on momentum/buy-pressure reversal.
3. Add liquidity shock exits.
4. Add MAE/MFE-based stop tuning.
5. Add minimum interval and price movement between staged exits.

### P2: Model discipline

1. Do not use `confidence` as calibrated certainty.
2. Build outcome labels from information available at entry time only.
3. Evaluate model performance by probability bucket and market regime.
4. Use walk-forward validation before changing production model weights.

## Recommended Safe Operation

Keep production in PAPER/SAFE_MODE or a deliberately limited paper profile until:

```text
No repeated partial-exit loop
No unexplained execution failures
No missing-liquidity normal entries
Daily loss accounting reconciles
At least 50-100 closed paper positions
Exit reasons are complete
Prediction calibration is measured
```

No profitability is inferred from this dump. The immediate goal is to eliminate mechanical loss amplification and make every decision auditable.
