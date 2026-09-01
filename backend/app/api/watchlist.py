from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, func, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import verify_token
from app.models import AuditLog, Pair, Token, MarketSnapshot

router = APIRouter(tags=["watchlist"], prefix="/watchlist")


@router.get("/history")
async def watchlist_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=10, le=100),
    search: str | None = Query(None, max_length=80),
    action: str | None = Query(None, pattern="^(WATCH_PAIR|UNWATCH_PAIR)$"),
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    query = (
        select(AuditLog, Pair, Token)
        .join(Pair, cast(Pair.id, String) == AuditLog.resource_id, isouter=True)
        .join(Token, Pair.base_token_id == Token.id, isouter=True)
        .where(AuditLog.resource == "PAIR")
        .where(AuditLog.action.in_(["WATCH_PAIR", "UNWATCH_PAIR"]))
    )
    count_query = select(func.count(AuditLog.id)).where(
        AuditLog.resource == "PAIR",
        AuditLog.action.in_(["WATCH_PAIR", "UNWATCH_PAIR"]),
    )
    if not payload.get("is_admin"):
        query = query.where(AuditLog.user_id == payload.get("sub"))
        count_query = count_query.where(AuditLog.user_id == payload.get("sub"))
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if search:
        query = query.where(Token.symbol.ilike(f"%{search}%"))
        count_query = count_query.where(
            AuditLog.resource_id.in_(select(Pair.id).join(Token, Pair.base_token_id == Token.id).where(Token.symbol.ilike(f"%{search}%")))
        )
    total = (await session.execute(count_query)).scalar_one()
    rows = (await session.execute(query.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size))).all()
    items = []
    for entry, pair, token in rows:
        snapshot = await session.execute(
            select(MarketSnapshot).where(MarketSnapshot.pair_id == pair.id).order_by(desc(MarketSnapshot.timestamp)).limit(1)
        ) if pair else None
        latest = snapshot.scalars().first() if snapshot else None
        items.append({
            "id": str(entry.id), "pair_id": entry.resource_id,
            "symbol": f"{token.symbol}/SOL" if token else "Unknown pair",
            "action": entry.action, "is_watched": bool(pair.is_watched) if pair else False,
            "price_usd": float(latest.price_usd) if latest and latest.price_usd else None,
            "liquidity_usd": float(latest.liquidity_usd) if latest and latest.liquidity_usd else None,
            "market_data_at": latest.timestamp.isoformat() if latest else None,
            "created_at": entry.created_at.isoformat(),
        })
    return {"items": items, "page": page, "page_size": page_size, "total": total, "pages": (total + page_size - 1) // page_size}
