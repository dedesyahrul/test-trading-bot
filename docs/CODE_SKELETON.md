# MemeX Security Implementation: Code Skeleton & Reference

> Ready-to-use code templates and implementation checklist

---

## Phase 1: Module Skeleton (Copy-Paste Ready)

### 1. Module Structure Setup

```bash
# Create the security module directory
mkdir -p backend/app/services/security
touch backend/app/services/security/__init__.py
touch backend/app/services/security/gate.py
touch backend/app/services/security/liquidity_guard.py
touch backend/app/services/security/honeypot_detector.py
touch backend/app/services/security/contract_analyzer.py
touch backend/app/services/security/holder_distribution.py
touch backend/app/services/security/models.py

# Create adapters for RPC calls
touch backend/app/adapters/solana_rpc.py
touch backend/app/adapters/metaplex.py

# Create tests
mkdir -p backend/tests/security
touch backend/tests/security/__init__.py
touch backend/tests/security/test_security_gate.py
touch backend/tests/security/test_contract_analyzer.py
touch backend/tests/security/test_holder_distribution.py
```

### 2. Data Classes (models.py)

```python
# backend/app/services/security/models.py

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from decimal import Decimal

@dataclass
class SecurityCheckResult:
    """Base result class for all security checks."""
    is_blocked: bool
    block_reason: Optional[str] = None
    risk_score: int = 0  # 0-100
    reasons: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)

@dataclass
class LiquidityCheckResult(SecurityCheckResult):
    """Liquidity guard result."""
    liquidity_usd: Optional[Decimal] = None
    threshold_met: bool = False

@dataclass
class HoneypotCheckResult(SecurityCheckResult):
    """Honeypot detector result."""
    buy_count: int = 0
    sell_count: int = 0
    buy_sell_ratio: float = 0.0

@dataclass
class ContractAnalysisResult(SecurityCheckResult):
    """Contract analysis result."""
    contract_address: str = ""
    has_transfer_fee: bool = False
    mint_authority: Optional[str] = None
    freeze_authority: Optional[str] = None
    update_authority: Optional[str] = None
    suspicious_functions: List[str] = field(default_factory=list)
    known_honeypot: bool = False

@dataclass
class HolderAnalysisResult(SecurityCheckResult):
    """Holder distribution result."""
    top_10_pct: float = 0.0
    top_10_count: int = 0
    concentration_score: int = 0
    is_concentrated: bool = False
    excluded_lp_count: int = 0

@dataclass
class SecurityGateResult:
    """Final result from SecurityGateService."""
    is_blocked: bool
    block_reason: Optional[str] = None
    security_gate_score: int = 0
    findings: Dict[str, SecurityCheckResult] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    passed_at: Optional[str] = None  # ISO timestamp
```

### 3. Base Security Guard (liquidity_guard.py)

```python
# backend/app/services/security/liquidity_guard.py

import logging
from decimal import Decimal
from app.services.security.models import LiquidityCheckResult

logger = logging.getLogger(__name__)

class LiquidityGuard:
    """Enhanced liquidity threshold checks."""
    
    # Thresholds (USD)
    CRITICAL_THRESHOLD = Decimal("1000")      # < $1k = automatic block
    HIGH_RISK_THRESHOLD = Decimal("5000")     # $1k-5k = high risk
    MEDIUM_THRESHOLD = Decimal("50000")       # $5k-50k = medium
    LOW_THRESHOLD = Decimal("100000")         # $50k-100k = low
    
    async def check(self, market_snapshot: dict) -> LiquidityCheckResult:
        """
        Check liquidity against hard constraints.
        
        Args:
            market_snapshot: {
                'liquidity_usd': float,
                'buy_count_24h': int,
                'sell_count_24h': int,
                ...
            }
        
        Returns:
            LiquidityCheckResult with risk_score 0-100
        """
        try:
            liquidity_usd = Decimal(str(market_snapshot.get('liquidity_usd') or 0))
        except (ValueError, TypeError):
            liquidity_usd = Decimal("0")
        
        # Hard constraint: < $1k
        if liquidity_usd < self.CRITICAL_THRESHOLD:
            return LiquidityCheckResult(
                is_blocked=True,
                block_reason=f"Liquidity ${float(liquidity_usd):.2f} below critical threshold ($1,000)",
                risk_score=100,
                liquidity_usd=liquidity_usd,
                reasons=[f"Critical liquidity shortage (${float(liquidity_usd):.2f})"],
            )
        
        # Calculate risk score based on tiers
        if liquidity_usd < self.HIGH_RISK_THRESHOLD:
            risk_score = 85
            tier = "HIGH_RISK"
        elif liquidity_usd < self.MEDIUM_THRESHOLD:
            risk_score = 60
            tier = "MEDIUM"
        elif liquidity_usd < self.LOW_THRESHOLD:
            risk_score = 30
            tier = "LOW"
        else:
            risk_score = 10
            tier = "SAFE"
        
        logger.info(f"Liquidity check: ${float(liquidity_usd):.2f} → {tier} (score: {risk_score})")
        
        return LiquidityCheckResult(
            is_blocked=False,
            risk_score=risk_score,
            liquidity_usd=liquidity_usd,
            threshold_met=True,
            reasons=[f"Liquidity: ${float(liquidity_usd):.2f} ({tier})"],
            details={
                'tier': tier,
                'liquidity_usd': float(liquidity_usd),
            }
        )
```

### 4. Honeypot Detector (honeypot_detector.py)

```python
# backend/app/services/security/honeypot_detector.py

import logging
from app.services.security.models import HoneypotCheckResult

logger = logging.getLogger(__name__)

class HoneypotDetector:
    """Enhanced honeypot detection (buy-only trap)."""
    
    # Hard constraint: buys > threshold AND sells = 0
    BUY_THRESHOLD = 50  # If > 50 buys but 0 sells
    
    async def check(self, market_snapshot: dict) -> HoneypotCheckResult:
        """
        Detect honeypot: token where buys exist but sells = 0.
        Indicates traders can't sell (trapped).
        
        Args:
            market_snapshot: {
                'buy_count_24h': int,
                'sell_count_24h': int,
                ...
            }
        
        Returns:
            HoneypotCheckResult
        """
        buy_count = market_snapshot.get('buy_count_24h') or 0
        sell_count = market_snapshot.get('sell_count_24h') or 0
        
        # Calculate ratio
        if sell_count == 0:
            if buy_count == 0:
                # No activity at all
                ratio = 0.0
                risk_score = 20
            else:
                # Infinite ratio (buys but no sells)
                ratio = float('inf')
                risk_score = 90
        else:
            ratio = buy_count / sell_count
            
            if ratio > 10:
                risk_score = 90
            elif ratio > 5:
                risk_score = 70
            elif ratio > 2:
                risk_score = 40
            elif 0.5 <= ratio <= 2:
                risk_score = 10
            else:
                risk_score = 50  # More sells than buys (unusual)
        
        # Hard constraint: buys > 50 AND sells = 0
        is_honeypot = sell_count == 0 and buy_count > self.BUY_THRESHOLD
        
        reason = ""
        if is_honeypot:
            reason = f"Honeypot detected: {buy_count} buys but 0 sells (trapped)"
        elif sell_count == 0 and buy_count > 0:
            reason = f"Low activity: {buy_count} buys but 0 sells (suspicious)"
        else:
            reason = f"Buy/sell ratio: {ratio:.2f}x ({buy_count} buys, {sell_count} sells)"
        
        logger.info(f"Honeypot check: {reason} (risk: {risk_score})")
        
        return HoneypotCheckResult(
            is_blocked=is_honeypot,
            block_reason=reason if is_honeypot else None,
            risk_score=risk_score,
            buy_count=buy_count,
            sell_count=sell_count,
            buy_sell_ratio=ratio,
            reasons=[reason],
            details={
                'buy_count': buy_count,
                'sell_count': sell_count,
                'ratio': ratio if ratio != float('inf') else 'inf',
                'is_honeypot': is_honeypot,
            }
        )
```

### 5. Contract Analyzer Skeleton (contract_analyzer.py)

```python
# backend/app/services/security/contract_analyzer.py

import logging
from typing import Optional
from app.services.security.models import ContractAnalysisResult
from app.adapters.solana_rpc import SolanaRPCClient
from app.adapters.metaplex import MetaplexClient

logger = logging.getLogger(__name__)

class ContractAnalyzer:
    """Analyze token contract for malicious patterns."""
    
    def __init__(self, rpc_client: SolanaRPCClient, metaplex_client: MetaplexClient):
        self.rpc = rpc_client
        self.metaplex = metaplex_client
    
    async def analyze(
        self,
        chain: str,
        token_address: str,
    ) -> ContractAnalysisResult:
        """
        Analyze token contract for:
        1. Transfer fee (hidden tax)
        2. Mint authority (can dilute)
        3. Freeze authority (can freeze)
        4. Known honeypot patterns
        
        Args:
            chain: "solana"
            token_address: Token mint address
        
        Returns:
            ContractAnalysisResult
        """
        try:
            # Step 1: Get mint account from RPC
            mint_account = await self.rpc.get_mint(token_address)
            if not mint_account:
                logger.warning(f"Could not fetch mint account for {token_address}")
                return ContractAnalysisResult(
                    is_blocked=False,
                    risk_score=30,  # Conservative if can't analyze
                    contract_address=token_address,
                    reasons=["Could not fetch contract data (RPC error)"],
                )
            
            # Step 2: Extract authorities
            mint_authority = mint_account.get('mint_authority')
            freeze_authority = mint_account.get('freeze_authority')
            
            # Step 3: Check for transfer fee (Solana extension)
            has_transfer_fee = await self._check_transfer_fee(token_address)
            
            # Step 4: Check against known honeypot patterns
            known_honeypot = await self._check_known_patterns(token_address)
            
            # Calculate risk score
            risk_score = 0
            reasons = []
            
            if has_transfer_fee:
                risk_score += 30
                reasons.append("Transfer fee detected (hidden tax)")
            
            if mint_authority:
                risk_score += 25
                reasons.append(f"Mint authority active: {mint_authority}")
            
            if freeze_authority:
                risk_score += 15
                reasons.append(f"Freeze authority exists: {freeze_authority}")
            
            if known_honeypot:
                risk_score = 95
                reasons.append("Known honeypot pattern detected")
            
            # Cap at 100
            risk_score = min(risk_score, 100)
            
            is_blocked = known_honeypot or (has_transfer_fee and mint_authority)
            
            return ContractAnalysisResult(
                is_blocked=is_blocked,
                block_reason=f"Malicious contract detected" if is_blocked else None,
                risk_score=risk_score,
                contract_address=token_address,
                has_transfer_fee=has_transfer_fee,
                mint_authority=mint_authority,
                freeze_authority=freeze_authority,
                known_honeypot=known_honeypot,
                reasons=reasons,
                details={
                    'has_transfer_fee': has_transfer_fee,
                    'mint_authority': mint_authority,
                    'freeze_authority': freeze_authority,
                    'known_honeypot': known_honeypot,
                }
            )
        
        except Exception as e:
            logger.error(f"Contract analysis error: {e}")
            return ContractAnalysisResult(
                is_blocked=False,
                risk_score=25,
                contract_address=token_address,
                reasons=[f"Analysis failed: {str(e)}"],
            )
    
    async def _check_transfer_fee(self, token_address: str) -> bool:
        """Check if token has transfer fee extension."""
        try:
            # Query RPC for transfer fee state
            # This requires parsing Solana program state
            # For now, return False (TODO: implement via Helius or custom parser)
            return False
        except Exception as e:
            logger.warning(f"Transfer fee check failed: {e}")
            return False
    
    async def _check_known_patterns(self, token_address: str) -> bool:
        """Check against known honeypot/scam patterns."""
        # TODO: Implement check against scam database
        # For now, always return False
        return False
```

### 6. Holder Distribution Analyzer (holder_distribution.py)

```python
# backend/app/services/security/holder_distribution.py

import logging
from typing import List, Dict
from app.services.security.models import HolderAnalysisResult
from app.adapters.solana_rpc import SolanaRPCClient

logger = logging.getLogger(__name__)

KNOWN_LP_ADDRESSES = {
    # Raydium LP
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1xF",
    # Orca LP
    "9W957wfaHHNaG9eZyEmu4r34Marj4KXQxupT8PGkxbreak",
    # Magic Eden
    "1BWutmtRyPHTu1JeuknkQv4FVsihgg6ein6qBUR5alaW",
    # Burn address
    "1111111111111111111111111111111111111111111111",
}

class HolderDistributionAnalyzer:
    """Analyze top token holder concentration."""
    
    CONCENTRATION_THRESHOLD = 80.0  # % - 80%+ in top 10 = concentration risk
    
    def __init__(self, rpc_client: SolanaRPCClient):
        self.rpc = rpc_client
    
    async def analyze(
        self,
        chain: str,
        token_address: str,
        top_n: int = 20,
    ) -> HolderAnalysisResult:
        """
        Analyze top token holders for concentration.
        
        Args:
            chain: "solana"
            token_address: Token mint address
            top_n: Number of top holders to analyze
        
        Returns:
            HolderAnalysisResult
        """
        try:
            # Step 1: Get total supply
            mint_info = await self.rpc.get_mint(token_address)
            total_supply = float(mint_info.get('supply') or 0)
            
            if total_supply == 0:
                return HolderAnalysisResult(
                    is_blocked=True,
                    block_reason="Zero total supply (invalid token)",
                    risk_score=100,
                    reasons=["Total supply is 0"],
                )
            
            # Step 2: Get top holders
            holders = await self.rpc.get_top_holders(token_address, top_n)
            if not holders:
                # If we can't get holder data, assume medium risk
                return HolderAnalysisResult(
                    is_blocked=False,
                    risk_score=35,
                    reasons=["Could not fetch holder data (RPC limit)"],
                )
            
            # Step 3: Filter out LP and burn addresses
            non_lp_holders = [
                h for h in holders
                if h['address'] not in KNOWN_LP_ADDRESSES
            ]
            
            # Step 4: Calculate concentration
            top_10_pct = self._calculate_top_n_percentage(
                non_lp_holders[:10],
                total_supply
            )
            
            # Step 5: Determine concentration risk
            concentration_score = self._calculate_concentration_score(top_10_pct)
            is_concentrated = top_10_pct > self.CONCENTRATION_THRESHOLD
            
            risk_score = concentration_score
            reasons = [f"Top 10 holders: {top_10_pct:.1f}% of supply"]
            
            if is_concentrated:
                reasons.append(f"CONCENTRATED: {top_10_pct:.1f}% > {self.CONCENTRATION_THRESHOLD}% threshold")
            
            logger.info(f"Holder analysis: {top_10_pct:.1f}% in top 10 (risk: {risk_score})")
            
            return HolderAnalysisResult(
                is_blocked=is_concentrated,
                block_reason=f"Holder concentration: {top_10_pct:.1f}% in top 10" if is_concentrated else None,
                risk_score=risk_score,
                top_10_pct=top_10_pct,
                top_10_count=len(non_lp_holders[:10]),
                concentration_score=concentration_score,
                is_concentrated=is_concentrated,
                excluded_lp_count=len(holders) - len(non_lp_holders),
                reasons=reasons,
                details={
                    'top_10_pct': top_10_pct,
                    'top_10_count': len(non_lp_holders[:10]),
                    'total_holders': len(holders),
                    'excluded_lp': len(holders) - len(non_lp_holders),
                }
            )
        
        except Exception as e:
            logger.error(f"Holder analysis error: {e}")
            return HolderAnalysisResult(
                is_blocked=False,
                risk_score=25,
                reasons=[f"Analysis failed: {str(e)}"],
            )
    
    def _calculate_top_n_percentage(self, holders: List[Dict], total_supply: float) -> float:
        """Calculate % of supply held by top N holders."""
        if not holders or total_supply == 0:
            return 0.0
        
        top_n_balance = sum(float(h.get('balance') or 0) for h in holders)
        return (top_n_balance / total_supply) * 100
    
    def _calculate_concentration_score(self, top_10_pct: float) -> int:
        """
        Convert top 10 % to risk score (0-100).
        
        > 85% → 95 (block)
        70-85% → 80 (high risk)
        50-70% → 60 (medium)
        < 50% → 10-20 (safe)
        """
        if top_10_pct > 85:
            return 95
        elif top_10_pct > 70:
            return 80
        elif top_10_pct > 50:
            return 60
        elif top_10_pct > 30:
            return 35
        else:
            return 10
```

### 7. Security Gate Orchestrator (gate.py)

```python
# backend/app/services/security/gate.py

import logging
from dataclasses import dataclass
from typing import Optional
from app.services.security.models import (
    SecurityGateResult,
    SecurityCheckResult,
)
from app.services.security.liquidity_guard import LiquidityGuard
from app.services.security.honeypot_detector import HoneypotDetector
from app.services.security.contract_analyzer import ContractAnalyzer
from app.services.security.holder_distribution import HolderDistributionAnalyzer

logger = logging.getLogger(__name__)

class SecurityGateService:
    """Main security gate orchestrator."""
    
    def __init__(
        self,
        liquidity_guard: LiquidityGuard,
        honeypot_detector: HoneypotDetector,
        contract_analyzer: ContractAnalyzer,
        holder_analyzer: HolderDistributionAnalyzer,
    ):
        self.liquidity_guard = liquidity_guard
        self.honeypot_detector = honeypot_detector
        self.contract_analyzer = contract_analyzer
        self.holder_analyzer = holder_analyzer
    
    async def evaluate_token(
        self,
        chain: str,
        token_address: str,
        pair_address: str,
        market_snapshot: dict,
    ) -> SecurityGateResult:
        """
        Run all security checks in sequence.
        Return BLOCK immediately on hard constraints.
        
        Order: Liquidity → Honeypot → Contract → Holders
        """
        findings = {}
        scores = {}
        reasons = []
        
        # 1. LIQUIDITY GUARD (fastest, hard constraint)
        logger.info(f"[SECURITY GATE] Evaluating {token_address}...")
        liquidity_result = await self.liquidity_guard.check(market_snapshot)
        findings['liquidity'] = liquidity_result
        
        if liquidity_result.is_blocked:
            logger.warning(f"[BLOCKED] Liquidity: {liquidity_result.block_reason}")
            return SecurityGateResult(
                is_blocked=True,
                block_reason=liquidity_result.block_reason,
                security_gate_score=100,
                findings=findings,
                reasons=[liquidity_result.block_reason],
            )
        scores['liquidity'] = liquidity_result.risk_score
        
        # 2. HONEYPOT DETECTOR (hard constraint)
        honeypot_result = await self.honeypot_detector.check(market_snapshot)
        findings['honeypot'] = honeypot_result
        
        if honeypot_result.is_blocked:
            logger.warning(f"[BLOCKED] Honeypot: {honeypot_result.block_reason}")
            return SecurityGateResult(
                is_blocked=True,
                block_reason=honeypot_result.block_reason,
                security_gate_score=95,
                findings=findings,
                reasons=[honeypot_result.block_reason],
            )
        scores['honeypot'] = honeypot_result.risk_score
        
        # 3. CONTRACT ANALYZER
        try:
            contract_result = await self.contract_analyzer.analyze(chain, token_address)
            findings['contract'] = contract_result
            
            if contract_result.is_blocked:
                logger.warning(f"[BLOCKED] Contract: {contract_result.block_reason}")
                return SecurityGateResult(
                    is_blocked=True,
                    block_reason=contract_result.block_reason,
                    security_gate_score=90,
                    findings=findings,
                    reasons=[contract_result.block_reason],
                )
            scores['contract'] = contract_result.risk_score
        except Exception as e:
            logger.warning(f"Contract analysis failed: {e}")
            scores['contract'] = 30
        
        # 4. HOLDER DISTRIBUTION
        try:
            holder_result = await self.holder_analyzer.analyze(chain, token_address)
            findings['holders'] = holder_result
            
            if holder_result.is_blocked:
                logger.warning(f"[BLOCKED] Holders: {holder_result.block_reason}")
                return SecurityGateResult(
                    is_blocked=True,
                    block_reason=holder_result.block_reason,
                    security_gate_score=85,
                    findings=findings,
                    reasons=[holder_result.block_reason],
                )
            scores['holders'] = holder_result.risk_score
        except Exception as e:
            logger.warning(f"Holder analysis failed: {e}")
            scores['holders'] = 25
        
        # PASSED: Calculate weighted security gate score
        security_gate_score = (
            scores.get('liquidity', 30) * 0.25 +
            scores.get('honeypot', 30) * 0.25 +
            scores.get('contract', 30) * 0.25 +
            scores.get('holders', 25) * 0.25
        )
        
        # Collect reasons
        for key, result in findings.items():
            if hasattr(result, 'reasons'):
                reasons.extend(result.reasons)
        
        logger.info(f"[PASSED] Security gate score: {int(security_gate_score)} ({', '.join(reasons[:2])}...)")
        
        return SecurityGateResult(
            is_blocked=False,
            block_reason=None,
            security_gate_score=int(security_gate_score),
            findings=findings,
            reasons=reasons,
        )
```

---

## Integration Checklist

### Update Worker

```python
# backend/app/workers/main.py

from app.services.security.gate import SecurityGateService

# In your assess_risk_worker or collect_market_data_worker:

async def assess_risk_worker(
    session: AsyncSession,
    pair_id: str,
    market_snapshot: dict,
    security_gate_service: SecurityGateService,  # Inject
    risk_engine: RiskEngine,
):
    """
    1. Security gate (NEW)
    2. Feature engineering
    3. Risk scoring
    """
    
    # STEP 1: Security Gate (NEW!)
    token_address = market_snapshot.get('token_address')
    gate_result = await security_gate_service.evaluate_token(
        chain="solana",
        token_address=token_address,
        pair_address=pair_address,
        market_snapshot=market_snapshot,
    )
    
    # If blocked, log and return early
    if gate_result.is_blocked:
        logger.warning(f"Token {token_address} blocked: {gate_result.block_reason}")
        
        # Save to security audit log
        audit_log = SecurityAuditLog(
            pair_id=pair_id,
            block_reason=gate_result.block_reason,
            block_details=gate_result.findings,
            blocked_at=datetime.utcnow(),
        )
        session.add(audit_log)
        await session.commit()
        return  # Stop processing
    
    # STEP 2: Feature Engineering (existing)
    features = await compute_features_worker(session, pair_id, market_snapshot)
    
    # STEP 3: Risk Assessment (updated to use security gate score)
    risk_assessment = await risk_engine.assess_risk(
        session=session,
        pair_id=pair_id,
        market_snapshot=market_snapshot,
        security_gate_score=gate_result.security_gate_score,  # NEW
        feature=features,
    )
    
    # Continue with existing pipeline...
```

### Update Risk Engine

```python
# backend/app/services/risk/engine.py

async def assess_risk(
    session: AsyncSession,
    pair_id,
    market_snapshot: MarketSnapshot,
    security_gate_score: int = 0,  # NEW parameter
    feature: Optional[Feature] = None,
) -> RiskAssessment:
    """
    Updated risk scoring with security gate contribution.
    """
    
    # Calculate individual risk scores
    liquidity_risk = self._calculate_liquidity_risk(market_snapshot)
    manipulation_risk = self._calculate_manipulation_risk(market_snapshot)
    volatility_risk = self._calculate_volatility_risk(feature)
    execution_risk = self._calculate_execution_risk(market_snapshot)
    
    # NEW: Weighted formula with security gate
    overall_risk_score = (
        security_gate_score * 0.40 +      # Security gate: 40%
        liquidity_risk * 0.20 +
        manipulation_risk * 0.15 +
        volatility_risk * 0.12 +
        execution_risk * 0.08 +
        metadata_risk * 0.05              # Future: metadata validation
    )
    
    # ... rest of existing logic ...
```

---

## Database Migrations

```python
# backend/alembic/versions/002_security_tables.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Security findings cache table
    op.create_table(
        'security_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pairs.id'), nullable=False),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False),
        
        # Contract analysis
        sa.Column('contract_address', sa.String, nullable=False),
        sa.Column('has_transfer_fee', sa.Boolean),
        sa.Column('mint_authority', sa.String),
        sa.Column('freeze_authority', sa.String),
        sa.Column('suspicious_functions', postgresql.ARRAY(sa.String)),
        
        # Holder distribution
        sa.Column('top_10_holders_pct', sa.Numeric(5, 2)),
        sa.Column('concentration_score', sa.SmallInteger),
        sa.Column('is_concentrated', sa.Boolean),
        
        # Overall
        sa.Column('security_gate_score', sa.SmallInteger),
        sa.Column('overall_finding', postgresql.JSON),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_security_findings_pair_id', 'security_findings', ['pair_id'])
    op.create_index('idx_security_findings_assessed_at', 'security_findings', ['assessed_at'])
    
    # Scam registry table
    op.create_table(
        'scam_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('address', sa.String, unique=True, nullable=False),
        sa.Column('address_type', sa.String),  # 'contract', 'dev_wallet'
        sa.Column('scam_type', sa.String),     # 'honeypot', 'rugpull'
        sa.Column('reported_by', sa.String),
        sa.Column('confidence', sa.Numeric(3, 2)),
        sa.Column('first_seen', sa.DateTime(timezone=True)),
        sa.Column('rugpull_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_scam_registry_address', 'scam_registry', ['address'])
    op.create_index('idx_scam_registry_type', 'scam_registry', ['address_type'])
    
    # Security audit log
    op.create_table(
        'security_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pairs.id')),
        sa.Column('block_reason', sa.String),
        sa.Column('block_details', postgresql.JSON),
        sa.Column('blocked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('auto_unblock_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_security_audit_blocked_at', 'security_audit_log', ['blocked_at'])
    op.create_index('idx_security_audit_auto_unblock', 'security_audit_log', ['auto_unblock_at'])

def downgrade():
    op.drop_table('security_audit_log')
    op.drop_table('scam_registry')
    op.drop_table('security_findings')
```

---

## Testing Examples

```python
# backend/tests/security/test_security_gate.py

import pytest
from unittest.mock import patch, AsyncMock
from app.services.security.gate import SecurityGateService
from app.services.security.liquidity_guard import LiquidityGuard
from app.services.security.honeypot_detector import HoneypotDetector
from app.services.security.contract_analyzer import ContractAnalyzer
from app.services.security.holder_distribution import HolderDistributionAnalyzer

@pytest.fixture
def security_gate_service():
    return SecurityGateService(
        liquidity_guard=LiquidityGuard(),
        honeypot_detector=HoneypotDetector(),
        contract_analyzer=AsyncMock(spec=ContractAnalyzer),
        holder_analyzer=AsyncMock(spec=HolderDistributionAnalyzer),
    )

@pytest.mark.asyncio
async def test_blocks_low_liquidity(security_gate_service):
    """Token with <$1k liquidity should be blocked."""
    market_snapshot = {
        'liquidity_usd': 500,
        'buy_count_24h': 50,
        'sell_count_24h': 45,
    }
    
    result = await security_gate_service.evaluate_token(
        chain="solana",
        token_address="token123",
        pair_address="pair123",
        market_snapshot=market_snapshot,
    )
    
    assert result.is_blocked == True
    assert "liquidity" in result.block_reason.lower()

@pytest.mark.asyncio
async def test_blocks_honeypot(security_gate_service):
    """Token with 0 sells but 100+ buys should be blocked."""
    market_snapshot = {
        'liquidity_usd': 50000,
        'buy_count_24h': 150,
        'sell_count_24h': 0,
    }
    
    result = await security_gate_service.evaluate_token(
        chain="solana",
        token_address="honeypot123",
        pair_address="pair123",
        market_snapshot=market_snapshot,
    )
    
    assert result.is_blocked == True
    assert "honeypot" in result.block_reason.lower()

@pytest.mark.asyncio
async def test_allows_legitimate_token(security_gate_service):
    """Legitimate token should pass."""
    market_snapshot = {
        'liquidity_usd': 100000,
        'buy_count_24h': 150,
        'sell_count_24h': 140,
    }
    
    # Mock contract and holder analyzers
    security_gate_service.contract_analyzer.analyze = AsyncMock(
        return_value=type('obj', (object,), {
            'is_blocked': False,
            'risk_score': 10,
            'reasons': []
        })()
    )
    security_gate_service.holder_analyzer.analyze = AsyncMock(
        return_value=type('obj', (object,), {
            'is_blocked': False,
            'risk_score': 5,
            'reasons': []
        })()
    )
    
    result = await security_gate_service.evaluate_token(
        chain="solana",
        token_address="good_token123",
        pair_address="pair123",
        market_snapshot=market_snapshot,
    )
    
    assert result.is_blocked == False
    assert result.security_gate_score < 40
```

---

## Implementation Checklist: Phase 1

- [ ] Create `/security/` module directory
- [ ] Implement `models.py` with data classes
- [ ] Implement `liquidity_guard.py`
- [ ] Implement `honeypot_detector.py`
- [ ] Implement `contract_analyzer.py` (skeleton)
- [ ] Implement `holder_distribution.py` (skeleton)
- [ ] Implement `gate.py` orchestrator
- [ ] Create `solana_rpc.py` adapter
- [ ] Create database migration (security tables)
- [ ] Write unit tests (all modules)
- [ ] Update worker to call security gate
- [ ] Update risk engine to use security gate score
- [ ] Deploy to staging
- [ ] 48-72 hour paper trading validation
- [ ] Tune thresholds based on data
- [ ] Deploy to production (paper mode)
- [ ] Monitor for 1 week
- [ ] Enable live trading (5% position size)

---

## Next Steps

1. **Copy-paste the skeletons** into your codebase
2. **Fill in the TODO sections** (RPC methods, contract parsing)
3. **Run unit tests** locally
4. **Deploy to staging** and test
5. **Paper trade 48 hours** 
6. **Deploy to production**

You're ready to build. Good luck!

---

*Code Version: 1.0*  
*Last Updated: 2026-09-03T15:21:18.723Z*  
*Status: Ready to Implement*
