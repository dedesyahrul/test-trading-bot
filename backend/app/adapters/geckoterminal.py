"""GeckoTerminal market-data adapter.

The adapter normalizes GeckoTerminal pools into the pair shape already used by
MemeX. It is a fallback/cross-check provider, not a replacement for the
existing DexScreener integration.
"""
import logging
from decimal import Decimal
from typing import Any, Optional

import httpx
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeckoTerminalClient:
    def __init__(self) -> None:
        self.base_url = settings.GECKO_TERMINAL_API_URL.rstrip("/")
        self.timeout = 8
        self._ohlcv_blocked_until: datetime | None = None

    async def _get(self, path: str, params: Optional[dict] = None) -> Any:
        try:
            async with httpx.AsyncClient(headers={"User-Agent": "MemeX/0.1"}) as client:
                response = await client.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("GeckoTerminal request failed %s: %s", path, type(exc).__name__)
            return None

    async def get_trending_pools(self, network: str = "solana") -> list[dict]:
        result = await self._get(f"/networks/{network}/trending_pools")
        pools = [self.normalize_pool(item) for item in (result or {}).get("data", []) if item]
        native = {"SOL", "WSOL", "USDC", "USDT", "USDH", "DAI", "USDS"}
        return [pool for pool in pools if pool["base_token"]["symbol"].upper() not in native and pool["quote_token"]["symbol"].upper() in {"SOL", "WSOL"}]

    async def get_pool(self, network: str, pool_address: str) -> Optional[dict]:
        result = await self._get(f"/networks/{network}/pools/{pool_address}")
        item = (result or {}).get("data")
        return self.normalize_pool(item) if item else None

    async def get_pool_ohlcv(self, network: str, pool_address: str, timeframe: str = "minute", limit: int = 100) -> list[dict]:
        """Get timestamped OHLCV candles for a pool."""
        if self._ohlcv_blocked_until and datetime.utcnow() < self._ohlcv_blocked_until:
            return []
        result = await self._get(
            f"/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}",
            params={"aggregate": 1, "limit": min(limit, 100)},
        )
        if result is None:
            # Avoid hammering a provider after a rate-limit response.
            self._ohlcv_blocked_until = datetime.utcnow() + timedelta(minutes=1)
        rows = ((result or {}).get("data") or {}).get("attributes", {}).get("ohlcv_list", [])
        candles = []
        for row in rows:
            if len(row) < 6:
                continue
            candles.append({"timestamp": row[0], "open": row[1], "high": row[2], "low": row[3], "close": row[4], "volume": row[5]})
        return candles

    @staticmethod
    def normalize_pool(item: dict) -> dict:
        attrs = item.get("attributes", {})
        relationships = item.get("relationships", {})
        base_id = (relationships.get("base_token", {}).get("data") or {}).get("id", "")
        quote_id = (relationships.get("quote_token", {}).get("data") or {}).get("id", "")
        base_address = base_id.split("_", 1)[-1] if "_" in base_id else None
        quote_address = quote_id.split("_", 1)[-1] if "_" in quote_id else None
        volume = attrs.get("volume_usd") or {}
        changes = attrs.get("price_change_percentage") or {}
        transactions = attrs.get("transactions") or {}
        h24_tx = transactions.get("h24") or {}
        name = attrs.get("name") or "UNKNOWN/UNKNOWN"
        symbols = name.split(" / ", 1)
        return {
            "chain": "solana",
            "dex": (attrs.get("dex_id") or "geckoterminal"),
            "pair_address": attrs.get("address"),
            "base_token": {"address": base_address, "symbol": symbols[0], "name": symbols[0]},
            "quote_token": {"address": quote_address, "symbol": symbols[-1], "name": symbols[-1]},
            "price_usd": Decimal(str(attrs["base_token_price_usd"])) if attrs.get("base_token_price_usd") else None,
            "price_change": {key: Decimal(str(changes[key])) if changes.get(key) is not None else None for key in ("m5", "h1", "h24")},
            "volume": {key: Decimal(str(volume[key])) if volume.get(key) is not None else None for key in ("m5", "h1", "h24")},
            "liquidity": {"usd": Decimal(str(attrs["reserve_in_usd"])) if attrs.get("reserve_in_usd") else None},
            "market_cap_usd": Decimal(str(attrs["market_cap_usd"])) if attrs.get("market_cap_usd") else None,
            "fdv_usd": Decimal(str(attrs["fdv_usd"])) if attrs.get("fdv_usd") else None,
            "pair_created_at": attrs.get("pool_created_at"),
            "transactions": {"h24": {"buys": h24_tx.get("buys"), "sells": h24_tx.get("sells")}},
            "provider": "geckoterminal",
        }
