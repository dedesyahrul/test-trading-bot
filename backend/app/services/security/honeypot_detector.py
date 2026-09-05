"""Honeypot detector for identifying buy-only trap tokens."""

import logging
from app.services.security.models import HoneypotCheckResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class HoneypotDetector:
    """Enhanced honeypot detection (buy-only trap).
    
    Detects tokens where traders can buy but cannot sell, trapping
    their funds. Identifies this by analyzing buy/sell ratios.
    """
    
    # Hard constraint: buys > threshold AND sells = 0
    BUY_THRESHOLD = settings.SECURITY_HONEYPOT_BUY_THRESHOLD
    
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
                reason = "No trading activity (new token)"
            else:
                # Infinite ratio (buys but no sells) = HONEYPOT
                ratio = float('inf')
                risk_score = 90
                reason = f"HONEYPOT: {buy_count} buys but 0 sells"
        else:
            ratio = buy_count / sell_count
            
            if ratio >= 10:
                risk_score = 90
                reason = f"Extreme buy/sell ratio: {ratio:.1f}x ({buy_count} buys vs {sell_count} sells)"
            elif ratio > 5:
                risk_score = 70
                reason = f"High buy/sell ratio: {ratio:.1f}x ({buy_count} buys vs {sell_count} sells)"
            elif ratio > 2:
                risk_score = 40
                reason = f"Elevated buy/sell ratio: {ratio:.1f}x ({buy_count} buys vs {sell_count} sells)"
            elif 0.5 <= ratio <= 2:
                risk_score = 10
                reason = f"Balanced buy/sell ratio: {ratio:.2f}x ({buy_count} buys vs {sell_count} sells)"
            else:
                risk_score = 50  # More sells than buys (unusual)
                reason = f"More sells than buys: {ratio:.2f}x ({buy_count} buys vs {sell_count} sells)"
        
        # Hard constraint: buys > 50 AND sells = 0
        is_honeypot = sell_count == 0 and buy_count > self.BUY_THRESHOLD
        
        if is_honeypot:
            logger.error(f"HONEYPOT DETECTED: {buy_count} buys, {sell_count} sells - BLOCKING")
        else:
            logger.info(f"Honeypot check: {reason} (risk: {risk_score})")
        
        return HoneypotCheckResult(
            is_blocked=is_honeypot,
            block_reason=reason if is_honeypot else None,
            risk_score=risk_score,
            buy_count=buy_count,
            sell_count=sell_count,
            buy_sell_ratio=ratio if ratio != float('inf') else 999,
            reasons=[reason],
            details={
                'buy_count': buy_count,
                'sell_count': sell_count,
                'ratio': ratio if ratio != float('inf') else 'inf',
                'is_honeypot': is_honeypot,
            }
        )
