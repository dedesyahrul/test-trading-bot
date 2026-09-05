"""Security Gate Integration for Worker Pipeline

Integrasi SecurityGateService ke dalam worker pipeline untuk 
memberikan pre-trade security filtering SEBELUM risk assessment.
"""

import logging
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.security.gate import SecurityGateService
from app.models import Pair, Token, Chain, MarketSnapshot, RiskAssessment
from app.services.risk.engine import RiskEngine
from app.core.database import async_session_maker
from app.adapters.solana_rpc import SolanaRPCClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize security gate service (singleton)
security_gate_service = SecurityGateService()


async def assess_risk_with_security_gate(
    session: AsyncSession,
    pair_id: str,
    market_snapshot: MarketSnapshot,
) -> tuple[bool, dict]:
    """
    Assess risk dengan security gate sebagai layer pertama (pre-trade filter).
    
    Returns:
        (is_blocked, result_dict)
        - is_blocked: True jika token di-BLOCK oleh security gate
        - result_dict: Dict berisi gate_result, risk_assessment, atau error info
    """
    try:
        # Get pair info
        pair = await session.get(Pair, pair_id)
        if not pair:
            logger.error(f"Pair {pair_id} not found")
            return True, {"error": "Pair not found"}
        
        logger.info(f"[SECURITY] Starting security gate evaluation for pair {pair_id}")
        
        # STEP 1: SECURITY GATE CHECK (Pre-trade filter)
        # This is the VETO layer - runs BEFORE any other processing
        token = await session.get(Token, pair.base_token_id)
        chain = await session.get(Chain, pair.chain_id)
        if not token or not chain:
            logger.error("Pair %s has incomplete token/chain references", pair_id)
            return True, {"error": "Pair token or chain not found"}

        developer_address = token.developer_address
        if not developer_address and pair.chain_id == "solana":
            # Populate the creator hint lazily; the registry decision itself
            # remains based only on confirmed local registry entries.
            developer_address = await SolanaRPCClient().get_token_creator(token.address)
            if developer_address:
                token.developer_address = developer_address
                await session.commit()

        liquidity_usd = market_snapshot.liquidity_usd if market_snapshot.liquidity_usd is not None else pair.liquidity_usd
        gate_result = await security_gate_service.evaluate_token(
            chain=pair.chain_id,
            token_address=token.address,
            pair_address=pair.pair_address,
            market_snapshot={
                'liquidity_usd': float(liquidity_usd) if liquidity_usd is not None else None,
                'buy_count_24h': market_snapshot.buy_count_24h or 0,
                'sell_count_24h': market_snapshot.sell_count_24h or 0,
                'volume_24h_usd': float(market_snapshot.volume_24h_usd or 0),
                'price_usd': float(market_snapshot.price_usd or 0),
                'trading_mode': settings.TRADING_MODE,
            },
            session=session,
            token_name=token.name,
            token_symbol=token.symbol,
            developer_address=developer_address,
        )
        
        # If security gate blocks the token, stop processing
        if gate_result.is_blocked or gate_result.is_deferred:
            logger.warning(
                "[SECURITY] %s by Security Gate for pair %s: %s",
                gate_result.status,
                pair_id,
                gate_result.reason,
            )
            
            if gate_result.is_blocked:
                try:
                    from app.models import SecurityAuditLog
                    audit_log = SecurityAuditLog(
                        pair_id=pair_id,
                        block_reason=gate_result.reason,
                        block_details=json.dumps({
                            key: value.__dict__ for key, value in gate_result.findings.items()
                        }, default=str),
                        security_score=gate_result.security_gate_score,
                        blocked_at=datetime.utcnow(),
                    )
                    session.add(audit_log)
                    await session.commit()
                except Exception as e:
                    logger.warning(f"Could not log to security audit: {e}")
            
            return True, {
                "blocked": gate_result.is_blocked,
                "deferred": gate_result.is_deferred,
                "block_reason": gate_result.reason,
                "security_score": gate_result.security_gate_score,
                "findings": gate_result.findings,
            }
        
        # Security gate PASSED - continue with risk assessment
        logger.info(
            f"[SECURITY] ✅ PASSED Security Gate for pair {pair_id} "
            f"(security score: {gate_result.security_gate_score}/100)"
        )
        
        # STEP 2: RISK ASSESSMENT (with security gate score)
        logger.debug(f"[RISK] Computing features and risk for pair {pair_id}")
        
        risk_assessment = await RiskEngine.assess_risk(
            session=session,
            pair_id=pair_id,
            market_snapshot=market_snapshot,
            security_gate_score=gate_result.security_gate_score,  # NEW!
        )
        
        logger.info(
            f"[RISK] Risk assessment completed for pair {pair_id}: "
            f"score={risk_assessment.risk_score}, level={risk_assessment.risk_level}"
        )
        
        return False, {
            "blocked": False,
            "security_gate_score": gate_result.security_gate_score,
            "risk_assessment": risk_assessment,
            "security_findings": gate_result.findings,
        }
        
    except Exception as e:
        logger.error(f"[SECURITY] Error in security gate assessment for pair {pair_id}: {e}", exc_info=True)
        return True, {"error": str(e), "type": "EXCEPTION"}


async def security_gate_summary(session: AsyncSession) -> dict:
    """
    Get summary of security gate decisions (untuk monitoring/debugging).
    
    Returns dict dengan statistics tentang blocks, passes, dll.
    """
    try:
        from app.models import SecurityAuditLog
        from sqlalchemy import func
        
        # Count blocks by reason (last 24 hours)
        result = await session.execute(
            select(
                SecurityAuditLog.block_reason,
                func.count(SecurityAuditLog.id).label('count')
            )
            .where(SecurityAuditLog.blocked_at >= datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            ))
            .group_by(SecurityAuditLog.block_reason)
        )
        
        blocks_by_reason = dict(result.all())
        total_blocks = sum(blocks_by_reason.values())
        
        return {
            "total_blocks_today": total_blocks,
            "blocks_by_reason": blocks_by_reason,
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.warning(f"Could not generate security summary: {e}")
        return {"error": str(e)}
