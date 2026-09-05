"""Read-only Solana JSON-RPC client used by the security gate."""

import logging
from typing import Any, Optional

import httpx
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)

TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss82G2j1"
# Official Token-2022 program id.
TOKEN_2022_PROGRAM_ID = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"


class SolanaRPCClient:
    """Fetch parsed mint state and largest token accounts from Solana RPC."""

    def __init__(self, rpc_url: Optional[str] = None, timeout: float = 8.0):
        configured_urls = [url.strip() for url in settings.SOLANA_RPC_URLS.split(",") if url.strip()]
        self.rpc_urls = configured_urls or [rpc_url or settings.SOLANA_RPC_URL]
        self.timeout = timeout
        self.max_retries = 2

    async def _call(self, method: str, params: list[Any]) -> Any:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        for attempt in range(self.max_retries + 1):
            try:
                rpc_url = self.rpc_urls[attempt % len(self.rpc_urls)]
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(rpc_url, json=payload)
                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise httpx.HTTPStatusError("temporary RPC failure", request=response.request, response=response)
                    response.raise_for_status()
                    body = response.json()
                if body.get("error"):
                    logger.warning("Solana RPC %s failed: %s", method, body["error"])
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.25 * (attempt + 1))
                        continue
                    return None
                return body.get("result")
            except (httpx.HTTPError, ValueError) as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.25 * (attempt + 1))
                    continue
                logger.warning("Solana RPC %s unavailable on attempt %d: %s", method, attempt + 1, exc)
        return None

    async def get_mint(self, mint_address: str) -> Optional[dict[str, Any]]:
        """Return supply and authority data for a mint address."""
        supply_result = await self._call("getTokenSupply", [mint_address, {"commitment": "confirmed"}])
        supply_value = (supply_result or {}).get("value") if isinstance(supply_result, dict) else None
        if not supply_value:
            return None

        account_result = await self._call(
            "getAccountInfo", [mint_address, {"encoding": "jsonParsed", "commitment": "confirmed"}]
        )
        account_value = (account_result or {}).get("value") if isinstance(account_result, dict) else None
        if not account_value:
            logger.info("Mint %s is not available at the selected RPC commitment", mint_address)
            return None
        if account_value.get("owner") not in {TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID}:
            logger.warning("Mint %s has unsupported owner program %s", mint_address, account_value.get("owner"))
            return None
        data = (account_value.get("data") or {})
        info = data.get("parsed", {}).get("info", {}) if isinstance(data, dict) else {}
        parsed_type = data.get("parsed", {}).get("type") if isinstance(data, dict) else None
        if parsed_type not in {None, "mint"}:
            return None
        return {
            "supply": float(supply_value.get("uiAmount") or 0),
            "raw_supply": int(supply_value.get("amount") or 0),
            "decimals": int(supply_value.get("decimals") or 0),
            "mint_authority": info.get("mintAuthority"),
            "freeze_authority": info.get("freezeAuthority"),
            "program_id": account_value.get("owner"),
            "extensions": info.get("extensions", []),
        }

    async def get_top_holders(self, mint_address: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return largest token accounts as a concentration proxy."""
        result = await self._call("getTokenLargestAccounts", [mint_address])
        values = (result or {}).get("value", []) if isinstance(result, dict) else []
        holders = []
        for row in values[:limit]:
            token_account = row.get("address")
            if not token_account:
                continue
            account = await self._call(
                "getAccountInfo", [token_account, {"encoding": "jsonParsed"}]
            )
            value = (account or {}).get("value") if isinstance(account, dict) else None
            info = (((value or {}).get("data") or {}).get("parsed") or {}).get("info", {})
            holders.append({
                "address": info.get("owner") or token_account,
                "token_account": token_account,
                "balance": float(row.get("uiAmount") or 0),
                "is_frozen": info.get("state") == "frozen",
            })
        return holders

    async def get_first_signatures(self, address: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Return oldest available signatures for an address.

        This is intentionally exposed for a future transaction parser; a
        signature is not treated as a developer identity without parsing the
        mint transaction instructions.
        """
        result = await self._call("getSignaturesForAddress", [address, {"limit": min(limit, 1000)}])
        return result if isinstance(result, list) else []

    async def get_token_creator(self, mint_address: str) -> Optional[str]:
        """Resolve the fee payer of the oldest available mint transaction.

        The RPC result is only used as a creator hint after checking that the
        transaction exists and has a signer. It is not treated as proof of
        maliciousness by itself.
        """
        signatures = await self.get_first_signatures(mint_address)
        if not signatures:
            return None
        oldest = signatures[-1].get("signature")
        if not oldest:
            return None
        transaction = await self._call(
            "getTransaction",
            [oldest, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
        )
        message = (((transaction or {}).get("transaction") or {}).get("message") or {})
        for key in message.get("accountKeys", []):
            if key.get("signer") and key.get("pubkey"):
                return key["pubkey"]
        return None
