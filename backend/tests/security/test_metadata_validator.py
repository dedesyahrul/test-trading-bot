import pytest

from app.services.security.metadata_validator import MetadataValidator


@pytest.mark.asyncio
async def test_reserved_symbol_with_wrong_address_is_blocked():
    result = await MetadataValidator().validate("USD Coin", "USDC", "fake-mint")
    assert result.is_blocked is True
    assert result.spoofed_symbol == "USDC"


@pytest.mark.asyncio
async def test_normal_symbol_is_allowed():
    result = await MetadataValidator().validate("Meme", "MEME", "mint")
    assert result.is_blocked is False
