# MemeX — Advanced Meme Coin Trading Platform

> Automated meme coin discovery, analysis, prediction, and trading platform.

---

## Overview

MemeX adalah platform web untuk melakukan automated trading meme coin di decentralized exchanges (DEX). Platform ini dirancang modular, scalable, secure, dan observable.

### Kapabilitas Utama

| # | Capability | Deskripsi |
|---|-----------|-----------|
| 1 | Token Discovery | Scan meme coin baru dari DEX |
| 2 | Market Data | Collect & normalize data dari DEX Screener API |
| 3 | Historical Data | Simpan snapshots untuk backtesting & ML |
| 4 | Feature Engineering | Hitung technical & behavioral features |
| 5 | Risk Analysis | Scoring risiko per token |
| 6 | ML Prediction | Probabilitas pergerakan harga |
| 7 | Trading Signal | Generate signal BUY/SELL/HOLD |
| 8 | Strategy Engine | Configurable trading strategies |
| 9 | Backtesting | Evaluasi strategi dengan historical data |
| 10 | Paper Trading | Virtual trading dengan real market data |
| 11 | Automated Trading | Auto BUY/SELL via DEX/aggregator |
| 12 | Portfolio Monitoring | Realtime position & PnL tracking |
| 13 | Web Dashboard | Vue 3 realtime dashboard |
| 14 | Observability | Logging, metrics, audit trail |

### Prinsip Arsitektur

```
Data ≠ Signal ≠ Decision ≠ Execution
```

ML model **tidak pernah** langsung melakukan transaksi. Setiap keputusan trading melewati:

```
Prediction + Strategy + Risk Management + Execution Constraints
```

---

## Technology Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Migration | Alembic |
| Validation | Pydantic |
| Async | asyncio |

### Database & Cache
| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL |
| Cache / Queue | Redis |
| Background Worker | ARQ (asyncio-native) |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | Vue 3 |
| Language | TypeScript |
| Build Tool | Vite |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Container | Docker |
| Orchestration | Docker Compose |
| Deployment | VPS / Cloud |

---

## Project Structure

```
memex/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes & endpoints
│   │   ├── core/             # Config, security, dependencies
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic layer
│   │   │   ├── market/       # Market data collection & normalization
│   │   │   ├── scanner/      # Token discovery
│   │   │   ├── features/     # Feature engineering
│   │   │   ├── risk/         # Risk scoring engine
│   │   │   ├── prediction/   # ML prediction engine
│   │   │   ├── strategy/     # Strategy engine
│   │   │   ├── trading/      # Execution engine (buy/sell)
│   │   │   ├── portfolio/    # Position & PnL management
│   │   │   └── backtest/     # Backtesting & paper trading
│   │   ├── adapters/         # External integrations
│   │   │   ├── dexscreener/  # DEX Screener API client
│   │   │   ├── blockchain/   # Blockchain adapters (abstract)
│   │   │   └── dex/          # DEX adapters (abstract)
│   │   ├── workers/          # ARQ background workers
│   │   └── websocket/        # WebSocket handlers
│   ├── alembic/              # Database migrations
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── pages/
│   │   ├── stores/
│   │   ├── services/
│   │   └── types/
│   ├── public/
│   └── package.json
├── ml/
│   ├── notebooks/            # Exploratory analysis
│   ├── training/             # Training scripts
│   ├── evaluation/           # Model evaluation
│   ├── models/               # Saved model artifacts
│   └── data/                 # Training datasets
├── infrastructure/
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   ├── frontend.Dockerfile
│   │   └── worker.Dockerfile
│   └── scripts/
├── docs/                     # Technical documentation (this folder)
└── docker-compose.yml
```

---

## Documentation Index

| Document | Deskripsi |
|----------|-----------|
| [architecture.md](architecture.md) | System architecture, component diagram, design decisions |
| [requirements.md](requirements.md) | Functional & non-functional requirements |
| [market-data.md](market-data.md) | DEX Screener integration, data pipeline, historical data |
| [database.md](database.md) | ERD, schema design, retention strategy |
| [feature-engineering.md](feature-engineering.md) | Feature computation pipeline |
| [scanner.md](scanner.md) | Token discovery system & worker architecture |
| [risk-engine.md](risk-engine.md) | Token risk scoring & portfolio risk |
| [prediction-engine.md](prediction-engine.md) | ML pipeline, model selection, evaluation |
| [strategy-engine.md](strategy-engine.md) | Trading strategies, decision pipeline, position sizing |
| [execution-engine.md](execution-engine.md) | Auto BUY/SELL, transaction lifecycle |
| [backtesting.md](backtesting.md) | Backtesting engine & metrics |
| [paper-trading.md](paper-trading.md) | Paper trading mode |
| [wallet-security.md](wallet-security.md) | Private key handling, encryption, kill switch |
| [security.md](security.md) | Authentication, authorization, input validation |
| [observability.md](observability.md) | Logging, metrics, resilience |
| [deployment.md](deployment.md) | Docker architecture, deployment guide |
| [docker-guide.md](docker-guide.md) | Panduan lengkap build, run, backup & maintenance Docker |
| [frontend.md](frontend.md) | Vue 3 dashboard design |
| [realtime.md](realtime.md) | WebSocket/SSE architecture |
| [api.md](api.md) | REST API specification |
| [roadmap.md](roadmap.md) | Phase 0–11 development roadmap |

---

## Quick Start (Development)

### Opsi A — Docker (Rekomendasi)

```bash
# Clone repository
git clone <repo-url> memex
cd memex

# Siapkan environment
cp .env.example .env

# Generate package-lock.json (pertama kali)
cd frontend && npm install && cd ..

# Build & jalankan semua service
docker compose build
docker compose up -d

# Migration database
docker compose exec backend alembic upgrade head
```

Akses:
- Frontend: http://localhost:13456
- API Docs: http://localhost:17845/docs
- Health: http://localhost:17845/api/health

> Panduan lengkap Docker (production, backup, troubleshooting): **[docker-guide.md](docker-guide.md)**

### Opsi B — Lokal Tanpa Docker

```bash
# Clone repository
git clone <repo-url> memex
cd memex

# Start infrastructure
docker compose up -d postgres redis

# Backend
cd backend
python -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Constraints

Sistem **HARUS** memenuhi constraints berikut:

1. Tidak melakukan trading ketika mode `PAPER`
2. Tidak melakukan BUY hanya berdasarkan prediction ML
3. Tidak menyimpan private key plaintext
4. Memiliki emergency stop (kill switch)
5. Memiliki maximum position size
6. Memiliki maximum daily loss
7. Memiliki slippage protection
8. Memiliki transaction reconciliation
9. Memiliki audit log
10. Memisahkan data layer, prediction, strategy, risk, dan execution
11. Dapat digunakan tanpa ML terlebih dahulu
12. Dapat mengganti model ML tanpa mengubah trading engine
13. Dapat mengganti blockchain adapter tanpa mengubah strategy engine

---

## License

`[TBD]` — To be determined.
