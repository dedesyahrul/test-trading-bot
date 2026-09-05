from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, asc, exists
from sqlalchemy.orm import aliased
from app.core.database import get_db_session
from app.core.security import verify_token
from app.schemas import PairResponse, EnrichedPairResponse, MarketSnapshotResponse, SignalResponse
from app.services import PairService, MarketDataService
from app.services.audit import AuditService
from app.services.chart_intelligence import ChartIntelligence
from app.models import Pair, MarketSnapshot, Signal, Token, RiskAssessment
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["market"], prefix="/market")


def _meme_pair_filter():
    """Keep Scanner focused on non-native Solana meme pairs."""
    base = aliased(Token)
    quote = aliased(Token)
    native = {"SOL", "WSOL", "USDC", "USDT", "USDH", "DAI", "USDS"}
    return (
        base.id == Pair.base_token_id,
        quote.id == Pair.quote_token_id,
        ~func.upper(base.symbol).in_(native),
        func.upper(quote.symbol).in_(["SOL", "WSOL"]),
    ), base, quote


async def _enrich_pair(session: AsyncSession, pair: Pair) -> dict:
    base = await session.get(Token, pair.base_token_id)
    quote = await session.get(Token, pair.quote_token_id)
    base_symbol = base.symbol if base else "?"
    quote_symbol = quote.symbol if quote else "?"

    snapshot = await MarketDataService.get_latest_snapshot(session, pair.id)

    risk_result = await session.execute(
        select(RiskAssessment)
        .where(RiskAssessment.pair_id == pair.id)
        .order_by(desc(RiskAssessment.timestamp))
        .limit(1)
    )
    risk = risk_result.scalars().first()

    signal_result = await session.execute(
        select(Signal)
        .where(Signal.pair_id == pair.id)
        .order_by(desc(Signal.timestamp))
        .limit(1)
    )
    latest_signal = signal_result.scalars().first()

    # Snapshot fields are nullable because a pair can be discovered before
    # its first successful market-data collection. Keep that state as null
    # instead of dereferencing an absent snapshot or inventing zero values.
    snapshot_price = snapshot.price_usd if snapshot is not None else None
    pair_price = pair.price_usd if pair is not None else None
    snapshot_liquidity = snapshot.liquidity_usd if snapshot is not None else None
    pair_liquidity = pair.liquidity_usd if pair is not None else None
    price_value = snapshot_price if snapshot_price is not None else pair_price
    liquidity_value = snapshot_liquidity if snapshot_liquidity is not None else pair_liquidity
    price_change_24h = snapshot.price_change_24h if snapshot is not None else None
    volume_24h_usd = snapshot.volume_24h_usd if snapshot is not None else None

    return {
        "id": pair.id,
        "chain_id": pair.chain_id,
        "base_token": base_symbol,
        "quote_token": quote_symbol,
        "symbol": f"{base_symbol}/{quote_symbol}",
        "dex_name": pair.dex_name,
        "price_usd": float(price_value) if price_value is not None else None,
        "price_change_24h": float(price_change_24h) / 100 if price_change_24h is not None else None,
        "volume_24h_usd": float(volume_24h_usd) if volume_24h_usd is not None else None,
        "liquidity_usd": float(liquidity_value) if liquidity_value is not None else None,
        "risk_level": risk.risk_level if risk else "UNKNOWN",
        "risk_score": float(risk.risk_score) if risk else None,
        "signal_type": latest_signal.signal_type if latest_signal else "HOLD",
        "is_watched": pair.is_watched,
        "created_at": pair.created_at.isoformat() if pair.created_at else None,
        "updated_at": pair.updated_at.isoformat() if pair.updated_at else None,
        "market_data_at": snapshot.timestamp.isoformat() if snapshot else None,
    }


@router.post("/discover")
async def discover_tokens(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Trigger token discovery from DexScreener."""
    from app.workers.main import discover_tokens_worker

    await discover_tokens_worker(None)
    result = await session.execute(select(Pair).order_by(desc(Pair.updated_at)).limit(100))
    pairs = result.scalars().all()
    enriched = []
    for pair in pairs:
        enriched.append(await _enrich_pair(session, pair))
    if not enriched:
        raise HTTPException(
            status_code=503,
            detail="No market pairs discovered. DexScreener may be unavailable; try Refresh again shortly.",
        )
    return {"discovered": len(enriched), "pairs": enriched}


@router.get("/pairs", response_model=list[EnrichedPairResponse])
async def get_pairs(
    chain_id: str = None,
    watched_only: bool = False,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get pairs with enriched market data."""
    query = select(Pair)
    if chain_id:
        query = query.where(Pair.chain_id == chain_id)
    if watched_only:
        query = query.where(Pair.is_watched == True)
    pair_filters, base_alias, quote_alias = _meme_pair_filter()
    query = query.join(base_alias, base_alias.id == Pair.base_token_id).join(quote_alias, quote_alias.id == Pair.quote_token_id).where(pair_filters[2], pair_filters[3])
    
    result = await session.execute(query.order_by(desc(Pair.updated_at)).limit(100))
    pairs = result.scalars().all()
    enriched = []
    for pair in pairs:
        enriched.append(await _enrich_pair(session, pair))
    return enriched


@router.get("/pairs/page")
async def get_pairs_page(
    page: int = 1,
    page_size: int = 25,
    search: str = None,
    risk_level: str = None,
    sort_by: str = "updated_at",
    sort_dir: str = "desc",
    watched_only: bool = False,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Paginated market board backed by locally persisted market snapshots."""
    page = max(1, page)
    page_size = min(100, max(10, page_size))
    query = select(Pair)
    count_query = select(func.count(Pair.id))
    filters = []
    pair_filters, base_alias, quote_alias = _meme_pair_filter()
    query = query.join(base_alias, base_alias.id == Pair.base_token_id).join(quote_alias, quote_alias.id == Pair.quote_token_id)
    count_query = count_query.join(base_alias, base_alias.id == Pair.base_token_id).join(quote_alias, quote_alias.id == Pair.quote_token_id)
    filters.extend([pair_filters[2], pair_filters[3]])
    if watched_only:
        filters.append(Pair.is_watched.is_(True))
    if search:
        token_ids = select(Token.id).where(
            or_(Token.symbol.ilike(f"%{search}%"), Token.address.ilike(f"%{search}%"))
        )
        filters.append(or_(Pair.base_token_id.in_(token_ids), Pair.quote_token_id.in_(token_ids)))
    if risk_level:
        filters.append(exists(
            select(RiskAssessment.id).where(
                RiskAssessment.pair_id == Pair.id,
                RiskAssessment.risk_level == risk_level.upper(),
            )
        ))
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)
    total = (await session.execute(count_query)).scalar_one()
    sort_column = {
        "updated_at": Pair.updated_at,
        "created_at": Pair.created_at,
        "liquidity": Pair.liquidity_usd,
        "price": Pair.price_usd,
    }.get(sort_by, Pair.updated_at)
    ordering = desc(sort_column) if sort_dir.lower() != "asc" else asc(sort_column)
    result = await session.execute(query.order_by(ordering).offset((page - 1) * page_size).limit(page_size))
    items = [await _enrich_pair(session, pair) for pair in result.scalars().all()]
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size,
        "updated_at": max((item.get("updated_at") or "" for item in items), default=None),
    }


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


@router.get("/pairs/{pair_id}/chart-intelligence")
async def get_chart_intelligence(
    pair_id: str,
    timeframe: str = "minute",
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Return the latest deterministic candle analysis for a pair."""
    if timeframe not in {"minute", "5m", "15m", "hour", "1h"}:
        raise HTTPException(status_code=400, detail="Unsupported timeframe. Use minute, 5m, 15m, or hour.")
    candles = await MarketDataService.get_candles(session, pair_id, timeframe, limit=100)
    assessment = ChartIntelligence.assess(candles)
    return {
        "pair_id": pair_id,
        "timeframe": timeframe,
        "candle_count": len(candles),
        "trend": assessment.trend,
        "behavior": assessment.behavior,
        "rsi": assessment.rsi,
        "atr": assessment.atr,
        "ema_fast": assessment.ema_fast,
        "ema_slow": assessment.ema_slow,
        "volume_ratio": assessment.volume_ratio,
        "candle_pattern": assessment.candle_pattern,
        "entry_allowed": assessment.entry_allowed,
        "reasons": assessment.reasons,
        "updated_at": (candles[-1].get("timestamp") if isinstance(candles[-1], dict) else candles[-1].timestamp).isoformat() if candles else None,
    }


@router.get("/pairs/{pair_id}/candles")
async def get_pair_candles(
    pair_id: str,
    timeframe: str = "minute",
    limit: int = 100,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Return timestamped OHLCV candles for a token chart."""
    if timeframe not in {"minute", "5m", "15m", "hour", "1h"}:
        raise HTTPException(status_code=400, detail="Unsupported timeframe. Use minute, 5m, 15m, or hour.")
    candles = await MarketDataService.get_candles(session, pair_id, timeframe, min(limit, 500))
    def serialize(candle):
        value = candle.get if isinstance(candle, dict) else lambda key, default=None: getattr(candle, key, default)
        return {"timestamp": value("timestamp").isoformat(), "open": float(value("open")), "high": float(value("high")), "low": float(value("low")), "close": float(value("close")), "volume": float(value("volume", 0) or 0)}
    return {
        "pair_id": pair_id,
        "timeframe": timeframe,
        "items": [
            serialize(candle)
            for candle in candles
        ],
    }


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
    await AuditService.record(session, "WATCH_PAIR", "PAIR", user_id=payload.get("sub"), resource_id=pair_id)
    await session.commit()
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
    await AuditService.record(session, "UNWATCH_PAIR", "PAIR", user_id=payload.get("sub"), resource_id=pair_id)
    await session.commit()
    return {"message": "Pair is no longer watched"}
