from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import base64
import logging

import httpx

from app.adapters.jupiter import JupiterClient, SOL_MINT
from app.core.config import settings
from app.services.wallet.service import WalletService

logger = logging.getLogger(__name__)


@dataclass
class Quote:
    """DEX quote for a swap."""
    token_in: str
    token_out: str
    amount_in: Decimal
    amount_out: Decimal
    price: Decimal
    slippage: float
    raw_quote: Optional[dict] = None


@dataclass
class UnsignedTransaction:
    """Unsigned blockchain transaction."""
    chain: str
    data: dict
    gas_estimate: Decimal
    priority_fee: Optional[Decimal] = None


@dataclass
class TransactionResult:
    """Result of transaction execution."""
    tx_hash: str
    status: str
    amount_out: Optional[Decimal] = None
    actual_slippage: Optional[float] = None
    error: Optional[str] = None


class BlockchainAdapter(ABC):
    @abstractmethod
    async def get_chain_id(self) -> str:
        pass

    @abstractmethod
    async def get_native_token(self) -> str:
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        pass


class DEXAdapter(ABC):
    @abstractmethod
    async def get_quote(self, token_in: str, token_out: str, amount: Decimal, slippage: float) -> Quote:
        pass

    @abstractmethod
    async def build_transaction(self, quote: Quote, wallet_address: str) -> UnsignedTransaction:
        pass


class WalletAdapter(ABC):
    @abstractmethod
    async def get_address(self) -> str:
        pass

    @abstractmethod
    async def sign_transaction(self, tx: UnsignedTransaction) -> bytes:
        pass


class ExecutionAdapter(ABC):
    @abstractmethod
    async def broadcast_transaction(self, signed_tx: bytes) -> str:
        pass

    @abstractmethod
    async def wait_for_confirmation(self, tx_hash: str, timeout_seconds: int = 60) -> TransactionResult:
        pass

    @abstractmethod
    async def estimate_gas(self, tx: UnsignedTransaction) -> Decimal:
        pass


class SolanaWalletAdapter(WalletAdapter):
    """Sign transactions using in-memory keypair."""

    async def get_address(self) -> str:
        addr = WalletService.get_address()
        if not addr:
            raise RuntimeError("Wallet not configured")
        return addr

    async def sign_transaction(self, tx: UnsignedTransaction) -> bytes:
        swap_tx = tx.data.get("swapTransaction")
        if not swap_tx:
            raise RuntimeError("No swap transaction in payload")
        signed = WalletService.sign_transaction_base64(swap_tx)
        if not signed:
            raise RuntimeError("Signing failed")
        return signed.encode()


class SolanaJupiterAdapter(BlockchainAdapter, DEXAdapter, ExecutionAdapter):
    """Solana + Jupiter DEX integration."""

    def __init__(self):
        self.jupiter = JupiterClient()
        self.slippage_bps = settings.DEFAULT_SLIPPAGE_BPS

    async def get_chain_id(self) -> str:
        return "solana"

    async def get_native_token(self) -> str:
        return "SOL"

    async def is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    settings.SOLANA_RPC_URL,
                    json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                )
                result = response.json()
                return result.get("result") == "ok"
        except Exception as e:
            logger.warning("Solana RPC health check failed: %s", e)
            return False

    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount: Decimal,
        slippage: float,
    ) -> Quote:
        slippage_bps = int(slippage * 10000) if slippage < 1 else int(slippage)
        amount_lamports = int(amount)

        raw = await self.jupiter.get_quote(
            input_mint=token_in,
            output_mint=token_out,
            amount_lamports=amount_lamports,
            slippage_bps=slippage_bps or self.slippage_bps,
        )
        in_amt, out_amt = JupiterClient.parse_quote_amounts(raw)
        price = JupiterClient.estimate_price(in_amt, out_amt)

        return Quote(
            token_in=token_in,
            token_out=token_out,
            amount_in=in_amt,
            amount_out=out_amt,
            price=price,
            slippage=slippage_bps / 10000,
            raw_quote=raw,
        )

    async def build_transaction(self, quote: Quote, wallet_address: str) -> UnsignedTransaction:
        if not quote.raw_quote:
            raise RuntimeError("Quote missing raw data for swap build")

        swap_data = await self.jupiter.get_swap_transaction(
            quote=quote.raw_quote,
            user_public_key=wallet_address,
        )
        return UnsignedTransaction(
            chain="solana",
            data=swap_data,
            gas_estimate=Decimal("5000"),
        )

    async def broadcast_transaction(self, signed_tx: bytes) -> str:
        signed_b64 = signed_tx.decode() if isinstance(signed_tx, bytes) else signed_tx
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                signed_b64,
                {"encoding": "base64", "skipPreflight": False, "maxRetries": 3},
            ],
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.SOLANA_RPC_URL, json=payload)
            result = response.json()
            if "error" in result:
                raise RuntimeError(result["error"].get("message", "Broadcast failed"))
            return result["result"]

    async def wait_for_confirmation(self, tx_hash: str, timeout_seconds: int = 60) -> TransactionResult:
        import asyncio

        for _ in range(timeout_seconds // 2):
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignatureStatuses",
                "params": [[tx_hash], {"searchTransactionHistory": True}],
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(settings.SOLANA_RPC_URL, json=payload)
                result = response.json()
                statuses = result.get("result", {}).get("value", [])
                if statuses and statuses[0]:
                    status = statuses[0]
                    if status.get("err"):
                        return TransactionResult(tx_hash=tx_hash, status="FAILED", error=str(status["err"]))
                    if status.get("confirmationStatus") in ("confirmed", "finalized"):
                        return TransactionResult(tx_hash=tx_hash, status="CONFIRMED")
            await asyncio.sleep(2)

        return TransactionResult(tx_hash=tx_hash, status="TIMEOUT")

    async def estimate_gas(self, tx: UnsignedTransaction) -> Decimal:
        return Decimal("5000")

    async def swap_sol_for_token(
        self,
        token_mint: str,
        amount_lamports: int,
        slippage_bps: Optional[int] = None,
    ) -> TransactionResult:
        """High-level: quote → build → sign → broadcast."""
        if not WalletService.is_configured():
            return TransactionResult(tx_hash="", status="FAILED", error="Wallet not configured")

        wallet_addr = WalletService.get_address()
        slippage = (slippage_bps or self.slippage_bps) / 10000

        quote = await self.get_quote(SOL_MINT, token_mint, Decimal(amount_lamports), slippage)
        unsigned = await self.build_transaction(quote, wallet_addr)
        signed_b64 = WalletService.sign_transaction_base64(unsigned.data["swapTransaction"])
        if not signed_b64:
            return TransactionResult(tx_hash="", status="FAILED", error="Signing failed")

        tx_hash = await self.broadcast_transaction(signed_b64.encode())
        return await self.wait_for_confirmation(tx_hash)

    async def swap_token_for_sol(
        self,
        token_mint: str,
        amount_raw: int,
        slippage_bps: Optional[int] = None,
    ) -> TransactionResult:
        """Sell token back to SOL."""
        if not WalletService.is_configured():
            return TransactionResult(tx_hash="", status="FAILED", error="Wallet not configured")

        wallet_addr = WalletService.get_address()
        slippage = (slippage_bps or self.slippage_bps) / 10000

        quote = await self.get_quote(token_mint, SOL_MINT, Decimal(amount_raw), slippage)
        unsigned = await self.build_transaction(quote, wallet_addr)
        signed_b64 = WalletService.sign_transaction_base64(unsigned.data["swapTransaction"])
        if not signed_b64:
            return TransactionResult(tx_hash="", status="FAILED", error="Signing failed")

        tx_hash = await self.broadcast_transaction(signed_b64.encode())
        return await self.wait_for_confirmation(tx_hash)
