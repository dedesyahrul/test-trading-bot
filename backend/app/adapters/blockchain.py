from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import logging

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
    status: str  # CONFIRMED, FAILED, TIMEOUT
    amount_out: Optional[Decimal] = None
    actual_slippage: Optional[float] = None
    error: Optional[str] = None


class BlockchainAdapter(ABC):
    """Abstract blockchain adapter for multi-chain support."""

    @abstractmethod
    async def get_chain_id(self) -> str:
        """Get chain identifier."""
        pass

    @abstractmethod
    async def get_native_token(self) -> str:
        """Get native token symbol."""
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if RPC connection is healthy."""
        pass


class DEXAdapter(ABC):
    """Abstract DEX adapter for quote and swap."""

    @abstractmethod
    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount: Decimal,
        slippage: float,
    ) -> Quote:
        """Get swap quote from DEX."""
        pass

    @abstractmethod
    async def build_transaction(
        self,
        quote: Quote,
        wallet_address: str,
    ) -> UnsignedTransaction:
        """Build unsigned transaction from quote."""
        pass


class WalletAdapter(ABC):
    """Abstract wallet adapter for signing."""

    @abstractmethod
    async def get_address(self) -> str:
        """Get wallet public address."""
        pass

    @abstractmethod
    async def sign_transaction(self, tx: UnsignedTransaction) -> bytes:
        """Sign transaction with private key."""
        pass


class ExecutionAdapter(ABC):
    """Abstract execution adapter for broadcasting."""

    @abstractmethod
    async def broadcast_transaction(self, signed_tx: bytes) -> str:
        """Broadcast signed transaction. Returns tx_hash."""
        pass

    @abstractmethod
    async def wait_for_confirmation(self, tx_hash: str, timeout_seconds: int = 60) -> TransactionResult:
        """Wait for transaction confirmation."""
        pass

    @abstractmethod
    async def estimate_gas(self, tx: UnsignedTransaction) -> Decimal:
        """Estimate gas cost."""
        pass


class SolanaJupiterAdapter(BlockchainAdapter, DEXAdapter, ExecutionAdapter):
    """Solana + Jupiter implementation (stub for Phase 3)."""

    async def get_chain_id(self) -> str:
        return "solana"

    async def get_native_token(self) -> str:
        return "SOL"

    async def is_healthy(self) -> bool:
        # TODO: Implement RPC health check
        return True

    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount: Decimal,
        slippage: float,
    ) -> Quote:
        # TODO: Call Jupiter API
        logger.info(f"Getting quote: {amount} {token_in} -> {token_out}")
        return Quote(
            token_in=token_in,
            token_out=token_out,
            amount_in=amount,
            amount_out=Decimal("0"),  # TODO: Fetch from API
            price=Decimal("1.0"),
            slippage=slippage,
        )

    async def build_transaction(
        self,
        quote: Quote,
        wallet_address: str,
    ) -> UnsignedTransaction:
        # TODO: Build Solana transaction
        logger.info(f"Building transaction for {wallet_address}")
        return UnsignedTransaction(
            chain="solana",
            data={},
            gas_estimate=Decimal("5000"),
        )

    async def broadcast_transaction(self, signed_tx: bytes) -> str:
        # TODO: Broadcast to Solana network
        logger.info("Broadcasting transaction")
        return "tx_hash_placeholder"

    async def wait_for_confirmation(self, tx_hash: str, timeout_seconds: int = 60) -> TransactionResult:
        # TODO: Poll RPC for confirmation
        logger.info(f"Waiting for confirmation: {tx_hash}")
        return TransactionResult(
            tx_hash=tx_hash,
            status="CONFIRMED",
        )

    async def estimate_gas(self, tx: UnsignedTransaction) -> Decimal:
        # TODO: Estimate gas
        return Decimal("5000")
