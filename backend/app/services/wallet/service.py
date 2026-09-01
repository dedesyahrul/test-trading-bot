"""In-memory wallet key management (never persisted to DB)."""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_keypair = None
_loaded = False


class WalletService:
    """Load and provide wallet signing only in execution context."""

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.WALLET_PRIVATE_KEY)

    @staticmethod
    def get_keypair():
        """Load Solana keypair from env into memory (once)."""
        global _keypair, _loaded

        if _loaded:
            return _keypair

        _loaded = True
        if not settings.WALLET_PRIVATE_KEY:
            logger.info("WALLET_PRIVATE_KEY not set — LIVE trading disabled")
            return None

        try:
            from solders.keypair import Keypair

            raw = settings.WALLET_PRIVATE_KEY.strip()
            if raw.startswith("["):
                import json
                secret = bytes(json.loads(raw))
            else:
                import base58
                secret = base58.b58decode(raw)

            _keypair = Keypair.from_bytes(secret)
            logger.info("Wallet loaded: %s", _keypair.pubkey())
            return _keypair
        except Exception as e:
            logger.error("Failed to load wallet key: %s", e)
            return None

    @staticmethod
    def get_address() -> Optional[str]:
        kp = WalletService.get_keypair()
        return str(kp.pubkey()) if kp else None

    @staticmethod
    def sign_transaction_base64(unsigned_tx_b64: str) -> Optional[str]:
        """Sign a base64-encoded versioned transaction, return signed base64."""
        kp = WalletService.get_keypair()
        if not kp:
            return None

        try:
            import base64
            from solders.transaction import VersionedTransaction

            raw = base64.b64decode(unsigned_tx_b64)
            tx = VersionedTransaction.from_bytes(raw)
            signed = VersionedTransaction(tx.message, [kp])
            return base64.b64encode(bytes(signed)).decode()
        except Exception as e:
            logger.error("Transaction signing failed: %s", e)
            return None
