"""Jupiter DEX aggregator API client for Solana swaps."""

import logging
from decimal import Decimal
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SOL_MINT = "So11111111111111111111111111111111111111112"


class JupiterClient:
    """HTTP client for Jupiter v6 quote and swap APIs."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.JUPITER_API_URL).rstrip("/")

    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount_lamports: int,
        slippage_bps: int = 50,
    ) -> dict[str, Any]:
        """Fetch swap quote from Jupiter."""
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount_lamports),
            "slippageBps": str(slippage_bps),
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/quote", params=params)
            response.raise_for_status()
            return response.json()

    async def get_swap_transaction(
        self,
        quote: dict[str, Any],
        user_public_key: str,
        wrap_unwrap_sol: bool = True,
    ) -> dict[str, Any]:
        """Build unsigned swap transaction from quote."""
        payload = {
            "quoteResponse": quote,
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": wrap_unwrap_sol,
            "dynamicComputeUnitLimit": True,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.base_url}/swap", json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def parse_quote_amounts(quote: dict[str, Any]) -> tuple[Decimal, Decimal]:
        """Extract in/out amounts from Jupiter quote response."""
        in_amount = Decimal(quote.get("inAmount", "0"))
        out_amount = Decimal(quote.get("outAmount", "0"))
        return in_amount, out_amount

    @staticmethod
    def estimate_price(in_amount: Decimal, out_amount: Decimal) -> Decimal:
        if in_amount <= 0:
            return Decimal("0")
        return out_amount / in_amount
