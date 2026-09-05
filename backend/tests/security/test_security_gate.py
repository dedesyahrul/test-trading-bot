"""Unit tests for security gate service."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.security.gate import SecurityGateService
from app.services.security.liquidity_guard import LiquidityGuard
from app.services.security.honeypot_detector import HoneypotDetector
from app.services.security.contract_analyzer import ContractAnalyzer
from app.services.security.holder_distribution import HolderDistributionAnalyzer


@pytest.fixture
def liquidity_guard():
    return LiquidityGuard()


@pytest.fixture
def honeypot_detector():
    return HoneypotDetector()


@pytest.fixture
def contract_analyzer():
    return ContractAnalyzer()


@pytest.fixture
def holder_analyzer():
    return HolderDistributionAnalyzer()


@pytest.fixture
def security_gate_service(liquidity_guard, honeypot_detector, contract_analyzer, holder_analyzer):
    return SecurityGateService(
        liquidity_guard=liquidity_guard,
        honeypot_detector=honeypot_detector,
        contract_analyzer=contract_analyzer,
        holder_analyzer=holder_analyzer,
    )


# ============================================================================
# Liquidity Guard Tests
# ============================================================================

@pytest.mark.asyncio
async def test_liquidity_guard_blocks_critical_low_liquidity(liquidity_guard):
    """Token with <$1k liquidity should be BLOCKED."""
    market_snapshot = {
        'liquidity_usd': 500,
        'trading_mode': 'SCAN',
        'buy_count_24h': 50,
        'sell_count_24h': 45,
    }
    
    result = await liquidity_guard.check(market_snapshot)
    
    assert result.is_blocked is True
    assert result.risk_score == 100
    assert "critical" in result.block_reason.lower()


@pytest.mark.asyncio
async def test_liquidity_guard_allows_high_liquidity(liquidity_guard):
    """Token with >$100k liquidity should PASS."""
    market_snapshot = {
        'liquidity_usd': 150000,
        'buy_count_24h': 50,
        'sell_count_24h': 45,
    }
    
    result = await liquidity_guard.check(market_snapshot)
    
    assert result.is_blocked is False
    assert result.risk_score == 10
    assert result.threshold_met is True


@pytest.mark.asyncio
async def test_liquidity_guard_medium_risk(liquidity_guard):
    """Token with $10k liquidity should be MEDIUM risk."""
    market_snapshot = {
        'liquidity_usd': 10000,
        'buy_count_24h': 50,
        'sell_count_24h': 45,
    }
    
    result = await liquidity_guard.check(market_snapshot)
    
    assert result.is_blocked is False
    assert result.risk_score == 60  # MEDIUM


@pytest.mark.asyncio
async def test_liquidity_guard_defers_missing_data(liquidity_guard):
    """Missing liquidity must defer a trade, not masquerade as zero liquidity."""
    result = await liquidity_guard.check({"buy_count_24h": 1, "sell_count_24h": 1})
    assert result.is_blocked is False
    assert result.is_unknown is True
    assert result.liquidity_usd is None


# ============================================================================
# Honeypot Detector Tests
# ============================================================================

@pytest.mark.asyncio
async def test_honeypot_detector_blocks_buy_only(honeypot_detector):
    """Token with 150 buys but 0 sells should be BLOCKED (honeypot)."""
    market_snapshot = {
        'liquidity_usd': 50000,
        'buy_count_24h': 150,
        'sell_count_24h': 0,
    }
    
    result = await honeypot_detector.check(market_snapshot)
    
    assert result.is_blocked is True
    assert result.risk_score == 90
    assert "honeypot" in result.block_reason.lower()


@pytest.mark.asyncio
async def test_honeypot_detector_allows_balanced_trading(honeypot_detector):
    """Token with balanced buy/sell should PASS."""
    market_snapshot = {
        'liquidity_usd': 50000,
        'buy_count_24h': 150,
        'sell_count_24h': 140,
    }
    
    result = await honeypot_detector.check(market_snapshot)
    
    assert result.is_blocked is False
    assert result.risk_score == 10  # Balanced ratio


@pytest.mark.asyncio
async def test_honeypot_detector_high_ratio(honeypot_detector):
    """Token with 10:1 buy/sell ratio should be HIGH RISK."""
    market_snapshot = {
        'liquidity_usd': 50000,
        'buy_count_24h': 100,
        'sell_count_24h': 10,
    }
    
    result = await honeypot_detector.check(market_snapshot)
    
    assert result.is_blocked is False
    assert result.risk_score == 90  # High risk


# ============================================================================
# Contract Analyzer Tests
# ============================================================================

@pytest.mark.asyncio
async def test_contract_analyzer_safe_contract(contract_analyzer):
    """Safe contract (no transfer fee, no mint authority) should PASS."""
    contract_analyzer.rpc.get_mint = AsyncMock(return_value={
        "supply": 1_000_000,
        "mint_authority": None,
        "freeze_authority": None,
    })
    result = await contract_analyzer.analyze("solana", "safe_token_123")
    
    assert result.is_blocked is False
    assert result.risk_score < 30
    assert result.has_transfer_fee is False
    assert result.mint_authority is None


# ============================================================================
# Holder Distribution Tests
# ============================================================================

@pytest.mark.asyncio
async def test_holder_analyzer_zero_supply_blocks(holder_analyzer):
    """Token with zero supply should be BLOCKED."""
    # Mock _get_total_supply to return 0
    with patch.object(holder_analyzer, '_get_total_supply', return_value=0):
        result = await holder_analyzer.analyze("solana", "zero_supply_token")
        
        assert result.is_blocked is True
        assert result.risk_score == 100


@pytest.mark.asyncio
async def test_holder_analyzer_blocks_concentrated_supply(holder_analyzer):
    """Top holders above the configured threshold should be blocked."""
    holder_analyzer.rpc.get_mint = AsyncMock(return_value={"supply": 1000})
    holder_analyzer.rpc.get_top_holders = AsyncMock(return_value=[
        {"address": "wallet-1", "balance": 900},
        {"address": "wallet-2", "balance": 50},
    ])

    result = await holder_analyzer.analyze("solana", "concentrated")

    assert result.is_blocked is True
    assert result.top_10_pct == 95


# ============================================================================
# Security Gate Service Tests
# ============================================================================

@pytest.mark.asyncio
async def test_security_gate_blocks_low_liquidity(security_gate_service):
    """SecurityGate should block tokens with <$1k liquidity."""
    market_snapshot = {
        'liquidity_usd': 500,
        'trading_mode': 'SCAN',
        'buy_count_24h': 50,
        'sell_count_24h': 45,
    }
    
    result = await security_gate_service.evaluate_token(
        chain="solana",
        token_address="low_liq_token",
        pair_address="pair_123",
        market_snapshot=market_snapshot,
    )
    
    assert result.is_blocked is True
    assert result.security_gate_score == 100
    assert "liquidity" in result.block_reason.lower()


@pytest.mark.asyncio
async def test_security_gate_blocks_honeypot(security_gate_service):
    """SecurityGate should block honeypot tokens (sells=0, buys>50)."""
    market_snapshot = {
        'liquidity_usd': 50000,
        'buy_count_24h': 150,
        'sell_count_24h': 0,
    }
    
    result = await security_gate_service.evaluate_token(
        chain="solana",
        token_address="honeypot_token",
        pair_address="pair_123",
        market_snapshot=market_snapshot,
    )
    
    assert result.is_blocked is True
    assert result.security_gate_score == 95
    assert "honeypot" in result.block_reason.lower()


@pytest.mark.asyncio
async def test_security_gate_defers_rpc_unavailable(security_gate_service):
    """Unavailable critical RPC data must prevent entry without labeling scam."""
    security_gate_service.contract_analyzer.analyze = AsyncMock(return_value=type("Result", (), {
        "is_blocked": False,
        "is_unknown": True,
        "risk_score": 100,
        "reasons": ["RPC unavailable"],
    })())
    result = await security_gate_service.evaluate_token(
        "solana", "mint", "pair", {"liquidity_usd": 50000, "buy_count_24h": 10, "sell_count_24h": 10}
    )
    assert result.is_blocked is False
    assert result.is_deferred is True


@pytest.mark.asyncio
async def test_security_gate_defers_missing_liquidity(security_gate_service):
    result = await security_gate_service.evaluate_token(
        "solana", "mint", "pair", {"liquidity_usd": None, "buy_count_24h": 2, "sell_count_24h": 2}
    )
    assert result.is_blocked is False
    assert result.is_deferred is True


@pytest.mark.asyncio
async def test_security_gate_does_not_treat_zero_as_missing(security_gate_service):
    """Explicit zero remains a hard liquidity block; only None is deferred."""
    result = await security_gate_service.evaluate_token(
        "solana", "mint", "pair", {"liquidity_usd": 0, "buy_count_24h": 0, "sell_count_24h": 0}
    )
    assert result.is_blocked is True
    assert result.is_deferred is False


@pytest.mark.asyncio
async def test_dexscreener_liquidity_is_preserved(security_gate_service):
    """A valid Dexscreener liquidity value must reach the guard unchanged."""
    result = await security_gate_service.liquidity_guard.check({
        "liquidity_usd": 25000,
        "buy_count_24h": 20,
        "sell_count_24h": 18,
    })
    assert result.is_blocked is False
    assert result.liquidity_usd == 25000
    assert result.threshold_met is True


@pytest.mark.asyncio
async def test_explicit_low_dexscreener_liquidity_is_blocked(security_gate_service):
    """A real low Dexscreener reserve remains a valid hard block."""
    result = await security_gate_service.evaluate_token(
        "solana", "mint", "pair", {"liquidity_usd": 230.45, "buy_count_24h": 4, "sell_count_24h": 3}
    )
    assert result.status == "BLOCKED"
    assert "230.45" in result.reason


@pytest.mark.asyncio
async def test_paper_mode_requires_one_thousand_liquidity(liquidity_guard):
    result = await liquidity_guard.check({
        "liquidity_usd": 3000,
        "trading_mode": "PAPER",
        "buy_count_24h": 10,
        "sell_count_24h": 10,
    })
    assert result.is_blocked is False
    assert result.threshold_met is True


@pytest.mark.asyncio
async def test_scan_mode_accepts_one_thousand_liquidity(liquidity_guard):
    result = await liquidity_guard.check({
        "liquidity_usd": 1200,
        "trading_mode": "SCAN",
        "buy_count_24h": 10,
        "sell_count_24h": 10,
    })
    assert result.is_blocked is False
    assert result.threshold_met is True


@pytest.mark.asyncio
async def test_position_size_cannot_exceed_pool_percentage(security_gate_service):
    result = await security_gate_service.evaluate_token(
        "solana",
        "mint",
        "pair",
        {"liquidity_usd": 10000, "buy_count_24h": 10, "sell_count_24h": 10, "trading_mode": "PAPER"},
        position_size_usd=600,
    )
    assert result.is_blocked is True
    assert "liquidity" in result.reason.lower()


@pytest.mark.asyncio
async def test_gate_status_and_reason_never_return_none(security_gate_service):
    result = await security_gate_service.evaluate_token(
        "solana", "mint", "pair", {"liquidity_usd": None, "buy_count_24h": 0, "sell_count_24h": 0}
    )
    assert result.status == "DEFERRED"
    assert result.reason


@pytest.mark.asyncio
async def test_security_gate_allows_legitimate_token(security_gate_service):
    """SecurityGate should allow legitimate tokens."""
    market_snapshot = {
        'liquidity_usd': 100000,
        'buy_count_24h': 150,
        'sell_count_24h': 140,
    }
    
    # Mock contract and holder analyzers to return safe results
    with patch.object(security_gate_service.contract_analyzer, 'analyze') as mock_contract:
        with patch.object(security_gate_service.holder_analyzer, 'analyze') as mock_holders:
            mock_contract.return_value = type('obj', (object,), {
                'is_blocked': False,
                'risk_score': 10,
                'reasons': []
            })()
            mock_holders.return_value = type('obj', (object,), {
                'is_blocked': False,
                'risk_score': 5,
                'reasons': []
            })()
            
            result = await security_gate_service.evaluate_token(
                chain="solana",
                token_address="legitimate_token",
                pair_address="pair_123",
                market_snapshot=market_snapshot,
            )
            
            assert result.is_blocked is False
            assert result.security_gate_score < 40  # Low risk
            assert result.passed_at is not None


@pytest.mark.asyncio
async def test_security_gate_score_calculation(security_gate_service):
    """SecurityGate should calculate weighted security score correctly."""
    market_snapshot = {
        'liquidity_usd': 100000,
        'buy_count_24h': 150,
        'sell_count_24h': 140,
    }
    
    with patch.object(security_gate_service.contract_analyzer, 'analyze') as mock_contract:
        with patch.object(security_gate_service.holder_analyzer, 'analyze') as mock_holders:
            mock_contract.return_value = type('obj', (object,), {
                'is_blocked': False,
                'risk_score': 20,
                'reasons': []
            })()
            mock_holders.return_value = type('obj', (object,), {
                'is_blocked': False,
                'risk_score': 30,
                'reasons': []
            })()
            
            result = await security_gate_service.evaluate_token(
                chain="solana",
                token_address="test_token",
                pair_address="pair_123",
                market_snapshot=market_snapshot,
            )
            
            # Expected: (10*0.25 + 10*0.25 + 20*0.25 + 30*0.25) = 17.5 ≈ 18
            assert 15 <= result.security_gate_score <= 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
