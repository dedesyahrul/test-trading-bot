from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.core.security import verify_token
from app.models import Trade, Position, Signal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["statistics"], prefix="/statistics")


@router.get("/summary")
async def get_statistics_summary(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get trading statistics summary."""
    try:
        # Get closed positions
        result = await session.execute(
            select(Position).where(Position.status == "CLOSED")
        )
        closed_positions = result.scalars().all()
        
        # Get open positions
        result = await session.execute(
            select(Position).where(Position.status == "OPEN")
        )
        open_positions = result.scalars().all()
        
        # Get recent trades
        result = await session.execute(
            select(Trade)
            .order_by(Trade.created_at.desc())
            .limit(20)
        )
        recent_trades = result.scalars().all()
        
        # Get signals
        result = await session.execute(
            select(Signal)
            .order_by(Signal.timestamp.desc())
            .limit(50)
        )
        signals = result.scalars().all()
        
        # Calculate statistics
        total_closed_pnl = sum(float(p.pnl_usd or 0) for p in closed_positions)
        total_open_pnl = sum(float(p.pnl_usd or 0) for p in open_positions)
        winning_positions = len([p for p in closed_positions if p.pnl_usd and p.pnl_usd > 0])
        losing_positions = len([p for p in closed_positions if p.pnl_usd and p.pnl_usd <= 0])
        
        total_closed = len(closed_positions)
        win_rate = (winning_positions / total_closed * 100) if total_closed > 0 else 0
        
        # Buy/sell signal counts
        buy_signals = len([s for s in signals if s.signal_type == "BUY"])
        sell_signals = len([s for s in signals if s.signal_type == "SELL"])
        
        return {
            "positions": {
                "open_count": len(open_positions),
                "closed_count": total_closed,
                "winning": winning_positions,
                "losing": losing_positions,
            },
            "pnl": {
                "total": total_closed_pnl + total_open_pnl,
                "realized": total_closed_pnl,
                "unrealized": total_open_pnl,
            },
            "performance": {
                "win_rate": f"{win_rate:.2f}%",
                "avg_trade_pnl": f"${total_closed_pnl / total_closed:.2f}" if total_closed > 0 else "$0.00",
            },
            "signals": {
                "buy_count": buy_signals,
                "sell_count": sell_signals,
                "total": len(signals),
            },
            "trades": {
                "total": len(recent_trades),
                "recent_20": [
                    {
                        "type": t.trade_type,
                        "price": float(t.price),
                        "amount": float(t.amount),
                        "created_at": t.created_at.isoformat(),
                    }
                    for t in recent_trades
                ],
            },
        }
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily")
async def get_daily_statistics(
    days: int = 7,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get daily trading statistics for the past N days."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await session.execute(
            select(Trade)
            .where(Trade.created_at >= start_date)
            .order_by(Trade.created_at)
        )
        trades = result.scalars().all()
        
        # Group by day
        daily_stats = {}
        for trade in trades:
            day = trade.created_at.date().isoformat()
            if day not in daily_stats:
                daily_stats[day] = {
                    "buy_count": 0,
                    "sell_count": 0,
                    "total_volume": 0,
                }
            
            daily_stats[day]["buy_count"] += 1 if trade.trade_type == "BUY" else 0
            daily_stats[day]["sell_count"] += 1 if trade.trade_type == "SELL" else 0
            daily_stats[day]["total_volume"] += float(trade.amount)
        
        return {
            "period": f"last_{days}_days",
            "daily": daily_stats,
        }
    except Exception as e:
        logger.error(f"Error calculating daily statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
