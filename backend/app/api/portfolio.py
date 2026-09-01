from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token
from app.services.portfolio.service import PortfolioService
from app.services.trading.engine import ExecutionEngine
from app.adapters.blockchain import SolanaJupiterAdapter
from app.core.events import EventPublisher
from app.services.audit import AuditService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["portfolio"], prefix="/portfolio")


def _get_execution_engine() -> ExecutionEngine:
    adapter = SolanaJupiterAdapter()
    return ExecutionEngine(adapter, adapter, None, adapter)


@router.get("/wallets/default")
async def get_default_wallet(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get or create default paper trading wallet."""
    wallet = await PortfolioService.get_or_create_default_wallet(session)
    if not wallet:
        raise HTTPException(status_code=404, detail="No user found to create wallet")
    return {
        "id": str(wallet.id),
        "chain_id": wallet.chain_id,
        "address": wallet.address,
        "label": wallet.label,
    }


@router.get("/positions")
async def list_positions(
    wallet_id: str = None,
    status: str = Query(None, description="OPEN or CLOSED"),
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """List positions with optional filters."""
    try:
        if not wallet_id:
            wallet = await PortfolioService.get_or_create_default_wallet(session)
            wallet_id = str(wallet.id) if wallet else None
        positions = await PortfolioService.list_positions(session, wallet_id, status)
        return {"positions": positions}
    except Exception as e:
        logger.error(f"Error listing positions: {e}")
        raise HTTPException(status_code=400, detail=str(e))


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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position details: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/positions/{position_id}/close")
async def close_position(
    position_id: str,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Manually close an open position."""
    try:
        engine = _get_execution_engine()
        trade = await engine.execute_sell(session, position_id, exit_reason="MANUAL")
        if not trade:
            raise HTTPException(status_code=400, detail="Failed to close position")

        await EventPublisher.publish(
            "ORDER_STATUS_CHANGED",
            {
                "position_id": position_id,
                "status": "CONFIRMED",
                "type": "SELL",
            },
        )
        await AuditService.record(session, "CLOSE_POSITION", "POSITION", user_id=payload.get("sub"),
                                  resource_id=position_id, details={"trade_id": str(trade.id)})
        await session.commit()
        return {"message": "Position closed", "trade_id": str(trade.id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=400, detail=str(e))
