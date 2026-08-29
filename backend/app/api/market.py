from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db_session
from app.core.security import verify_token
from app.schemas import PairResponse, MarketSnapshotResponse, SignalResponse
from app.services import PairService, MarketDataService
from app.models import Pair, MarketSnapshot, Signal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market"], prefix="/market")


@router.get("/pairs", response_model=list[PairResponse])
async def get_pairs(
    chain_id: str = None,
    watched_only: bool = False,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get pairs."""
    query = select(Pair)
    if chain_id:
        query = query.where(Pair.chain_id == chain_id)
    if watched_only:
        query = query.where(Pair.is_watched == True)
    
    result = await session.execute(query.limit(100))
    pairs = result.scalars().all()
    return pairs


@router.get("/pairs/{pair_id}/snapshots", response_model=list[MarketSnapshotResponse])
async def get_pair_snapshots(
    pair_id: str,
    limit: int = 100,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get market snapshots for a pair."""
    result = await session.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.pair_id == pair_id)
        .order_by(desc(MarketSnapshot.timestamp))
        .limit(limit)
    )
    snapshots = result.scalars().all()
    return snapshots


@router.get("/pairs/{pair_id}/signals", response_model=list[SignalResponse])
async def get_pair_signals(
    pair_id: str,
    limit: int = 50,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get signals for a pair."""
    result = await session.execute(
        select(Signal)
        .where(Signal.pair_id == pair_id)
        .order_by(desc(Signal.timestamp))
        .limit(limit)
    )
    signals = result.scalars().all()
    return signals


@router.post("/pairs/{pair_id}/watch")
async def watch_pair(
    pair_id: str,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Watch a pair."""
    pair = await PairService.set_watched(session, pair_id, True)
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    logger.info(f"Pair {pair_id} is now watched")
    return {"message": "Pair is now watched"}


@router.post("/pairs/{pair_id}/unwatch")
async def unwatch_pair(
    pair_id: str,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Unwatch a pair."""
    pair = await PairService.set_watched(session, pair_id, False)
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    logger.info(f"Pair {pair_id} is no longer watched")
    return {"message": "Pair is no longer watched"}
