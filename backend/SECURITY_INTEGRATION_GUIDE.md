"""Integration guide for SecurityGateService with memeX workers.

This module shows how to integrate the security gate into the existing
worker pipeline to add security-first pre-trade filtering.
"""

# ============================================================================
# STEP 1: Import the SecurityGateService
# ============================================================================

# Add this to backend/app/workers/main.py at the top:

from app.services.security.gate import SecurityGateService

# Initialize the security gate service (once, at module level)
security_gate_service = SecurityGateService()


# ============================================================================
# STEP 2: Add security gate check to assess_risk_worker
# ============================================================================

# Find this function in backend/app/workers/main.py and add security gate:

async def assess_risk_worker(pair_id: str) -> None:
    """Assess risk for a pair. NOW WITH SECURITY GATE!
    
    Pipeline:
    1. [NEW] Security Gate - Pre-trade filter (honeypot, liquidity, etc.)
    2. Feature Engineering - Compute technicals
    3. Risk Assessment - Risk scoring
    4. Signal Generation - Buy/sell decision
    """
    async with async_session_maker() as session:
        try:
            pair = await session.get(Pair, pair_id)
            if not pair:
                logger.warning("Pair %s not found", pair_id)
                return
            
            # Get latest market snapshot
            market_data_service = MarketDataService(session)
            snapshot = await market_data_service.get_latest_snapshot(pair_id)
            
            if not snapshot:
                logger.warning("No market snapshot for pair %s", pair_id)
                return
            
            # ================================================================
            # NEW: SECURITY GATE CHECK (Layer 0 - before anything else)
            # ================================================================
            logger.info(f"[RISK] Starting risk assessment for pair {pair_id}")
            logger.info(f"[SECURITY] Running security gate for token {pair.base_token.address}")
            
            gate_result = await security_gate_service.evaluate_token(
                chain=pair.chain.name.lower(),
                token_address=pair.base_token.address,
                pair_address=pair.pair_address,
                market_snapshot={
                    'liquidity_usd': float(snapshot.liquidity_usd or 0),
                    'buy_count_24h': snapshot.buy_count_24h or 0,
                    'sell_count_24h': snapshot.sell_count_24h or 0,
                    'volume_24h_usd': float(snapshot.volume_24h_usd or 0),
                    'price_usd': float(snapshot.price_usd or 0),
                    # Include other market data as needed
                }
            )
            
            # If security gate blocks the token, log and stop processing
            if gate_result.is_blocked:
                logger.error(
                    f"[SECURITY] Token {pair.base_token.address} BLOCKED by security gate: "
                    f"{gate_result.block_reason}"
                )
                
                # Save to security audit log (if you implement it)
                # audit_log = SecurityAuditLog(
                #     pair_id=pair_id,
                #     block_reason=gate_result.block_reason,
                #     block_details=gate_result.findings,
                #     blocked_at=datetime.utcnow(),
                # )
                # session.add(audit_log)
                # await session.commit()
                
                return  # Stop processing this token
            
            # Security gate passed - continue with normal pipeline
            logger.info(
                f"[SECURITY] Token {pair.base_token.address} PASSED security gate "
                f"(security score: {gate_result.security_gate_score}/100)"
            )
            
            # ================================================================
            # EXISTING: Feature Engineering (unchanged)
            # ================================================================
            feature_engine = FeatureEngineering(session)
            features = await feature_engine.compute_features(
                pair_id=pair_id,
                snapshots=[snapshot],
                pair=pair,
            )
            
            if not features:
                logger.warning("No features computed for pair %s", pair_id)
                return
            
            # ================================================================
            # MODIFIED: Risk Assessment (now includes security_gate_score)
            # ================================================================
            risk_engine = RiskEngine()
            risk_assessment = await risk_engine.assess_risk(
                session=session,
                pair_id=pair_id,
                market_snapshot=snapshot,
                feature=features,
                security_gate_score=gate_result.security_gate_score,  # NEW!
            )
            
            if not risk_assessment:
                logger.warning("Risk assessment failed for pair %s", pair_id)
                return
            
            logger.info(
                f"Risk assessment for {pair_id}: score={risk_assessment.risk_score}, "
                f"level={risk_assessment.risk_level}"
            )
            
            # ================================================================
            # EXISTING: Signal Generation (unchanged, but now uses security-adjusted risk)
            # ================================================================
            # ... rest of existing code ...
            
        except Exception as e:
            logger.error(f"assess_risk_worker error for pair {pair_id}: {e}", exc_info=True)


# ============================================================================
# STEP 3: Update RiskEngine to accept security_gate_score
# ============================================================================

# Modify backend/app/services/risk/engine.py:

# In the assess_risk() method, add security_gate_score parameter:

async def assess_risk(
    session: AsyncSession,
    pair_id,
    market_snapshot: MarketSnapshot,
    security_gate_score: int = 0,  # NEW PARAMETER
    feature: Optional[Feature] = None,
) -> RiskAssessment:
    """Assess token risk with security-first weighting.
    
    Args:
        security_gate_score: 0-100 from SecurityGateService
    """
    
    # Calculate individual risk scores
    liquidity_risk = self._calculate_liquidity_risk(market_snapshot)
    manipulation_risk = self._calculate_manipulation_risk(market_snapshot)
    volatility_risk = self._calculate_volatility_risk(feature)
    execution_risk = self._calculate_execution_risk(market_snapshot)
    
    # NEW: Weighted formula with security gate contribution (40%)
    overall_risk_score = (
        security_gate_score * 0.40 +      # Security gate: 40% weight (CRITICAL)
        liquidity_risk * 0.20 +
        manipulation_risk * 0.15 +
        volatility_risk * 0.12 +
        execution_risk * 0.08 +
        metadata_risk * 0.05               # Future: metadata validation
    )
    
    # Determine risk level
    risk_level = "UNKNOWN"
    for (min_score, max_score), level in self.RISK_LEVELS.items():
        if min_score <= overall_risk_score <= max_score:
            risk_level = level
            break
    
    # ... rest of existing code ...


# ============================================================================
# STEP 4: Database Schema Updates (Optional, for audit trail)
# ============================================================================

# Add these tables to capture security decisions:

# alembic/versions/003_security_audit.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Security audit log table
    op.create_table(
        'security_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.func.gen_random_uuid()),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('pairs.id')),
        sa.Column('block_reason', sa.String, nullable=False),
        sa.Column('block_details', postgresql.JSON),
        sa.Column('security_score', sa.SmallInteger),
        sa.Column('blocked_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now()),
        sa.Column('auto_unblock_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_security_audit_pair_id', 'security_audit_log', ['pair_id'])
    op.create_index('idx_security_audit_blocked_at', 'security_audit_log', ['blocked_at'])

def downgrade():
    op.drop_table('security_audit_log')


# ============================================================================
# STEP 5: Configuration (Optional settings for security gate)
# ============================================================================

# Add to backend/app/core/config.py:

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Security Gate Configuration
    SECURITY_GATE_ENABLED: bool = True
    SECURITY_LIQUIDITY_THRESHOLD_USD: int = 1000  # Hard constraint
    SECURITY_HONEYPOT_BUY_THRESHOLD: int = 50     # Hard constraint
    SECURITY_HOLDER_CONCENTRATION_THRESHOLD: float = 85.0  # % (hard constraint)
    
    # Risk score contribution from security gate
    SECURITY_SCORE_WEIGHT: float = 0.40  # 40% of total risk score


# ============================================================================
# STEP 6: Monitoring and Logging
# ============================================================================

# Add metrics to track security decisions:

from prometheus_client import Counter, Histogram

# Security metrics
security_gate_blocks = Counter(
    'security_gate_blocks_total',
    'Total tokens blocked by security gate',
    ['reason']  # honeypot, liquidity, contract, holders
)

security_gate_latency = Histogram(
    'security_gate_latency_seconds',
    'Time to evaluate token through security gate'
)

security_tokens_evaluated = Counter(
    'security_tokens_evaluated_total',
    'Total tokens evaluated by security gate',
    ['result']  # blocked, passed
)

# Usage in SecurityGateService:
import time

async def evaluate_token(...) -> SecurityGateResult:
    start_time = time.time()
    
    # ... evaluation logic ...
    
    duration = time.time() - start_time
    security_gate_latency.observe(duration)
    
    if result.is_blocked:
        security_gate_blocks.labels(reason=extract_reason(result)).inc()
        security_tokens_evaluated.labels(result='blocked').inc()
    else:
        security_tokens_evaluated.labels(result='passed').inc()
    
    return result


# ============================================================================
# STEP 7: Testing the Integration
# ============================================================================

# Test file: backend/tests/test_security_integration.py

import pytest
from unittest.mock import AsyncMock, patch
from app.services.security.gate import SecurityGateService
from app.workers.main import assess_risk_worker

@pytest.mark.asyncio
async def test_assess_risk_worker_blocks_honeypot(async_session):
    """assess_risk_worker should stop processing if security gate blocks."""
    
    # Setup: Create pair and market snapshot
    pair = await create_test_pair(async_session)
    snapshot = await create_test_snapshot(
        async_session, 
        pair_id=pair.id,
        buy_count_24h=150,
        sell_count_24h=0,  # Honeypot!
    )
    
    # Mock security gate to return blocked result
    with patch('app.workers.main.security_gate_service.evaluate_token') as mock_gate:
        mock_gate.return_value = type('obj', (object,), {
            'is_blocked': True,
            'block_reason': 'Honeypot detected: 150 buys, 0 sells',
            'security_gate_score': 95,
        })()
        
        # Call assess_risk_worker
        await assess_risk_worker(pair.id)
        
        # Verify: No risk assessment should be created
        result = await async_session.execute(
            select(RiskAssessment).where(RiskAssessment.pair_id == pair.id)
        )
        risk_assessments = result.scalars().all()
        assert len(risk_assessments) == 0, "Risk assessment should not be created for blocked token"


@pytest.mark.asyncio
async def test_assess_risk_worker_continues_on_pass(async_session):
    """assess_risk_worker should continue if security gate passes."""
    
    # Setup: Create pair and market snapshot (safe)
    pair = await create_test_pair(async_session)
    snapshot = await create_test_snapshot(
        async_session,
        pair_id=pair.id,
        liquidity_usd=100000,
        buy_count_24h=150,
        sell_count_24h=140,
    )
    
    # Mock security gate to return passed result
    with patch('app.workers.main.security_gate_service.evaluate_token') as mock_gate:
        mock_gate.return_value = type('obj', (object,), {
            'is_blocked': False,
            'block_reason': None,
            'security_gate_score': 15,
        })()
        
        # Mock feature engine
        with patch('app.workers.main.FeatureEngineering.compute_features') as mock_features:
            mock_features.return_value = {'volatility_1h': 0.5}
            
            # Call assess_risk_worker
            await assess_risk_worker(pair.id)
            
            # Verify: Risk assessment should be created
            result = await async_session.execute(
                select(RiskAssessment).where(RiskAssessment.pair_id == pair.id)
            )
            risk_assessments = result.scalars().all()
            assert len(risk_assessments) > 0, "Risk assessment should be created for passed token"


# ============================================================================
# STEP 8: Gradual Rollout
# ============================================================================

# Week 1: Enable in STAGING with paper trading
# - Run for 48-72 hours
# - Collect metrics on blocking rate, false positives
# - Monitor logs for any issues

# Week 2: Enable in PRODUCTION with paper mode
# - Start with all trading disabled
# - Security gate should still work
# - Collect real-world metrics

# Week 3: Enable with small position sizing (5%)
# - Gradually increase to 10%, then 25%, then 50%

# Week 4: Full deployment (100% position sizing)
# - Security gate is fully operational
# - Continue monitoring


# ============================================================================
# IMPLEMENTATION CHECKLIST
# ============================================================================

IMPLEMENTATION_CHECKLIST = """
□ Import SecurityGateService in workers/main.py
□ Initialize security_gate_service at module level
□ Add security gate check to assess_risk_worker
□ Update RiskEngine to accept security_gate_score parameter
□ Update risk scoring formula with 40% security weight
□ Create database migration for security_audit_log table
□ Add configuration settings to core/config.py
□ Add Prometheus metrics
□ Write integration tests
□ Test with honeypot token (should block)
□ Test with legitimate token (should pass)
□ Deploy to staging
□ Run 48-72 hour paper trading validation
□ Collect metrics and adjust thresholds
□ Deploy to production (paper mode)
□ Gradually increase position sizing
□ Enable live trading
"""

print(IMPLEMENTATION_CHECKLIST)
