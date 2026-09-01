"""Transparent decision score from observable market inputs only."""


class DecisionScoreService:
    @staticmethod
    def calculate(momentum: float | None, volume: float | None, liquidity: float | None,
                  prediction: float | None, risk_score: float, market_factor: float = 0.5) -> float:
        def clamp(value: float) -> float:
            return max(0.0, min(1.0, value))

        momentum_score = clamp((momentum or 0.0) / 0.10)
        volume_score = clamp((volume or 0.0) / 100000.0)
        liquidity_score = clamp((liquidity or 0.0) / 100000.0)
        prediction_score = clamp(prediction if prediction is not None else 0.5)
        risk_score_normalized = 1.0 - clamp(risk_score / 100.0)
        return round(100 * (
            momentum_score * 0.25 + volume_score * 0.15 + liquidity_score * 0.20
            + market_factor * 0.10 + prediction_score * 0.10 + risk_score_normalized * 0.20
        ), 2)
