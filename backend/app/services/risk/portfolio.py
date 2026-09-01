"""Portfolio-level entry controls based on persisted positions and trades."""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Position


class PortfolioRiskService:
    @staticmethod
    async def entry_guard(session: AsyncSession, wallet_id, pair_id, proposed_size: Decimal,
                          config: dict) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        open_result = await session.execute(
            select(Position).where(Position.wallet_id == wallet_id, Position.status == "OPEN")
        )
        positions = list(open_result.scalars().all())
        exposure = sum(Decimal(str(p.current_price or p.entry_price)) * Decimal(str(p.current_amount or p.entry_amount)) for p in positions)
        pair_exposure = sum(
            Decimal(str(p.current_price or p.entry_price)) * Decimal(str(p.current_amount or p.entry_amount))
            for p in positions if str(p.pair_id) == str(pair_id)
        )
        max_portfolio = Decimal(str(config.get("max_portfolio_exposure_usd", 5000)))
        max_pair = Decimal(str(config.get("max_pair_exposure_usd", 1500)))
        if exposure + proposed_size > max_portfolio:
            reasons.append(f"Portfolio exposure limit reached: {exposure + proposed_size:.2f} > {max_portfolio:.2f}")
        if pair_exposure + proposed_size > max_pair:
            reasons.append(f"Pair exposure limit reached: {pair_exposure + proposed_size:.2f} > {max_pair:.2f}")

        cooldown_minutes = int(config.get("loss_cooldown_minutes", 30))
        cooldown_since = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
        loss_result = await session.execute(
            select(Position).where(
                Position.wallet_id == wallet_id,
                Position.pair_id == pair_id,
                Position.status == "CLOSED",
                Position.pnl_usd < 0,
                Position.closed_at >= cooldown_since,
            ).limit(1)
        )
        if loss_result.scalars().first():
            reasons.append(f"Pair is in loss cooldown for {cooldown_minutes} minutes")
        return not reasons, reasons
