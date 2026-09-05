"""Developer wallet risk checks backed by the local scam registry."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ScamRegistry
from app.services.security.models import DeveloperCheckResult


class DeveloperRegistry:
    """Block developers present in the locally curated scam registry."""

    async def check(self, session: AsyncSession, developer_address: Optional[str]) -> DeveloperCheckResult:
        if not developer_address:
            return DeveloperCheckResult(
                is_blocked=False,
                risk_score=30,
                reasons=["Developer address unavailable"],
            )
        result = await session.execute(
            select(func.count(ScamRegistry.id)).where(
                ScamRegistry.address == developer_address,
                ScamRegistry.address_type == "dev_wallet",
            )
        )
        scam_count = int(result.scalar() or 0)
        return DeveloperCheckResult(
            is_blocked=scam_count > 0,
            block_reason=f"Developer listed in scam registry ({scam_count} record(s))" if scam_count else None,
            risk_score=100 if scam_count else 0,
            developer_address=developer_address,
            scam_count=scam_count,
            reasons=["Developer registry match" if scam_count else "Developer not found in registry"],
        )
