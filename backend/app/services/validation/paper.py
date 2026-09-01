"""Paper trading validation report service."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Position, Trade, BotState

logger = logging.getLogger(__name__)

VALIDATION_DAYS = 7


async def generate_paper_validation_report(session: AsyncSession) -> dict:
    """Generate 7-day paper trading validation report."""
    since = datetime.utcnow() - timedelta(days=VALIDATION_DAYS)

    bot_state = await session.get(BotState, 1)
    trading_mode = bot_state.trading_mode if bot_state else "PAPER"

    closed_result = await session.execute(
        select(Position).where(
            Position.status == "CLOSED",
            Position.closed_at >= since,
        )
    )
    closed = closed_result.scalars().all()

    open_result = await session.execute(
        select(func.count(Position.id)).where(Position.status == "OPEN")
    )
    open_count = open_result.scalar() or 0

    trades_result = await session.execute(
        select(func.count(Trade.id)).where(Trade.created_at >= since)
    )
    trade_count = trades_result.scalar() or 0

    total_pnl = sum(Decimal(p.pnl_usd or 0) for p in closed)
    wins = len([p for p in closed if (p.pnl_usd or 0) > 0])
    losses = len([p for p in closed if (p.pnl_usd or 0) <= 0])
    win_rate = (wins / len(closed) * 100) if closed else 0

    avg_pnl = float(total_pnl / len(closed)) if closed else 0
    max_drawdown = _calc_max_drawdown(closed)

    # Validation criteria per docs/paper-trading.md
    criteria = {
        "min_trades": {"required": 10, "actual": trade_count, "passed": trade_count >= 10},
        "min_closed_positions": {"required": 5, "actual": len(closed), "passed": len(closed) >= 5},
        "win_rate_above_40": {"required": 40.0, "actual": round(win_rate, 2), "passed": win_rate >= 40},
        "max_drawdown_below_20": {"required": 20.0, "actual": round(max_drawdown, 2), "passed": max_drawdown < 20},
        "paper_mode_active": {"required": "PAPER", "actual": trading_mode, "passed": trading_mode == "PAPER"},
    }

    all_passed = all(c["passed"] for c in criteria.values())

    return {
        "period_days": VALIDATION_DAYS,
        "since": since.isoformat(),
        "trading_mode": trading_mode,
        "summary": {
            "total_trades": trade_count,
            "closed_positions": len(closed),
            "open_positions": open_count,
            "total_pnl_usd": float(total_pnl),
            "win_rate_pct": round(win_rate, 2),
            "wins": wins,
            "losses": losses,
            "avg_pnl_per_trade_usd": round(avg_pnl, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
        },
        "validation_criteria": criteria,
        "ready_for_live": all_passed,
        "recommendation": (
            "Paper validation PASSED — consider small-capital LIVE test."
            if all_passed
            else "Paper validation INCOMPLETE — continue paper trading."
        ),
    }


def _calc_max_drawdown(closed_positions: list) -> float:
    if not closed_positions:
        return 0.0
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in sorted(closed_positions, key=lambda x: x.closed_at or datetime.utcnow()):
        cumulative += float(p.pnl_usd or 0)
        if cumulative > peak:
            peak = cumulative
        if peak > 0:
            dd = (peak - cumulative) / peak * 100
            max_dd = max(max_dd, dd)
    return max_dd
