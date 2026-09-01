import httpx
import logging
import asyncio
from decimal import Decimal
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

DEXSCREENER_BASE = "https://api.dexscreener.com"


class DEXScreenerClient:
    """Client for DEX Screener API."""

    def __init__(self):
        self.base_url = settings.DEX_SCREENER_API_URL
        # A dead pair must not stall the whole five-minute collection cycle.
        self.timeout = 5
        self.max_retries = 0

    async def _get(self, url: str, params: Optional[dict] = None, timeout: Optional[float] = None) -> Any:
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    headers={"User-Agent": "MemeX/0.1 market-data-client"}
                ) as client:
                    response = await client.get(url, params=params, timeout=timeout or self.timeout)
                    if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                        retry_after = response.headers.get("retry-after")
                        try:
                            delay = float(retry_after) if retry_after else 2 ** attempt
                        except ValueError:
                            delay = 2 ** attempt
                        await asyncio.sleep(min(delay, 8))
                        continue
                    response.raise_for_status()
                    return response.json()
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.error(
                    "DEX Screener request failed %s after %d retries: %s (%s)",
                    url, self.max_retries, type(e).__name__, e or "no response",
                )
                return None
            except httpx.HTTPStatusError as e:
                logger.warning("DEX Screener returned HTTP %s for %s", e.response.status_code, url)
                return None
            except (httpx.HTTPError, ValueError) as e:
                logger.error("DEX Screener request failed %s: %s", url, e)
                return None
        return None

    async def search_pairs(self, query: str) -> Dict[str, Any]:
        """Search pairs by token or pair address."""
        result = await self._get(f"{self.base_url}/search", params={"q": query}, timeout=20)
        return result if isinstance(result, dict) else {}

    async def get_pair_by_chain_and_address(self, chain: str, pair_address: str) -> Dict[str, Any]:
        """Get pair details by chain and pair address."""
        result = await self._get(f"{self.base_url}/pairs/{chain}/{pair_address}")
        if isinstance(result, dict) and (result.get("pair") or result.get("pairs")):
            return result
        if result is None:
            return {}
        # Some provider responses omit the singular pair field. Search is a
        # safe fallback and lets the worker match the exact pair address.
        fallback = await self.search_pairs(pair_address)
        if isinstance(fallback, dict):
            return fallback
        return result if isinstance(result, dict) else {}

    async def get_token_pairs(self, chain: str, token_address: str) -> List[Dict[str, Any]]:
        """Get all pairs for a token address on a chain."""
        result = await self._get(f"{DEXSCREENER_BASE}/token-pairs/v1/{chain}/{token_address}")
        return result if isinstance(result, list) else []

    async def get_tokens(self, chain: str, token_addresses: List[str]) -> List[Dict[str, Any]]:
        """Resolve multiple token addresses in one official batch request."""
        addresses = ",".join(token_addresses[:30])
        if not addresses:
            return []
        result = await self._get(
            f"{DEXSCREENER_BASE}/tokens/v1/{chain}/{addresses}", timeout=20
        )
        return result if isinstance(result, list) else []

    async def get_token_boosts(self) -> List[Dict[str, Any]]:
        """Get latest boosted/trending tokens."""
        result = await self._get(f"{DEXSCREENER_BASE}/token-boosts/latest/v1", timeout=20)
        return result if isinstance(result, list) else []

    async def get_token_profiles(self, recent: bool = False) -> List[Dict[str, Any]]:
        """Get official latest/recent token profiles (60 requests/minute)."""
        path = "recent-updates" if recent else "latest"
        result = await self._get(
            f"{DEXSCREENER_BASE}/token-profiles/{path}/v1", timeout=20
        )
        if isinstance(result, list):
            return result
        return [result] if isinstance(result, dict) and result.get("tokenAddress") else []

    async def get_trending_pairs(self, chain: Optional[str] = None) -> Dict[str, Any]:
        """Get trending pairs via token boosts, then resolve pair data."""
        target_chain = chain or "solana"
        # Keep the original MemeX discovery source: boosted tokens first,
        # then resolve each token to its most liquid pair.
        boosts = await self.get_token_boosts()
        if not boosts:
            # A broad SOL search returns SOL/USDC and other major markets, not
            # newly discovered meme tokens. Do not use it as a new-token source.
            return {}

        seen_tokens: set[str] = set()
        pairs: List[Dict[str, Any]] = []

        for boost in boosts:
            boost_chain = boost.get("chainId")
            token_address = boost.get("tokenAddress")
            if boost_chain != target_chain or not token_address:
                continue
            if token_address in seen_tokens:
                continue
            seen_tokens.add(token_address)

            token_pairs = await self.get_token_pairs(boost_chain, token_address)
            if not token_pairs:
                continue

            eligible = [p for p in token_pairs if self.is_meme_pair_candidate(p, target_chain)]
            if not eligible:
                continue
            eligible.sort(key=lambda p: p.get("pairCreatedAt") or 0, reverse=True)
            pairs.append(eligible[0])
            if len(pairs) >= 50:
                break

        if pairs:
            return {"pairs": pairs}

        return {}

    @staticmethod
    def is_meme_pair_candidate(pair: Dict[str, Any], chain: str = "solana") -> bool:
        """Reject native/stable major markets from meme-token discovery."""
        if pair.get("chainId") != chain or not pair.get("pairAddress"):
            return False
        base = pair.get("baseToken") or {}
        quote = pair.get("quoteToken") or {}
        base_symbol = (base.get("symbol") or "").upper()
        quote_symbol = (quote.get("symbol") or "").upper()
        native = {"SOL", "WSOL", "USDC", "USDT", "USDH", "DAI", "USDS"}
        return bool(base.get("address") and quote.get("address")) and base_symbol not in native and quote_symbol in {"SOL", "WSOL"}

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
                "m5": Decimal(volume.get("m5", 0)) if volume.get("m5") else None,
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
