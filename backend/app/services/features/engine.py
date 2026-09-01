import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import MarketSnapshot, Feature
import math

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """Compute ML features from market snapshots."""

    @staticmethod
    async def compute_features(
        session: AsyncSession,
        pair_id,
        current_snapshot: MarketSnapshot,
    ) -> Feature:
        """Compute all features for a pair given current snapshot."""
        
        # Get historical snapshots for comparison
        one_min_ago = datetime.utcnow() - timedelta(minutes=1)
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        result_1m = await session.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.pair_id == pair_id)
            .where(MarketSnapshot.timestamp >= one_min_ago)
            .order_by(MarketSnapshot.timestamp.asc())
        )
        snapshots_1m = result_1m.scalars().all()
        
        result_1h = await session.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.pair_id == pair_id)
            .where(MarketSnapshot.timestamp >= one_hour_ago)
            .order_by(MarketSnapshot.timestamp.asc())
        )
        snapshots_1h = result_1h.scalars().all()
        
        # Price features
        return_1m = FeatureEngineering._compute_return(snapshots_1m, current_snapshot)
        return_5m = float(current_snapshot.price_change_5m or 0) / 100 if current_snapshot.price_change_5m else None
        return_1h = float(current_snapshot.price_change_1h or 0) / 100 if current_snapshot.price_change_1h else None
        
        volatility_1h = FeatureEngineering._compute_volatility(snapshots_1h)
        momentum_1h = FeatureEngineering._compute_momentum(snapshots_1h)
        
        # Volume features
        volume_1h_usd = float(current_snapshot.volume_1h_usd or 0) if current_snapshot.volume_1h_usd else None
        volume_24h_usd = float(current_snapshot.volume_24h_usd or 0) if current_snapshot.volume_24h_usd else None
        liquidity_usd = float(current_snapshot.liquidity_usd or 0) if current_snapshot.liquidity_usd else None

        volume_growth_1h = None
        volume_acceleration = None
        volume_spike = None
        if snapshots_1h and len(snapshots_1h) >= 2:
            first_vol = float(snapshots_1h[0].volume_1h_usd or snapshots_1h[0].volume_24h_usd or 0)
            last_vol = float(snapshots_1h[-1].volume_1h_usd or snapshots_1h[-1].volume_24h_usd or 0)
            if first_vol > 0:
                volume_growth_1h = (last_vol - first_vol) / first_vol
            if len(snapshots_1h) >= 3:
                mid = len(snapshots_1h) // 2
                early_avg = sum(
                    float(s.volume_1h_usd or s.volume_24h_usd or 0) for s in snapshots_1h[:mid]
                ) / mid
                late_avg = sum(
                    float(s.volume_1h_usd or s.volume_24h_usd or 0) for s in snapshots_1h[mid:]
                ) / (len(snapshots_1h) - mid)
                if early_avg > 0:
                    volume_acceleration = (late_avg - early_avg) / early_avg
            avg_vol = sum(
                float(s.volume_1h_usd or s.volume_24h_usd or 0) for s in snapshots_1h[:-1]
            ) / max(len(snapshots_1h) - 1, 1)
            current_vol = float(current_snapshot.volume_1h_usd or current_snapshot.volume_24h_usd or 0)
            if avg_vol > 0:
                volume_spike = current_vol / avg_vol

        liquidity_change = None
        liquidity_ratio = None
        if snapshots_1h and liquidity_usd is not None:
            first_liq = float(snapshots_1h[0].liquidity_usd or 0)
            if first_liq > 0:
                liquidity_change = (liquidity_usd - first_liq) / first_liq
            if volume_24h_usd and volume_24h_usd > 0:
                liquidity_ratio = liquidity_usd / volume_24h_usd
        
        # Transaction features
        buy_count_24h = current_snapshot.buy_count_24h or 0
        sell_count_24h = current_snapshot.sell_count_24h or 0
        buy_sell_ratio_1h = FeatureEngineering._compute_buy_sell_ratio(buy_count_24h, sell_count_24h)
        buy_pressure = FeatureEngineering._compute_buy_pressure(buy_count_24h, sell_count_24h)
        
        # Create feature record
        feature = Feature(
            pair_id=pair_id,
            timestamp=datetime.utcnow(),
            return_1m=Decimal(str(return_1m)) if return_1m is not None else None,
            return_5m=Decimal(str(return_5m)) if return_5m is not None else None,
            return_1h=Decimal(str(return_1h)) if return_1h is not None else None,
            volatility_1h=Decimal(str(volatility_1h)) if volatility_1h is not None else None,
            momentum_1h=Decimal(str(momentum_1h)) if momentum_1h is not None else None,
            volume_growth_1h=Decimal(str(volume_growth_1h)) if volume_growth_1h is not None else None,
            volume_acceleration=Decimal(str(volume_acceleration)) if volume_acceleration is not None else None,
            volume_spike=Decimal(str(volume_spike)) if volume_spike is not None else None,
            buy_sell_ratio_1h=Decimal(str(buy_sell_ratio_1h)) if buy_sell_ratio_1h is not None else None,
            buy_pressure=Decimal(str(buy_pressure)) if buy_pressure is not None else None,
            liquidity_change=Decimal(str(liquidity_change)) if liquidity_change is not None else None,
            liquidity_ratio=Decimal(str(liquidity_ratio)) if liquidity_ratio is not None else None,
            raw_data={
                "snapshots_count_1h": len(snapshots_1h),
                "buy_count_24h": buy_count_24h,
                "sell_count_24h": sell_count_24h,
            },
        )
        
        session.add(feature)
        await session.commit()
        await session.refresh(feature)
        logger.info(f"Features computed for pair {pair_id}")
        return feature

    @staticmethod
    def _compute_return(snapshots: list[MarketSnapshot], current: MarketSnapshot) -> Optional[float]:
        """Compute returns between two snapshots."""
        if not snapshots or len(snapshots) < 1:
            return None
        
        first_snapshot = snapshots[0]
        if first_snapshot.price_usd == 0 or first_snapshot.price_usd is None:
            return None
        
        return float((current.price_usd - first_snapshot.price_usd) / first_snapshot.price_usd)

    @staticmethod
    def _compute_volatility(snapshots: list[MarketSnapshot]) -> Optional[float]:
        """Compute volatility as standard deviation of returns."""
        if len(snapshots) < 2:
            return None
        
        returns = []
        for i in range(1, len(snapshots)):
            prev_price = float(snapshots[i-1].price_usd or 0)
            curr_price = float(snapshots[i].price_usd or 0)
            if prev_price > 0:
                ret = (curr_price - prev_price) / prev_price
                returns.append(ret)
        
        if len(returns) < 2:
            return None
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance)

    @staticmethod
    def _compute_momentum(snapshots: list[MarketSnapshot]) -> Optional[float]:
        """Compute momentum as rate of change."""
        if len(snapshots) < 2:
            return None
        
        first_price = float(snapshots[0].price_usd or 0)
        last_price = float(snapshots[-1].price_usd or 0)
        
        if first_price == 0:
            return None
        
        return (last_price - first_price) / first_price

    @staticmethod
    def _compute_buy_sell_ratio(buys: int, sells: int) -> Optional[float]:
        """Compute buy/sell ratio."""
        if sells == 0:
            return float(buys) if buys > 0 else None
        return float(buys) / float(sells)

    @staticmethod
    def _compute_buy_pressure(buys: int, sells: int) -> Optional[float]:
        """Compute buy pressure (% of total transactions that are buys)."""
        total = buys + sells
        if total == 0:
            return None
        return float(buys) / float(total)
