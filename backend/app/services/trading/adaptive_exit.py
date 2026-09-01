"""Conservative, data-driven exit calculations.

This service is deliberately deterministic and does not claim predictive certainty.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ExitAssessment:
    action: str
    pressure: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    trail_price: Decimal
    reason: str
    fraction: Decimal = Decimal("1")


class AdaptiveExitService:
    @staticmethod
    def levels(entry_price: Decimal, volatility: Decimal | None, liquidity_usd: Decimal | None) -> tuple[Decimal, Decimal]:
        vol = max(Decimal("0"), volatility or Decimal("0"))
        stop_distance = min(Decimal("0.15"), max(Decimal("0.06"), Decimal("0.06") + vol * Decimal("0.50")))
        # Thin liquidity gets a closer target so exposure is not held indefinitely.
        target_distance = min(Decimal("0.30"), max(Decimal("0.10"), Decimal("0.10") + vol * Decimal("0.80")))
        if liquidity_usd is not None and liquidity_usd < Decimal("5000"):
            target_distance = min(target_distance, Decimal("0.14"))
        return entry_price * (Decimal("1") - stop_distance), entry_price * (Decimal("1") + target_distance)

    @staticmethod
    def assess(position, snapshot) -> ExitAssessment:
        entry = Decimal(str(position.entry_price))
        price = Decimal(str(snapshot.price_usd))
        highest = max(Decimal(str(position.highest_price or entry)), price)
        volatility = Decimal(str(abs(float(snapshot.price_change_1h or 0)) / 100))
        stop, target = AdaptiveExitService.levels(entry, volatility, snapshot.liquidity_usd)
        pnl = (price - entry) / entry if entry else Decimal("0")
        sell = Decimal(str(snapshot.sell_count_24h or 0)); buy = Decimal(str(snapshot.buy_count_24h or 0))
        pressure = Decimal("0")
        if snapshot.liquidity_usd is None:
            pressure = Decimal("100")
        if buy + sell > 0:
            pressure += (sell / (buy + sell)) * Decimal("55")
        if snapshot.price_change_5m is not None and float(snapshot.price_change_5m) < 0:
            pressure += min(Decimal("25"), Decimal(str(abs(float(snapshot.price_change_5m)))))
        if snapshot.liquidity_usd is not None and snapshot.liquidity_usd < 5000:
            pressure += Decimal("20")
        trail = highest * (Decimal("1") - Decimal("0.07"))
        if price <= stop:
            return ExitAssessment("AGGRESSIVE_EXIT", min(pressure + 40, Decimal("100")), stop, target, trail, "Adaptive stop loss reached")
        if pnl >= Decimal("0.08") and price <= trail:
            return ExitAssessment("PARTIAL_EXIT", min(pressure + 25, Decimal("100")), stop, target, trail, "Profit retraced from high-water mark", Decimal("0.5"))
        if pressure >= 75 and pnl > 0:
            return ExitAssessment("PARTIAL_EXIT", pressure, stop, target, trail, "Exit pressure is elevated while profitable", Decimal("0.25"))
        if pressure >= 90:
            return ExitAssessment("AGGRESSIVE_EXIT", pressure, stop, target, trail, "Market pressure is critical")
        if price >= target:
            return ExitAssessment("PARTIAL_EXIT", pressure, stop, target, trail, "Adaptive take profit reached", Decimal("0.5"))
        return ExitAssessment("HOLD", pressure, stop, target, trail, "Thesis remains valid")
