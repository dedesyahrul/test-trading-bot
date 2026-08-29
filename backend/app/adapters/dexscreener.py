import httpx
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class DEXScreenerClient:
    """Client for DEX Screener API."""

    def __init__(self):
        self.base_url = settings.DEX_SCREENER_API_URL
        self.timeout = 30

    async def search_pairs(self, query: str) -> Dict[str, Any]:
        """Search pairs by token or pair address."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={"q": query},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"DEX Screener search error: {e}")
            return {}

    async def get_pair_by_chain_and_address(self, chain: str, pair_address: str) -> Dict[str, Any]:
        """Get pair details by chain and pair address."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/pairs/{chain}/{pair_address}",
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"DEX Screener get pair error: {e}")
            return {}

    async def get_trending_pairs(self, chain: Optional[str] = None) -> Dict[str, Any]:
        """Get trending pairs."""
        try:
            params = {}
            if chain:
                params["chain"] = chain

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/trending",
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"DEX Screener trending error: {e}")
            return {}

    @staticmethod
    def normalize_pair_data(pair_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize pair data from DEX Screener API response."""
        if not pair_data:
            return {}

        try:
            # Extract base pair info
            pair_info = {
                "chain": pair_data.get("chainId"),
                "dex": pair_data.get("dexId"),
                "pair_address": pair_data.get("pairAddress"),
                "base_token": {
                    "address": pair_data.get("baseToken", {}).get("address"),
                    "symbol": pair_data.get("baseToken", {}).get("symbol"),
                    "name": pair_data.get("baseToken", {}).get("name"),
                },
                "quote_token": {
                    "address": pair_data.get("quoteToken", {}).get("address"),
                    "symbol": pair_data.get("quoteToken", {}).get("symbol"),
                    "name": pair_data.get("quoteToken", {}).get("name"),
                },
            }

            # Price data
            price_data = pair_data.get("priceUsd")
            if price_data:
                pair_info["price_usd"] = Decimal(price_data)

            # Price changes
            price_change = pair_data.get("priceChange", {})
            pair_info["price_change"] = {
                "m5": Decimal(price_change.get("m5", 0)) if price_change.get("m5") else None,
                "h1": Decimal(price_change.get("h1", 0)) if price_change.get("h1") else None,
                "h24": Decimal(price_change.get("h24", 0)) if price_change.get("h24") else None,
            }

            # Volume
            volume = pair_data.get("volume", {})
            pair_info["volume"] = {
                "h5": Decimal(volume.get("h5", 0)) if volume.get("h5") else None,
                "h1": Decimal(volume.get("h1", 0)) if volume.get("h1") else None,
                "h24": Decimal(volume.get("h24", 0)) if volume.get("h24") else None,
            }

            # Liquidity
            liquidity = pair_data.get("liquidity", {})
            pair_info["liquidity"] = {
                "usd": Decimal(liquidity.get("usd", 0)) if liquidity.get("usd") else None,
                "base": Decimal(liquidity.get("base", 0)) if liquidity.get("base") else None,
                "quote": Decimal(liquidity.get("quote", 0)) if liquidity.get("quote") else None,
            }

            # Market info
            pair_info["market_cap_usd"] = Decimal(pair_data.get("marketCap", 0)) if pair_data.get("marketCap") else None
            pair_info["fdv_usd"] = Decimal(pair_data.get("fdv", 0)) if pair_data.get("fdv") else None
            pair_info["pair_created_at"] = pair_data.get("pairCreatedAt")

            # Transactions
            txns = pair_data.get("txns", {})
            pair_info["transactions"] = {
                "h5": txns.get("h5"),
                "h1": txns.get("h1"),
                "h24": txns.get("h24"),
            }

            return pair_info
        except Exception as e:
            logger.error(f"Error normalizing pair data: {e}")
            return {}
