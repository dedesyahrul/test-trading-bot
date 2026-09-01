"""Central risk decisions shared by strategy and execution layers."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RiskDecision:
    decision: str
    size_usd: Decimal
    reasons: list[str]


class RiskDecisionService:
    @staticmethod
    def decide(risk_score: float, risk_level: str, liquidity_usd: float | None, volatility: float | None,
               max_risk_score: float = 50, max_position_usd: Decimal = Decimal("1000"),
               account_balance: Decimal = Decimal("10000"), max_risk_per_trade_pct: Decimal = Decimal("0.01")) -> RiskDecision:
        reasons: list[str] = []
        if liquidity_usd is None or liquidity_usd < 1000:
            return RiskDecision("EMERGENCY", Decimal("0"), ["Liquidity is below emergency threshold"])
        if risk_score > max_risk_score or risk_level in {"CRITICAL", "HIGH"}:
            return RiskDecision("REJECT", Decimal("0"), [f"Risk score {risk_score:.0f} exceeds entry tolerance"])
        # Risk budget is the maximum amount that may be lost at the adaptive stop.
        stop_distance = max(Decimal("0.06"), Decimal("0.06") + Decimal(str(volatility or 0)) * Decimal("0.5"))
        size = min(max_position_usd, account_balance * max(Decimal("0"), max_risk_per_trade_pct) / stop_distance)
        if risk_score > max_risk_score * 0.7:
            size *= Decimal("0.5")
            reasons.append("Reduced size for elevated risk")
        if volatility is not None and volatility > 0.5:
            size *= Decimal("0.5")
            reasons.append("Reduced size for elevated volatility")
        if liquidity_usd < 5000:
            size *= Decimal("0.5")
            reasons.append("Reduced size for thin liquidity")
        return RiskDecision("REDUCE_SIZE" if reasons else "ALLOW", max(size, Decimal("0")), reasons)
