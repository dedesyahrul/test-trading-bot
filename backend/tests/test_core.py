"""Unit tests for pure logic (no database required)."""

import importlib.util
import math
from decimal import Decimal
from pathlib import Path
import pytest
from datetime import datetime, timedelta

BACKEND_ROOT = Path(__file__).parent.parent


def _load_module(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND_ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


risk_engine = _load_module("risk_engine", "app/services/risk/engine.py")
features_engine = _load_module("features_engine", "app/services/features/engine.py")

RiskEngine = risk_engine.RiskEngine
FeatureEngineering = features_engine.FeatureEngineering
from app.services.data_quality import DataQualityService, DataQualityStatus
from app.services.audit import _redact
from app.services.risk.decision import RiskDecisionService
from app.services.decision_score import DecisionScoreService
from app.services.trading.adaptive_exit import AdaptiveExitService
from app.adapters.dexscreener import DEXScreenerClient
from app.adapters.geckoterminal import GeckoTerminalClient
from app.services.chart_intelligence import ChartIntelligence


class FakeSnapshot:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_liquidity_risk_critical():
    snap = FakeSnapshot(liquidity_usd=500)
    assert RiskEngine._calculate_liquidity_risk(snap) == 100


def test_liquidity_risk_low():
    snap = FakeSnapshot(liquidity_usd=200000)
    assert RiskEngine._calculate_liquidity_risk(snap) == 0


def test_manipulation_risk_balanced():
    snap = FakeSnapshot(buy_count_24h=100, sell_count_24h=80)
    score = RiskEngine._calculate_manipulation_risk(snap)
    assert score < 50


def test_hard_constraint_zero_liquidity():
    snap = FakeSnapshot(liquidity_usd=0, buy_count_24h=0, sell_count_24h=0, volume_24h_usd=1000)
    is_blocked, reason = RiskEngine._check_hard_constraints(snap)
    assert is_blocked is True
    assert "Liquidity" in reason


def test_buy_sell_ratio():
    assert FeatureEngineering._compute_buy_sell_ratio(100, 50) == 2.0
    assert FeatureEngineering._compute_buy_sell_ratio(100, 0) == 100.0


def test_buy_pressure():
    assert FeatureEngineering._compute_buy_pressure(75, 25) == 0.75


def test_volatility_empty():
    assert FeatureEngineering._compute_volatility([]) is None


def test_momentum_calculation():
    snaps = [
        FakeSnapshot(price_usd=Decimal("1.0")),
        FakeSnapshot(price_usd=Decimal("1.1")),
    ]
    momentum = FeatureEngineering._compute_momentum(snaps)
    assert momentum == pytest.approx(0.1)


def test_data_quality_rejects_stale_snapshot():
    snapshot = FakeSnapshot(
        timestamp=datetime.utcnow() - timedelta(minutes=10),
        price_usd=Decimal("1"), liquidity_usd=Decimal("10000"),
        volume_24h_usd=Decimal("10000"),
    )
    status, reasons = DataQualityService.assess(snapshot)
    assert status == DataQualityStatus.STALE
    assert reasons


def test_risk_decision_reduces_size_for_thin_liquidity():
    decision = RiskDecisionService.decide(35, "MEDIUM", 3000, 0.2)
    assert decision.decision == "REDUCE_SIZE"
    assert decision.size_usd == Decimal("312.5")


def test_risk_decision_rejects_unsafe_liquidity():
    decision = RiskDecisionService.decide(10, "LOW", 500, 0.1)
    assert decision.decision == "EMERGENCY"
    assert decision.size_usd == Decimal("0")


def test_audit_details_redact_secrets():
    details = _redact({"username": "alice", "access_token": "jwt", "nested": {"private_key": "secret"}})
    assert details == {
        "username": "alice",
        "access_token": "[REDACTED]",
        "nested": {"private_key": "[REDACTED]"},
    }


def test_decision_score_is_bounded_and_transparent():
    score = DecisionScoreService.calculate(0.10, 100000, 100000, 1.0, 0)
    assert score == 95.0


def test_risk_budget_limits_position_size():
    decision = RiskDecisionService.decide(20, "LOW", 100000, 0.2, max_position_usd=Decimal("1000"))
    assert decision.size_usd == Decimal("625")


def test_adaptive_levels_widen_with_volatility():
    calm_stop, calm_target = AdaptiveExitService.levels(Decimal("100"), Decimal("0"), Decimal("100000"))
    volatile_stop, volatile_target = AdaptiveExitService.levels(Decimal("100"), Decimal("0.4"), Decimal("100000"))
    assert volatile_stop < calm_stop
    assert volatile_target > calm_target


def test_dexscreener_normalizes_official_pair_shape():
    normalized = DEXScreenerClient.normalize_pair_data({
        "chainId": "solana",
        "dexId": "pumpswap",
        "pairAddress": "pair-1",
        "baseToken": {"address": "token-1", "symbol": "TEST", "name": "Test"},
        "quoteToken": {"address": "sol", "symbol": "SOL", "name": "Solana"},
        "priceUsd": "1.25",
        "liquidity": {"usd": 10000},
        "volume": {"h24": 50000},
        "priceChange": {"m5": 2.0},
        "txns": {"h24": {"buys": 10, "sells": 5}},
    })
    assert normalized["chain"] == "solana"
    assert normalized["pair_address"] == "pair-1"
    assert normalized["price_usd"] == Decimal("1.25")


def test_geckoterminal_normalizes_pool_shape():
    normalized = GeckoTerminalClient.normalize_pool({
        "attributes": {
            "address": "pool-1", "name": "TEST / SOL", "base_token_price_usd": "1.25",
            "reserve_in_usd": "10000", "volume_usd": {"h24": "50000"},
            "price_change_percentage": {"m5": "2.0"},
            "transactions": {"h24": {"buys": 10, "sells": 5}},
        },
        "relationships": {
            "base_token": {"data": {"id": "solana_token-1"}},
            "quote_token": {"data": {"id": "solana_sol"}},
        },
    })
    assert normalized["provider"] == "geckoterminal"
    assert normalized["pair_address"] == "pool-1"
    assert normalized["price_usd"] == Decimal("1.25")


def test_chart_intelligence_requires_history():
    result = ChartIntelligence.assess([])
    assert result.entry_allowed is False
    assert result.behavior == "INSUFFICIENT_DATA"


def test_chart_intelligence_detects_bullish_candles():
    candles = [FakeSnapshot(timestamp=datetime.utcnow() + timedelta(minutes=i), open=Decimal(str(1 + i * 0.01)), high=Decimal(str(1.02 + i * 0.01)), low=Decimal(str(0.99 + i * 0.01)), close=Decimal(str(1.01 + i * 0.01)), volume=1000) for i in range(25)]
    result = ChartIntelligence.assess(candles)
    assert result.trend == "BULLISH"
    assert result.entry_allowed is True
