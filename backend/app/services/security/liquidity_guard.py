"""Liquidity guard for detecting insufficient liquidity."""

import logging
from decimal import Decimal
from app.services.security.models import LiquidityCheckResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class LiquidityGuard:
    """Enhanced liquidity threshold checks.
    
    Prevents trading tokens with insufficient liquidity that would result
    in high slippage and difficulty exiting positions.
    """
    
    # Thresholds (USD)
    CRITICAL_THRESHOLD = Decimal(str(settings.SECURITY_LIQUIDITY_THRESHOLD_USD))
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
        raw_liquidity = market_snapshot.get("liquidity_usd")
        if raw_liquidity is None or raw_liquidity == "":
            logger.warning("Liquidity check DEFERRED: market data unavailable")
            return LiquidityCheckResult(
                is_blocked=False,
                risk_score=100,
                threshold_met=False,
                is_unknown=True,
                block_reason=None,
                reasons=["Liquidity data unavailable; trade deferred"],
            )
        try:
            liquidity_usd = Decimal(str(raw_liquidity))
        except (ValueError, TypeError):
            logger.warning("Liquidity check DEFERRED: invalid market data %r", raw_liquidity)
            return LiquidityCheckResult(
                is_blocked=False,
                risk_score=100,
                threshold_met=False,
                is_unknown=True,
                reasons=["Liquidity data invalid; trade deferred"],
            )
        
        mode = str(market_snapshot.get("trading_mode") or settings.TRADING_MODE).upper()
        if mode == "LIVE":
            minimum_liquidity = Decimal(str(settings.SECURITY_LIVE_MIN_LIQUIDITY_USD))
        elif mode == "PAPER":
            minimum_liquidity = Decimal(str(settings.SECURITY_PAPER_MIN_LIQUIDITY_USD))
        else:
            minimum_liquidity = self.CRITICAL_THRESHOLD

        # Hard constraint for the active execution mode.
        if liquidity_usd < minimum_liquidity:
            severity = "critical" if liquidity_usd < self.CRITICAL_THRESHOLD else "below-mode-minimum"
            logger.warning(
                "Liquidity check FAILED: $%.2f < $%.2f (%s mode)",
                float(liquidity_usd), float(minimum_liquidity), mode,
            )
            return LiquidityCheckResult(
                is_blocked=True,
                block_reason=(
                    f"Liquidity ${float(liquidity_usd):.2f} below minimum "
                    f"${float(minimum_liquidity):.2f} for {mode} trading ({severity})"
                ),
                risk_score=100,
                liquidity_usd=liquidity_usd,
                threshold_met=False,
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
        
        logger.info(f"Liquidity check PASSED: ${float(liquidity_usd):.2f} → {tier} (score: {risk_score})")
        
        return LiquidityCheckResult(
            is_blocked=False,
            risk_score=risk_score,
            liquidity_usd=liquidity_usd,
            threshold_met=True,
            reasons=[f"Liquidity: ${float(liquidity_usd):.2f} ({tier})"],
                details={
                    'tier': tier,
                    'liquidity_usd': float(liquidity_usd),
                    'minimum_liquidity_usd': float(minimum_liquidity),
                    'trading_mode': mode,
                }
        )
