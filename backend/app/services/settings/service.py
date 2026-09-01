"""Settings service for strategy and risk configuration."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BotState, Strategy

DEFAULT_RISK_CONFIG = {
    "max_position_size_usd": 1000,
    "max_daily_loss_usd": 500,
    "max_positions": 5,
    "min_liquidity_usd": 5000,
    "max_risk_score": 50,
    "max_risk_per_trade_pct": 0.01,
    "max_portfolio_exposure_usd": 5000,
    "max_pair_exposure_usd": 1500,
    "loss_cooldown_minutes": 30,
    "paper_initial_balance": 100,
}

DEFAULT_STRATEGIES = [
    {
        "strategy_key": "momentum_v1",
        "name": "Momentum Strategy",
        "strategy_type": "momentum",
        "parameters": {
            "min_volume_24h": 50000,
            "min_price_change_5m": 0.05,
            "min_volume_spike": 2.0,
            "min_buy_sell_ratio": 1.2,
            "max_risk_score": 50,
            "take_profit_pct": 0.20,
            "stop_loss_pct": 0.10,
        },
        "is_active": True,
        "description": "Pure breakout detection",
    },
    {
        "strategy_key": "ml_sniper_v1",
        "name": "ML-Assisted Sniper",
        "strategy_type": "ml_assisted",
        "parameters": {
            "min_volume_24h": 50000,
            "max_risk_score": 40,
            "take_profit_pct": 0.15,
            "stop_loss_pct": 0.10,
        },
        "is_active": True,
        "description": "ML-ready placeholder for future integration",
    },
]


class SettingsService:
    @staticmethod
    async def get_or_create_bot_state(session: AsyncSession) -> BotState:
        bot_state = await session.get(BotState, 1)
        if not bot_state:
            bot_state = BotState(id=1, risk_config=DEFAULT_RISK_CONFIG.copy())
            session.add(bot_state)
            await session.commit()
            await session.refresh(bot_state)
        elif not bot_state.risk_config:
            bot_state.risk_config = DEFAULT_RISK_CONFIG.copy()
            await session.commit()
            await session.refresh(bot_state)
        return bot_state

    @staticmethod
    async def seed_default_strategies(session: AsyncSession) -> None:
        result = await session.execute(select(Strategy))
        if result.scalars().first():
            return
        for data in DEFAULT_STRATEGIES:
            session.add(Strategy(**data))
        await session.commit()

    @staticmethod
    async def get_all_strategies(session: AsyncSession) -> list[Strategy]:
        await SettingsService.seed_default_strategies(session)
        result = await session.execute(select(Strategy).order_by(Strategy.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_strategy_by_key(session: AsyncSession, strategy_key: str) -> Optional[Strategy]:
        result = await session.execute(
            select(Strategy).where(Strategy.strategy_key == strategy_key)
        )
        return result.scalars().first()

    @staticmethod
    async def update_strategy(
        session: AsyncSession,
        strategy_key: str,
        enabled: bool,
        parameters: dict,
    ) -> Strategy:
        strategy = await SettingsService.get_strategy_by_key(session, strategy_key)
        if not strategy:
            raise ValueError(f"Strategy {strategy_key} not found")
        strategy.is_active = enabled
        strategy.parameters = parameters
        await session.commit()
        await session.refresh(strategy)
        return strategy

    @staticmethod
    async def get_risk_config(session: AsyncSession) -> dict:
        bot_state = await SettingsService.get_or_create_bot_state(session)
        return bot_state.risk_config or DEFAULT_RISK_CONFIG.copy()

    @staticmethod
    async def update_risk_config(session: AsyncSession, config: dict) -> dict:
        bot_state = await SettingsService.get_or_create_bot_state(session)
        bot_state.risk_config = config
        await session.commit()
        await session.refresh(bot_state)
        return bot_state.risk_config
