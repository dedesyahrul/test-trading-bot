"""Phase 1B Integration Guide - SecurityGateService Integration

Panduan lengkap untuk mengintegrasikan SecurityGateService ke dalam 
worker pipeline memeX.
"""

# ============================================================================
# STEP 1: ADD IMPORTS TO workers/main.py
# ============================================================================

# Add these imports at the top of backend/app/workers/main.py:
"""
from app.services.security.gate import SecurityGateService
from app.workers.security_integration import assess_risk_with_security_gate
"""

# Initialize security gate service (module level):
"""
security_gate_service = SecurityGateService()
"""


# ============================================================================
# STEP 2: UPDATE assess_risk_worker FUNCTION
# ============================================================================

# Replace the current assess_risk_worker function with:

"""
async def assess_risk_worker(ctx, pair_id):
    \"\"\"Worker to assess token risk with SECURITY GATE first.\"\"\"
    logger.info(f"[ASSESS_RISK] Starting risk assessment for pair {pair_id}")
    
    async with async_session_maker() as session:
        try:
            # Get latest market snapshot
            latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
            if not latest_snapshot:
                logger.warning(f"No market data for pair {pair_id}")
                return
            
            # SECURITY GATE CHECK (NEW - Pre-trade filter)
            is_blocked, result = await assess_risk_with_security_gate(
                session=session,
                pair_id=pair_id,
                market_snapshot=latest_snapshot,
            )
            
            # If blocked by security gate, stop processing
            if is_blocked:
                logger.error(
                    f"[ASSESS_RISK] Token {pair_id} blocked by security gate: "
                    f"{result.get('block_reason', 'Unknown reason')}"
                )
                return  # Stop processing, don't generate signals
            
            # If passed security gate, use the risk assessment returned
            risk_assessment = result.get('risk_assessment')
            if risk_assessment:
                logger.info(
                    f"[ASSESS_RISK] Risk assessment completed for pair {pair_id}: "
                    f"level={risk_assessment.risk_level}, score={risk_assessment.risk_score}"
                )
                # Risk assessment already saved to DB by assess_risk_with_security_gate
            
        except Exception as e:
            logger.error(f"[ASSESS_RISK] Error assessing risk for pair {pair_id}: {e}", exc_info=True)
"""


# ============================================================================
# STEP 3: UPDATE _run_intelligence_pipeline FUNCTION
# ============================================================================

# In the _run_intelligence_pipeline function, update the risk assessment section:

# OLD CODE:
"""
logger.warning("Features ready for pair %s; assessing risk", pair_id)
risk_assessment = await RiskEngine.assess_risk(
    session, pair_id, latest_snapshot, feature=computed_feature
)
logger.warning("Risk ready for pair %s: score=%s", pair_id, risk_assessment.risk_score)
"""

# NEW CODE:
"""
logger.warning("Features ready for pair %s; assessing risk", pair_id)

# Call security gate check first
is_blocked, gate_result = await assess_risk_with_security_gate(
    session=session,
    pair_id=pair_id,
    market_snapshot=latest_snapshot,
)

# If security gate blocks, skip signal generation
if is_blocked:
    logger.error(f"[PIPELINE] Token {pair_id} blocked by security gate")
    session.add(TradeDecision(
        pair_id=pair_id,
        strategy_id="security_gate",
        decision="REJECT",
        reasons=[gate_result.get('block_reason', 'Security gate violation')],
    ))
    await session.commit()
    return

# Security gate passed - get risk assessment
risk_assessment = gate_result.get('risk_assessment')
logger.warning("Risk ready for pair %s: score=%s", pair_id, risk_assessment.risk_score)
"""


# ============================================================================
# STEP 4: DATABASE MIGRATION (OPTIONAL)
# ============================================================================

# Create file: backend/alembic/versions/004_security_audit_log.py

"""
\"\"\"Add security audit log table.

Revision ID: 004
Revises: 003
Create Date: 2026-09-03 16:17:44.000000
\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'security_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('block_reason', sa.String(), nullable=True),
        sa.Column('block_details', sa.String(), nullable=True),
        sa.Column('security_score', sa.Integer(), nullable=True),
        sa.Column('blocked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('auto_unblock_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pair_id'], ['pairs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_security_audit_blocked_at', 'security_audit_log', ['blocked_at'], unique=False)
    op.create_index('idx_security_audit_pair_id', 'security_audit_log', ['pair_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_security_audit_pair_id', table_name='security_audit_log')
    op.drop_index('idx_security_audit_blocked_at', table_name='security_audit_log')
    op.drop_table('security_audit_log')
"""


# ============================================================================
# STEP 5: ADD SecurityAuditLog MODEL (IF NOT EXISTS)
# ============================================================================

# Add to backend/app/models/__init__.py or backend/app/models.py:

"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

class SecurityAuditLog(Base):
    __tablename__ = 'security_audit_log'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey('pairs.id'), nullable=True)
    block_reason = Column(String, nullable=True)
    block_details = Column(String, nullable=True)
    security_score = Column(Integer, nullable=True)
    blocked_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    auto_unblock_at = Column(DateTime(timezone=True), nullable=True)
    
    pair = relationship('Pair', back_populates='security_audit_logs')
"""


# ============================================================================
# STEP 6: UPDATE PAIR MODEL
# ============================================================================

# Add relationship to Pair model:

"""
security_audit_logs = relationship(
    'SecurityAuditLog',
    back_populates='pair',
    cascade='all, delete-orphan'
)
"""


# ============================================================================
# TESTING THE INTEGRATION
# ============================================================================

# Run unit tests:
"""
pytest backend/tests/security/test_security_gate.py -v
"""

# Run integration tests with mock data:
"""
pytest backend/tests/test_security_integration.py -v
"""

# Test with specific pair:
"""
# In a Python script or test:
from app.workers.security_integration import assess_risk_with_security_gate
from app.core.database import async_session_maker

async def test_integration():
    async with async_session_maker() as session:
        # Test with a real pair_id from your database
        is_blocked, result = await assess_risk_with_security_gate(
            session=session,
            pair_id="pair-id-here",
            market_snapshot=snapshot,
        )
        print(f"Blocked: {is_blocked}")
        print(f"Result: {result}")
"""


# ============================================================================
# DEPLOYMENT CHECKLIST FOR PHASE 1B
# ============================================================================

"""
□ 1. Add imports to workers/main.py
□ 2. Initialize security_gate_service in workers/main.py
□ 3. Update assess_risk_worker function
□ 4. Update _run_intelligence_pipeline function
□ 5. Create database migration for security_audit_log table
□ 6. Add SecurityAuditLog model to models
□ 7. Update Pair model with relationship
□ 8. Run unit tests
□ 9. Run integration tests
□ 10. Deploy to staging environment
□ 11. Monitor security decisions in staging
□ 12. Verify no false positives in staging
□ 13. Proceed to Phase 1C (paper trading validation)
"""
