"""Deterministic chart intelligence from OHLCV candles.

No chart conclusion is produced until enough timestamped candles exist.
"""
from dataclasses import dataclass
from decimal import Decimal
from statistics import mean


@dataclass(frozen=True)
class ChartAssessment:
    trend: str
    behavior: str
    rsi: float | None
    atr: float | None
    ema_fast: float | None
    ema_slow: float | None
    volume_ratio: float | None
    candle_pattern: str
    entry_allowed: bool
    reasons: list[str]


class ChartIntelligence:
    @staticmethod
    def _value(candle, key):
        return candle.get(key) if isinstance(candle, dict) else getattr(candle, key)

    @staticmethod
    def _ema(values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        result = mean(values[:period])
        multiplier = 2 / (period + 1)
        for value in values[period:]:
            result = (value - result) * multiplier + result
        return result

    @staticmethod
    def assess(candles: list) -> ChartAssessment:
        if len(candles) < 21:
            return ChartAssessment("UNKNOWN", "INSUFFICIENT_DATA", None, None, None, None, None, "UNKNOWN", False, ["At least 21 candles are required"])
        ordered = sorted(candles, key=lambda candle: ChartIntelligence._value(candle, "timestamp"))
        closes = [float(ChartIntelligence._value(c, "close")) for c in ordered]
        highs = [float(ChartIntelligence._value(c, "high")) for c in ordered]
        lows = [float(ChartIntelligence._value(c, "low")) for c in ordered]
        volumes = [float(ChartIntelligence._value(c, "volume") or 0) for c in ordered]
        fast = ChartIntelligence._ema(closes, 9)
        slow = ChartIntelligence._ema(closes, 21)
        true_ranges = [max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])) for i in range(1, len(closes))]
        atr = mean(true_ranges[-14:]) if len(true_ranges) >= 14 else None
        gains = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
        losses = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
        avg_gain = mean(gains[-14:]); avg_loss = mean(losses[-14:])
        rsi = 100.0 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
        baseline_volume = mean(volumes[-21:-1])
        volume_ratio = volumes[-1] / baseline_volume if baseline_volume > 0 else None
        last = ordered[-1]
        last_open = float(ChartIntelligence._value(last, "open")); last_close = float(ChartIntelligence._value(last, "close")); last_high = float(ChartIntelligence._value(last, "high")); last_low = float(ChartIntelligence._value(last, "low"))
        body = abs(last_close - last_open)
        candle_range = max(last_high - last_low, 1e-12)
        upper_wick = last_high - max(last_open, last_close)
        lower_wick = min(last_open, last_close) - last_low
        pattern = "LONG_UPPER_WICK" if upper_wick / candle_range > 0.45 else "LONG_LOWER_WICK" if lower_wick / candle_range > 0.45 else "BULLISH" if last_close > last_open else "BEARISH"
        trend = "BULLISH" if fast and slow and fast > slow and closes[-1] > fast else "BEARISH" if fast and slow and fast < slow and closes[-1] < fast else "RANGE"
        behavior = "BREAKDOWN" if trend == "BEARISH" and rsi < 40 else "EUPHORIA" if rsi > 78 and (volume_ratio or 0) > 2 else "MOMENTUM" if trend == "BULLISH" and (volume_ratio or 0) >= 1 else "DISTRIBUTION" if pattern == "LONG_UPPER_WICK" else "ACCUMULATION"
        reasons = [f"Trend: {trend}", f"Behavior: {behavior}", f"RSI: {rsi:.1f}"]
        if volume_ratio is not None: reasons.append(f"Volume ratio: {volume_ratio:.2f}x")
        allowed = trend != "BEARISH" and behavior not in {"BREAKDOWN", "EUPHORIA", "DISTRIBUTION"}
        if not allowed: reasons.append("Chart conditions do not support a new entry")
        return ChartAssessment(trend, behavior, rsi, atr, fast, slow, volume_ratio, pattern, allowed, reasons)
