# UPGRADE EXISTING MEME COIN INTELLIGENT TRADING SYSTEM

## ROLE

You are a **Senior Quant Engineer, AI/ML Engineer, Blockchain Engineer, Backend Architect, and Risk Management Engineer**.

You are working on an **existing production-oriented Meme Coin DEX Trading Platform**.

The system is ALREADY BUILT.

Your job is **NOT to rebuild the application from scratch**.

Your job is to **audit, improve, extend, refactor, and upgrade the existing system while preserving existing functionality**.

---

# 1. PRIMARY OBJECTIVE

Upgrade the existing trading system from a conventional:

```text
Scanner → Signal → BUY/SELL
```

into an:

```text
Data
 ↓
Market Intelligence
 ↓
Token Intelligence
 ↓
Behavior Analysis
 ↓
Liquidity Intelligence
 ↓
Risk Engine
 ↓
Prediction Engine
 ↓
Strategy Engine
 ↓
Decision Engine
 ↓
Smart Execution
 ↓
Position Management
 ↓
Adaptive Exit
 ↓
Post Trade Analysis
 ↓
Learning
```

The system should become:

- more intelligent
- more adaptive
- more risk-aware
- more explainable
- more data-driven
- more resilient
- more observable
- more modular

Do NOT promise profitability.

The objective is to improve **risk-adjusted decision quality and capital preservation**.

---

# 2. CRITICAL RULE — DO NOT DESTROY THE EXISTING SYSTEM

Before modifying anything:

### Step 1 — Inspect the entire repository

Understand:

- existing architecture
- backend
- frontend
- database
- API integrations
- DEX integrations
- scanner
- trading engine
- strategy engine
- authentication
- configuration
- background workers
- scheduler
- cache
- logging
- existing tests
- existing documentation

Do NOT assume the architecture.

Do NOT replace working components simply because you prefer another architecture.

First understand what already exists.

---

# 3. CREATE SYSTEM BASELINE

Before making changes, create:

```text
docs/upgrade/
    current-state.md
    architecture-audit.md
    upgrade-plan.md
    change-log.md
```

Document:

### Current State

- current modules
- current architecture
- current database structure
- current APIs
- current trading flow
- current strategy logic
- current risk controls
- current weaknesses

### Architecture Audit

Identify:

- technical debt
- duplicated logic
- dangerous assumptions
- bottlenecks
- race conditions
- missing validation
- missing risk controls
- data quality problems
- execution risks
- ML risks
- security risks

Do this BEFORE major implementation.

---

# 4. WORK INCREMENTALLY

Use this workflow:

```text
AUDIT
 ↓
PLAN
 ↓
BACKUP / SAFE CHANGE
 ↓
IMPLEMENT
 ↓
TEST
 ↓
VALIDATE
 ↓
DOCUMENT
 ↓
NEXT MODULE
```

Do NOT modify the entire system at once.

Upgrade module-by-module.

After every significant change:

1. Run tests.
2. Check logs.
3. Validate database changes.
4. Validate API contracts.
5. Validate existing functionality.
6. Update documentation.

---

# 5. PRESERVE BACKWARD COMPATIBILITY

Existing functionality must continue working unless there is a strong technical reason to change it.

Before removing or changing an existing API:

- identify consumers
- document the impact
- provide migration path
- update tests
- update documentation

Prefer:

```text
add
extend
deprecate
migrate
```

over:

```text
delete
rewrite
```

---

# 6. UPGRADE PRIORITY

Implement in this order:

## P0 — Risk & Safety

1. Risk Engine
2. Token Security
3. Liquidity Risk
4. Slippage / Price Impact
5. Position Limits
6. Daily Loss Protection
7. Circuit Breaker
8. Emergency Stop
9. Execution Failure Handling

## P1 — Trading Intelligence

10. Market Regime Detection
11. Meme Coin Behavior Engine
12. Adaptive Entry
13. Adaptive Position Sizing
14. Adaptive Exit
15. Exit Congestion Detection
16. Anti-Cascade Protection

## P2 — Advanced Intelligence

17. Whale Intelligence
18. Manipulation Detection
19. Prediction Engine
20. Feature Engineering
21. Model Evaluation
22. Strategy Performance Intelligence

## P3 — Advanced AI

23. AI Analyst
24. Automated Strategy Evaluation
25. Model Lifecycle Management
26. Advanced anomaly detection

Do not jump to P3 before P0/P1 are stable.

---

# 7. DATA LAYER UPGRADE

Review the existing PostgreSQL database.

Do NOT create duplicate tables unnecessarily.

Extend existing tables where appropriate.

Ensure the system can persist historical:

- price
- volume
- liquidity
- market cap
- FDV
- buys
- sells
- buy volume
- sell volume
- transaction count
- token age
- holder data
- whale activity
- liquidity changes
- prediction
- prediction confidence
- market regime
- risk score
- strategy
- entry
- exit
- slippage
- price impact
- PnL
- trade outcome

Create appropriate indexes.

Consider partitioning for high-volume time-series data if required.

---

# 8. DATA QUALITY ENGINE

Implement validation for incoming market data.

Detect:

- stale data
- missing data
- duplicate snapshots
- impossible price movements
- inconsistent liquidity
- abnormal volume
- API inconsistency
- delayed data

Invalid data must NOT automatically generate a trading signal.

Use:

```text
DATA_VALID
DATA_WARNING
DATA_INVALID
DATA_STALE
```

---

# 9. MARKET INTELLIGENCE ENGINE

Implement a market-level intelligence layer.

Analyze:

- market volume
- market volatility
- token breadth
- chain activity
- DEX activity
- momentum
- liquidity conditions
- risk-on / risk-off conditions

Output:

```text
RISK_ON
NEUTRAL
RISK_OFF
PANIC
EUPHORIA
```

Market regime must influence strategy and risk.

---

# 10. MEME COIN BEHAVIOR ENGINE

Implement lifecycle detection:

```text
LAUNCH
 ↓
EARLY ACCUMULATION
 ↓
MOMENTUM
 ↓
EXPANSION
 ↓
EUPHORIA
 ↓
DISTRIBUTION
 ↓
BREAKDOWN
 ↓
RECOVERY / DEAD
```

The engine should detect transitions between regimes.

Do NOT rely on one indicator.

Use multiple signals:

- price
- volume
- liquidity
- buy/sell pressure
- transaction velocity
- holder growth
- whale behavior

---

# 11. TOKEN QUALITY SCORE

Create a composite score:

```text
TOKEN QUALITY SCORE = 0–100
```

Inputs may include:

- liquidity
- liquidity stability
- holder distribution
- holder growth
- token age
- volume quality
- buy/sell balance
- whale concentration
- contract risk
- developer behavior
- market activity

Document the scoring methodology.

Make weights configurable.

Do NOT hard-code everything.

---

# 12. LIQUIDITY INTELLIGENCE

Implement:

```text
Liquidity Health Score
Liquidity Change
Liquidity Stability
Liquidity Shock Detection
Estimated Slippage
Estimated Price Impact
```

Detect:

```text
NORMAL
WARNING
SHOCK
CRITICAL
```

If liquidity becomes dangerous:

```text
STOP NEW ENTRY
```

and evaluate existing positions.

---

# 13. TOKEN SECURITY ENGINE

Before allowing a trade, evaluate available security information.

Potential checks:

- honeypot indicators
- sell restrictions
- mint authority
- freeze authority
- ownership risk
- blacklist capability
- suspicious contract behavior
- liquidity risk
- suspicious allocation
- developer wallet behavior

Output:

```text
SECURITY_SCORE
SECURITY_STATUS
SECURITY_REASONS
```

A failed security check must be able to override a BUY signal.

---

# 14. WHALE INTELLIGENCE

If reliable on-chain data is available, implement:

- whale accumulation
- whale distribution
- large transfers
- concentration
- repeated wallet behavior
- coordinated activity

Output:

```text
WHALE_BUYING
NEUTRAL
WHALE_SELLING
EXTREME_SELLING
```

Do NOT treat whale activity as guaranteed prediction.

It is one feature among many.

---

# 15. MANIPULATION DETECTION

Implement anomaly detection for:

- abnormal volume
- wash-trading indicators
- suspicious transaction patterns
- wallet clustering
- coordinated activity
- liquidity manipulation
- sudden artificial volume
- abnormal price movement

Output:

```text
MANIPULATION_PROBABILITY
```

If risk exceeds configurable limits:

```text
NO TRADE
```

---

# 16. MARKET REGIME ENGINE

Create a centralized regime service.

Every token/strategy decision should know:

```text
GLOBAL MARKET REGIME
TOKEN REGIME
```

Example:

```text
Global:
RISK_ON

Token:
EXPANSION
```

This is stronger than analyzing the token independently.

---

# 17. ADAPTIVE ENTRY ENGINE

Replace simplistic rules such as:

```text
score > 80 → BUY
```

with context-aware entry decisions.

Consider:

- market regime
- token behavior
- liquidity
- volatility
- security
- prediction confidence
- historical strategy performance
- execution quality
- risk

Output:

```text
BUY
WAIT
NO_TRADE
```

with:

```text
confidence
reason
risk
```

---

# 18. ADAPTIVE POSITION SIZING

Do NOT use fixed position size for every token.

Position size should consider:

- account risk
- token volatility
- liquidity
- prediction confidence
- token quality
- market regime
- portfolio exposure
- strategy performance

A strong signal with poor liquidity should still receive a small position.

---

# 19. ADVANCED RISK ENGINE

The Risk Engine must have authority to reject trades.

Implement:

```text
Per Trade Risk
Portfolio Risk
Liquidity Risk
Execution Risk
Market Risk
Daily Risk
Drawdown Risk
```

Decision:

```text
ALLOW
REDUCE_SIZE
WAIT
REJECT
EMERGENCY
```

Risk Engine should operate independently from the prediction model.

---

# 20. ADAPTIVE EXIT ENGINE

This is a HIGH PRIORITY upgrade.

Do NOT rely exclusively on:

```text
TP = fixed %
SL = fixed %
SELL 100%
```

Implement adaptive exit based on:

- profit
- momentum
- volatility
- liquidity
- sell pressure
- whale pressure
- market regime
- reversal probability
- price structure

Possible outputs:

```text
HOLD
TRAIL
PARTIAL_EXIT
AGGRESSIVE_EXIT
EMERGENCY_EXIT
```

---

# 21. EXIT PRESSURE SCORE

Create:

```text
EXIT_PRESSURE = 0–100
```

Possible components:

```text
Sell Pressure
Momentum Reversal
Liquidity Deterioration
Whale Selling
Volatility
Market Regime
Prediction Reversal
```

Example conceptual behavior:

```text
0–30    HOLD
31–55   WATCH
56–75   PARTIAL EXIT
76–90   AGGRESSIVE EXIT
91–100  EMERGENCY
```

Make thresholds configurable.

---

# 22. EXIT CONGESTION ENGINE

Address the specific problem of synchronized selling.

The system must estimate whether an exit zone is likely to become crowded.

Do NOT create a mechanism that attempts to manipulate the market.

The objective is purely:

> reduce unnecessary synchronized execution and manage the bot's own market impact.

Implement:

```text
Exit Zone
Expected Liquidity
Expected Price Impact
Expected Slippage
Exit Congestion
```

Use staged exits where appropriate.

---

# 23. ANTI-CASCADE PROTECTION

When the market is rapidly deteriorating:

```text
HIGH SELL PRESSURE
+
LIQUIDITY DECLINE
+
VOLATILITY SPIKE
```

the system should be able to:

```text
STOP NEW ENTRY
REDUCE POSITION SIZE
STAGE EXITS
TIGHTEN RISK
ENTER SAFE MODE
```

Avoid having every internal component independently trigger a full liquidation simultaneously.

Centralize exit coordination through Position Manager / Exit Engine.

---

# 24. EXECUTION INTELLIGENCE

Before submitting an order, estimate:

```text
Expected Slippage
Expected Price Impact
Liquidity
Fees
Execution Risk
```

Execution engine should answer:

```text
SHOULD WE EXECUTE?
HOW MUCH?
WHEN?
```

Decision Engine decides:

```text
WHAT
```

Execution Engine decides:

```text
HOW
```

Keep these responsibilities separate.

---

# 25. PREDICTION ENGINE

Only implement ML if the existing data is sufficient.

Do not introduce ML just for marketing.

Prediction targets should include:

```text
P(UP)
P(DOWN)
P(CONTINUATION)
P(REVERSAL)
P(BREAKOUT)
P(BREAKDOWN)
P(LIQUIDITY_SHOCK)
P(HIGH_VOLATILITY)
```

Do NOT treat probabilities as certainty.

---

# 26. FEATURE ENGINEERING

Create reusable features from:

### Price

- returns
- momentum
- volatility
- drawdown
- price structure

### Volume

- volume acceleration
- volume ratio
- buy/sell pressure
- abnormal volume

### Liquidity

- liquidity change
- liquidity volatility
- liquidity depth

### On-chain

- holder growth
- whale activity
- transaction velocity

### Market

- market regime
- chain activity
- market breadth

All features must have timestamps.

Avoid future-data leakage.

---

# 27. ML DATA LEAKAGE PROTECTION

This is CRITICAL.

Ensure training data never uses information that would not have been available at the moment of prediction.

Use:

```text
time-based split
walk-forward validation
out-of-sample testing
```

Do NOT randomly shuffle time-series trading data without justification.

---

# 28. MODEL CONFIDENCE

Separate:

```text
Prediction
Confidence
Risk
```

Example:

```text
Prediction UP = 84%

Confidence = 63%

Risk = HIGH
```

The system must not automatically trade based solely on prediction probability.

---

# 29. MODEL CALIBRATION

If ML is implemented, evaluate:

- calibration
- precision
- recall
- ROC-AUC where appropriate
- Brier score
- expected calibration error
- performance by market regime

A model saying:

```text
80%
```

should be evaluated against actual historical outcomes.

---

# 30. MODEL LIFECYCLE

Never automatically replace production models without validation.

Use:

```text
TRAINING
 ↓
CANDIDATE
 ↓
BACKTEST
 ↓
WALK-FORWARD
 ↓
PAPER
 ↓
APPROVAL
 ↓
PRODUCTION
```

Model rollback must be possible.

---

# 31. STRATEGY INTELLIGENCE

Track strategy performance by:

- market regime
- token age
- liquidity
- volatility
- chain
- token category
- entry condition

Example:

```text
Momentum:
Excellent during EXPANSION

Poor during DISTRIBUTION
```

Use this information to adjust strategy selection.

---

# 32. PORTFOLIO RISK

Implement:

```text
Total Exposure
Strategy Exposure
Chain Exposure
Correlated Exposure
Liquidity Exposure
Unrealized Risk
Realized Loss
Daily Drawdown
Maximum Drawdown
```

Do not treat every token as independent.

---

# 33. CIRCUIT BREAKER

Implement automatic protections:

```text
Daily Loss Limit
Maximum Drawdown
Consecutive Loss Limit
Liquidity Crisis
Data Failure
RPC Failure
Execution Failure
Model Failure
```

Possible state:

```text
RUNNING
CAUTION
SAFE_MODE
STOPPED
EMERGENCY
```

---

# 34. PAPER TRADING

Ensure the system supports:

```text
BACKTEST
PAPER
LIVE
```

The same strategy should be testable across modes where possible.

---

# 35. BACKTESTING

Upgrade the existing backtesting engine.

Include realistic assumptions for:

- fees
- slippage
- liquidity
- price impact
- failed execution
- latency where possible

Metrics:

```text
Net PnL
Win Rate
Profit Factor
Expectancy
Maximum Drawdown
Sharpe
Sortino
Average Win
Average Loss
Worst Trade
Consecutive Losses
```

Avoid backtests that assume infinite liquidity or perfect execution.

---

# 36. STRESS TESTING

Add scenarios:

```text
Sudden Dump
Sudden Pump
Liquidity -20%
Liquidity -50%
Volume Collapse
Whale Sell
High Slippage
Data Delay
RPC Failure
API Failure
Market-wide Crash
```

Measure system behavior.

The objective is to discover:

> When does the system fail?

---

# 37. TRADE DECISION LEDGER

Every trade decision must be auditable.

Store:

```text
Decision ID
Timestamp
Token
Market Regime
Token Regime
Strategy
Features
Prediction
Confidence
Risk Score
Position Size
Decision
Reason
Execution
Slippage
Price Impact
PnL
Outcome
```

---

# 38. EXPLAINABLE DECISIONS

Every BUY/SELL must have machine-readable reasons.

Example:

```text
BUY

Score: 87

Positive:
- Momentum acceleration
- Healthy liquidity
- Holder growth
- Strong buy pressure

Negative:
- High volatility

Risk:
MEDIUM

Reason:
Strong momentum with healthy liquidity,
but elevated volatility requires reduced position size.
```

Do not generate explanations that are disconnected from actual decision inputs.

---

# 39. AI ANALYST

If an LLM layer already exists or can be safely added, create an AI Analyst that can explain:

- why a token received a score
- why a trade was rejected
- why an exit occurred
- why risk increased
- why drawdown increased
- which strategies are performing well

The AI Analyst must be **read-only by default**.

It must NOT directly execute trades.

---

# 40. OBSERVABILITY

Add structured logging for:

```text
Signal
Risk Decision
Strategy Decision
Prediction
Order
Execution
Position
Exit
Error
Circuit Breaker
```

Use correlation IDs / decision IDs.

A single trade should be traceable from:

```text
Market Data
→ Signal
→ Risk
→ Decision
→ Order
→ Execution
→ Position
→ Exit
→ PnL
```

---

# 41. API DESIGN

Review existing APIs.

Do not break existing endpoints unnecessarily.

Add APIs for:

```text
Market Intelligence
Token Intelligence
Risk
Prediction
Strategies
Positions
Trade Decisions
Execution
Model Performance
System Health
```

Use consistent:

```text
HTTP status
error format
pagination
validation
authentication
authorization
```

---

# 42. FRONTEND UPGRADE

Improve existing dashboard rather than rebuilding it.

Add:

### Market

- Market Regime
- Market Risk
- Trending Tokens

### Token

- Quality Score
- Security
- Liquidity
- Behavior
- Whale Activity
- Prediction
- Risk

### Trading

- Positions
- PnL
- Exposure
- Entry / Exit
- Execution

### Intelligence

- Prediction
- Strategy Performance
- Model Performance
- Anomalies

### Risk

- Drawdown
- Daily Loss
- Portfolio Risk
- Liquidity Risk

---

# 43. CONFIGURATION

Do not hard-code thresholds.

Use configuration for:

```text
Risk Limits
Position Limits
Entry Thresholds
Exit Thresholds
Liquidity Thresholds
Slippage Limits
Circuit Breaker
Prediction Threshold
Model Settings
```

Separate:

```text
development
testing
paper
production
```

configuration.

---

# 44. SECURITY

Review:

- private key handling
- secrets
- API keys
- authentication
- authorization
- rate limiting
- input validation
- SQL injection
- command injection
- unsafe logging
- sensitive information exposure

Private keys must NEVER appear in logs.

---

# 45. DATABASE MIGRATION SAFETY

Every schema modification must:

1. Create migration.
2. Preserve existing data.
3. Be reversible where practical.
4. Be documented.
5. Be tested.

Do NOT directly modify production schema manually.

---

# 46. TESTING REQUIREMENTS

Add or update:

### Unit Tests

For:

- scoring
- risk
- strategy
- prediction
- exit
- position sizing

### Integration Tests

For:

- API
- database
- scanner
- execution
- workers

### Simulation Tests

For:

- pump
- dump
- liquidity shock
- whale sell
- API failure
- RPC failure
- cascading exit

### Regression Tests

Ensure existing functionality still works.

---

# 47. DOCUMENT EVERYTHING

Every implemented change MUST update documentation.

Use:

```text
docs/
```

and maintain:

```text
docs/upgrade/
    current-state.md
    architecture-audit.md
    upgrade-plan.md
    change-log.md
```

For each implementation, document:

```text
What changed
Why it changed
How it works
Inputs
Outputs
Dependencies
Configuration
Database changes
API changes
Risks
Testing
Rollback strategy
```

---

# 48. CHANGE LOG FORMAT

For every meaningful change:

```markdown
## [DATE] — Feature Name

### Added

- ...

### Changed

- ...

### Database

- ...

### API

- ...

### Risk Impact

- ...

### Tests

- ...

### Rollback

- ...
```

---

# 49. DO NOT OVERENGINEER

Before adding a new component ask:

1. Is it solving a real problem?
2. Is there enough data?
3. Can it be tested?
4. Does it improve decision quality?
5. Does it introduce more risk than value?
6. Can the existing architecture support it?

If not, document:

```text
[DEFERRED]
```

instead of forcing implementation.

---

# 50. NO FAKE INTELLIGENCE

Never create fake:

```text
AI score
ML confidence
prediction
whale signal
sentiment
```

without a real underlying methodology/data source.

If a feature cannot yet be implemented properly:

```text
TODO
TBD
DATA_REQUIRED
DEFERRED
```

is preferable.

---

# 51. NO GUARANTEED PROFIT

Never implement logic based on assumptions such as:

```text
AI prediction = guaranteed
Win rate = guaranteed
Profit = guaranteed
```

The system must explicitly account for uncertainty.

---

# 52. FINAL ARCHITECTURE TARGET

The upgraded system should evolve toward:

```text
                  ┌─────────────────────┐
                  │    DATA SOURCES     │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │    DATA QUALITY     │
                  └──────────┬──────────┘
                             ↓
              ┌──────────────────────────────┐
              │     INTELLIGENCE LAYER       │
              │                              │
              │ Market                       │
              │ Token                        │
              │ Behavior                     │
              │ Liquidity                    │
              │ Whale                        │
              │ Security                     │
              │ Manipulation                 │
              └──────────────┬───────────────┘
                             ↓
                  ┌─────────────────────┐
                  │  PREDICTION ENGINE  │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │    RISK ENGINE      │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │  STRATEGY ENGINE    │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │  DECISION ENGINE    │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │ EXECUTION ENGINE    │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │ POSITION MANAGER    │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │  ADAPTIVE EXIT      │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │ POST-TRADE ANALYSIS │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │ LEARNING / EVALUATE │
                  └─────────────────────┘
```

---

# 53. EXECUTION RULE

Start by inspecting the existing project.

Do NOT immediately code.

First return:

```text
1. Current Architecture Summary
2. Existing Trading Flow
3. Existing Risk Controls
4. Existing Database
5. Existing API
6. Existing Strategy
7. Existing Weaknesses
8. Upgrade Plan
9. Files That Will Be Modified
10. Files That Will Be Created
11. Database Changes
12. API Changes
13. Testing Plan
14. Risk Assessment
```

Then begin implementation **P0 first**.

After P0 is implemented and tested, continue to P1.

Do not wait for human confirmation between every small change unless the change is destructive, irreversible, or requires a major architectural decision.

---

# 54. SUCCESS CRITERIA

The upgrade is successful when:

- Existing system still works.
- Risk controls are stronger.
- Bad/unsafe tokens can be rejected.
- Liquidity risk is detected.
- Position sizing is adaptive.
- Entry decisions are contextual.
- Exit decisions are adaptive.
- Synchronized exit risk is reduced.
- Market impact is considered.
- Portfolio risk is visible.
- Circuit breakers work.
- Every decision is explainable.
- Every trade is auditable.
- Historical data is available for analysis.
- ML does not suffer from obvious data leakage.
- Backtesting is realistic.
- Paper trading works.
- System failures are handled safely.
- Documentation accurately reflects the implementation.

---

# FINAL PRINCIPLE

The system should not try to be a bot that is "always right".

Build a system that is:

```text
INTELLIGENT
+
RISK AWARE
+
ADAPTIVE
+
DATA DRIVEN
+
EXPLAINABLE
+
AUDITABLE
+
RESILIENT
```

The most important objective is:

> **Preserve capital first. Capture opportunities second.**

Never sacrifice risk controls simply to increase the number of trades.
