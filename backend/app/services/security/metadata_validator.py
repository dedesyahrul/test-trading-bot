"""Deterministic checks for malformed and impersonating token metadata."""

import re

from app.services.security.models import MetadataCheckResult


class MetadataValidator:
    """Reject malformed symbols and non-canonical reserved token symbols."""

    SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,12}$")
    CANONICAL = {
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "SOL": "So11111111111111111111111111111111111111112",
        "WSOL": "So11111111111111111111111111111111111111112",
    }

    async def validate(self, name: str | None, symbol: str | None, address: str) -> MetadataCheckResult:
        normalized_name = (name or "").strip()
        normalized_symbol = (symbol or "").strip().upper()
        if not self.SYMBOL_PATTERN.fullmatch(normalized_symbol):
            return MetadataCheckResult(
                is_blocked=True,
                block_reason="Invalid token symbol format",
                risk_score=100,
                name=normalized_name,
                symbol=normalized_symbol,
                reasons=["Symbol must contain 2-12 uppercase alphanumeric characters"],
            )
        canonical_address = self.CANONICAL.get(normalized_symbol)
        if canonical_address and address != canonical_address:
            return MetadataCheckResult(
                is_blocked=True,
                block_reason=f"Token impersonates {normalized_symbol}",
                risk_score=100,
                name=normalized_name,
                symbol=normalized_symbol,
                spoofed_symbol=normalized_symbol,
                reasons=[f"Reserved symbol {normalized_symbol} uses a non-canonical address"],
            )
        return MetadataCheckResult(
            is_blocked=False,
            risk_score=0,
            name=normalized_name,
            symbol=normalized_symbol,
            reasons=["Metadata format valid"],
        )
