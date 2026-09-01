import logging
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import MarketSnapshot, Feature, RiskAssessment
from app.services.strategy.engine import strategy_runner
from app.services.risk.engine import RiskEngine
import math

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Record of a simulated trade during backtest."""
    timestamp: datetime
    pair_id: str
    trade_type: str
    price: Decimal
    amount: Decimal
    fee_pct: float = 0.0025


@dataclass
class BacktestMetrics:
    """Performance metrics from backtest."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: Decimal
    total_pnl_pct: float
    max_drawdown: float
    sharpe_ratio: float
    avg_trade_pnl: Decimal


class BacktestEngine:
    """Simulate strategy performance on historical data using strategy engine."""

    FEE_RATE = Decimal("0.0025")

    def __init__(self):
        self.trades: List[BacktestTrade] = []
        self.positions: List[dict] = []

    @staticmethod
    def _build_feature(snapshot: MarketSnapshot, history: List[MarketSnapshot]) -> Feature:
        """Build in-memory feature from snapshot history (no DB write)."""
        return_5m = float(snapshot.price_change_5m or 0) / 100 if snapshot.price_change_5m else None
        return_1h = float(snapshot.price_change_1h or 0) / 100 if snapshot.price_change_1h else None

        volume_spike = None
        if len(history) >= 2:
            avg_vol = sum(float(s.volume_1h_usd or s.volume_24h_usd or 0) for s in history[:-1]) / (len(history) - 1)
            current_vol = float(snapshot.volume_1h_usd or snapshot.volume_24h_usd or 0)
            if avg_vol > 0:
                volume_spike = current_vol / avg_vol

        buy_count = snapshot.buy_count_24h or 0
        sell_count = snapshot.sell_count_24h or 0
        buy_sell_ratio = float(buy_count) / float(sell_count) if sell_count > 0 else (float(buy_count) if buy_count else None)

        volatility = None
        if len(history) >= 2:
            returns = []
            for i in range(1, len(history)):
                prev = float(history[i - 1].price_usd or 0)
                curr = float(history[i].price_usd or 0)
                if prev > 0:
                    returns.append((curr - prev) / prev)
            if len(returns) >= 2:
                mean_r = sum(returns) / len(returns)
                variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
                volatility = math.sqrt(variance)

        return Feature(
            pair_id=snapshot.pair_id,
            timestamp=snapshot.timestamp,
            return_5m=Decimal(str(return_5m)) if return_5m is not None else None,
            return_1h=Decimal(str(return_1h)) if return_1h is not None else None,
            volume_spike=Decimal(str(volume_spike)) if volume_spike is not None else None,
            buy_sell_ratio_1h=Decimal(str(buy_sell_ratio)) if buy_sell_ratio is not None else None,
            volatility_1h=Decimal(str(volatility)) if volatility is not None else None,
        )

    @staticmethod
    def _build_risk(snapshot: MarketSnapshot, feature: Feature) -> RiskAssessment:
        """Build in-memory risk assessment (no DB write)."""
        liquidity_risk = RiskEngine._calculate_liquidity_risk(snapshot)
        manipulation_risk = RiskEngine._calculate_manipulation_risk(snapshot)
        volatility_risk = RiskEngine._calculate_volatility_risk(
            {"volatility_1h": float(feature.volatility_1h) if feature.volatility_1h else None}
        )
        execution_risk = RiskEngine._calculate_execution_risk(snapshot)
        is_blacklisted, _ = RiskEngine._check_hard_constraints(snapshot)

        overall = (
            liquidity_risk * 0.30
            + manipulation_risk * 0.30
            + volatility_risk * 0.20
            + execution_risk * 0.20
        )
        if is_blacklisted:
            overall = max(overall, 90)

        risk_level = "UNKNOWN"
        for (lo, hi), level in RiskEngine.RISK_LEVELS.items():
            if lo <= overall <= hi:
                risk_level = level
                break

        return RiskAssessment(
            pair_id=snapshot.pair_id,
            risk_score=Decimal(str(round(overall, 2))),
            risk_level=risk_level,
            timestamp=snapshot.timestamp,
        )

    async def backtest(
        self,
        session: AsyncSession,
        pair_id: str,
        start_date: datetime,
        end_date: datetime,
        initial_balance: Decimal = Decimal("1000"),
        position_size_pct: float = 0.05,
    ) -> BacktestMetrics:
        """Run backtest replaying feature → risk → strategy pipeline on historical data."""

        logger.info("Starting backtest for pair %s from %s to %s", pair_id, start_date, end_date)

        await strategy_runner.load_from_db(session)

        result = await session.execute(
            select(MarketSnapshot)
            .where(
                and_(
                    MarketSnapshot.pair_id == pair_id,
                    MarketSnapshot.timestamp >= start_date,
                    MarketSnapshot.timestamp <= end_date,
                )
            )
            .order_by(MarketSnapshot.timestamp.asc())
        )
        snapshots = result.scalars().all()

        if len(snapshots) < 5:
            logger.warning("Insufficient data for backtest: %d snapshots", len(snapshots))
            return self._create_empty_metrics()

        self.trades = []
        self.positions = []
        cash = initial_balance
        open_position = None

        for i, snapshot in enumerate(snapshots):
            if not snapshot.price_usd or snapshot.price_usd <= 0:
                continue

            history = snapshots[max(0, i - 20): i + 1]
            feature = self._build_feature(snapshot, history)
            risk = self._build_risk(snapshot, feature)

            if open_position:
                price = snapshot.price_usd
                hit_tp = open_position["take_profit"] and price >= open_position["take_profit"]
                hit_sl = open_position["stop_loss"] and price <= open_position["stop_loss"]
                if hit_tp or hit_sl:
                    cash, open_position = self._close_position(
                        open_position, snapshot, cash, pair_id
                    )
                    continue

            signals = await strategy_runner.evaluate_all(pair_id, snapshot, feature, risk)
            buy_signal = next((s for s in signals if s.signal_type == "BUY"), None)

            if open_position is None and buy_signal:
                trade_value = cash * Decimal(str(position_size_pct))
                if trade_value <= 0:
                    continue
                buy_price = snapshot.price_usd * (Decimal("1") + self.FEE_RATE)
                buy_amount = trade_value / buy_price
                fee = trade_value * self.FEE_RATE

                open_position = {
                    "entry_price": buy_price,
                    "entry_amount": buy_amount,
                    "entry_fee": fee,
                    "take_profit": buy_signal.target_tp,
                    "stop_loss": buy_signal.target_sl,
                }
                cash -= trade_value + fee
                self.trades.append(BacktestTrade(
                    timestamp=snapshot.timestamp,
                    pair_id=pair_id,
                    trade_type="BUY",
                    price=buy_price,
                    amount=buy_amount,
                ))

        if open_position and snapshots:
            cash, _ = self._close_position(open_position, snapshots[-1], cash, pair_id)

        final_balance = cash
        return self._calculate_metrics(initial_balance, final_balance)

    def _close_position(
        self,
        open_position: dict,
        snapshot: MarketSnapshot,
        cash: Decimal,
        pair_id: str,
    ) -> tuple[Decimal, None]:
        exit_price = snapshot.price_usd * (Decimal("1") - self.FEE_RATE)
        sell_amount = open_position["entry_amount"]
        proceeds = sell_amount * exit_price
        fee = proceeds * self.FEE_RATE
        pnl = proceeds - fee - (open_position["entry_amount"] * open_position["entry_price"]) - open_position["entry_fee"]
        pnl_pct = (exit_price - open_position["entry_price"]) / open_position["entry_price"]

        self.trades.append(BacktestTrade(
            timestamp=snapshot.timestamp,
            pair_id=pair_id,
            trade_type="SELL",
            price=exit_price,
            amount=sell_amount,
        ))
        self.positions.append({
            "entry_price": open_position["entry_price"],
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })
        return cash + proceeds - fee, None

    def _calculate_metrics(self, initial_balance: Decimal, final_balance: Decimal) -> BacktestMetrics:
        total_trades = len([t for t in self.trades if t.trade_type == "BUY"])
        winning_trades = len([p for p in self.positions if p["pnl"] > 0])
        losing_trades = len([p for p in self.positions if p["pnl"] <= 0])
        total_closed_trades = len(self.positions)

        win_rate = (winning_trades / total_closed_trades * 100) if total_closed_trades > 0 else 0
        total_pnl = final_balance - initial_balance
        total_pnl_pct = float((total_pnl / initial_balance) * 100) if initial_balance > 0 else 0

        cumulative_pnl = Decimal("0")
        peak = Decimal("0")
        max_drawdown = 0.0
        for position in self.positions:
            cumulative_pnl += position["pnl"]
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            if peak > 0:
                drawdown = float((peak - cumulative_pnl) / peak * 100)
                max_drawdown = max(max_drawdown, drawdown)

        avg_trade_pnl = (total_pnl / Decimal(str(total_closed_trades))) if total_closed_trades > 0 else Decimal("0")

        pnl_values = [float(p["pnl"]) for p in self.positions]
        if len(pnl_values) > 1:
            mean_pnl = sum(pnl_values) / len(pnl_values)
            variance = sum((x - mean_pnl) ** 2 for x in pnl_values) / len(pnl_values)
            std_dev = variance ** 0.5
            sharpe_ratio = (mean_pnl / std_dev) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0.0

        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            avg_trade_pnl=avg_trade_pnl,
        )

    def _create_empty_metrics(self) -> BacktestMetrics:
        return BacktestMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            total_pnl=Decimal("0"),
            total_pnl_pct=0,
            max_drawdown=0,
            sharpe_ratio=0,
            avg_trade_pnl=Decimal("0"),
        )
