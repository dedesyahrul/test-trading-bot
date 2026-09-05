import logging
from decimal import Decimal
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import RiskAssessment, MarketSnapshot, Feature
import math

logger = logging.getLogger(__name__)


class RiskEngine:
    """Calculate risk scores for tokens."""

    # Risk thresholds
    LIQUIDITY_THRESHOLD_CRITICAL = 1000  # USD
    LIQUIDITY_THRESHOLD_HIGH = 5000
    LIQUIDITY_THRESHOLD_MEDIUM = 50000
    LIQUIDITY_THRESHOLD_LOW = 100000

    # Risk levels
    RISK_LEVELS = {
        (0, 30): "LOW",
        (31, 60): "MEDIUM",
        (61, 85): "HIGH",
        (86, 100): "CRITICAL",
    }

    @staticmethod
    async def assess_risk(
        session: AsyncSession,
        pair_id,
        market_snapshot: MarketSnapshot,
        feature: Optional[Feature] = None,
        security_gate_score: int = 0,  # Security gate score (0-100)
    ) -> RiskAssessment:
        """Assess token risk and return RiskAssessment with security-first weighting.

        Args:
            session: Database session
            pair_id: Pair ID to assess
            market_snapshot: Market data snapshot
            security_gate_score: Security gate score (0-100) from SecurityGateService (NEW)
            feature: Computed features (optional)
        """

        # Initialize risk scores for each category
        liquidity_risk = RiskEngine._calculate_liquidity_risk(market_snapshot)
        manipulation_risk = RiskEngine._calculate_manipulation_risk(market_snapshot)
        volatility_risk = RiskEngine._calculate_volatility_risk(feature)
        execution_risk = RiskEngine._calculate_execution_risk(market_snapshot)

        # Check hard constraints first
        is_blacklisted, constraint_reason = RiskEngine._check_hard_constraints(market_snapshot)

        # NEW: Weighted formula with SECURITY FIRST (40% security gate)
        # This ensures security decisions override other factors
        overall_risk_score = (
            security_gate_score * 0.40 +     # SECURITY FIRST (40%)
            liquidity_risk * 0.20 +
            manipulation_risk * 0.15 +
            volatility_risk * 0.12 +
            execution_risk * 0.08
            # metadata_risk * 0.05  # Future enhancement
        )

        # Determine risk level
        risk_level = "UNKNOWN"
        for (min_score, max_score), level in RiskEngine.RISK_LEVELS.items():
            if min_score <= overall_risk_score <= max_score:
                risk_level = level
                break

        # Build reasons
        reasons = []
        if liquidity_risk > 50:
            reasons.append(f"Low liquidity risk (score: {liquidity_risk:.0f})")
        if manipulation_risk > 50:
            reasons.append(f"High manipulation risk (score: {manipulation_risk:.0f})")
        if volatility_risk > 50:
            reasons.append(f"High volatility risk (score: {volatility_risk:.0f})")
        if is_blacklisted:
            reasons.append(f"Hard constraint violation: {constraint_reason}")

        # Create assessment
        assessment = RiskAssessment(
            pair_id=pair_id,
            risk_score=Decimal(str(round(overall_risk_score, 2))),
            risk_level=risk_level,
            liquidity_risk=Decimal(str(round(liquidity_risk, 2))),
            manipulation_risk=Decimal(str(round(manipulation_risk, 2))),
            volatility_risk=Decimal(str(round(volatility_risk, 2))),
            execution_risk=Decimal(str(round(execution_risk, 2))),
            reasons=reasons,
            timestamp=datetime.utcnow(),
        )

        session.add(assessment)
        await session.commit()
        await session.refresh(assessment)
        logger.info(f"Risk assessment completed for pair {pair_id}: score={overall_risk_score:.0f}")
        return assessment

    @staticmethod
    def _calculate_liquidity_risk(snapshot: MarketSnapshot) -> float:
        """Calculate liquidity risk (0-100)."""
        if not snapshot.liquidity_usd:
            return 100  # Unknown liquidity = high risk

        liquidity_usd = float(snapshot.liquidity_usd)

        if liquidity_usd < RiskEngine.LIQUIDITY_THRESHOLD_CRITICAL:
            return 100
        elif liquidity_usd < RiskEngine.LIQUIDITY_THRESHOLD_HIGH:
            return 80
        elif liquidity_usd < RiskEngine.LIQUIDITY_THRESHOLD_MEDIUM:
            return 50
        elif liquidity_usd < RiskEngine.LIQUIDITY_THRESHOLD_LOW:
            return 20
        else:
            return 0

    @staticmethod
    def _calculate_manipulation_risk(snapshot: MarketSnapshot) -> float:
        """Calculate manipulation risk based on buy/sell ratio and transaction patterns."""
        if not snapshot.buy_count_24h or not snapshot.sell_count_24h:
            return 50  # Unknown = medium risk

        buy_count = snapshot.buy_count_24h
        sell_count = snapshot.sell_count_24h

        # Extreme buy/sell ratio indicates potential wash trading
        if sell_count == 0:
            return 90 if buy_count > 50 else 50
        
        ratio = buy_count / sell_count
        
        if ratio > 10:  # 10:1 or worse
            return 90
        elif ratio > 5:  # 5:1
            return 70
        elif ratio > 2:  # 2:1
            return 40
        elif ratio > 0.5 and ratio < 2:  # Balanced
            return 10
        else:
            return 50  # Abnormal (more sells than buys)

    @staticmethod
    def _calculate_volatility_risk(feature) -> float:
        """Calculate volatility risk."""
        if not feature:
            return 50

        volatility = feature.get("volatility_1h") if isinstance(feature, dict) else getattr(feature, "volatility_1h", None)
        if not volatility:
            return 30

        volatility = float(volatility)
        
        if volatility > 2.0:  # 200% std dev
            return 90
        elif volatility > 1.0:  # 100%
            return 70
        elif volatility > 0.5:  # 50%
            return 40
        else:
            return 10

    @staticmethod
    def _calculate_execution_risk(snapshot: MarketSnapshot) -> float:
        """Calculate execution risk (slippage, available liquidity for entry/exit)."""
        # Simple heuristic: volume to liquidity ratio
        if not snapshot.volume_24h_usd or not snapshot.liquidity_usd:
            return 50

        volume_24h = float(snapshot.volume_24h_usd)
        liquidity = float(snapshot.liquidity_usd)

        if liquidity == 0:
            return 100

        volume_to_liquidity = volume_24h / liquidity

        if volume_to_liquidity > 100:  # High turnover
            return 80
        elif volume_to_liquidity > 10:
            return 50
        elif volume_to_liquidity > 1:
            return 20
        else:
            return 10

    @staticmethod
    def _check_hard_constraints(snapshot: MarketSnapshot) -> tuple[bool, str]:
        """Check hard kill-switch constraints."""
        
        # Zero liquidity
        if not snapshot.liquidity_usd or float(snapshot.liquidity_usd) < 1000:
            return True, "Liquidity below $1,000"
        
        # Honey pot detection (only buys, no sells)
        if snapshot.buy_count_24h and snapshot.sell_count_24h == 0 and snapshot.buy_count_24h > 50:
            return True, "Potential honey pot (sells = 0, buys > 50)"
        
        # Dead coin (very low volume after 3 days)
        if snapshot.volume_24h_usd and float(snapshot.volume_24h_usd) < 500:
            # Would need to check pair age in production
            return False, ""
        
        return False, ""
