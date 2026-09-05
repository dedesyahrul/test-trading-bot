"""Regression tests for nullable market enrichment values."""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.market import _enrich_pair


@pytest.mark.asyncio
async def test_enrich_pair_without_snapshot_returns_nullable_values(monkeypatch):
    pair = SimpleNamespace(
        id="pair-id",
        chain_id="solana",
        base_token_id="base-id",
        quote_token_id="quote-id",
        dex_name="raydium",
        price_usd=None,
        liquidity_usd=None,
        is_watched=False,
        created_at=None,
        updated_at=None,
    )
    tokens = {
        "base-id": SimpleNamespace(symbol="MEME"),
        "quote-id": SimpleNamespace(symbol="SOL"),
    }
    risk_result = SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: None))
    signal_result = SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: None))
    session = SimpleNamespace(
        get=AsyncMock(side_effect=lambda _, key: tokens.get(key)),
        execute=AsyncMock(side_effect=[risk_result, signal_result]),
    )
    monkeypatch.setattr(
        "app.api.market.MarketDataService.get_latest_snapshot",
        AsyncMock(return_value=None),
    )

    result = await _enrich_pair(session, pair)

    assert result["price_usd"] is None
    assert result["liquidity_usd"] is None
    assert result["price_change_24h"] is None
    assert result["volume_24h_usd"] is None
