"""Update Prometheus gauges from database."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import ACTIVE_POSITIONS, TOTAL_PNL_24H, WIN_RATE_24H
from app.models import Position

logger = logging.getLogger(__name__)


async def refresh_business_metrics(session: AsyncSession) -> None:
    """Refresh business metric gauges from current DB state."""
    try:
        open_result = await session.execute(
            select(func.count(Position.id)).where(Position.status == "OPEN")
        )
        ACTIVE_POSITIONS.set(open_result.scalar() or 0)

        since = datetime.utcnow() - timedelta(hours=24)
        closed_result = await session.execute(
            select(Position).where(
                Position.status == "CLOSED",
                Position.closed_at >= since,
            )
        )
        closed = closed_result.scalars().all()

        total_pnl = sum(float(p.pnl_usd or 0) for p in closed)
        TOTAL_PNL_24H.set(total_pnl)

        if closed:
            wins = len([p for p in closed if (p.pnl_usd or 0) > 0])
            WIN_RATE_24H.set(wins / len(closed) * 100)
        else:
            WIN_RATE_24H.set(0)
    except Exception as e:
        logger.warning("Failed to refresh metrics: %s", e)
