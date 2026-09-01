from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token
from app.models import BotState, Position
from app.services.portfolio.service import PortfolioService
from app.services.settings.service import DEFAULT_RISK_CONFIG

router = APIRouter(tags=["risk"], prefix="/risk")


@router.get("/portfolio")
async def get_portfolio_risk(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    bot_state = await session.get(BotState, 1)
    config = (bot_state.risk_config if bot_state else None) or DEFAULT_RISK_CONFIG
    wallet = await PortfolioService.get_or_create_default_wallet(session)
    if not wallet:
        return {"exposure_usd": 0, "pair_exposure": [], "circuit_state": bot_state.circuit_state if bot_state else "UNKNOWN"}

    result = await session.execute(select(Position).where(Position.wallet_id == wallet.id, Position.status == "OPEN"))
    positions = list(result.scalars().all())
    by_pair: dict[str, Decimal] = {}
    for position in positions:
        value = Decimal(str(position.current_price or position.entry_price)) * Decimal(str(position.current_amount or position.entry_amount))
        by_pair[str(position.pair_id)] = by_pair.get(str(position.pair_id), Decimal("0")) + value
    exposure = sum(by_pair.values(), Decimal("0"))
    return {
        "exposure_usd": float(exposure),
        "max_exposure_usd": float(config.get("max_portfolio_exposure_usd", 5000)),
        "pair_exposure": [{"pair_id": pair_id, "exposure_usd": float(value), "share": float(value / exposure) if exposure else 0} for pair_id, value in by_pair.items()],
        "open_positions": len(positions),
        "circuit_state": bot_state.circuit_state if bot_state else "UNKNOWN",
        "daily_loss_usd": float(bot_state.daily_loss_usd or 0) if bot_state else 0,
    }
