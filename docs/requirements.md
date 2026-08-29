# MemeX — Requirements Specification

> Dokumen ini mendefinisikan semua functional dan non-functional requirements untuk platform MemeX.

---

## Table of Contents

- [1. Functional Requirements](#1-functional-requirements)
- [2. Non-Functional Requirements](#2-non-functional-requirements)
- [3. Hard Constraints](#3-hard-constraints)
- [4. Assumptions](#4-assumptions)
- [5. Out of Scope](#5-out-of-scope)

---

## 1. Functional Requirements

### FR-01: Token Discovery

| ID | Requirement | Priority |
|----|------------|----------|
| FR-01.1 | Sistem dapat menemukan token/pair baru dari DEX | Must |
| FR-01.2 | Sistem dapat mendeteksi token yang mengalami peningkatan volume | Must |
| FR-01.3 | Sistem dapat mendeteksi momentum (price acceleration) | Must |
| FR-01.4 | Sistem dapat mendeteksi perubahan liquidity signifikan | Must |
| FR-01.5 | Sistem dapat mendeteksi abnormal trading activity | Should |
| FR-01.6 | Sistem menggunakan caching untuk efisiensi | Must |
| FR-01.7 | Sistem menghindari rate limit dengan queue/backoff | Must |

### FR-02: Market Data Collection

| ID | Requirement | Priority |
|----|------------|----------|
| FR-02.1 | Collect current price dan price change (1m, 5m, 15m, 1h, 6h, 24h) | Must |
| FR-02.2 | Collect volume data (1m, 5m, 15m, 1h, 24h) | Must |
| FR-02.3 | Collect transaction data (buys, sells, buy/sell volume, ratio) | Must |
| FR-02.4 | Collect liquidity data (USD, change, ratio to market cap) | Must |
| FR-02.5 | Collect market info (market cap, FDV, pair age, DEX, chain) | Must |
| FR-02.6 | Normalize data format dari berbagai sumber | Must |
| FR-02.7 | Validate data quality sebelum storage | Must |

### FR-03: Historical Data

| ID | Requirement | Priority |
|----|------------|----------|
| FR-03.1 | Simpan historical snapshots untuk backtesting | Must |
| FR-03.2 | Simpan historical snapshots untuk ML training | Must |
| FR-03.3 | Mendukung multiple aggregation intervals | Must |
| FR-03.4 | Implementasi retention/cleanup policy | Must |

### FR-04: Feature Engineering

| ID | Requirement | Priority |
|----|------------|----------|
| FR-04.1 | Hitung price features (return, volatility, momentum) | Must |
| FR-04.2 | Hitung volume features (growth, acceleration, spike) | Must |
| FR-04.3 | Hitung transaction features (buy/sell ratio, pressure) | Must |
| FR-04.4 | Hitung liquidity features (change, ratio) | Must |
| FR-04.5 | Hitung behavioral features (whale activity, holder growth) | Should |
| FR-04.6 | Mendokumentasikan sumber data per feature | Must |

### FR-05: Risk Analysis

| ID | Requirement | Priority |
|----|------------|----------|
| FR-05.1 | Hitung risk score per token | Must |
| FR-05.2 | Classify risk level (LOW/MEDIUM/HIGH/CRITICAL) | Must |
| FR-05.3 | Semua risk thresholds configurable | Must |
| FR-05.4 | Risk categories: liquidity, holder, contract, developer, manipulation, rug pull, slippage, execution | Must |

### FR-06: Prediction Engine

| ID | Requirement | Priority |
|----|------------|----------|
| FR-06.1 | Predict probabilitas price movement | Must |
| FR-06.2 | Target: P(price ≥ X% dalam T menit) | Must |
| FR-06.3 | Mendukung multiple ML models | Must |
| FR-06.4 | Mendukung model versioning | Must |
| FR-06.5 | Sistem bisa berjalan tanpa ML (rule-based fallback) | Must |
| FR-06.6 | Model dapat diganti tanpa mengubah trading engine | Must |

### FR-07: ML Evaluation

| ID | Requirement | Priority |
|----|------------|----------|
| FR-07.1 | Train/validation/test split dengan time-series method | Must |
| FR-07.2 | Data leakage prevention | Must |
| FR-07.3 | Track metrics: precision, recall, F1, ROC-AUC, PR-AUC | Must |
| FR-07.4 | Model calibration assessment | Should |
| FR-07.5 | Hubungkan model metrics dengan trading performance | Must |

### FR-08: Trading Signal

| ID | Requirement | Priority |
|----|------------|----------|
| FR-08.1 | Generate signal BUY / SELL / HOLD / SKIP | Must |
| FR-08.2 | Setiap signal memiliki confidence score | Must |
| FR-08.3 | Setiap signal memiliki reasons (pro dan contra) | Must |

### FR-09: Strategy Engine

| ID | Requirement | Priority |
|----|------------|----------|
| FR-09.1 | Mendukung multiple strategies (Momentum, Volume, ML-assisted) | Must |
| FR-09.2 | Strategy configurable via parameters | Must |
| FR-09.3 | Strategy dapat ditambah tanpa mengubah core engine | Must |
| FR-09.4 | Strategy abstraction class/interface | Must |

### FR-10: Trading Decision

| ID | Requirement | Priority |
|----|------------|----------|
| FR-10.1 | Decision pipeline: Risk → Prediction → Strategy → Portfolio Risk → Execution Check | Must |
| FR-10.2 | Setiap decision memiliki reason dan warnings | Must |
| FR-10.3 | Decision harus melewati semua gates sebelum execution | Must |

### FR-11: Position Sizing

| ID | Requirement | Priority |
|----|------------|----------|
| FR-11.1 | Risk-based position sizing | Must |
| FR-11.2 | Consider: balance, risk per trade, volatility, liquidity, confidence | Must |
| FR-11.3 | Maximum exposure per position | Must |
| FR-11.4 | Maximum number of concurrent positions | Must |
| FR-11.5 | Maximum daily loss limit | Must |
| FR-11.6 | Semua parameter configurable | Must |

### FR-12: Backtesting

| ID | Requirement | Priority |
|----|------------|----------|
| FR-12.1 | Backtest strategy terhadap historical data | Must |
| FR-12.2 | Include trading fee dalam simulasi | Must |
| FR-12.3 | Include slippage estimation | Must |
| FR-12.4 | Include liquidity constraint | Must |
| FR-12.5 | Output: win rate, PnL, ROI, max drawdown, Sharpe ratio, etc | Must |

### FR-13: Paper Trading

| ID | Requirement | Priority |
|----|------------|----------|
| FR-13.1 | Paper trading mode menggunakan real market data | Must |
| FR-13.2 | Tidak melakukan transaksi blockchain | Must |
| FR-13.3 | Virtual BUY/SELL dengan PnL tracking | Must |
| FR-13.4 | Switching antara PAPER dan LIVE mode | Must |

### FR-14: Auto Trading (BUY/SELL)

| ID | Requirement | Priority |
|----|------------|----------|
| FR-14.1 | Automated BUY berdasarkan signal + strategy + risk check | Must |
| FR-14.2 | Automated SELL berdasarkan TP/SL/trailing/time/prediction | Must |
| FR-14.3 | Handle: tx failure, timeout, insufficient balance/liquidity | Must |
| FR-14.4 | Handle: slippage exceeded, RPC failure, duplicate tx | Must |
| FR-14.5 | Retry logic dengan max attempts | Must |
| FR-14.6 | Transaction reconciliation | Must |

### FR-15: Take Profit / Stop Loss

| ID | Requirement | Priority |
|----|------------|----------|
| FR-15.1 | Fixed TP dan SL | Must |
| FR-15.2 | Trailing stop | Must |
| FR-15.3 | Partial take profit (e.g., TP1 +20%, TP2 +40%) | Should |
| FR-15.4 | Time-based exit | Should |
| FR-15.5 | Prediction-based exit | Should |
| FR-15.6 | Risk-based exit | Should |
| FR-15.7 | Semua parameter configurable | Must |

### FR-16: Portfolio Monitoring

| ID | Requirement | Priority |
|----|------------|----------|
| FR-16.1 | Realtime position tracking | Must |
| FR-16.2 | Unrealized PnL calculation | Must |
| FR-16.3 | Trade history dengan transaction hash | Must |
| FR-16.4 | Portfolio snapshots | Must |

### FR-17: Wallet Security

| ID | Requirement | Priority |
|----|------------|----------|
| FR-17.1 | Encrypted private key storage | Must |
| FR-17.2 | Environment variable based secret management | Must |
| FR-17.3 | Hot wallet limitation | Must |
| FR-17.4 | Transaction limits | Must |
| FR-17.5 | Emergency stop (kill switch) | Must |
| FR-17.6 | Audit log untuk semua wallet operations | Must |

### FR-18: Web Dashboard

| ID | Requirement | Priority |
|----|------------|----------|
| FR-18.1 | Dashboard: balance, PnL, positions, recent trades, bot status | Must |
| FR-18.2 | Scanner: new tokens, trending, scores, predictions | Must |
| FR-18.3 | Token Detail: chart, price, volume, liquidity, prediction, risk, signal | Must |
| FR-18.4 | Positions: entry, current price, unrealized PnL, TP/SL, trailing | Must |
| FR-18.5 | Trades: history, PnL, tx hash | Must |
| FR-18.6 | Strategy: configuration, thresholds | Must |
| FR-18.7 | ML: model version, performance, prediction history | Should |
| FR-18.8 | Settings: risk, capital, max position, API config, trading mode | Must |

### FR-19: Realtime Updates

| ID | Requirement | Priority |
|----|------------|----------|
| FR-19.1 | Realtime price updates tanpa page refresh | Must |
| FR-19.2 | Realtime signal updates | Must |
| FR-19.3 | Realtime position updates | Must |
| FR-19.4 | Realtime trade notifications | Must |
| FR-19.5 | Realtime bot status | Must |

### FR-20: Bot Control

| ID | Requirement | Priority |
|----|------------|----------|
| FR-20.1 | Start bot | Must |
| FR-20.2 | Stop bot (graceful) | Must |
| FR-20.3 | Pause bot (no new trades, keep monitoring) | Must |
| FR-20.4 | Emergency stop (kill switch) | Must |
| FR-20.5 | Bot state machine with defined transitions | Must |

### FR-21: Observability

| ID | Requirement | Priority |
|----|------------|----------|
| FR-21.1 | Application logging (structured) | Must |
| FR-21.2 | Trading log (setiap decision dan execution) | Must |
| FR-21.3 | Audit log (semua sensitive operations) | Must |
| FR-21.4 | System metrics (API latency, throughput, etc.) | Must |
| FR-21.5 | Health checks untuk semua services | Must |
| FR-21.6 | Worker monitoring | Must |

---

## 2. Non-Functional Requirements

### NFR-01: Scalability

| ID | Requirement | Target | Rationale |
|----|------------|--------|-----------|
| NFR-01.1 | Single instance deployment support | 1 instance | Initial target: single VPS |
| NFR-01.2 | Watch up to N tokens concurrently | 500 tokens | Reasonable for single instance with rate limiting |
| NFR-01.3 | Historical data storage | 6+ months | Untuk ML training & backtesting |

### NFR-02: Reliability

| ID | Requirement | Target | Rationale |
|----|------------|--------|-----------|
| NFR-02.1 | Worker auto-restart on crash | Auto | Supervisor/systemd level |
| NFR-02.2 | Graceful shutdown | Max 30s | Complete pending operations |
| NFR-02.3 | Data consistency | Eventually consistent | Redis cache + PostgreSQL source of truth |
| NFR-02.4 | Transaction idempotency | Must | Prevent duplicate trades |

### NFR-03: Latency

| ID | Requirement | Target | Rationale |
|----|------------|--------|-----------|
| NFR-03.1 | API response time (p95) | < 500ms | Dashboard responsiveness |
| NFR-03.2 | WebSocket update latency | < 1s | Near-realtime feel |
| NFR-03.3 | Signal to execution time | < 5s | Competitive execution |
| NFR-03.4 | Market data collection cycle | 10-30s | Balance freshness vs rate limit |

> [!NOTE]
> Latency targets di atas adalah **guideline**, bukan hard SLA. Actual performance bergantung pada network conditions, external API latency, dan blockchain confirmation time.

### NFR-04: Availability

| ID | Requirement | Target | Rationale |
|----|------------|--------|-----------|
| NFR-04.1 | System uptime | 99% (monthly) | Single instance without HA |
| NFR-04.2 | Planned maintenance window | < 30 min | Docker-based deployment |
| NFR-04.3 | Recovery time | < 5 min | Docker restart + auto-migration |

### NFR-05: Security

| ID | Requirement | Target |
|----|------------|--------|
| NFR-05.1 | Authentication required untuk semua API endpoints | Must |
| NFR-05.2 | Encrypted secrets storage | Must |
| NFR-05.3 | No plaintext private keys in database | Must |
| NFR-05.4 | HTTPS for all external communication | Must |
| NFR-05.5 | Input validation pada semua user inputs | Must |

### NFR-06: Maintainability

| ID | Requirement | Target |
|----|------------|--------|
| NFR-06.1 | Modular architecture dengan clear boundaries | Must |
| NFR-06.2 | Strategy dapat ditambah tanpa core changes | Must |
| NFR-06.3 | ML model dapat diganti tanpa code changes | Must |
| NFR-06.4 | Blockchain adapter dapat ditambah tanpa core changes | Must |
| NFR-06.5 | Database migration versioned (Alembic) | Must |

### NFR-07: Observability

| ID | Requirement | Target |
|----|------------|--------|
| NFR-07.1 | Structured logging (JSON) | Must |
| NFR-07.2 | Trading audit trail | Must |
| NFR-07.3 | Health check endpoint | Must |
| NFR-07.4 | Key metrics collection | Must |

### NFR-08: Testability

| ID | Requirement | Target |
|----|------------|--------|
| NFR-08.1 | Unit tests untuk semua services | Must |
| NFR-08.2 | Integration tests untuk API | Must |
| NFR-08.3 | Backtesting sebagai strategy validation | Must |
| NFR-08.4 | Paper trading sebagai end-to-end validation | Must |

---

## 3. Hard Constraints

Berikut adalah constraints yang **tidak boleh dilanggar**:

| # | Constraint | Kategori |
|---|-----------|----------|
| C-01 | Tidak melakukan trading ketika mode PAPER | Safety |
| C-02 | Tidak melakukan BUY hanya berdasarkan prediction ML (harus lewat strategy + risk check) | Safety |
| C-03 | Tidak menyimpan private key plaintext di database | Security |
| C-04 | Memiliki emergency stop (kill switch) | Safety |
| C-05 | Memiliki maximum position size | Risk |
| C-06 | Memiliki maximum daily loss limit | Risk |
| C-07 | Memiliki slippage protection | Risk |
| C-08 | Memiliki transaction reconciliation | Integrity |
| C-09 | Memiliki audit log | Compliance |
| C-10 | Memisahkan data, prediction, strategy, risk, dan execution layers | Architecture |
| C-11 | Dapat digunakan tanpa ML (rule-based mode) | Flexibility |
| C-12 | Dapat mengganti model ML tanpa mengubah trading engine | Maintainability |
| C-13 | Dapat mengganti blockchain adapter tanpa mengubah strategy engine | Maintainability |

---

## 4. Assumptions

| # | Assumption | Impact if Wrong |
|---|-----------|-----------------|
| A-01 | DEX Screener API tetap free/accessible | Perlu alternative data source |
| A-02 | Rate limit 60-300 req/min cukup | Perlu paid tier atau multi-source |
| A-03 | Single instance deployment (1 VPS) | Jika butuh HA, perlu redesign worker coordination |
| A-04 | Single user (operator) | Jika multi-tenant, perlu redesign auth & data isolation |
| A-05 | Solana sebagai chain pertama | Jika bukan, adapter pertama berbeda |

---

## 5. Out of Scope

Berikut **tidak** termasuk dalam scope saat ini:

| Item | Alasan |
|------|--------|
| Multi-tenant support | Complexity tidak diperlukan untuk v1 |
| Mobile app | Web dashboard cukup untuk v1 |
| Social sentiment analysis | Bisa ditambahkan sebagai feature source nanti |
| Copy trading | Feature advanced untuk future phase |
| Token creation/launch | Bukan trading platform concern |
| Cross-DEX arbitrage | Strategy specific, bisa ditambahkan nanti |
| High-frequency trading (sub-second) | Blockchain latency membuat ini tidak feasible |
