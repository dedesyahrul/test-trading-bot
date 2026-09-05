"""Security gate service - main orchestrator for all security checks."""

import logging
from datetime import datetime
from typing import Optional, Dict

from app.services.security.models import SecurityGateResult
from app.services.security.liquidity_guard import LiquidityGuard
from app.services.security.honeypot_detector import HoneypotDetector
from app.services.security.contract_analyzer import ContractAnalyzer
from app.services.security.holder_distribution import HolderDistributionAnalyzer
from app.core.config import settings
from app.services.security.metadata_validator import MetadataValidator
from app.services.security.developer_registry import DeveloperRegistry
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SecurityGateService:
    """Main security gate orchestrator.
    
    Runs all security checks in sequence. Blocks immediately on hard constraints.
    Order of execution: Liquidity → Honeypot → Contract → Holders
    
    This is the VETO LAYER - security decisions override predictions.
    """
    
    def __init__(
        self,
        liquidity_guard: Optional[LiquidityGuard] = None,
        honeypot_detector: Optional[HoneypotDetector] = None,
        contract_analyzer: Optional[ContractAnalyzer] = None,
        holder_analyzer: Optional[HolderDistributionAnalyzer] = None,
        metadata_validator: Optional[MetadataValidator] = None,
        developer_registry: Optional[DeveloperRegistry] = None,
    ):
        """Initialize security gate service with all security modules.
        
        Args:
            liquidity_guard: Liquidity threshold checker
            honeypot_detector: Honeypot (buy-only) detector
            contract_analyzer: Contract bytecode analyzer
            holder_analyzer: Holder concentration analyzer
        """
        self.liquidity_guard = liquidity_guard or LiquidityGuard()
        self.honeypot_detector = honeypot_detector or HoneypotDetector()
        self.contract_analyzer = contract_analyzer or ContractAnalyzer()
        self.holder_analyzer = holder_analyzer or HolderDistributionAnalyzer()
        self.metadata_validator = metadata_validator or MetadataValidator()
        self.developer_registry = developer_registry or DeveloperRegistry()
    
    async def evaluate_token(
        self,
        chain: str,
        token_address: str,
        pair_address: str,
        market_snapshot: dict,
        session: Optional[AsyncSession] = None,
        token_name: Optional[str] = None,
        token_symbol: Optional[str] = None,
        developer_address: Optional[str] = None,
        position_size_usd: Optional[float] = None,
    ) -> SecurityGateResult:
        """
        Run all security checks in sequence.
        Return BLOCK immediately on hard constraints.
        
        Order: Liquidity → Honeypot → Contract → Holders
        
        Args:
            chain: "solana"
            token_address: Token mint address
            pair_address: DEX pair address
            market_snapshot: Market data from DEX Screener
                {
                    'liquidity_usd': float,
                    'buy_count_24h': int,
                    'sell_count_24h': int,
                    ...
                }
        
        Returns:
            SecurityGateResult with is_blocked flag and security_gate_score
        """
        if not settings.SECURITY_GATE_ENABLED:
            logger.warning("[SECURITY GATE] Disabled by configuration")
            if settings.TRADING_MODE.upper() == "LIVE":
                return SecurityGateResult(
                    is_blocked=True,
                    block_reason="Security gate cannot be disabled in LIVE trading mode",
                    security_gate_score=100,
                    reasons=["Unsafe configuration: security gate disabled for LIVE trading"],
                )
            return SecurityGateResult(
                is_blocked=False,
                security_gate_score=50,
                reasons=["Security gate disabled by configuration"],
                passed_at=datetime.utcnow().isoformat(),
            )

        # A missing pair address cannot be safely evaluated for execution.
        if not pair_address:
            return SecurityGateResult(
                is_blocked=True,
                block_reason="Pair address unavailable for security verification",
                security_gate_score=100,
                reasons=["Missing DEX pair address"],
            )

        findings = {}
        scores = {}
        reasons = []
        
        logger.info(f"[SECURITY GATE] Evaluating token {token_address} on {chain}")
        
        # LAYER 1: LIQUIDITY GUARD (fastest, hard constraint)
        logger.debug(f"[SECURITY GATE] Step 1/4: Liquidity check")
        liquidity_result = await self.liquidity_guard.check(market_snapshot)
        findings['liquidity'] = liquidity_result
        
        if liquidity_result.is_blocked:
            logger.error(f"[SECURITY GATE] ❌ BLOCKED by Liquidity Guard: {liquidity_result.block_reason}")
            return SecurityGateResult(
                is_blocked=True,
                block_reason=liquidity_result.block_reason,
                security_gate_score=100,
                findings=findings,
                reasons=[liquidity_result.block_reason],
            )
        if liquidity_result.is_unknown:
            return SecurityGateResult(
                is_blocked=False,
                is_deferred=True,
                security_gate_score=100,
                findings=findings,
                reasons=liquidity_result.reasons,
            )
        if position_size_usd is not None and liquidity_result.liquidity_usd:
            max_position = float(liquidity_result.liquidity_usd) * settings.SECURITY_MAX_POSITION_LIQUIDITY_PCT
            if position_size_usd > max_position:
                return SecurityGateResult(
                    is_blocked=True,
                    block_reason=(
                        f"Position ${position_size_usd:.2f} exceeds "
                        f"{settings.SECURITY_MAX_POSITION_LIQUIDITY_PCT:.1%} of liquidity "
                        f"(${max_position:.2f})"
                    ),
                    security_gate_score=100,
                    findings=findings,
                    reasons=["Position too large relative to pool liquidity"],
                )
        scores['liquidity'] = liquidity_result.risk_score
        logger.debug(f"[SECURITY GATE] ✅ Liquidity OK (score: {liquidity_result.risk_score})")
        
        # LAYER 2: HONEYPOT DETECTOR (hard constraint)
        logger.debug(f"[SECURITY GATE] Step 2/4: Honeypot check")
        honeypot_result = await self.honeypot_detector.check(market_snapshot)
        findings['honeypot'] = honeypot_result
        
        if honeypot_result.is_blocked:
            logger.error(f"[SECURITY GATE] ❌ BLOCKED by Honeypot Detector: {honeypot_result.block_reason}")
            return SecurityGateResult(
                is_blocked=True,
                block_reason=honeypot_result.block_reason,
                security_gate_score=95,
                findings=findings,
                reasons=[honeypot_result.block_reason],
            )
        scores['honeypot'] = honeypot_result.risk_score
        logger.debug(f"[SECURITY GATE] ✅ Honeypot OK (score: {honeypot_result.risk_score})")
        
        # LAYER 3: CONTRACT ANALYZER
        logger.debug(f"[SECURITY GATE] Step 3/4: Contract analysis")
        try:
            contract_result = await self.contract_analyzer.analyze(chain, token_address)
            findings['contract'] = contract_result
            
            if contract_result.is_blocked:
                logger.error(f"[SECURITY GATE] ❌ BLOCKED by Contract Analyzer: {contract_result.block_reason}")
                return SecurityGateResult(
                    is_blocked=True,
                    block_reason=contract_result.block_reason,
                    security_gate_score=90,
                    findings=findings,
                    reasons=[contract_result.block_reason],
                )
            if getattr(contract_result, "is_unknown", False):
                return SecurityGateResult(
                    is_blocked=False,
                    is_deferred=True,
                    security_gate_score=100,
                    findings=findings,
                    reasons=contract_result.reasons,
                )
            scores['contract'] = contract_result.risk_score
            logger.debug(f"[SECURITY GATE] ✅ Contract OK (score: {contract_result.risk_score})")
        except Exception as e:
            logger.warning(f"[SECURITY GATE] ⚠️  Contract analysis failed: {e}")
            return SecurityGateResult(
                is_blocked=False,
                is_deferred=True,
                security_gate_score=100,
                findings=findings,
                reasons=[f"Contract verification unavailable; trade deferred: {e}"],
            )
        
        # LAYER 4: HOLDER DISTRIBUTION ANALYZER
        logger.debug(f"[SECURITY GATE] Step 4/4: Holder concentration check")
        try:
            holder_result = await self.holder_analyzer.analyze(chain, token_address)
            findings['holders'] = holder_result
            
            if holder_result.is_blocked:
                logger.error(f"[SECURITY GATE] ❌ BLOCKED by Holder Analyzer: {holder_result.block_reason}")
                return SecurityGateResult(
                    is_blocked=True,
                    block_reason=holder_result.block_reason,
                    security_gate_score=85,
                findings=findings,
                    reasons=[holder_result.block_reason],
                )
            if getattr(holder_result, "is_unknown", False):
                return SecurityGateResult(
                    is_blocked=False,
                    is_deferred=True,
                    security_gate_score=100,
                    findings=findings,
                    reasons=holder_result.reasons,
                )
            scores['holders'] = holder_result.risk_score
            logger.debug(f"[SECURITY GATE] ✅ Holders OK (score: {holder_result.risk_score})")
        except Exception as e:
            logger.warning(f"[SECURITY GATE] ⚠️  Holder analysis failed: {e}")
            return SecurityGateResult(
                is_blocked=False,
                is_deferred=True,
                security_gate_score=100,
                findings=findings,
                reasons=[f"Holder verification unavailable; trade deferred: {e}"],
            )

        # LAYER 5: metadata spoofing checks when token metadata is available.
        if token_symbol is not None or token_name is not None:
            metadata_result = await self.metadata_validator.validate(
                token_name, token_symbol, token_address
            )
            findings['metadata'] = metadata_result
            if metadata_result.is_blocked:
                return SecurityGateResult(
                    is_blocked=True,
                    block_reason=metadata_result.block_reason,
                    security_gate_score=100,
                    findings=findings,
                    reasons=[metadata_result.block_reason],
                )
            scores['metadata'] = metadata_result.risk_score

        # LAYER 6: local developer scam registry. A registry hit is a veto.
        if session is not None:
            developer_result = await self.developer_registry.check(session, developer_address)
            findings['developer'] = developer_result
            if developer_result.is_blocked:
                return SecurityGateResult(
                    is_blocked=True,
                    block_reason=developer_result.block_reason,
                    security_gate_score=100,
                    findings=findings,
                    reasons=[developer_result.block_reason],
                )
            scores['developer'] = developer_result.risk_score
        
        # ALL CHECKS PASSED: Calculate weighted security gate score
        security_gate_score = (
            scores.get('liquidity', 30) * 0.25 +
            scores.get('honeypot', 30) * 0.25 +
            scores.get('contract', 30) * 0.25 +
            scores.get('holders', 25) * 0.20 +
            scores.get('metadata', 0) * 0.05 +
            scores.get('developer', 0) * 0.05
        )
        
        # Collect all reasons
        for key, result in findings.items():
            if hasattr(result, 'reasons') and result.reasons:
                reasons.extend(result.reasons)
        
        logger.info(
            f"[SECURITY GATE] ✅ PASSED token {token_address} "
            f"with security score {int(security_gate_score)}/100"
        )
        
        return SecurityGateResult(
            is_blocked=False,
            block_reason=None,
            security_gate_score=int(security_gate_score),
            findings=findings,
            reasons=reasons,
            passed_at=datetime.utcnow().isoformat(),
        )
