from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db_session
from app.core.security import verify_token
from app.services.settings import SettingsService
from app.services.audit import AuditService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"], prefix="/settings")


class StrategyConfigUpdate(BaseModel):
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
    max_risk_per_trade_pct: float = 0.01
    max_portfolio_exposure_usd: float = 5000
    max_pair_exposure_usd: float = 1500
    loss_cooldown_minutes: int = 30
    paper_initial_balance: float = 100


class TradingConfig(BaseModel):
    """Trading configuration."""
    trading_mode: str  # PAPER or LIVE
    risk_config: RiskConfig
    strategies: list[StrategyConfigUpdate]


@router.get("/trading")
async def get_trading_settings(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get current trading settings."""
    bot_state = await SettingsService.get_or_create_bot_state(session)
    risk_config = await SettingsService.get_risk_config(session)
    strategies = await SettingsService.get_all_strategies(session)

    return {
        "trading_mode": bot_state.trading_mode,
        "bot_state": bot_state.state,
        "risk_config": risk_config,
        "strategies": [
            {
                "id": s.strategy_key,
                "name": s.name,
                "description": s.description,
                "enabled": s.is_active,
                "parameters": s.parameters,
            }
            for s in strategies
        ],
        "last_update": bot_state.last_update.isoformat() if bot_state.last_update else None,
    }


@router.put("/trading")
async def update_trading_settings(
    config: TradingConfig,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Update trading settings."""
    bot_state = await SettingsService.get_or_create_bot_state(session)
    bot_state.trading_mode = config.trading_mode
    await SettingsService.update_risk_config(session, config.risk_config.model_dump())

    for strategy in config.strategies:
        await SettingsService.update_strategy(
            session,
            strategy.strategy_id,
            strategy.enabled,
            strategy.parameters,
        )

    await session.commit()
    await AuditService.record(session, "UPDATE_TRADING_SETTINGS", "SETTINGS", user_id=payload.get("sub"),
                              details={"trading_mode": config.trading_mode, "strategy_count": len(config.strategies)})
    await session.commit()
    logger.info("Trading settings updated: mode=%s", config.trading_mode)
    return {"message": "Settings updated", "trading_mode": config.trading_mode}


@router.get("/strategies")
async def get_strategies(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get available strategies and their configurations."""
    strategies = await SettingsService.get_all_strategies(session)
    return {
        "strategies": [
            {
                "id": s.strategy_key,
                "name": s.name,
                "description": s.description,
                "enabled": s.is_active,
                "parameters": s.parameters,
            }
            for s in strategies
        ]
    }


@router.put("/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    config: StrategyConfigUpdate,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Update strategy configuration."""
    try:
        strategy = await SettingsService.update_strategy(
            session,
            strategy_id,
            config.enabled,
            config.parameters,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    logger.info("Strategy %s updated", strategy_id)
    return {
        "message": f"Strategy {strategy_id} updated",
        "config": {
            "strategy_id": strategy.strategy_key,
            "enabled": strategy.is_active,
            "parameters": strategy.parameters,
        },
    }


@router.get("/risk")
async def get_risk_settings(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get risk management settings."""
    return await SettingsService.get_risk_config(session)


@router.put("/risk")
async def update_risk_settings(
    config: RiskConfig,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Update risk management settings."""
    updated = await SettingsService.update_risk_config(session, config.model_dump())
    logger.info("Risk settings updated")
    return {"message": "Risk settings updated", "config": updated}
