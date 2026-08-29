import logging
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import MarketSnapshot, Position, Trade
from app.services.strategy.engine import strategy_runner

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Record of a simulated trade during backtest."""
    timestamp: datetime
    pair_id: str
    trade_type: str  # BUY or SELL
    price: Decimal
    amount: Decimal
    fee_pct: float = 0.0025  # 0.25% fee


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
    """Simulate strategy performance on historical data."""

    def __init__(self):
        self.trades: List[BacktestTrade] = []
        self.positions: List[dict] = []

    async def backtest(
        self,
        session: AsyncSession,
        pair_id: str,
        start_date: datetime,
        end_date: datetime,
        initial_balance: Decimal = Decimal("1000"),
        position_size_pct: float = 0.05,
    ) -> BacktestMetrics:
        """Run backtest on historical data for a pair."""
        
        logger.info(f"Starting backtest for pair {pair_id} from {start_date} to {end_date}")
        
        # Get historical snapshots
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
        
        if len(snapshots) < 2:
            logger.warning(f"Insufficient data for backtest: {len(snapshots)} snapshots")
            return self._create_empty_metrics()

        self.trades = []
        self.positions = []
        current_balance = initial_balance
        open_position = None
        trade_count = 0

        # Simulate trading through time
        for i, snapshot in enumerate(snapshots):
            # TODO: Compute features for this timestamp
            # TODO: Assess risk for this timestamp
            # TODO: Run strategies to get signals
            # For now, simple buy-and-hold simulation
            
            if open_position is None and snapshot.price_usd > 0:
                # Buy signal (simplified)
                buy_price = snapshot.price_usd
                buy_amount = (current_balance * Decimal(str(position_size_pct))) / buy_price
                fee = buy_amount * buy_price * Decimal("0.0025")
                
                open_position = {
                    "entry_price": buy_price,
                    "entry_amount": buy_amount,
                    "entry_index": i,
                    "fee": fee,
                }
                
                self.trades.append(
                    BacktestTrade(
                        timestamp=snapshot.timestamp,
                        pair_id=pair_id,
                        trade_type="BUY",
                        price=buy_price,
                        amount=buy_amount,
                    )
                )
                current_balance -= buy_amount * buy_price + fee
                trade_count += 1
                logger.info(f"BUY at {buy_price} (position size: {buy_amount})")

            elif open_position is not None and snapshot.price_usd > 0:
                # Simple exit: after 10 candles or at stop loss/take profit
                exit_price = snapshot.price_usd
                pnl_pct = (exit_price - open_position["entry_price"]) / open_position["entry_price"]
                
                # Exit conditions
                should_exit = (
                    i - open_position["entry_index"] >= 10  # Hold for 10 candles
                    or pnl_pct <= -0.10  # Stop loss at -10%
                    or pnl_pct >= 0.20  # Take profit at +20%
                )
                
                if should_exit:
                    sell_amount = open_position["entry_amount"]
                    fee = sell_amount * exit_price * Decimal("0.0025")
                    pnl = (exit_price - open_position["entry_price"]) * sell_amount - open_position["fee"] - fee
                    
                    self.trades.append(
                        BacktestTrade(
                            timestamp=snapshot.timestamp,
                            pair_id=pair_id,
                            trade_type="SELL",
                            price=exit_price,
                            amount=sell_amount,
                        )
                    )
                    
                    current_balance += sell_amount * exit_price - fee
                    self.positions.append({
                        "entry_price": open_position["entry_price"],
                        "exit_price": exit_price,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                    })
                    
                    open_position = None
                    trade_count += 1
                    logger.info(f"SELL at {exit_price} (PnL: {pnl_pct*100:.2f}%)")

        # Close any remaining position
        if open_position is not None and len(snapshots) > 0:
            exit_price = snapshots[-1].price_usd
            if exit_price > 0:
                pnl_pct = (exit_price - open_position["entry_price"]) / open_position["entry_price"]
                pnl = (exit_price - open_position["entry_price"]) * open_position["entry_amount"] - open_position["fee"]
                self.positions.append({
                    "entry_price": open_position["entry_price"],
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                })

        # Calculate metrics
        metrics = self._calculate_metrics(initial_balance, current_balance)
        logger.info(f"Backtest completed: {metrics}")
        return metrics

    def _calculate_metrics(self, initial_balance: Decimal, final_balance: Decimal) -> BacktestMetrics:
        """Calculate performance metrics."""
        
        total_trades = len([t for t in self.trades if t.trade_type == "BUY"])
        winning_trades = len([p for p in self.positions if p["pnl"] > 0])
        losing_trades = len([p for p in self.positions if p["pnl"] <= 0])
        total_closed_trades = len(self.positions)
        
        win_rate = (winning_trades / total_closed_trades * 100) if total_closed_trades > 0 else 0
        
        total_pnl = final_balance - initial_balance
        total_pnl_pct = (total_pnl / initial_balance) * 100 if initial_balance > 0 else 0
        
        # Max drawdown
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
        
        # Average trade PnL
        avg_trade_pnl = (total_pnl / Decimal(str(total_closed_trades))) if total_closed_trades > 0 else Decimal("0")
        
        # Sharpe ratio (simplified)
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
        """Create empty metrics for failed backtest."""
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
