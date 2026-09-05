"""Tests for the read-only Solana RPC adapter using mocked responses."""

import pytest

from app.adapters.solana_rpc import SolanaRPCClient
from app.adapters.solana_rpc import TOKEN_2022_PROGRAM_ID


@pytest.mark.asyncio
async def test_get_mint_parses_supply_and_authorities(monkeypatch):
    client = SolanaRPCClient(rpc_url="http://rpc.test")
    responses = [
        {"value": {"amount": "1000000", "decimals": 6, "uiAmount": 1.0}},
        {"value": {"owner": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss82G2j1", "data": {"parsed": {"type": "mint", "info": {
            "mintAuthority": "authority",
            "freezeAuthority": None,
        }}}}},
    ]

    async def fake_call(method, params):
        return responses.pop(0)

    monkeypatch.setattr(client, "_call", fake_call)
    result = await client.get_mint("mint")

    assert result == {
        "supply": 1.0,
        "raw_supply": 1000000,
        "decimals": 6,
        "mint_authority": "authority",
        "freeze_authority": None,
        "program_id": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss82G2j1",
        "extensions": [],
    }


@pytest.mark.asyncio
async def test_get_top_holders_limits_and_normalizes(monkeypatch):
    client = SolanaRPCClient(rpc_url="http://rpc.test")

    async def fake_call(method, params):
        if method == "getTokenLargestAccounts":
            return {"value": [{"address": "account-1", "uiAmount": 75}]}
        return {"value": {"data": {"parsed": {"info": {"owner": "holder-1"}}}}}

    monkeypatch.setattr(client, "_call", fake_call)
    result = await client.get_top_holders("mint", limit=1)

    assert result == [{"address": "holder-1", "token_account": "account-1", "balance": 75.0, "is_frozen": False}]


@pytest.mark.asyncio
async def test_get_mint_rejects_unknown_program(monkeypatch):
    client = SolanaRPCClient(rpc_url="http://rpc.test")

    async def fake_call(method, params):
        if method == "getTokenSupply":
            return {"value": {"amount": "1", "decimals": 0, "uiAmount": 1}}
        return {"value": {"owner": "unknown", "data": {"parsed": {"type": "mint", "info": {}}}}}

    monkeypatch.setattr(client, "_call", fake_call)
    assert await client.get_mint("mint") is None


def test_rpc_urls_are_configurable(monkeypatch):
    monkeypatch.setattr("app.adapters.solana_rpc.settings.SOLANA_RPC_URLS", "http://one,http://two")
    client = SolanaRPCClient()
    assert client.rpc_urls == ["http://one", "http://two"]


@pytest.mark.asyncio
async def test_get_mint_accepts_parsed_response_without_type(monkeypatch):
    client = SolanaRPCClient(rpc_url="http://rpc.test")
    async def fake_call(method, params):
        if method == "getTokenSupply":
            return {"value": {"amount": "1", "decimals": 0, "uiAmount": 1}}
        return {"value": {"owner": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss82G2j1", "data": {"parsed": {"info": {}}}}}
    monkeypatch.setattr(client, "_call", fake_call)
    result = await client.get_mint("mint")
    assert result["program_id"] == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss82G2j1"


@pytest.mark.asyncio
async def test_get_mint_accepts_token_2022_program(monkeypatch):
    client = SolanaRPCClient(rpc_url="http://rpc.test")

    async def fake_call(method, params):
        if method == "getTokenSupply":
            return {"value": {"amount": "1000", "decimals": 0, "uiAmount": 1000}}
        return {"value": {"owner": TOKEN_2022_PROGRAM_ID, "data": {"parsed": {
            "type": "mint", "info": {"extensions": []}
        }}}}

    monkeypatch.setattr(client, "_call", fake_call)
    result = await client.get_mint("pump-mint")
    assert result["program_id"] == TOKEN_2022_PROGRAM_ID
