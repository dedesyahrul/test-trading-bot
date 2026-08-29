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
        
        # Transaction features
        buy_count_24h = current_snapshot.buy_count_24h or 0
        sell_count_24h = current_snapshot.sell_count_24h or 0
        buy_sell_ratio_1h = FeatureEngineering._compute_buy_sell_ratio(buy_count_24h, sell_count_24h)
        buy_pressure = FeatureEngineering._compute_buy_pressure(buy_count_24h, sell_count_24h)
        
        # Liquidity features
        liquidity_usd = float(current_snapshot.liquidity_usd or 0) if current_snapshot.liquidity_usd else None
        
        # Create feature record
        feature = Feature(
            pair_id=pair_id,
            timestamp=datetime.utcnow(),
            return_1m=Decimal(str(return_1m)) if return_1m is not None else None,
            return_5m=Decimal(str(return_5m)) if return_5m is not None else None,
            return_1h=Decimal(str(return_1h)) if return_1h is not None else None,
            volatility_1h=Decimal(str(volatility_1h)) if volatility_1h is not None else None,
            momentum_1h=Decimal(str(momentum_1h)) if momentum_1h is not None else None,
            volume_growth_1h=None,  # TODO: compute from historical
            volume_acceleration=None,  # TODO: compute from historical
            volume_spike=None,  # TODO: compute
            buy_sell_ratio_1h=Decimal(str(buy_sell_ratio_1h)) if buy_sell_ratio_1h is not None else None,
            buy_pressure=Decimal(str(buy_pressure)) if buy_pressure is not None else None,
            liquidity_change=None,  # TODO: compute from historical
            liquidity_ratio=None,  # TODO: compute
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
