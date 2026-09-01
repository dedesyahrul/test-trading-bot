# Upgrade Change Log

## 2026-08-30 - Automatic Database Setup

### Added

- Compose `db-migrate` service runs `alembic upgrade head` before backend and worker start.
- Idempotent seed creates the Solana chain, bot state, and default strategies after a clean database reset.
- `PAPER_INITIAL_BALANCE` is passed consistently to migration, backend, and worker services.

### Risk Impact

- Worker cannot start against an unmigrated database.
- Database setup does not reset or delete existing market, position, or audit data.

### Usage

```bash
docker compose up -d --build
docker compose ps
```

The `db-migrate` service must show `Exited (0)` before backend and worker are considered ready.

## 2026-08-30 - Docker Desktop Auto-Start

## 2026-08-30 - VPS Same-Origin API

## 2026-08-30 - VPS Frontend Build Permissions

### Fixed

- Added `frontend/.dockerignore` so host `node_modules` and build artifacts are never copied into the Linux image.
- Frontend production dependencies are installed inside the image with audit/funding prompts disabled.
- Vite binary permissions are normalized before build and invoked with `npx --no-install`.

### Deployment

Rebuild the frontend without cache on the VPS:

```bash
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Fixed

- Production frontend no longer defaults API and WebSocket URLs to `localhost`.
- Browser requests now use same-origin `/api` and `/ws`, routed by Nginx to the backend container.
- This prevents public VPS browsers from interpreting `localhost` as the user's own computer and avoids Private Network Access/CORS failures.
- Backend can additionally read `CORS_ORIGINS` as a comma-separated or JSON-like list for direct API access.

### Deployment

After changing this value, rebuild the production frontend because Vite embeds environment values during build:

```bash
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

The production Dockerfile now accepts Vite build args, while empty values intentionally select same-origin `/api` and `/ws`.

### Docker Build Fix

- Production frontend now copies `frontend/nginx.conf` from inside its build context.
- This fixes production image builds where the previous Dockerfile attempted to copy `infrastructure/docker/nginx.conf` from outside the frontend context.

### Added

- Development runtime services now use `restart: unless-stopped`.
- Postgres, Redis, backend, worker, and frontend restart automatically when Docker Engine starts.
- `db-migrate` remains a one-shot prerequisite and is not configured to loop.

### Usage

```bash
docker compose up -d --build
```

After that, opening Docker Desktop starts previously-running services automatically. Docker Desktop itself must also be configured to start with Windows.

## 2026-08-30 - Configurable Paper Balance

### Fixed

- PAPER sizing no longer assumes a hard-coded `10,000 USD` balance.
- The balance now comes from `PAPER_INITIAL_BALANCE`, then `INITIAL_BALANCE`, with a `100 USD` default.
- Risk-budget sizing receives the configured PAPER balance.

### Configuration

```env
PAPER_INITIAL_BALANCE=100
```

This is virtual balance only and does not fund LIVE trading.

### Validation

- Runtime container reads `PAPER_INITIAL_BALANCE=100`.
- Risk sizing now uses the configured PAPER balance instead of the old hard-coded `10,000 USD` value.
- Bot still requires `RUNNING` state, watched pairs, and a qualifying BUY signal; small capital does not bypass risk or strategy filters.

### Runtime Note

- After a clean reset, migrations must be applied before the worker can query `pairs` or `bot_state`.
- A `RUNNING/PAPER` bot can legitimately have zero positions when current strategy decisions are `SKIP`; the Dashboard now explains this behavior.

## 2026-08-30 — Database Performance Analysis

### Added

- Read-only analysis of active MemeX PostgreSQL data in `database-analysis-2026-08-30.md`.

### Findings

- 5,231 market snapshots, 25 positions, 47 trades, and 971 predictions are available for analysis.
- `ml_sniper_v1` currently outperforms `momentum_v1` in the small sample, but results are concentrated in one pair.
- 772 snapshots have missing liquidity data.
- The bot is in `SAFE_MODE` after a recorded daily loss of approximately `549.68 USD`.
- Prediction probability and confidence require calibration before being used for larger sizing.

### Next Priority

- Reconcile circuit-breaker accounting, add direct decision-to-position correlation, and implement portfolio concentration limits.

## 2026-08-30 — Position Monitoring Reliability

### Added

- Latest market snapshot timestamp, exit pressure, high-water mark, MAE, and MFE to position responses.
- Ten-second frontend polling fallback for Positions when WebSocket events are unavailable.
- Explicit worker warning logs for every position-monitor cycle.

### Changed

- Position monitoring continues to use the latest available snapshot and reports when market data is not advancing.

### Risk Impact

- Operators can distinguish a frozen UI from a stale market-data source.
- Existing positions remain visible even when WebSocket delivery is interrupted.

## 2026-08-30 — Fix Repeated Paper Exit Failure

### Fixed

- Paper partial exits generated the same `paper_sell_<position_id>` transaction hash on every retry.
- The unique `trades.tx_hash` constraint caused repeated exits to fail and could make the monitor appear inactive.
- Each virtual sell now receives a unique transaction hash.
- Monitor rollback is isolated per position so one failed position does not stop monitoring other positions.

### Testing

- Worker processed 4 open positions successfully after restart.
- Trade count advanced from 47 to 48.
- No duplicate-key or monitor traceback appeared in the post-fix log.

## 2026-08-30 — Market Data Failure Isolation

### Fixed

- DexScreener timeouts were allowed to consume an entire collection cycle across pairs.
- Client timeout reduced to 10 seconds with bounded retry/backoff for transient HTTP/network failures.
- HTTP status and final retry context are now logged more clearly.
- Worker accepts both `pair` and `pairs` response shapes.
- A failed pair keeps its last snapshot and does not generate a new signal from missing data.

### Risk Impact

- One unavailable DexScreener pair no longer silently blocks other pairs.
- Stale data is not treated as fresh data; existing positions remain eligible for exit evaluation.

### Additional Fix

- Collection cron cycles are now serialized within the worker process. A slow provider cycle is skipped by the next cron invocation instead of being run concurrently and multiplying timeout load.
- Timeout logs now include the exception type even when the provider returns an empty error message.

## 2026-08-30 — Clean Reset Discovery and WebSocket Recovery

### Fixed

- Discovery fallback now searches the native token (`SOL`) instead of the literal chain name, which commonly returned no pairs after a clean reset.
- WebSocket subscriptions are queued until the socket is open and automatically restored after reconnect.
- Scanner reports a useful discovery/provider message instead of only showing an empty-state message.

### Additional Fix

- Discovery/search calls now use a longer 20-second provider timeout than pair polling, while pair polling remains short to protect the worker cycle.
- Discovery resolves recent token profiles through the official batch `GET /tokens/v1/{chainId}/{tokenAddresses}` endpoint instead of issuing one resolver request per profile.
- Discovery returns HTTP 503 when the provider yields no pairs instead of falsely returning a successful empty result.
- Intentional WebSocket disconnects no longer schedule reconnect timers, preventing subscription noise during page navigation.

## 2026-08-30 — GeckoTerminal Fallback Provider

### Added

- GeckoTerminal adapter for trending pools and individual pool refresh.
- DexScreener remains the primary provider; GeckoTerminal is used only when DexScreener returns no usable data.
- Provider-normalized pair data and regression coverage.

### Risk Impact

- Temporary DexScreener failure no longer necessarily leaves the scanner empty.
- Provider fallback does not bypass data-quality or risk gates.

### Configuration

- `GECKO_TERMINAL_API_URL`, defaulting to `https://api.geckoterminal.com/api/v2`.

### Bug Fix

- Fixed discovery fallback incorrectly applying the DexScreener normalizer to already-normalized GeckoTerminal pools.
- Incomplete provider records without chain, pair, or token addresses are now skipped explicitly.
- Existing native/stable pairs such as `SOL/USDC` are retained for historical integrity but excluded from meme-token Scanner results.

### Behavior

- Scanner discovery now prefers non-native token/SOL pairs. `SOL/USDC`, `SOL/USDT`, and `SOL/SOL` are not treated as meme-token candidates.
- Existing rows are not deleted automatically; cleanup remains an explicit testing/database operation.

### Wallet Reset Fix

- Default paper-wallet creation now seeds the Solana chain when the database was reset and the chain foreign-key row is missing.
- This prevents `/api/portfolio/wallets/default` from returning a backend `500` that browsers commonly surface as a CORS failure.

### DexScreener Reference Alignment

- Discovery now intentionally uses the original MemeX flow: `GET /token-boosts/latest/v1`, then `GET /token-pairs/v1/{chainId}/{tokenAddress}`.
- Existing official pair endpoint remains `GET /latest/dex/pairs/{chainId}/{pairId}`.
- Search remains the fallback source. Token profile/batch endpoints remain available helpers but are not part of the primary discovery flow.
- Discovery calls respect the documented 60 requests/minute rate limit through bounded request volume and no retry storm.

### Provider Isolation

- Pair request timeout is now 5 seconds.
- Network/timeouts are not retried because retrying a dead pair blocks fresh data for all other pairs.
- Missing pair response shapes use a bounded address-search fallback.

## 2026-08-30 — Portfolio Risk and Exit Telemetry

### Added

- Portfolio exposure and per-pair concentration guard before new entries.
- Loss cooldown for a pair after a losing close.
- Direct decision correlation fields for positions and trades.
- Exit reason, thesis invalidation, MAE, and MFE telemetry.
- Portfolio risk endpoint at `GET /api/risk/portfolio`.

### Changed

- Automated position monitoring now records adaptive exit metadata and preserves partial-exit behavior.
- Entry remains allowed to evaluate exits while portfolio safeguards block only new entries.

### Database

- Migration `007_position_risk_telemetry` adds telemetry and correlation fields.

### Risk Impact

- Concentrated exposure and rapid re-entry after a loss are rejected.
- Exit behavior can be analyzed by reason and excursion instead of aggregate PnL only.

### Tests

- Compile, regression tests, migration validation, and Docker builds run after integration.

### Rollback

- Stop workers, run `alembic downgrade -1`, then restore the previous worker image. Existing core position data remains, while telemetry fields are removed.

## 2026-08-30 — P0 Risk and Audit Foundation

### Added

- Snapshot data-quality classification.
- Structured risk decision and adaptive sizing services.
- Decision ledger persistence.
- Circuit-breaker state fields and execution guards.

### Database

- Added migration `004_p0_risk_audit`.

### Risk Impact

- Invalid or stale data cannot create a signal.
- Risk can reject or reduce a trade before execution.
- Daily-loss and failure protections are centralized.

### Tests

- Added unit coverage for data quality, risk decisions, and sizing.

### Rollback

- Run `alembic downgrade -1`; existing market, signal, and position data remains intact.

## 2026-08-30 — Adaptive Entry and Exit Controls

### Added

- Decision score from observable momentum, volume, liquidity, prediction availability, market factor, and risk.
- Risk-budget sizing with a configurable maximum risk per trade.
- Volatility/liquidity-aware initial stop and take-profit levels.
- High-water mark, trailing profit, profit lock, exit pressure, and conservative partial exits.
- Partial exit support for PAPER and LIVE execution paths.

### Changed

- Automated position monitoring now returns an exit fraction instead of always requesting a full close.
- Manual close remains a full exit for backward compatibility.

### Database

- Added adaptive position state in migration `005_adaptive_positions`.
- Added decision score in migration `006_decision_score`.

### API

- Existing position and close endpoints remain compatible.

### Risk Impact

- Position loss budget is capped before entry.
- Volatile or thin-liquidity positions receive smaller sizing and wider/shorter adaptive levels.
- Profitable positions can lock gains and exit in stages instead of synchronized 100% selling.

### Tests

- Added unit coverage for decision score, risk-budget sizing, and adaptive levels.

### Rollback

- Downgrade `006_decision_score` and `005_adaptive_positions` after stopping the worker. Existing position rows are preserved, but adaptive-only fields will be removed.
