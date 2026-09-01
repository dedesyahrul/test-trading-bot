"""Validation gates for market snapshots before they enter intelligence."""
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal


class DataQualityStatus(str, Enum):
    VALID = "DATA_VALID"
    WARNING = "DATA_WARNING"
    INVALID = "DATA_INVALID"
    STALE = "DATA_STALE"


class DataQualityService:
    @staticmethod
    def assess(snapshot, now: datetime | None = None, stale_after_seconds: int = 180) -> tuple[DataQualityStatus, list[str]]:
        reasons: list[str] = []
        now = now or datetime.utcnow()
        timestamp = snapshot.timestamp.replace(tzinfo=None) if snapshot.timestamp.tzinfo else snapshot.timestamp
        if timestamp < now - timedelta(seconds=stale_after_seconds):
            return DataQualityStatus.STALE, ["Market snapshot is stale"]
        if not snapshot.price_usd or Decimal(str(snapshot.price_usd)) <= 0:
            return DataQualityStatus.INVALID, ["Price is missing or non-positive"]
        if snapshot.liquidity_usd is not None and Decimal(str(snapshot.liquidity_usd)) < 0:
            return DataQualityStatus.INVALID, ["Liquidity cannot be negative"]
        if snapshot.volume_24h_usd is not None and Decimal(str(snapshot.volume_24h_usd)) < 0:
            return DataQualityStatus.INVALID, ["Volume cannot be negative"]
        for field in ("price_change_1m", "price_change_5m", "price_change_1h", "price_change_24h"):
            value = getattr(snapshot, field, None)
            if value is not None and abs(float(value)) > 10000:
                return DataQualityStatus.INVALID, [f"{field} is outside plausible bounds"]
        if snapshot.liquidity_usd is None or snapshot.volume_24h_usd is None:
            reasons.append("Liquidity or volume is unavailable")
        return (DataQualityStatus.WARNING if reasons else DataQualityStatus.VALID), reasons
