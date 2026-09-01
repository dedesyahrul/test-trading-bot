"""ML prediction inference engine."""

import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feature, Prediction

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parents[3] / "models" / "artifacts"
DEFAULT_MODEL = "momentum_scalp_v1.pkl"

FEATURE_COLUMNS = [
    "return_1m", "return_5m", "return_1h",
    "volatility_1h", "momentum_1h",
    "volume_growth_1h", "volume_acceleration", "volume_spike",
    "buy_sell_ratio_1h", "buy_pressure",
    "liquidity_change", "liquidity_ratio",
]


class PredictionEngine:
    """Load LightGBM model and run inference on features."""

    _model = None
    _model_version = "v1"
    _model_id = "momentum_scalp"

    @classmethod
    def _load_model(cls):
        if cls._model is not None:
            return cls._model

        model_path = MODEL_DIR / DEFAULT_MODEL
        if not model_path.exists():
            logger.warning("ML model not found at %s — inference disabled", model_path)
            return None

        cls._model = joblib.load(model_path)
        logger.info("ML model loaded: %s", model_path)
        return cls._model

    @staticmethod
    def _feature_vector(feature: Feature) -> np.ndarray:
        values = []
        for col in FEATURE_COLUMNS:
            val = getattr(feature, col, None)
            values.append(float(val) if val is not None else 0.0)
        return np.array([values])

    @classmethod
    async def predict(
        cls,
        session: AsyncSession,
        pair_id,
        feature: Feature,
        prediction_type: str = "momentum_scalp_15m",
    ) -> Optional[Prediction]:
        """Run inference and persist prediction."""
        model = cls._load_model()
        if model is None or feature is None:
            return None

        try:
            X = cls._feature_vector(feature)
            proba = model.predict_proba(X)[0]
            probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
            confidence = abs(probability - 0.5) * 2

            prediction = Prediction(
                pair_id=pair_id,
                model_id=cls._model_id,
                model_version=cls._model_version,
                prediction_type=prediction_type,
                probability=Decimal(str(round(probability, 4))),
                confidence=Decimal(str(round(confidence, 4))),
                reason=f"ML probability={probability:.2%}",
            )
            session.add(prediction)
            await session.commit()
            await session.refresh(prediction)
            return prediction
        except Exception as e:
            logger.error("Prediction failed for pair %s: %s", pair_id, e)
            return None

    @classmethod
    def is_available(cls) -> bool:
        return (MODEL_DIR / DEFAULT_MODEL).exists()
