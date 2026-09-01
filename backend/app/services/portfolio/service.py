import logging
from decimal import Decimal
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.models import Position, Trade, MarketSnapshot, Pair, Token, Wallet, User
from app.services import MarketDataService

logger = logging.getLogger(__name__)


class PortfolioService:
    """Monitor and manage portfolio positions."""

    @staticmethod
    async def get_or_create_default_wallet(session: AsyncSession) -> Optional[Wallet]:
        """Get first wallet or create a paper trading wallet."""
        result = await session.execute(select(Wallet).where(Wallet.is_active == True).limit(1))
        wallet = result.scalars().first()
        if wallet:
            return wallet

        user_result = await session.execute(select(User).limit(1))
        user = user_result.scalars().first()
        if not user:
            return None

        # A clean database reset removes the chain seed as well. Ensure the
        # foreign-key target exists before creating the default paper wallet.
        from app.services import ChainService
        await ChainService.create_or_get_chain(session, "solana")

        wallet = Wallet(
            user_id=user.id,
            chain_id="solana",
            address="paper-wallet-default",
            label="Paper Trading",
            is_active=True,
        )
        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)
        return wallet

    @staticmethod
    async def list_positions(
        session: AsyncSession,
        wallet_id=None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """List positions with token symbols."""
        query = select(Position)
        if wallet_id:
            query = query.where(Position.wallet_id == wallet_id)
        if status:
            query = query.where(Position.status == status)
        query = query.order_by(desc(Position.created_at))

        result = await session.execute(query)
        positions = result.scalars().all()
        enriched = []
        for position in positions:
            enriched.append(await PortfolioService._enrich_position(session, position))
        return enriched

    @staticmethod
    async def _enrich_position(session: AsyncSession, position: Position) -> dict:
        pair = await session.get(Pair, position.pair_id)
        symbol = "UNKNOWN"
        if pair:
            base = await session.get(Token, pair.base_token_id)
            quote = await session.get(Token, pair.quote_token_id)
            if base and quote:
                symbol = f"{base.symbol}/{quote.symbol}"

        latest_snapshot = await MarketDataService.get_latest_snapshot(session, position.pair_id)

        duration = None
        if position.closed_at and position.created_at:
            delta = position.closed_at - position.created_at
            hours = int(delta.total_seconds() // 3600)
            minutes = int((delta.total_seconds() % 3600) // 60)
            duration = f"{hours}h {minutes}m"

        return {
            "id": str(position.id),
            "pair_id": str(position.pair_id),
            "wallet_id": str(position.wallet_id),
            "symbol": symbol,
            "entry_price": float(position.entry_price),
            "entry_amount": float(position.entry_amount),
            "current_price": float(position.current_price or position.entry_price),
            "exit_price": float(position.current_price or 0) if position.status == "CLOSED" else None,
            "stop_loss": float(position.stop_loss) if position.stop_loss else None,
            "take_profit": float(position.take_profit) if position.take_profit else None,
            "status": position.status,
            "pnl": float(position.pnl_usd or 0),
            "pnl_percent": float(position.pnl_percent or 0),
            "created_at": position.created_at.isoformat(),
            "closed_at": position.closed_at.isoformat() if position.closed_at else None,
            "duration": duration,
            "market_data_at": latest_snapshot.timestamp.isoformat() if latest_snapshot else None,
            "exit_reason": position.exit_reason,
            "exit_pressure": float(position.exit_pressure or 0),
            "highest_price": float(position.highest_price or position.entry_price),
            "mae_usd": float(position.mae_usd or 0),
            "mfe_usd": float(position.mfe_usd or 0),
        }

    @staticmethod
    async def update_position_prices(
        session: AsyncSession,
        position_id,
    ) -> tuple[Optional[Position], bool, str, Decimal]:
        """Update price and calculate an adaptive exit action."""
        
        position = await session.get(Position, position_id)
        if not position or position.status != "OPEN":
            return position, False, "", Decimal("0")
        
        latest_snapshot = await MarketDataService.get_latest_snapshot(session, position.pair_id)
        if not latest_snapshot or not latest_snapshot.price_usd:
            return position, False, "", Decimal("0")
        
        from app.services.trading.adaptive_exit import AdaptiveExitService
        current_price = latest_snapshot.price_usd
        position.current_price = current_price
        position.highest_price = max(position.highest_price or position.entry_price, current_price)
        
        pnl = (current_price - position.entry_price) * position.entry_amount
        pnl_pct = (current_price - position.entry_price) / position.entry_price if position.entry_price > 0 else Decimal("0")
        
        adverse = (current_price - position.entry_price) * position.entry_amount
        favorable = (position.highest_price - position.entry_price) * position.entry_amount
        position.mae_usd = min(Decimal(str(position.mae_usd or 0)), adverse)
        position.mfe_usd = max(Decimal(str(position.mfe_usd or 0)), favorable)
        position.pnl_usd = pnl
        position.pnl_percent = pnl_pct
        
        assessment = AdaptiveExitService.assess(position, latest_snapshot)
        position.stop_loss = assessment.stop_loss
        position.take_profit = assessment.take_profit
        position.exit_pressure = assessment.pressure
        if position.profit_lock_price is None and pnl_pct >= Decimal("0.04"):
            position.profit_lock_price = position.entry_price * Decimal("1.01")
        if position.profit_lock_price and current_price <= position.profit_lock_price and pnl_pct > 0 and (position.partial_exit_count or 0) == 0:
            assessment = assessment.__class__("PARTIAL_EXIT", assessment.pressure, assessment.stop_loss, assessment.take_profit, assessment.trail_price, "Profit lock protected gains", Decimal("0.5"))
        should_close = assessment.action != "HOLD"
        reason = assessment.reason
        if should_close:
            if assessment.action == "PARTIAL_EXIT":
                position.exit_reason = "PROFIT_LOCK" if "lock" in reason.lower() else "PARTIAL_EXIT"
            elif "stop" in reason.lower():
                position.exit_reason = "STOP_LOSS"
            elif "target" in reason.lower():
                position.exit_reason = "TAKE_PROFIT"
            else:
                position.exit_reason = "THESIS_INVALIDATED"
        
        await session.commit()
        return position, should_close, reason, assessment.fraction

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
