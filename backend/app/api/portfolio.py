from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token
from app.services.portfolio.service import PortfolioService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["portfolio"], prefix="/portfolio")


@router.get("/summary/{wallet_id}")
async def get_portfolio_summary(
    wallet_id: str,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get portfolio summary for wallet."""
    try:
        summary = await PortfolioService.get_portfolio_summary(session, wallet_id)
        return summary
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/positions/{position_id}")
async def get_position_details(
    position_id: str,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a position."""
    try:
        details = await PortfolioService.get_position_details(session, position_id)
        if not details:
            raise HTTPException(status_code=404, detail="Position not found")
        return details
    except Exception as e:
        logger.error(f"Error getting position details: {e}")
        raise HTTPException(status_code=400, detail=str(e))
