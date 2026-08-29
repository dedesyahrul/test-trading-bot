import logging
from decimal import Decimal
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Position, Trade, Wallet, BotState
from app.adapters.blockchain import Quote, UnsignedTransaction, TransactionResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Orchestrates trading execution in PAPER and LIVE modes."""

    def __init__(self, blockchain_adapter, dex_adapter, wallet_adapter, execution_adapter):
        self.blockchain_adapter = blockchain_adapter
        self.dex_adapter = dex_adapter
        self.wallet_adapter = wallet_adapter
        self.execution_adapter = execution_adapter

    async def execute_buy(
        self,
        session: AsyncSession,
        pair_id,
        wallet_id,
        signal_confidence: float,
        target_tp: Optional[Decimal] = None,
        target_sl: Optional[Decimal] = None,
    ) -> Optional[Position]:
        """Execute BUY signal. Returns Position if successful, None otherwise."""
        
        logger.info(f"Executing BUY for pair {pair_id}")
        
        # Get bot state (PAPER or LIVE mode)
        bot_state = await session.get(BotState, 1)
        if not bot_state:
            logger.error("Bot state not found")
            return None
        
        trading_mode = bot_state.trading_mode
        
        # Pre-trade validation
        if not await self._validate_trade(session, wallet_id, pair_id, trading_mode):
            logger.warning("Trade validation failed")
            return None
        
        # Get wallet
        wallet = await session.get(Wallet, wallet_id)
        if not wallet:
            logger.error(f"Wallet {wallet_id} not found")
            return None
        
        if trading_mode == "PAPER":
            return await self._execute_paper_buy(
                session,
                pair_id,
                wallet_id,
                target_tp,
                target_sl,
            )
        else:  # LIVE
            return await self._execute_live_buy(
                session,
                pair_id,
                wallet_id,
                target_tp,
                target_sl,
            )

    async def execute_sell(
        self,
        session: AsyncSession,
        position_id,
    ) -> Optional[Trade]:
        """Execute SELL to close position. Returns Trade if successful."""
        
        logger.info(f"Executing SELL for position {position_id}")
        
        # Get position
        position = await session.get(Position, position_id)
        if not position:
            logger.error(f"Position {position_id} not found")
            return None
        
        # Get bot state
        bot_state = await session.get(BotState, 1)
        if not bot_state:
            logger.error("Bot state not found")
            return None
        
        trading_mode = bot_state.trading_mode
        
        if trading_mode == "PAPER":
            return await self._execute_paper_sell(session, position)
        else:  # LIVE
            return await self._execute_live_sell(session, position)

    async def _validate_trade(
        self,
        session: AsyncSession,
        wallet_id,
        pair_id,
        trading_mode: str,
    ) -> bool:
        """Validate trade before execution."""
        
        # Check emergency stop
        bot_state = await session.get(BotState, 1)
        if bot_state and bot_state.state == "EMERGENCY_STOP":
            logger.warning("Emergency stop is active - blocking BUY")
            return False
        
        # Check duplicate position
        result = await session.execute(
            select(Position)
            .where(Position.pair_id == pair_id)
            .where(Position.wallet_id == wallet_id)
            .where(Position.status == "OPEN")
        )
        if result.scalars().first():
            logger.warning(f"Duplicate position for pair {pair_id}")
            return False
        
        # Check wallet balance (simplified - full implementation would check actual balance)
        wallet = await session.get(Wallet, wallet_id)
        if not wallet:
            return False
        
        logger.info(f"Trade validation passed for pair {pair_id}")
        return True

    async def _execute_paper_buy(
        self,
        session: AsyncSession,
        pair_id,
        wallet_id,
        target_tp: Optional[Decimal],
        target_sl: Optional[Decimal],
    ) -> Optional[Position]:
        """Execute virtual BUY (paper trading)."""
        
        from app.services import MarketDataService
        
        # Get latest market snapshot
        latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
        if not latest_snapshot:
            logger.error("No market data for pair")
            return None
        
        entry_price = latest_snapshot.price_usd
        if not entry_price:
            logger.error("No price available")
            return None
        
        # Calculate entry amount (2% of virtual balance)
        virtual_balance = Decimal("10000")  # Virtual paper trading balance
        trade_size = virtual_balance * Decimal("0.02")
        entry_amount = trade_size / entry_price
        
        # Apply virtual slippage
        entry_price_with_slippage = entry_price * Decimal("1.0025")  # 0.25% slippage
        
        # Create position
        position = Position(
            pair_id=pair_id,
            wallet_id=wallet_id,
            entry_price=entry_price_with_slippage,
            entry_amount=entry_amount,
            stop_loss=target_sl,
            take_profit=target_tp,
            status="OPEN",
        )
        
        session.add(position)
        await session.commit()
        await session.refresh(position)
        
        # Record trade
        trade = Trade(
            position_id=position.id,
            trade_type="BUY",
            price=entry_price_with_slippage,
            amount=entry_amount,
            fee_usd=trade_size * Decimal("0.0025"),
            tx_hash=f"paper_{position.id}",  # Virtual tx hash
            status="CONFIRMED",
            confirmed_at=datetime.utcnow(),
        )
        
        session.add(trade)
        await session.commit()
        
        logger.info(f"Paper BUY executed for pair {pair_id}: {entry_amount} @ {entry_price_with_slippage}")
        return position

    async def _execute_live_buy(
        self,
        session: AsyncSession,
        pair_id,
        wallet_id,
        target_tp: Optional[Decimal],
        target_sl: Optional[Decimal],
    ) -> Optional[Position]:
        """Execute actual BUY (live trading) - stub for Phase 3."""
        
        logger.info(f"LIVE BUY would execute for pair {pair_id}")
        # TODO: Implement actual blockchain execution
        return None

    async def _execute_paper_sell(
        self,
        session: AsyncSession,
        position: Position,
    ) -> Optional[Trade]:
        """Execute virtual SELL (paper trading)."""
        
        from app.services import MarketDataService
        
        # Get latest market snapshot
        latest_snapshot = await MarketDataService.get_latest_snapshot(session, position.pair_id)
        if not latest_snapshot:
            logger.error("No market data for pair")
            return None
        
        exit_price = latest_snapshot.price_usd
        if not exit_price:
            logger.error("No price available")
            return None
        
        # Apply virtual slippage
        exit_price_with_slippage = exit_price * Decimal("0.9975")  # 0.25% slippage
        
        # Calculate PnL
        pnl = (exit_price_with_slippage - position.entry_price) * position.entry_amount
        pnl_pct = (exit_price_with_slippage - position.entry_price) / position.entry_price
        
        # Record trade
        trade = Trade(
            position_id=position.id,
            trade_type="SELL",
            price=exit_price_with_slippage,
            amount=position.entry_amount,
            fee_usd=position.entry_price * position.entry_amount * Decimal("0.0025"),
            tx_hash=f"paper_sell_{position.id}",
            status="CONFIRMED",
            confirmed_at=datetime.utcnow(),
        )
        
        session.add(trade)
        
        # Close position
        position.status = "CLOSED"
        position.current_price = exit_price_with_slippage
        position.pnl_usd = pnl
        position.pnl_percent = pnl_pct
        position.closed_at = datetime.utcnow()
        
        await session.commit()
        
        logger.info(f"Paper SELL executed for pair {position.pair_id}: PnL={pnl:.2f} ({pnl_pct*100:.2f}%)")
        return trade

    async def _execute_live_sell(
        self,
        session: AsyncSession,
        position: Position,
    ) -> Optional[Trade]:
        """Execute actual SELL (live trading) - stub for Phase 3."""
        
        logger.info(f"LIVE SELL would execute for position {position.id}")
        # TODO: Implement actual blockchain execution
        return None
