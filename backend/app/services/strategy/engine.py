import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Signal, Feature, RiskAssessment, MarketSnapshot, Prediction
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Standard trading signal object."""
    pair_id: str
    strategy_id: str
    signal_type: str  # BUY, SELL, HOLD, SKIP
    confidence: float  # 0.0 to 1.0
    reasons_pro: list[str]
    reasons_contra: list[str]
    recommended_size: Optional[float] = None
    target_tp: Optional[Decimal] = None
    target_sl: Optional[Decimal] = None


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    def __init__(self, strategy_id: str, parameters: dict):
        self.strategy_id = strategy_id
        self.parameters = parameters

    @abstractmethod
    async def evaluate(
        self,
        pair_id: str,
        market_snapshot: MarketSnapshot,
        feature: Optional[Feature],
        risk_assessment: Optional[RiskAssessment],
        prediction: Optional["Prediction"] = None,
    ) -> TradingSignal:
        """Evaluate market conditions and return trading signal."""
        pass

    def calculate_position_size(
        self,
        risk_score: float,
        balance: Decimal,
        confidence: float,
        base_allocation_pct: float = 0.02,
    ) -> float:
        """Calculate position size using risk-adjusted Kelly Criterion."""
        base_allocation = balance * Decimal(str(base_allocation_pct))
        risk_modifier = (100 - risk_score) / 100
        confidence_modifier = max(0.5, min(1.0, confidence))  # Clamp 0.5 to 1.0
        
        final_size = base_allocation * Decimal(str(risk_modifier)) * Decimal(str(confidence_modifier))
        return float(final_size)


class MomentumStrategy(BaseStrategy):
    """Pure momentum strategy - detects breakouts without ML."""

    async def evaluate(
        self,
        pair_id: str,
        market_snapshot: MarketSnapshot,
        feature: Optional[Feature],
        risk_assessment: Optional[RiskAssessment],
        prediction: Optional[Prediction] = None,
    ) -> TradingSignal:
        """Evaluate momentum signals."""
        
        reasons_pro = []
        reasons_contra = []
        signal_type = "HOLD"
        confidence = 0.0

        # Check minimum volume
        min_volume_24h = self.parameters.get("min_volume_24h", 50000)
        if market_snapshot.volume_24h_usd and float(market_snapshot.volume_24h_usd) < min_volume_24h:
            reasons_contra.append(f"Volume too low: ${float(market_snapshot.volume_24h_usd):,.0f} < ${min_volume_24h:,.0f}")
            signal_type = "SKIP"

        # Check price change
        min_price_change = self.parameters.get("min_price_change_5m", 0.05)  # 5%
        if feature and feature.return_5m:
            price_change = float(feature.return_5m)
            if price_change > min_price_change:
                reasons_pro.append(f"Strong 5m price change: {price_change*100:.2f}%")
                confidence += 0.3
            else:
                reasons_contra.append(f"Insufficient price change: {price_change*100:.2f}% < {min_price_change*100:.2f}%")

        # Check volume spike
        if feature and feature.volume_spike:
            volume_spike = float(feature.volume_spike)
            min_spike = self.parameters.get("min_volume_spike", 2.0)
            if volume_spike > min_spike:
                reasons_pro.append(f"Volume spike detected: {volume_spike:.1f}x")
                confidence += 0.2
            else:
                reasons_contra.append(f"Insufficient volume spike: {volume_spike:.1f}x < {min_spike:.1f}x")

        # Check buy/sell ratio
        if feature and feature.buy_sell_ratio_1h:
            buy_sell_ratio = float(feature.buy_sell_ratio_1h)
            min_ratio = self.parameters.get("min_buy_sell_ratio", 1.2)
            if buy_sell_ratio > min_ratio:
                reasons_pro.append(f"Positive buy/sell ratio: {buy_sell_ratio:.2f}")
                confidence += 0.2
            else:
                reasons_contra.append(f"Poor buy/sell ratio: {buy_sell_ratio:.2f} < {min_ratio:.2f}")

        # Check risk score
        max_risk_score = self.parameters.get("max_risk_score", 50)
        if risk_assessment and float(risk_assessment.risk_score) > max_risk_score:
            reasons_contra.append(f"Risk score too high: {float(risk_assessment.risk_score):.0f} > {max_risk_score}")
            signal_type = "SKIP"
        elif risk_assessment:
            reasons_pro.append(f"Risk acceptable: {float(risk_assessment.risk_score):.0f}")

        # Final decision
        if signal_type != "SKIP" and confidence >= 0.5:
            signal_type = "BUY"
        elif signal_type == "HOLD" and confidence < 0.3:
            signal_type = "SKIP"

        # Calculate take profit and stop loss
        target_tp = None
        target_sl = None
        if signal_type == "BUY" and market_snapshot.price_usd:
            tp_pct = self.parameters.get("take_profit_pct", 0.20)
            sl_pct = self.parameters.get("stop_loss_pct", 0.10)
            target_tp = market_snapshot.price_usd * Decimal(str(1 + tp_pct))
            target_sl = market_snapshot.price_usd * Decimal(str(1 - sl_pct))

        return TradingSignal(
            pair_id=pair_id,
            strategy_id=self.strategy_id,
            signal_type=signal_type,
            confidence=confidence,
            reasons_pro=reasons_pro,
            reasons_contra=reasons_contra,
            target_tp=target_tp,
            target_sl=target_sl,
        )


class MLAssistedStrategy(BaseStrategy):
    """ML-assisted sniper strategy — uses LightGBM prediction when model is available."""

    async def evaluate(
        self,
        pair_id: str,
        market_snapshot: MarketSnapshot,
        feature: Optional[Feature],
        risk_assessment: Optional[RiskAssessment],
        prediction: Optional[Prediction] = None,
    ) -> TradingSignal:
        from app.core.config import settings
        from app.services.prediction.engine import PredictionEngine

        reasons_pro = []
        reasons_contra = []
        signal_type = "HOLD"
        confidence = 0.0

        min_volume_24h = self.parameters.get("min_volume_24h", 50000)
        if market_snapshot.volume_24h_usd and float(market_snapshot.volume_24h_usd) < min_volume_24h:
            reasons_contra.append("Volume too low")
            signal_type = "SKIP"
        else:
            reasons_pro.append("Adequate volume")
            confidence += 0.15

        max_risk_score = self.parameters.get("max_risk_score", 40)
        if risk_assessment and float(risk_assessment.risk_score) > max_risk_score:
            reasons_contra.append(f"Risk too high: {float(risk_assessment.risk_score):.0f}")
            signal_type = "SKIP"
        elif risk_assessment:
            confidence += 0.2

        ml_threshold = self.parameters.get(
            "ml_probability_threshold", settings.ML_PREDICTION_THRESHOLD
        )

        if prediction and PredictionEngine.is_available():
            prob = float(prediction.probability)
            if prob >= ml_threshold:
                reasons_pro.append(f"ML probability {prob:.1%} >= {ml_threshold:.0%}")
                confidence += prob * 0.5
            else:
                reasons_contra.append(f"ML probability {prob:.1%} < {ml_threshold:.0%}")
                if signal_type != "SKIP":
                    signal_type = "SKIP"
        elif PredictionEngine.is_available():
            reasons_contra.append("No ML prediction available")
        else:
            reasons_pro.append("ML model not trained — using risk/volume only")
            confidence += 0.15

        if signal_type != "SKIP" and confidence >= 0.5:
            signal_type = "BUY"
        elif signal_type == "HOLD" and confidence < 0.3:
            signal_type = "SKIP"

        target_tp = None
        target_sl = None
        if signal_type == "BUY" and market_snapshot.price_usd:
            tp_pct = self.parameters.get("take_profit_pct", 0.15)
            sl_pct = self.parameters.get("stop_loss_pct", 0.10)
            target_tp = market_snapshot.price_usd * Decimal(str(1 + tp_pct))
            target_sl = market_snapshot.price_usd * Decimal(str(1 - sl_pct))

        return TradingSignal(
            pair_id=pair_id,
            strategy_id=self.strategy_id,
            signal_type=signal_type,
            confidence=min(confidence, 1.0),
            reasons_pro=reasons_pro,
            reasons_contra=reasons_contra,
            target_tp=target_tp,
            target_sl=target_sl,
        )


class StrategyRunner:
    """Orchestrates strategy execution."""

    def __init__(self):
        self.strategies = {}

    def register_strategy(self, strategy: BaseStrategy):
        """Register a strategy."""
        self.strategies[strategy.strategy_id] = strategy
        logger.info(f"Strategy registered: {strategy.strategy_id}")

    def clear_strategies(self):
        """Remove all registered strategies."""
        self.strategies.clear()

    async def load_from_db(self, session: AsyncSession) -> None:
        """Load active strategies from database settings."""
        from app.services.settings.service import SettingsService

        self.clear_strategies()
        db_strategies = await SettingsService.get_all_strategies(session)
        for db_strategy in db_strategies:
            if not db_strategy.is_active:
                continue
            params = db_strategy.parameters or {}
            if db_strategy.strategy_type == "momentum":
                self.register_strategy(
                    MomentumStrategy(strategy_id=db_strategy.strategy_key, parameters=params)
                )
            elif db_strategy.strategy_type == "ml_assisted":
                self.register_strategy(
                    MLAssistedStrategy(strategy_id=db_strategy.strategy_key, parameters=params)
                )
            else:
                logger.warning("Unknown strategy type: %s", db_strategy.strategy_type)

        if not self.strategies:
            logger.warning("No active strategies in DB, using defaults")
            self._register_defaults()

    def _register_defaults(self):
        """Register hardcoded defaults as fallback."""
        self.register_strategy(
            MomentumStrategy(
                strategy_id="momentum_v1",
                parameters={
                    "min_volume_24h": 50000,
                    "min_price_change_5m": 0.05,
                    "min_volume_spike": 2.0,
                    "min_buy_sell_ratio": 1.2,
                    "max_risk_score": 50,
                    "take_profit_pct": 0.20,
                    "stop_loss_pct": 0.10,
                },
            )
        )
        self.register_strategy(
            MLAssistedStrategy(
                strategy_id="ml_sniper_v1",
                parameters={
                    "min_volume_24h": 50000,
                    "max_risk_score": 40,
                    "take_profit_pct": 0.15,
                    "stop_loss_pct": 0.10,
                },
            )
        )

    async def evaluate_all(
        self,
        pair_id: str,
        market_snapshot: MarketSnapshot,
        feature: Optional[Feature],
        risk_assessment: Optional[RiskAssessment],
        prediction: Optional[Prediction] = None,
    ) -> list[TradingSignal]:
        """Run all registered strategies and return signals."""
        signals = []
        for strategy_id, strategy in self.strategies.items():
            try:
                signal = await strategy.evaluate(
                    pair_id, market_snapshot, feature, risk_assessment, prediction
                )
                signals.append(signal)
            except Exception as e:
                logger.error(f"Error evaluating strategy {strategy_id}: {e}")
        return signals


# Initialize default strategy runner (loaded from DB at worker runtime)
strategy_runner = StrategyRunner()
strategy_runner._register_defaults()
