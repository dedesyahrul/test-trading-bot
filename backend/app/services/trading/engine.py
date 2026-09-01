import logging
import uuid
from decimal import Decimal
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Position, Trade, Wallet, BotState
from app.adapters.blockchain import Quote, UnsignedTransaction, TransactionResult
from app.core.config import settings
from app.services.settings.service import SettingsService, DEFAULT_RISK_CONFIG

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
        position_size_usd: Optional[Decimal] = None,
        decision_id=None,
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
                position_size_usd,
                decision_id,
            )
        else:  # LIVE
            return await self._execute_live_buy(
                session,
                pair_id,
                wallet_id,
                target_tp,
                target_sl,
                position_size_usd,
                decision_id,
            )

    async def execute_sell(
        self,
        session: AsyncSession,
        position_id,
        fraction: Decimal = Decimal("1"),
        exit_reason: str = "MANUAL",
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
            return await self._execute_paper_sell(session, position, fraction, exit_reason)
        else:  # LIVE
            return await self._execute_live_sell(session, position, fraction, exit_reason)

    async def _validate_trade(
        self,
        session: AsyncSession,
        wallet_id,
        pair_id,
        trading_mode: str,
    ) -> bool:
        """Validate trade before execution."""
        
        bot_state = await session.get(BotState, 1)
        if not bot_state:
            logger.warning("Trade validation failed for %s: bot state missing", pair_id)
            return False

        if bot_state.state in ("EMERGENCY_STOP", "STOPPED", "STOPPING"):
            logger.warning("Trade validation failed for %s: bot state %s", pair_id, bot_state.state)
            return False

        if bot_state.state == "PAUSED":
            logger.warning("Trade validation failed for %s: bot is paused", pair_id)
            return False

        risk_config = bot_state.risk_config or DEFAULT_RISK_CONFIG

        # Check duplicate position
        result = await session.execute(
            select(Position)
            .where(Position.pair_id == pair_id)
            .where(Position.wallet_id == wallet_id)
            .where(Position.status == "OPEN")
        )
        if result.scalars().first():
            logger.warning("Trade validation failed for %s: duplicate open position", pair_id)
            return False

        # Max open positions
        max_positions = risk_config.get("max_positions", 5)
        result = await session.execute(
            select(func.count(Position.id))
            .where(Position.wallet_id == wallet_id)
            .where(Position.status == "OPEN")
        )
        open_count = result.scalar() or 0
        if open_count >= max_positions:
            logger.warning("Trade validation failed for %s: max positions %d/%d", pair_id, open_count, max_positions)
            return False

        # Daily loss limit
        max_daily_loss = Decimal(str(risk_config.get("max_daily_loss_usd", 500)))
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await session.execute(
            select(Position)
            .where(Position.wallet_id == wallet_id)
            .where(Position.status == "CLOSED")
            .where(Position.closed_at >= today_start)
        )
        daily_loss = sum(
            Decimal(p.pnl_usd or 0) for p in result.scalars().all() if (p.pnl_usd or 0) < 0
        )
        if abs(daily_loss) >= max_daily_loss:
            logger.warning("Trade validation failed for %s: daily loss $%s", pair_id, abs(daily_loss))
            return False

        # Min liquidity check
        from app.services import MarketDataService
        latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
        min_liquidity = risk_config.get("min_liquidity_usd", 5000)
        if not latest_snapshot or latest_snapshot.liquidity_usd is None:
            logger.warning("Trade validation failed for %s: liquidity unavailable", pair_id)
            return False
        if float(latest_snapshot.liquidity_usd) < min_liquidity:
            logger.warning("Trade validation failed for %s: liquidity $%s < $%s", pair_id, latest_snapshot.liquidity_usd, min_liquidity)
            return False

        wallet = await session.get(Wallet, wallet_id)
        if not wallet:
            logger.warning("Trade validation failed for %s: wallet missing", pair_id)
            return False
        
        logger.info(f"Trade validation passed for pair {pair_id}")
        return True

    async def _get_trade_size(self, session: AsyncSession) -> Decimal:
        """Calculate trade size from risk config."""
        bot_state = await session.get(BotState, 1)
        risk_config = (bot_state.risk_config if bot_state else None) or DEFAULT_RISK_CONFIG
        max_position_size = Decimal(str(risk_config.get("max_position_size_usd", 1000)))
        virtual_balance = Decimal(str(risk_config.get("paper_initial_balance", settings.PAPER_INITIAL_BALANCE)))
        return min(virtual_balance * Decimal("0.02"), max_position_size)

    async def _execute_paper_buy(
        self,
        session: AsyncSession,
        pair_id,
        wallet_id,
        target_tp: Optional[Decimal],
        target_sl: Optional[Decimal],
        position_size_usd: Optional[Decimal] = None,
        decision_id=None,
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
        
        # Calculate entry amount from risk config
        trade_size = position_size_usd or await self._get_trade_size(session)
        entry_amount = trade_size / entry_price
        
        # Apply virtual slippage
        entry_price_with_slippage = entry_price * Decimal("1.0025")  # 0.25% slippage
        from app.services.trading.adaptive_exit import AdaptiveExitService
        adaptive_stop, adaptive_target = AdaptiveExitService.levels(
            entry_price_with_slippage,
            Decimal(str(abs(float(latest_snapshot.price_change_1h or 0)) / 100)),
            latest_snapshot.liquidity_usd,
        )
        
        # Create position
        position = Position(
            pair_id=pair_id,
            wallet_id=wallet_id,
            entry_price=entry_price_with_slippage,
            entry_amount=entry_amount,
            current_amount=entry_amount,
            initial_stop_loss=adaptive_stop,
            highest_price=entry_price_with_slippage,
            stop_loss=adaptive_stop,
            take_profit=adaptive_target,
            decision_id=decision_id,
            status="OPEN",
        )
        
        session.add(position)
        await session.commit()
        await session.refresh(position)
        
        # Record trade
        trade = Trade(
            position_id=position.id,
            decision_id=position.decision_id,
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
        position_size_usd: Optional[Decimal] = None,
        decision_id=None,
    ) -> Optional[Position]:
        """Execute actual BUY via Jupiter swap (SOL → token)."""
        from app.services import MarketDataService
        from app.models import Pair, Token
        from app.services.wallet.service import WalletService
        from app.adapters.blockchain import SolanaJupiterAdapter
        from app.core.metrics import TRADES_EXECUTED

        if not WalletService.is_configured():
            logger.error("LIVE BUY blocked: wallet not configured")
            return None

        pair = await session.get(Pair, pair_id)
        if not pair:
            return None

        base_token = await session.get(Token, pair.base_token_id)
        if not base_token:
            logger.error("Base token not found for pair %s", pair_id)
            return None

        latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
        if not latest_snapshot or not latest_snapshot.price_usd:
            return None

        trade_size_usd = position_size_usd or await self._get_trade_size(session)
        max_live = Decimal(str(settings.MAX_LIVE_TRADE_USD))
        trade_size_usd = min(trade_size_usd, max_live)

        # Approximate SOL amount (assume ~$150/SOL for sizing; Jupiter quotes exact amount)
        sol_price_estimate = Decimal("150")
        sol_amount = trade_size_usd / sol_price_estimate
        lamports = int(sol_amount * Decimal("1000000000"))

        adapter = SolanaJupiterAdapter()
        result = await adapter.swap_sol_for_token(
            token_mint=base_token.address,
            amount_lamports=lamports,
        )

        if result.status != "CONFIRMED":
            logger.error("LIVE BUY failed: %s", result.error)
            TRADES_EXECUTED.labels(trade_type="BUY", mode="LIVE").inc()
            return None

        entry_price = latest_snapshot.price_usd
        entry_amount = trade_size_usd / entry_price
        from app.services.trading.adaptive_exit import AdaptiveExitService
        adaptive_stop, adaptive_target = AdaptiveExitService.levels(
            entry_price, Decimal(str(abs(float(latest_snapshot.price_change_1h or 0)) / 100)), latest_snapshot.liquidity_usd
        )

        position = Position(
            pair_id=pair_id,
            wallet_id=wallet_id,
            entry_price=entry_price,
            entry_amount=entry_amount,
            current_amount=entry_amount,
            initial_stop_loss=adaptive_stop,
            highest_price=entry_price,
            stop_loss=adaptive_stop,
            take_profit=adaptive_target,
            decision_id=decision_id,
            status="OPEN",
        )
        session.add(position)
        await session.commit()
        await session.refresh(position)

        trade = Trade(
            position_id=position.id,
            decision_id=position.decision_id,
            trade_type="BUY",
            price=entry_price,
            amount=entry_amount,
            fee_usd=trade_size_usd * Decimal("0.0025"),
            tx_hash=result.tx_hash,
            status="CONFIRMED",
            confirmed_at=datetime.utcnow(),
        )
        session.add(trade)
        await session.commit()

        TRADES_EXECUTED.labels(trade_type="BUY", mode="LIVE").inc()
        logger.info("LIVE BUY executed: %s tx=%s", position.id, result.tx_hash)
        return position

    async def _execute_live_sell(
        self,
        session: AsyncSession,
        position: Position,
        fraction: Decimal = Decimal("1"),
        exit_reason: str = "MANUAL",
    ) -> Optional[Trade]:
        """Execute actual SELL via Jupiter swap (token → SOL)."""
        from app.models import Pair, Token
        from app.services.wallet.service import WalletService
        from app.adapters.blockchain import SolanaJupiterAdapter
        from app.core.metrics import TRADES_EXECUTED

        if not WalletService.is_configured():
            logger.error("LIVE SELL blocked: wallet not configured")
            return None

        pair = await session.get(Pair, position.pair_id)
        if not pair:
            return None

        base_token = await session.get(Token, pair.base_token_id)
        if not base_token:
            return None

        # Use entry amount as raw token amount (simplified; production needs decimals)
        fraction = min(Decimal("1"), max(Decimal("0"), Decimal(str(fraction))))
        amount_to_sell = (position.current_amount or position.entry_amount) * fraction
        amount_raw = int(float(amount_to_sell) * (10 ** base_token.decimals))

        adapter = SolanaJupiterAdapter()
        result = await adapter.swap_token_for_sol(
            token_mint=base_token.address,
            amount_raw=amount_raw,
        )

        if result.status != "CONFIRMED":
            logger.error("LIVE SELL failed: %s", result.error)
            return None

        from app.services import MarketDataService
        latest_snapshot = await MarketDataService.get_latest_snapshot(session, position.pair_id)
        exit_price = latest_snapshot.price_usd if latest_snapshot else position.current_price or position.entry_price

        pnl = (exit_price - position.entry_price) * position.entry_amount
        pnl_pct = (exit_price - position.entry_price) / position.entry_price if position.entry_price > 0 else Decimal("0")

        trade = Trade(
            position_id=position.id,
            decision_id=position.decision_id,
            trade_type="SELL",
            price=exit_price,
            amount=amount_to_sell,
            fee_usd=position.entry_price * position.entry_amount * Decimal("0.0025"),
            tx_hash=result.tx_hash,
            status="CONFIRMED",
            confirmed_at=datetime.utcnow(),
        )
        session.add(trade)

        position.current_amount = max(Decimal("0"), (position.current_amount or position.entry_amount) - amount_to_sell)
        position.partial_exit_count = (position.partial_exit_count or 0) + (1 if fraction < 1 else 0)
        position.status = "CLOSED" if fraction >= 1 or position.current_amount <= Decimal("0.00000001") else "OPEN"
        position.current_price = exit_price
        position.exit_reason = exit_reason[:40]
        position.pnl_usd = pnl
        position.pnl_percent = pnl_pct
        if position.status == "CLOSED":
            position.closed_at = datetime.utcnow()
        await session.commit()

        TRADES_EXECUTED.labels(trade_type="SELL", mode="LIVE").inc()
        logger.info("LIVE SELL executed: position %s tx=%s", position.id, result.tx_hash)
        return trade

    async def _execute_paper_sell(
        self,
        session: AsyncSession,
        position: Position,
        fraction: Decimal = Decimal("1"),
        exit_reason: str = "MANUAL",
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
        
        fraction = min(Decimal("1"), max(Decimal("0"), Decimal(str(fraction))))
        if fraction <= 0:
            return None
        amount_to_sell = (position.current_amount or position.entry_amount) * fraction
        pnl = (exit_price_with_slippage - position.entry_price) * amount_to_sell
        pnl_pct = (exit_price_with_slippage - position.entry_price) / position.entry_price
        
        # Record trade
        trade = Trade(
            position_id=position.id,
            trade_type="SELL",
            price=exit_price_with_slippage,
            amount=amount_to_sell,
            fee_usd=position.entry_price * position.entry_amount * Decimal("0.0025"),
            # Each partial exit is a separate virtual trade and must have a
            # unique transaction identifier because trades.tx_hash is unique.
            tx_hash=f"paper_sell_{position.id}_{uuid.uuid4().hex}",
            status="CONFIRMED",
            confirmed_at=datetime.utcnow(),
        )
        
        session.add(trade)
        
        remaining_amount = (position.current_amount or position.entry_amount) - amount_to_sell
        position.current_amount = max(Decimal("0"), remaining_amount)
        position.partial_exit_count = (position.partial_exit_count or 0) + (1 if fraction < 1 else 0)
        position.status = "CLOSED" if fraction >= 1 or position.current_amount <= Decimal("0.00000001") else "OPEN"
        position.current_price = exit_price_with_slippage
        position.exit_reason = exit_reason[:40]
        position.pnl_usd = (exit_price_with_slippage - position.entry_price) * position.entry_amount
        position.pnl_percent = (exit_price_with_slippage - position.entry_price) / position.entry_price
        if position.status == "CLOSED":
            position.closed_at = datetime.utcnow()
        
        await session.commit()
        
        logger.info(f"Paper SELL executed for pair {position.pair_id}: PnL={pnl:.2f} ({pnl_pct*100:.2f}%)")
        return trade
