from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db_session
from app.core.security import verify_token
from app.models import BotState
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"], prefix="/settings")


class StrategyConfig(BaseModel):
    """Strategy configuration."""
    strategy_id: str
    enabled: bool
    parameters: dict


class RiskConfig(BaseModel):
    """Risk management configuration."""
    max_position_size_usd: float
    max_daily_loss_usd: float
    max_positions: int
    min_liquidity_usd: float
    max_risk_score: int


class TradingConfig(BaseModel):
    """Trading configuration."""
    trading_mode: str  # PAPER or LIVE
    risk_config: RiskConfig
    strategies: list[StrategyConfig]


@router.get("/trading")
async def get_trading_settings(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get current trading settings."""
    bot_state = await session.get(BotState, 1)
    if not bot_state:
        raise HTTPException(status_code=404, detail="Bot state not found")
    
    return {
        "trading_mode": bot_state.trading_mode,
        "bot_state": bot_state.state,
        "last_update": bot_state.last_update.isoformat(),
    }


@router.put("/trading")
async def update_trading_settings(
    config: TradingConfig,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Update trading settings."""
    bot_state = await session.get(BotState, 1)
    if not bot_state:
        bot_state = BotState(id=1)
        session.add(bot_state)
    
    bot_state.trading_mode = config.trading_mode
    await session.commit()
    
    logger.info(f"Trading settings updated: mode={config.trading_mode}")
    return {"message": "Settings updated", "trading_mode": config.trading_mode}


@router.get("/strategies")
async def get_strategies(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get available strategies and their configurations."""
    # TODO: Fetch from database when strategy configuration table is created
    return {
        "strategies": [
            {
                "id": "momentum_v1",
                "name": "Momentum Strategy",
                "description": "Pure breakout detection",
                "enabled": True,
                "parameters": {
                    "min_volume_24h": 50000,
                    "min_price_change_5m": 0.05,
                    "min_volume_spike": 2.0,
                    "min_buy_sell_ratio": 1.2,
                    "max_risk_score": 50,
                    "take_profit_pct": 0.20,
                    "stop_loss_pct": 0.10,
                },
            },
            {
                "id": "ml_sniper_v1",
                "name": "ML-Assisted Sniper",
                "description": "ML-ready placeholder for future integration",
                "enabled": True,
                "parameters": {
                    "min_volume_24h": 50000,
                    "max_risk_score": 40,
                    "take_profit_pct": 0.15,
                    "stop_loss_pct": 0.10,
                },
            },
        ]
    }


@router.put("/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    config: StrategyConfig,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Update strategy configuration."""
    # TODO: Persist to database when strategy configuration table is created
    logger.info(f"Strategy {strategy_id} updated: {config}")
    return {"message": f"Strategy {strategy_id} updated", "config": config}


@router.get("/risk")
async def get_risk_settings(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get risk management settings."""
    return {
        "max_position_size_usd": 1000,
        "max_daily_loss_usd": 500,
        "max_positions": 5,
        "min_liquidity_usd": 5000,
        "max_risk_score": 50,
    }


@router.put("/risk")
async def update_risk_settings(
    config: RiskConfig,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Update risk management settings."""
    # TODO: Persist to database
    logger.info(f"Risk settings updated: {config}")
    return {"message": "Risk settings updated", "config": config}
