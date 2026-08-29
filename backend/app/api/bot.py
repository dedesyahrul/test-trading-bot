from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token
from app.schemas import BotStateResponse
from app.models import BotState
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bot"], prefix="/bot")


@router.get("/status", response_model=BotStateResponse)
async def get_bot_status(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get bot status."""
    bot_state = await session.get(BotState, 1)
    if not bot_state:
        # Create default state
        bot_state = BotState(id=1, state="STOPPED", trading_mode="PAPER")
        session.add(bot_state)
        await session.commit()
        await session.refresh(bot_state)
    return bot_state


@router.post("/start")
async def start_bot(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Start the bot."""
    bot_state = await session.get(BotState, 1)
    if not bot_state:
        bot_state = BotState(id=1, state="STARTING", trading_mode="PAPER")
        session.add(bot_state)
    else:
        bot_state.state = "STARTING"
    
    await session.commit()
    logger.info("Bot start requested")
    return {"message": "Bot is starting"}


@router.post("/stop")
async def stop_bot(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Stop the bot gracefully."""
    bot_state = await session.get(BotState, 1)
    if not bot_state:
        bot_state = BotState(id=1, state="STOPPED", trading_mode="PAPER")
        session.add(bot_state)
    else:
        bot_state.state = "STOPPING"
    
    await session.commit()
    logger.info("Bot stop requested")
    return {"message": "Bot is stopping"}


@router.post("/pause")
async def pause_bot(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Pause the bot (no new trades, keep monitoring)."""
    bot_state = await session.get(BotState, 1)
    if not bot_state:
        bot_state = BotState(id=1, state="PAUSED", trading_mode="PAPER")
        session.add(bot_state)
    else:
        bot_state.state = "PAUSED"
    
    await session.commit()
    logger.info("Bot pause requested")
    return {"message": "Bot is paused"}


@router.post("/emergency-stop")
async def emergency_stop_bot(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Emergency stop (kill switch) - stop all activity immediately."""
    bot_state = await session.get(BotState, 1)
    if not bot_state:
        bot_state = BotState(id=1, state="EMERGENCY_STOP", trading_mode="PAPER")
        session.add(bot_state)
    else:
        bot_state.state = "EMERGENCY_STOP"
    
    await session.commit()
    logger.critical("EMERGENCY STOP ACTIVATED")
    return {"message": "Emergency stop activated"}


@router.post("/reset")
async def reset_bot(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Reset bot to STOPPED state."""
    bot_state = await session.get(BotState, 1)
    if not bot_state:
        bot_state = BotState(id=1, state="STOPPED", trading_mode="PAPER")
        session.add(bot_state)
    else:
        bot_state.state = "STOPPED"
        bot_state.error_message = None
    
    await session.commit()
    logger.info("Bot reset")
    return {"message": "Bot reset to STOPPED state"}
