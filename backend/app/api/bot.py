from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token
from app.schemas import BotStateResponse
from app.models import BotState
import logging
from datetime import timedelta
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
from app.services.audit import AuditService

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
    await AuditService.record(session, "BOT_START", "BOT", user_id=payload.get("sub"),
                              details={"trading_mode": bot_state.trading_mode})
    await session.commit()

    # Do not make users wait for the next five-minute cron tick after starting.
    # The worker still owns the actual pipeline and execution logic.
    redis_pool = None
    try:
        redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        await redis_pool.enqueue_job("collect_market_data_worker")
        await redis_pool.enqueue_job(
            "process_watched_pairs_pipeline",
            _defer_by=timedelta(seconds=30),
        )
    except Exception as exc:
        logger.exception("Could not enqueue initial trading jobs")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trading worker is unavailable. Make sure the worker and Redis services are running.",
        ) from exc
    finally:
        if redis_pool:
            await redis_pool.close()

    logger.info("Bot start requested")
    return {"message": "Bot is starting", "state": "STARTING"}


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
    await AuditService.record(session, "BOT_STOP", "BOT", user_id=payload.get("sub"))
    await session.commit()
    logger.info("Bot stop requested")
    return {"message": "Bot is stopping", "state": "STOPPING"}


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
    await AuditService.record(session, "BOT_PAUSE", "BOT", user_id=payload.get("sub"))
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
    await AuditService.record(session, "EMERGENCY_STOP", "BOT", user_id=payload.get("sub"))
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
    await AuditService.record(session, "BOT_RESET", "BOT", user_id=payload.get("sub"))
    await session.commit()
    logger.info("Bot reset")
    return {"message": "Bot reset to STOPPED state"}
