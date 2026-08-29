import logging
from decimal import Decimal
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import Position, Trade, MarketSnapshot
from app.services import MarketDataService

logger = logging.getLogger(__name__)


class PortfolioService:
    """Monitor and manage portfolio positions."""

    @staticmethod
    async def update_position_prices(
        session: AsyncSession,
        position_id,
    ) -> Optional[Position]:
        """Update position current price and PnL from latest market data."""
        
        position = await session.get(Position, position_id)
        if not position or position.status != "OPEN":
            return None
        
        # Get latest market snapshot
        latest_snapshot = await MarketDataService.get_latest_snapshot(session, position.pair_id)
        if not latest_snapshot or not latest_snapshot.price_usd:
            return position
        
        current_price = latest_snapshot.price_usd
        position.current_price = current_price
        
        # Calculate unrealized PnL
        pnl = (current_price - position.entry_price) * position.entry_amount
        pnl_pct = (current_price - position.entry_price) / position.entry_price if position.entry_price > 0 else Decimal("0")
        
        position.pnl_usd = pnl
        position.pnl_percent = pnl_pct
        
        # Check TP/SL
        should_close = False
        reason = ""
        
        if position.take_profit and current_price >= position.take_profit:
            should_close = True
            reason = "Take Profit hit"
        elif position.stop_loss and current_price <= position.stop_loss:
            should_close = True
            reason = "Stop Loss hit"
        
        if should_close:
            logger.info(f"Position {position_id} should close: {reason}")
            # Would trigger SELL execution here
        
        await session.commit()
        return position

    @staticmethod
    async def get_portfolio_summary(
        session: AsyncSession,
        wallet_id,
    ) -> dict:
        """Get portfolio summary for wallet."""
        
        # Get all open positions
        result = await session.execute(
            select(Position)
            .where(Position.wallet_id == wallet_id)
            .where(Position.status == "OPEN")
        )
        open_positions = result.scalars().all()
        
        # Get all closed positions
        result = await session.execute(
            select(Position)
            .where(Position.wallet_id == wallet_id)
            .where(Position.status == "CLOSED")
        )
        closed_positions = result.scalars().all()
        
        # Calculate totals
        total_open_pnl = sum(Decimal(p.pnl_usd or 0) for p in open_positions)
        total_closed_pnl = sum(Decimal(p.pnl_usd or 0) for p in closed_positions)
        total_pnl = total_open_pnl + total_closed_pnl
        
        total_entry_value = sum(Decimal(p.entry_price or 0) * Decimal(p.entry_amount or 0) for p in open_positions)
        total_current_value = sum(Decimal(p.current_price or 0) * Decimal(p.entry_amount or 0) for p in open_positions)
        
        return {
            "total_pnl": float(total_pnl),
            "total_open_pnl": float(total_open_pnl),
            "total_closed_pnl": float(total_closed_pnl),
            "open_positions_count": len(open_positions),
            "closed_positions_count": len(closed_positions),
            "total_entry_value": float(total_entry_value),
            "total_current_value": float(total_current_value),
            "unrealized_pnl": float(total_open_pnl),
            "realized_pnl": float(total_closed_pnl),
        }

    @staticmethod
    async def get_position_details(
        session: AsyncSession,
        position_id,
    ) -> Optional[dict]:
        """Get detailed information about a position."""
        
        position = await session.get(Position, position_id)
        if not position:
            return None
        
        # Get trades for this position
        result = await session.execute(
            select(Trade)
            .where(Trade.position_id == position_id)
            .order_by(Trade.created_at)
        )
        trades = result.scalars().all()
        
        return {
            "position_id": str(position.id),
            "pair_id": str(position.pair_id),
            "entry_price": float(position.entry_price),
            "entry_amount": float(position.entry_amount),
            "current_price": float(position.current_price or 0),
            "current_amount": float(position.current_amount or 0),
            "stop_loss": float(position.stop_loss) if position.stop_loss else None,
            "take_profit": float(position.take_profit) if position.take_profit else None,
            "status": position.status,
            "pnl_usd": float(position.pnl_usd or 0),
            "pnl_percent": float(position.pnl_percent or 0),
            "created_at": position.created_at.isoformat(),
            "closed_at": position.closed_at.isoformat() if position.closed_at else None,
            "trades": [
                {
                    "trade_type": t.trade_type,
                    "price": float(t.price),
                    "amount": float(t.amount),
                    "tx_hash": t.tx_hash,
                    "status": t.status,
                    "created_at": t.created_at.isoformat(),
                }
                for t in trades
            ],
        }
