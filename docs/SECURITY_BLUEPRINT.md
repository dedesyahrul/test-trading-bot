# MemeX — Security-First Architecture Blueprint

> Comprehensive technical design for transforming memeX into a world-class security-first meme token trading bot

---

## Executive Summary

**Current State:** MemeX has solid foundational infrastructure (FastAPI, PostgreSQL, worker pipeline, Vue 3 frontend, risk engine basics). However, security measures are **incomplete and insufficient** for production meme coin trading.

**Goal:** Implement a **security-first pre-trade filter pipeline** that automatically blocks/flags high-risk tokens before any trade executes, regardless of prediction model confidence.

**Key Insight:** Security must veto trading decisions. A perfect prediction model is useless if the token is a honeypot or rugpull trap.

---

## 1. Current State Analysis

### 1.1 What Exists (Strengths)

| Component | Status | Details |
|-----------|--------|---------|
| **Risk Engine** | ✅ Implemented | Weighted scoring (liquidity 30%, manipulation 30%, volatility 20%, execution 20%) |
| **Hard Constraints** | ✅ Partial | Honeypot detection (sells=0), liquidity threshold ($1k), dead coin detection |
| **Market Data Pipeline** | ✅ Implemented | DEX Screener integration, 5-minute collection cycle, feature engineering |
| **Worker Architecture** | ✅ Implemented | ARQ-based background jobs, 7 workers (discovery, market, features, risk, signals, buy, monitor) |
| **Database Schema** | ✅ Implemented | 14 ORM models including RiskAssessment, MarketSnapshot, Token, Pair |
| **Portfolio Tracking** | ✅ Implemented | Position tracking, PnL calculation, multi-position support |
| **Execution Engine** | ✅ Implemented | Paper/Live modes, Jupiter swap integration, position management |
| **Paper Trading** | ✅ Implemented | Full simulation without real trades |

### 1.2 Critical Gaps (Security Vulnerabilities)

| Gap | Severity | Impact | Example |
|-----|----------|--------|---------|
| **No Contract Analysis** | CRITICAL | Cannot detect malicious contract bytecode, hidden functions, or token mint hooks | Honeypot with hidden `transferFee()` function |
| **No Mint Authority Check** | CRITICAL | Minter can create unlimited supply, diluting holders | Minter address not checked or revoked |
| **No Holder Distribution** | HIGH | Top 10 wallets can own 90%+ supply → instant rugpull | Founders hold 85% of supply off-chain |
| **No Liquidity Pool Analysis** | HIGH | Cannot detect concentrated liquidity, fake LP, or LP pair manipulations | 100% liquidity in single whale wallet |
| **No Dev/Owner Wallet Tracking** | HIGH | Cannot flag tokens where owner/dev has history of rugs or scams | Same dev address as 5 previous scam tokens |
| **No Metadata Validation** | MEDIUM | Fake token names/symbols mimicking legit projects | "USDC" token with manipulated metadata |
| **No Social/Community Verification** | MEDIUM | Cannot assess team credibility, Twitter followers, Telegram member count | Brand new account, 0 followers, zero community |
| **Limited Exchange Listing Check** | MEDIUM | Cannot verify if token is listed on major exchanges (reduces rug risk) | Token only on tiny DEX with no major exchange presence |
| **No Sybil/Wash Trading Detection** | MEDIUM | Cannot detect coordinated bots creating fake volume | 1000 trades/min all from 3 wallet addresses |
| **No Price Manipulation Detection** | MEDIUM | Limited detection of pump-and-dumps or coordinated price spikes | Price +1000% in 30 sec, then -80% immediately |

---

## 2. Security-First Architecture

### 2.1 Pre-Trade Filter Pipeline (Kill Switches First)

```
┌─────────────────────────────────────────────────────────┐
│                 Market Data Worker                       │
│           (Collects pair/token data every 5m)            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         SECURITY GATE LAYER (NEW)                        │
│    Kill Switches & Hard Constraints (Veto Only)         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1. Liquidity Guard                                      │
│     └─ < $1k USD → BLOCK (return immediately)           │
│                                                           │
│  2. Honeypot Detector                                    │
│     └─ sells=0 & buys>50 in 15m → BLOCK                 │
│                                                           │
│  3. Contract Analysis                                    │
│     └─ Fetch contract bytecode, check for:              │
│        • Transfer fee function (hidden tax)             │
│        • Mint authority not renounced                   │
│        • Suspicious function selectors                  │
│        → BLOCK if malicious detected                    │
│                                                           │
│  4. Mint Authority Check                                │
│     └─ Is mint authority null/renounced?                │
│        If NO → REDUCE_RISK_TOLERANCE by 50%             │
│                                                           │
│  5. Top Holder Analysis                                 │
│     └─ Do top 10 holders own > 80% supply?              │
│        If YES (excluding LP/burn) → BLOCK               │
│                                                           │
│  6. Dev/Owner History Check                             │
│     └─ Is owner/dev address in scam list?               │
│        Previous rug count > 2? → BLOCK                  │
│                                                           │
└────────────────┬───────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   [BLOCK]         [PASS: Continue]
        │                 │
        ▼                 ▼
   Add to          ┌─────────────────────────────────────┐
   Blacklist       │     Feature Engineering Worker      │
                   │  (Compute technicals, momentum, etc) │
                   └────────────────┬────────────────────┘
                                    │
                                    ▼
                   ┌─────────────────────────────────────┐
                   │      Risk Scoring Worker            │
                   │  (Weighted scoring with adjusted     │
                   │   tolerance from security gate)     │
                   └────────────────┬────────────────────┘
                                    │
                                    ▼
                   ┌─────────────────────────────────────┐
                   │   Prediction Engine Worker          │
                   │   (Only if risk_score ACCEPTABLE)   │
                   └────────────────┬────────────────────┘
                                    │
                                    ▼
                   ┌─────────────────────────────────────┐
                   │      Signal Generator               │
                   │   (Strategy + Confidence Filter)    │
                   └────────────────┬────────────────────┘
                                    │
                                    ▼
                   ┌─────────────────────────────────────┐
                   │   Execution Engine (FINAL VETO)     │
                   │   Portfolio risk check + position   │
                   │   sizing before sending tx          │
                   └─────────────────────────────────────┘
```

### 2.2 Security Gate Module Architecture

```python
# New module: backend/app/services/security/

SecurityGateService (NEW)
├── gate.py                          # Main gate orchestrator
├── liquidity_guard.py               # Liquidity threshold checks
├── honeypot_detector.py             # Sells=0, buy-only detection
├── contract_analyzer.py             # On-chain contract analysis (NEW)
├── mint_authority_checker.py        # Mint authority detection (NEW)
├── holder_distribution.py           # Top holder analysis (NEW)
├── dev_wallet_tracker.py            # Dev/owner history check (NEW)
├── metadata_validator.py            # Token metadata validation (NEW)
├── exchange_listing_checker.py      # CEX listing verification (NEW)
├── wash_trading_detector.py         # Sybil/bot trading detection (NEW)
├── price_action_analyzer.py         # Price spike/dump detection (NEW)
└── __init__.py
```

---

## 3. Security Module Specifications

### 3.1 Contract Analyzer (CRITICAL)

**Purpose:** Detect malicious or suspicious contract code before trading.

**Implementation:**
```python
class ContractAnalyzer:
    """
    Fetch contract bytecode from Solana RPC, analyze for:
    1. Hidden transfer fee functions
    2. Mint authority status
    3. Freeze authority status
    4. Suspicious function selectors
    5. Known attack patterns (flash loans, reentrancy, etc.)
    """
    
    async def analyze_token_contract(
        self, 
        chain: str,           # "solana"
        token_address: str,   # Mint address
    ) -> ContractAnalysisResult:
        """
        Returns:
        {
            "is_safe": bool,
            "risk_flags": [str],  # List of detected issues
            "has_transfer_fee": bool,
            "mint_authority": str | None,  # null = renounced
            "freeze_authority": str | None,
            "confidence": float (0-1),
        }
        """
        pass
```

**Data Sources:**
- Solana RPC `getProgramAccounts` for token metadata
- Contract bytecode analysis via Metaplex program
- Mint authority from `token.info.mintAuthority`
- Known honeypot/scam contract patterns DB

**Risk Scoring Impact:**
- Transfer fee detected → +30 points
- Mint authority not renounced → +25 points
- Freeze authority exists → +15 points
- Known scam pattern → +50 points (BLOCK)

---

### 3.2 Holder Distribution Analyzer (CRITICAL)

**Purpose:** Detect concentrated ownership that enables rugpull.

**Implementation:**
```python
class HolderDistributionAnalyzer:
    """
    Analyze top token holders to detect concentration risk.
    Exclude LP and burn addresses from analysis.
    """
    
    async def analyze_top_holders(
        self,
        chain: str,
        token_address: str,
        top_n: int = 20,
    ) -> HolderAnalysisResult:
        """
        Returns:
        {
            "top_holders": [
                {"address": "...", "balance": 1000000, "pct_supply": 15.2},
                ...
            ],
            "top_10_pct": 75.3,  # % of supply in top 10
            "concentration_score": 85,  # 0-100
            "is_concentrated": bool,  # True if > 80% in top 10
            "excluded_lp": int,  # # of LP/burn addresses excluded
        }
        """
        pass
```

**Data Sources:**
- Solana RPC `getTokenSupply` → total supply
- `getTokenAccountsByOwner` → holder list (capped at ~1000 top holders)
- Metaplex verified metadata for LP/burn address detection
- Known LP token addresses (Raydium, Orca, etc.)

**Risk Scoring Impact:**
- Top 10 holders > 80% supply → +50 points (BLOCK if > 85%)
- Top 10 holders 70-80% → +35 points
- Top holder > 30% → +25 points

---

### 3.3 Dev Wallet Tracker (HIGH)

**Purpose:** Flag tokens where dev/owner has history of scams or rugs.

**Implementation:**
```python
class DevWalletTracker:
    """
    Track token creator/owner wallets and check against scam database.
    """
    
    async def check_dev_wallet(
        self,
        chain: str,
        token_address: str,
    ) -> DevWalletCheckResult:
        """
        Returns:
        {
            "dev_address": str,
            "created_tokens_count": int,
            "scam_tokens_created": int,
            "avg_rugpull_duration": str,  # e.g., "2.5 days"
            "is_flagged": bool,
            "risk_score": int (0-100),
            "details": [str],
        }
        """
        pass
```

**Data Sources:**
- Token creator from `token.creator` (Metaplex)
- Internal scam database (maintain list of known scam addresses)
- On-chain token creation history via RPC
- Cross-reference with public scam lists (Rugpull.io, etc.)

**Risk Scoring Impact:**
- Dev created 3+ scam tokens → +60 points (BLOCK)
- Dev created 1-2 scam tokens → +40 points
- Average rugpull duration < 7 days → +30 points

---

### 3.4 Mint Authority Checker (CRITICAL)

**Purpose:** Detect if token minter can create unlimited supply.

**Implementation:**
```python
class MintAuthorityChecker:
    """
    Check if mint authority is null (renounced) or still active.
    Active mint = token can be diluted infinitely.
    """
    
    async def check_mint_authority(
        self,
        chain: str,
        token_address: str,
    ) -> MintAuthorityCheckResult:
        """
        Returns:
        {
            "is_renounced": bool,
            "mint_authority": str | None,
            "freeze_authority": str | None,
            "update_authority": str | None,
            "risk_score": int (0-100),
        }
        """
        pass
```

**Data Sources:**
- Solana RPC `getMint` → get MintState
- Check `mintAuthority` field (null = renounced)
- Cross-check with Metaplex program state

**Risk Scoring Impact:**
- Mint authority is NOT renounced → +40 points
- Freeze authority exists → +20 points
- Update authority != null → +15 points

---

### 3.5 Wash Trading Detector (MEDIUM)

**Purpose:** Identify coordinated bot trading or artificial volume.

**Implementation:**
```python
class WashTradingDetector:
    """
    Detect sybil attacks, bot trading, and artificial volume.
    """
    
    async def analyze_trading_patterns(
        self,
        chain: str,
        pair_address: str,
        time_window: int = 60,  # Last 60 minutes
    ) -> WashTradingAnalysisResult:
        """
        Returns:
        {
            "unique_buyers": int,
            "unique_sellers": int,
            "buy_sell_ratio": float,
            "top_trader_concentration": float,  # % volume from top 10 traders
            "transaction_velocity": int,  # txns per minute
            "is_suspicious": bool,
            "risk_score": int (0-100),
            "flags": [str],
        }
        """
        pass
```

**Data Sources:**
- Solana transaction history via RPC `getSignaturesForAddress`
- Parse swap/transfer instructions from tx logs
- Track unique wallet addresses per timeframe
- DEX Screener transaction data (buy_count_24h, sell_count_24h)

**Risk Scoring Impact:**
- Top 10 traders = 80%+ volume → +45 points
- Buy/sell ratio > 10:1 → +40 points
- Transaction velocity > 1000/min → +30 points
- Unique buyers < 10 (but buy_count > 100) → +35 points

---

### 3.6 Price Action Analyzer (MEDIUM)

**Purpose:** Detect pump-and-dumps, extreme spikes, and manipulation.

**Implementation:**
```python
class PriceActionAnalyzer:
    """
    Detect suspicious price movements (pump/dump, flash crashes).
    """
    
    async def analyze_price_action(
        self,
        pair_address: str,
        lookback_minutes: int = 60,
    ) -> PriceActionAnalysisResult:
        """
        Returns:
        {
            "max_gain_pct": float,      # Highest peak in lookback
            "max_loss_pct": float,      # Largest drop from peak
            "volatility_1h": float,     # Std dev of returns
            "is_pump_dump": bool,       # Detected pump & dump pattern
            "flash_crash_detected": bool,
            "suspicious_spikes": int,   # # of >50% moves in <5min
            "risk_score": int (0-100),
        }
        """
        pass
```

**Data Sources:**
- Market snapshot historical data (collected every 5 minutes)
- DEX Screener price change (m5, h1, h24)
- On-chain transaction logs for exact price per tx

**Risk Scoring Impact:**
- Pump-dump pattern detected → +50 points
- Max gain > 1000% in 1h → +40 points (BLOCK if 10,000%+)
- Flash crash detected → +35 points
- Volatility > 200% → +30 points

---

### 3.7 Metadata Validator (MEDIUM)

**Purpose:** Detect fake/misleading token metadata.

**Implementation:**
```python
class MetadataValidator:
    """
    Validate token name, symbol, and metadata against known legitimate projects.
    """
    
    async def validate_metadata(
        self,
        chain: str,
        token_address: str,
        name: str,
        symbol: str,
        decimals: int,
    ) -> MetadataValidationResult:
        """
        Returns:
        {
            "is_valid": bool,
            "name_suspicious": bool,
            "symbol_suspicious": bool,
            "is_fake_usdc": bool,  # Impersonating USDC?
            "similar_to_known": str | None,  # e.g., "USDC" (actual address: ...)
            "risk_score": int (0-100),
        }
        """
        pass
```

**Data Sources:**
- Token metadata from Metaplex
- Known legitimate token list (CoinGecko, Coingecko verified tokens)
- String similarity matching (Levenshtein distance)
- Symbol/name against scam pattern database

**Risk Scoring Impact:**
- Looks like "USDC" but different address → +60 points (BLOCK)
- Symbol length != 2-10 chars → +15 points
- Name contains suspicious keywords → +20 points

---

### 3.8 Exchange Listing Checker (MEDIUM)

**Purpose:** Verify token is listed on major exchanges (reduces rug risk).

**Implementation:**
```python
class ExchangeListingChecker:
    """
    Check if token has CEX (Binance, FTX, Coinbase, etc.) or major DEX listings.
    Tokens listed on major exchanges = lower rug risk.
    """
    
    async def check_listings(
        self,
        chain: str,
        token_address: str,
    ) -> ListingCheckResult:
        """
        Returns:
        {
            "cex_listed": bool,
            "cex_exchanges": [str],  # ["binance", "ftx", ...]
            "major_dex": bool,       # Raydium, Orca, Magic Eden?
            "coingecko_listed": bool,
            "tier": str,  # "major_cex", "minor_cex", "major_dex", "minor_dex"
            "risk_score": int (0-100),
        }
        """
        pass
```

**Data Sources:**
- CoinGecko API (free tier has exchange data)
- Coingecko verified token list
- Known major DEX pair lists (Raydium, Orca API)
- Birdeye integration

**Risk Scoring Impact:**
- No CEX, no major DEX → +30 points
- Major CEX listed → -20 points (reward)
- CoinGecko listed → -10 points (reward)

---

## 4. Enhanced Risk Scoring System

### 4.1 Risk Score Calculation (Revised)

**New Weighted Formula:**

```
Overall Risk Score = (
    Security Gate Score × 40%  +    ← NEW: Contract + holders + dev
    Liquidity Risk × 20% +
    Manipulation Risk × 15% +
    Volatility Risk × 12% +
    Execution Risk × 8% +
    Metadata Risk × 5%
)
```

### 4.2 Security Gate Score Breakdown

| Category | Weight | Components | Max Points |
|----------|--------|------------|-----------|
| **Contract Analysis** | 15% | Transfer fee, mint authority, freeze authority | 60 |
| **Holder Distribution** | 15% | Top 10 %, concentration risk | 50 |
| **Dev Wallet History** | 10% | Scam count, rugpull duration | 60 |
| **Price Action** | 5% | Pump/dump patterns, flash crashes | 40 |
| **Wash Trading** | 5% | Sybil detection, artificial volume | 35 |
| **Metadata** | 5% | Name/symbol spoofing | 20 |
| **Exchange Listing** | 5% | CEX/major DEX presence | 30 |
| **Mint Authority** | 5% | Renounced vs active | 40 |
| **Liquidity** | 20% | Absolute USD, pool composition | 100 |
| **Volume/Liquidity** | 5% | Turnover rate | 30 |

### 4.3 Risk Levels with Hard Blocks

```
┌─────────────────────────────────────────────────────────┐
│ RISK SCORE MAPPING & TRADING DECISIONS                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ SCORE: 0-20   │ LEVEL: SAFE                              │
│               │ ACTION: ✅ ALLOW                          │
│               │ Max Position: 100% of configured size    │
│               │ Stop Loss: -8%                           │
│               │ Take Profit: +15%                        │
│                                                           │
├─────────────────────────────────────────────────────────┤
│ SCORE: 21-40  │ LEVEL: LOW-MEDIUM                        │
│               │ ACTION: ✅ ALLOW (REDUCED)               │
│               │ Max Position: 50% of configured size     │
│               │ Stop Loss: -6%                           │
│               │ Take Profit: +12%                        │
│                                                           │
├─────────────────────────────────────────────────────────┤
│ SCORE: 41-60  │ LEVEL: MEDIUM                            │
│               │ ACTION: ⚠️ CAUTION                        │
│               │ Max Position: 25% of configured size     │
│               │ Stop Loss: -5%                           │
│               │ Take Profit: +10%                        │
│               │ Require high confidence signal (>0.8)    │
│                                                           │
├─────────────────────────────────────────────────────────┤
│ SCORE: 61-80  │ LEVEL: HIGH                              │
│               │ ACTION: 🚫 REJECT                        │
│               │ Explanation: "Risk score 65 exceeds      │
│               │ entry tolerance (max: 60)"              │
│               │ Reasons: [list of detected issues]      │
│                                                           │
├─────────────────────────────────────────────────────────┤
│ SCORE: 81-100 │ LEVEL: CRITICAL                          │
│               │ ACTION: 🚫 BLOCK + BLACKLIST             │
│               │ Explanation: "Critical risk detected"    │
│               │ Reasons: [honeypot, concentrated         │
│               │           holders, dev scam history]     │
│               │ Auto-blacklist for 7 days               │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 4.4 Hard Constraint Examples (Immediate BLOCK)

```python
HARD_CONSTRAINTS = [
    # Liquidity Guard
    ("liquidity_usd < 1000", "Critical liquidity shortage"),
    
    # Honeypot Detection
    ("buys_24h > 50 AND sells_24h == 0", "Honeypot: buy-only trap"),
    
    # Holder Concentration
    ("top_10_pct > 85%", "Critical holder concentration"),
    
    # Dev Scam History
    ("dev_scam_count >= 3", "Dev has 3+ known scam tokens"),
    
    # Contract Malice
    ("contract_flag == 'HONEYPOT' OR 'RUGPULL_VECTOR'", "Known malicious contract"),
    
    # Mint Authority
    ("mint_authority != NULL AND suspicious_mints > 5", "Active minter with history of dilution"),
    
    # Price Manipulation (Extreme)
    ("price_change_1m > 5000%", "Extreme price spike (possible exploit)"),
    
    # Wash Trading (Obvious)
    ("unique_buyers < 5 AND buys_24h > 100", "Clear artificial volume"),
]
```

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Build security service module and integrate with existing risk engine.

**Tasks:**
1. Create `backend/app/services/security/` module structure
2. Implement `SecurityGateService` orchestrator
3. Implement `LiquidityGuard` (enhance existing checks)
4. Implement `HoneypotDetector` (enhance existing)
5. Add database tables for security findings (audit trail)
6. Update worker to call security gate BEFORE feature engineering
7. Write unit tests for each security module
8. **Verification:** Run against 100 known scam/honeypot tokens → should block all

**Estimated effort:** 80 hours

---

### Phase 2: Critical Security Modules (Weeks 3-4)

**Goal:** Implement contract analysis and holder distribution detection.

**Tasks:**
1. Implement `ContractAnalyzer`
   - Fetch token contract via Solana RPC
   - Analyze bytecode for known patterns
   - Check transfer fees, authorities
   - Integrate Helius or similar RPC for enhanced contract parsing
   
2. Implement `HolderDistributionAnalyzer`
   - Fetch top 20 holders via RPC
   - Calculate concentration metrics
   - Exclude LP/burn addresses
   - Cache results (holders don't change frequently)

3. Implement `MintAuthorityChecker`
   - Check if mint authority renounced
   - Flag active mint authority
   - Track mint history (has minter created new supply?)

4. Database migration for security findings cache

5. **Verification:**
   - Test against 50 high-quality tokens → should allow
   - Test against 50 scam tokens → should block

**Estimated effort:** 120 hours

---

### Phase 3: Dev/Owner Tracking (Week 5)

**Goal:** Identify and flag tokens created by known scammers.

**Tasks:**
1. Implement `DevWalletTracker`
   - Get token creator from Metaplex
   - Check against internal scam database
   - Query on-chain token creation history
   
2. Build scam database infrastructure
   - Import public scam lists (Rugpull.io, etc.)
   - Daily sync with known scam sources
   - Allow manual scam address additions
   
3. Add dev wallet flagging to risk decision logic

4. **Verification:**
   - Test against known dev addresses from past scams → should flag

**Estimated effort:** 60 hours

---

### Phase 4: Advanced Detection (Weeks 6-7)

**Goal:** Implement wash trading, price action, and metadata validation.

**Tasks:**
1. Implement `WashTradingDetector`
   - Parse on-chain transactions
   - Track unique traders per timeframe
   - Detect bot patterns (same timing, amounts)

2. Implement `PriceActionAnalyzer`
   - Detect pump-and-dump patterns
   - Flag flash crashes
   - Monitor volatility spikes

3. Implement `MetadataValidator`
   - Check for name/symbol spoofing
   - Validate against known legitimate projects

4. Implement `ExchangeListingChecker`
   - Query CoinGecko API
   - Check major DEX presence
   - Award points for legitimate listings

5. **Verification:**
   - Run against recent pump-and-dump patterns → should flag
   - Check 100 newly deployed tokens → risk distribution should be reasonable

**Estimated effort:** 140 hours

---

### Phase 5: Integration & Testing (Week 8)

**Goal:** Integrate all security modules into main trading pipeline.

**Tasks:**
1. Update `assess_risk_worker` to call security gate
2. Refactor risk scoring to new weighted formula
3. Update trading decision logic with hard constraint blocks
4. Implement blacklist feature (24-72 hour auto-blacklist for critical risks)
5. Add security reasoning to trade rejection messages
6. Create comprehensive logging/audit trail
7. Backtesting against historical data
8. Paper trading validation (48 hours)
9. Documentation update
10. Performance optimization (cache security findings)

**Verification:**
- Paper trading 48 hours → 0 honeypot trades, 0 rugpull exposures
- Manual review of blocked tokens → validate decisions are correct

**Estimated effort:** 100 hours

---

### Phase 6: Monitoring & Refinement (Week 9+)

**Goal:** Continuous improvement and real-world validation.

**Tasks:**
1. Monitor false positive rate (blocked good tokens)
2. Monitor false negative rate (allowed scam tokens)
3. Adjust risk thresholds based on real data
4. Add community feedback mechanism for scam reporting
5. Quarterly scam database audit
6. ML-based anomaly detection for new attack vectors

**Estimated effort:** Ongoing (20 hours/week)

---

## 6. Tech Stack Recommendations

### Backend Enhancements

| Layer | Current | Recommended | Reason |
|-------|---------|-------------|--------|
| **Async HTTP** | httpx | httpx + aiohttp pool | Better connection pooling |
| **RPC Client** | Manual httpx | Helius SDK or Solders | Better contract parsing, caching |
| **Contract Analysis** | None | Anchor IDL + custom bytecode parser | Solana program introspection |
| **ML Detection** | None | scikit-learn + Isolation Forest | Anomaly detection for new patterns |
| **Caching** | Redis basic | Redis with Lua scripts | Atomic cache + security findings |
| **Database** | PostgreSQL | PostgreSQL + TimescaleDB extension | Time-series data for price/volume |
| **Rate Limiting** | None | asyncio-throttle + Redis | Protect against RPC rate limits |

### New Dependencies

```
# backend/requirements.txt additions

# Contract & RPC
solders==0.19.0                    # Solana binary format parsing
anchor-py==0.19.0                  # Anchor IDL support (optional)

# Analysis
scikit-learn==1.3.0                # ML anomaly detection
python-levenshtein==0.21.0         # String similarity for metadata validation

# Data
pandas==2.0.0                      # Historical analysis
numpy==1.24.0                      # Numerical operations

# Monitoring
prometheus-client==0.17.0          # Already in requirements

# Testing
pytest-asyncio==0.21.0             # Async test support
responses==0.23.0                  # HTTP mocking
```

---

## 7. Data Schema Updates

### New Tables

```sql
-- Security Gate Findings Cache
CREATE TABLE security_findings (
    id UUID PRIMARY KEY,
    pair_id UUID REFERENCES pairs(id),
    assessed_at TIMESTAMPTZ NOT NULL,
    
    -- Contract Analysis
    contract_address VARCHAR NOT NULL,
    has_transfer_fee BOOLEAN,
    mint_authority VARCHAR,
    freeze_authority VARCHAR,
    suspicious_functions TEXT[],
    
    -- Holder Distribution
    top_10_holders_pct DECIMAL(5,2),
    concentration_score SMALLINT,
    is_concentrated BOOLEAN,
    
    -- Dev History
    dev_address VARCHAR,
    dev_scam_count SMALLINT DEFAULT 0,
    dev_flagged BOOLEAN DEFAULT FALSE,
    
    -- Price Action
    max_gain_1h_pct DECIMAL(10,2),
    pump_dump_detected BOOLEAN,
    
    -- Wash Trading
    unique_buyers_1h SMALLINT,
    unique_sellers_1h SMALLINT,
    
    -- Metadata
    metadata_valid BOOLEAN,
    is_fake_stablecoin BOOLEAN,
    
    -- Overall
    security_gate_score SMALLINT,
    overall_finding JSONB,  -- Full analysis result
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Scam Database (for dev/contract blacklisting)
CREATE TABLE scam_registry (
    id UUID PRIMARY KEY,
    address VARCHAR UNIQUE NOT NULL,
    address_type VARCHAR,  -- 'contract', 'dev_wallet', 'lp_token'
    scam_type VARCHAR,     -- 'honeypot', 'rugpull', 'fake_token', etc.
    reported_by VARCHAR,   -- data source
    confidence DECIMAL(3,2),  -- 0-1
    first_seen TIMESTAMPTZ,
    rugpull_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT confidence_range CHECK (confidence >= 0 AND confidence <= 1)
);

-- Security Audit Log
CREATE TABLE security_audit_log (
    id UUID PRIMARY KEY,
    pair_id UUID REFERENCES pairs(id),
    block_reason VARCHAR,
    block_details JSONB,
    blocked_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    auto_unblock_at TIMESTAMPTZ,
    INDEX ON blocked_at DESC,
    INDEX ON auto_unblock_at DESC
);
```

---

## 8. Deployment Checklist

- [ ] All security modules unit tested (>90% coverage)
- [ ] Integration tests with mock Solana RPC
- [ ] 48-hour paper trading with 0 scam trades
- [ ] Manual review of 50 blocked tokens (should all be clearly risky)
- [ ] Manual review of 50 allowed tokens (should all seem reasonable)
- [ ] Database migrations tested on staging
- [ ] RPC rate limits verified and cache tuned
- [ ] Security findings cache TTL set appropriately (e.g., 24 hours)
- [ ] Logging and alerting configured for blocked trades
- [ ] Team training on security reasoning output
- [ ] Gradual rollout: Paper → 5% position sizing → Full size
- [ ] 24/7 monitoring for false negatives (scam tokens that got through)

---

## 9. Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Honeypot Detection Rate** | >99% | Test against known honeypots |
| **False Positive Rate** | <5% | % of legitimate tokens blocked |
| **Scam Token Block Rate** | >95% | Historical scam tokens in dataset |
| **Rugpull Prevention** | 100% | No trades on tokens that rugpulled within 30 days |
| **Response Time (Security Gate)** | <500ms | Avg time to evaluate one token |
| **Database Query Time** | <100ms | Holder/contract lookups |

---

## 10. Future Enhancements (Post-Launch)

1. **ML-Based Anomaly Detection**
   - Train models on historical scam patterns
   - Real-time anomaly scoring
   - Adaptive thresholds based on market regime

2. **Community Scam Reporting**
   - User-submitted scam alerts
   - Reputation system for reporters
   - Auto-inclusion in scam registry after verification

3. **Advanced On-Chain Analysis**
   - LP concentration by wallet
   - Swap history analysis per holder
   - MEV attack detection

4. **Social & Community Verification**
   - Twitter follower verification
   - Telegram member growth tracking
   - Discord community analysis

5. **Exchange Delisting Monitoring**
   - Alert if token removed from major exchanges
   - Price correlation with delisting announcements

6. **Regulatory Compliance**
   - Sanctions list screening (OFAC)
   - Regulatory filing checks

---

## 11. Testing Strategy

### Unit Tests (Per Module)

```python
# test_security_gate.py
def test_liquidity_guard_blocks_low_liquidity():
    # Token with $500 liquidity → should block
    pass

def test_honeypot_detector_catches_sells_zero():
    # 50 buys, 0 sells → should block
    pass

def test_contract_analyzer_detects_transfer_fee():
    # Contract with transfer fee function → should flag
    pass

def test_holder_distribution_detects_concentration():
    # Top 10 = 85% supply → should block
    pass

# ... etc for each module
```

### Integration Tests

```python
# test_security_pipeline.py
def test_end_to_end_scam_token():
    # Feed known scam token through pipeline
    # Should block with clear reasons
    pass

def test_end_to_end_legitimate_token():
    # Feed known good token through pipeline
    # Should pass or low risk score
    pass
```

### Backtesting

```python
# backtest_security.py
def backtest_security_against_historical_scams():
    # Load all scam tokens from past 12 months
    # Run security gate on each
    # Measure: % blocked, % caught before rug
    pass
```

---

## 12. References & Data Sources

### Public Scam Lists
- Rugpull.io API
- Telegram scam reporting channels
- DeFi security firms (Certora, Trail of Bits reports)
- DEX Screener community reports

### On-Chain Data APIs
- Solana RPC (self-hosted or Helius)
- Metaplex verified metadata
- Birdeye token analytics
- Magic Eden API

### ML/Analysis Resources
- Solana token security research papers
- Honeypot detection algorithms (academic)
- Wash trading detection techniques

---

## Conclusion

This blueprint transforms memeX into a **security-first trading bot** with:

✅ Comprehensive pre-trade security gate (honeypot, contract, holders, dev history)  
✅ Veto authority for security over predictions  
✅ Hard constraints that auto-block obvious scams  
✅ Risk scoring weighted toward security  
✅ Full audit trail for blocked trades  
✅ Production-ready detection for 90%+ of common meme coin scams  

**Timeline:** 8-9 weeks full implementation, 6-8 weeks if prioritized modules only.  
**Effort:** ~500 hours development + QA.  
**ROI:** Eliminates catastrophic losses to honeypots/rugs, builds user trust, enables higher leverage.

---

*Document Version: 1.0*  
*Last Updated: 2026-09-03*  
*Author: MemeX Security Architecture Team*
