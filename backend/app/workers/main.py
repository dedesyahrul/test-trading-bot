import logging
from decimal import Decimal
from datetime import datetime
from arq import cron
from arq.connections import RedisSettings
from app.core.config import settings
from app.core.database import async_session_maker
from app.core.events import EventPublisher
from app.services import PairService, MarketDataService, TokenService, ChainService
from app.adapters.dexscreener import DEXScreenerClient
from app.services.features.engine import FeatureEngineering
from app.services.risk.engine import RiskEngine
from app.services.strategy.engine import strategy_runner
from sqlalchemy import select
from app.models import Pair, Token, Signal, BotState, TradeDecision, Position
from app.services.data_quality import DataQualityService, DataQualityStatus
from app.services.risk.decision import RiskDecisionService
from app.services.risk.portfolio import PortfolioRiskService
from app.adapters.geckoterminal import GeckoTerminalClient
from app.services.decision_score import DecisionScoreService
from app.services.trading.adaptive_exit import AdaptiveExitService
from app.services.chart_intelligence import ChartIntelligence
from app.services.security.gate import SecurityGateService
from app.workers.security_integration import assess_risk_with_security_gate
import asyncio

logger = logging.getLogger(__name__)

dex_screener_client = DEXScreenerClient()
gecko_terminal_client = GeckoTerminalClient()
security_gate_service = SecurityGateService()
market_collection_lock = asyncio.Lock()

TRADING_ACTIVE_STATES = {"RUNNING", "STARTING"}


async def _get_bot_state(session):
    return await session.get(BotState, 1)


async def _sync_bot_state(session) -> str:
    """Transition STARTING->RUNNING and STOPPING->STOPPED."""
    bot_state = await _get_bot_state(session)
    if not bot_state:
        return "STOPPED"
    if bot_state.state == "STARTING":
        bot_state.state = "RUNNING"
        await session.commit()
    elif bot_state.state == "STOPPING":
        bot_state.state = "STOPPED"
        await session.commit()
    return bot_state.state


async def _can_execute_trades(session) -> bool:
    state = await _sync_bot_state(session)
    bot_state = await _get_bot_state(session)
    if state not in TRADING_ACTIVE_STATES or (bot_state and bot_state.circuit_state in {"SAFE_MODE", "EMERGENCY"}):
        return False
    if bot_state:
        from datetime import datetime
        from sqlalchemy import desc
        from app.services.settings.service import DEFAULT_RISK_CONFIG
        max_loss = Decimal(str((bot_state.risk_config or DEFAULT_RISK_CONFIG).get("max_daily_loss_usd", 500)))
        result = await session.execute(
            select(Position).where(Position.status == "CLOSED").where(Position.closed_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
        )
        daily_loss = sum(Decimal(str(p.pnl_usd or 0)) for p in result.scalars().all() if (p.pnl_usd or 0) < 0)
        bot_state.daily_loss_usd = daily_loss
        if abs(daily_loss) >= max_loss:
            bot_state.circuit_state = "SAFE_MODE"
            bot_state.error_message = "Daily loss limit reached; new entries blocked"
            await session.commit()
            return False
    return True


async def _get_default_wallet(session):
    from app.services.portfolio.service import PortfolioService
    return await PortfolioService.get_or_create_default_wallet(session)


async def _execute_buy_for_signal(session, signal, pair_id, position_size_usd=None, decision_id=None) -> None:
    """Execute BUY if signal qualifies."""
    if signal.signal_type != "BUY":
        return
    if not await _can_execute_trades(session):
        logger.info("Bot not in trading state, skipping BUY for pair %s", pair_id)
        return

    # Final veto for the internal execution path as well as the ARQ worker.
    latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
    pair = await session.get(Pair, pair_id)
    token = await session.get(Token, pair.base_token_id) if pair else None
    if not latest_snapshot or not pair or not token:
        logger.warning("Security data unavailable; refusing BUY for pair %s", pair_id)
        return
    liquidity_usd = latest_snapshot.liquidity_usd if latest_snapshot.liquidity_usd is not None else pair.liquidity_usd
    gate_result = await security_gate_service.evaluate_token(
        chain=pair.chain_id,
        token_address=token.address,
        pair_address=pair.pair_address or "",
        market_snapshot={
            "liquidity_usd": float(liquidity_usd) if liquidity_usd is not None else None,
            "buy_count_24h": latest_snapshot.buy_count_24h or 0,
            "sell_count_24h": latest_snapshot.sell_count_24h or 0,
            "volume_24h_usd": float(latest_snapshot.volume_24h_usd or 0),
            "price_usd": float(latest_snapshot.price_usd or 0),
            "trading_mode": settings.TRADING_MODE,
        },
        position_size_usd=float(position_size_usd) if position_size_usd is not None else None,
    )
    if gate_result.is_blocked or gate_result.is_deferred:
        logger.warning("Final security veto %s BUY for pair %s: %s", gate_result.status, pair_id, gate_result.reason)
        return

    wallet = await _get_default_wallet(session)
    if not wallet:
        logger.warning("No wallet available for BUY execution")
        return

    bot_state = await _get_bot_state(session)
    risk_config = (bot_state.risk_config if bot_state else None) or {}
    allowed, reasons = await PortfolioRiskService.entry_guard(
        session, wallet.id, pair_id, Decimal(str(position_size_usd or 0)), risk_config
    )
    if not allowed:
        logger.warning("Entry blocked for pair %s: %s", pair_id, "; ".join(reasons))
        return

    from app.services.trading.engine import ExecutionEngine
    from app.adapters.blockchain import SolanaJupiterAdapter

    adapter = SolanaJupiterAdapter()
    engine = ExecutionEngine(adapter, adapter, None, adapter)
    position = await engine.execute_buy(
        session,
        pair_id,
        wallet.id,
        float(signal.confidence),
        signal.target_tp,
        signal.target_sl,
        position_size_usd,
        decision_id,
    )
    if position:
        logger.info("BUY executed: position %s for pair %s", position.id, pair_id)
        await EventPublisher.publish(
            "ORDER_STATUS_CHANGED",
            {
                "pair_id": str(pair_id),
                "position_id": str(position.id),
                "status": "CONFIRMED",
                "type": "BUY",
            },
        )
        await EventPublisher.publish(
            "POSITION_UPDATED",
            {
                "position_id": str(position.id),
                "pair_id": str(pair_id),
                "status": "OPEN",
            },
        )


async def _run_intelligence_pipeline(session, pair_id) -> None:
    """Run feature → risk → predict → signal → execute pipeline for a pair."""
    import time
    from sqlalchemy import desc
    from app.models import RiskAssessment, Feature, Signal as SignalModel
    from app.services.prediction.engine import PredictionEngine
    from app.core.metrics import PREDICTION_DURATION, SIGNALS_GENERATED

    if not await _can_execute_trades(session):
        return

    await strategy_runner.load_from_db(session)

    latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
    if not latest_snapshot:
        return

    # Security is a veto layer and must run before feature/prediction work.
    pair = await session.get(Pair, pair_id)
    token = await session.get(Token, pair.base_token_id) if pair else None
    if not pair or not token:
        logger.error("Security gate cannot resolve pair/token %s", pair_id)
        return
    liquidity_usd = latest_snapshot.liquidity_usd if latest_snapshot.liquidity_usd is not None else pair.liquidity_usd
    gate_result = await security_gate_service.evaluate_token(
        chain=pair.chain_id,
        token_address=token.address,
        pair_address=pair.pair_address or "",
        market_snapshot={
            "liquidity_usd": float(liquidity_usd) if liquidity_usd is not None else None,
            "buy_count_24h": latest_snapshot.buy_count_24h or 0,
            "sell_count_24h": latest_snapshot.sell_count_24h or 0,
            "volume_24h_usd": float(latest_snapshot.volume_24h_usd or 0),
            "price_usd": float(latest_snapshot.price_usd or 0),
            "trading_mode": settings.TRADING_MODE,
        },
    )
    if gate_result.is_blocked or gate_result.is_deferred:
        logger.warning("Security gate %s pair %s: %s", gate_result.status, pair_id, gate_result.reason)
        session.add(TradeDecision(
            pair_id=pair_id,
            strategy_id="security_gate",
            decision="REJECT" if gate_result.is_blocked else "DEFERRED",
            reasons=[gate_result.reason],
        ))
        await session.commit()
        return

    quality, quality_reasons = DataQualityService.assess(latest_snapshot)
    if quality in {DataQualityStatus.INVALID, DataQualityStatus.STALE}:
        session.add(TradeDecision(
            pair_id=pair_id, strategy_id="data_quality", decision="REJECT",
            data_quality=quality.value, reasons=quality_reasons,
        ))
        await session.commit()
        return

    computed_feature = await FeatureEngineering.compute_features(session, pair_id, latest_snapshot)
    candles = await MarketDataService.get_candles(session, pair_id)
    chart = ChartIntelligence.assess(candles)
    if not chart.entry_allowed and chart.trend != "UNKNOWN":
        logger.warning("Chart gate blocked entry for %s: %s", pair_id, chart.behavior)
    logger.warning("Features ready for pair %s; assessing risk", pair_id)
    risk_assessment = await RiskEngine.assess_risk(
        session, pair_id, latest_snapshot,
        security_gate_score=gate_result.security_gate_score,
        feature=computed_feature,
    )
    logger.warning("Risk ready for pair %s: score=%s", pair_id, risk_assessment.risk_score)

    result_feature = await session.execute(
        select(Feature).where(Feature.pair_id == pair_id).order_by(desc(Feature.timestamp)).limit(1)
    )
    feature = result_feature.scalars().first()

    prediction = None
    if feature and PredictionEngine.is_available():
        t0 = time.perf_counter()
        prediction = await PredictionEngine.predict(session, pair_id, feature)
        PREDICTION_DURATION.observe(time.perf_counter() - t0)

    signals_list = await strategy_runner.evaluate_all(
        pair_id, latest_snapshot, feature, risk_assessment, prediction
    )
    logger.warning("Strategies evaluated for pair %s: %d signal(s)", pair_id, len(signals_list))

    for signal in signals_list:
        bot_state = await _get_bot_state(session)
        risk_config = (bot_state.risk_config if bot_state else None) or {}
        risk_decision = RiskDecisionService.decide(
            float(risk_assessment.risk_score), risk_assessment.risk_level,
            float(latest_snapshot.liquidity_usd) if latest_snapshot.liquidity_usd else None,
            float(feature.volatility_1h) if feature and feature.volatility_1h else None,
            max_risk_score=float(risk_config.get("max_risk_score", 50)),
            max_position_usd=Decimal(str(risk_config.get("max_position_size_usd", 1000))),
            account_balance=Decimal(str(risk_config.get("paper_initial_balance", settings.PAPER_INITIAL_BALANCE))),
            max_risk_per_trade_pct=Decimal(str(risk_config.get("max_risk_per_trade_pct", 0.01))),
        )
        prediction_probability = float(prediction.probability) if prediction else None
        decision_score = DecisionScoreService.calculate(
            float(feature.return_5m or 0) if feature and feature.return_5m else None,
            float(latest_snapshot.volume_24h_usd) if latest_snapshot.volume_24h_usd else None,
            float(latest_snapshot.liquidity_usd) if latest_snapshot.liquidity_usd else None,
            prediction_probability, float(risk_assessment.risk_score),
        )
        decision_record = TradeDecision(
            pair_id=pair_id, strategy_id=signal.strategy_id,
            decision=risk_decision.decision if signal.signal_type == "BUY" and (chart.entry_allowed or chart.trend == "UNKNOWN") else "WAIT",
            signal_type=signal.signal_type, confidence=signal.confidence,
            risk_score=risk_assessment.risk_score, risk_level=risk_assessment.risk_level,
            decision_score=decision_score,
            position_size_usd=risk_decision.size_usd, data_quality=quality.value,
            features={"volatility_1h": float(feature.volatility_1h) if feature and feature.volatility_1h else None},
            reasons=signal.reasons_pro + signal.reasons_contra + risk_decision.reasons + chart.reasons,
        )
        session.add(decision_record)
        await session.flush()
        decision_id = decision_record.id
        if signal.signal_type == "BUY":
            logger.info("Entry decision score for %s: %.2f", pair_id, decision_score)
        session.add(SignalModel(
            pair_id=signal.pair_id,
            strategy_id=signal.strategy_id,
            signal_type=signal.signal_type,
            confidence=signal.confidence,
            reasons_pro=signal.reasons_pro,
            reasons_contra=signal.reasons_contra,
        ))
        await EventPublisher.publish(
            "SIGNAL_GENERATED",
            {
                "pair_id": str(pair_id),
                "strategy_id": signal.strategy_id,
                "signal_type": signal.signal_type,
                "confidence": float(signal.confidence),
            },
        )
        SIGNALS_GENERATED.labels(signal_type=signal.signal_type).inc()
        if signal.signal_type == "BUY" and (chart.entry_allowed or chart.trend == "UNKNOWN") and risk_decision.decision in {"ALLOW", "REDUCE_SIZE"}:
            await _execute_buy_for_signal(session, signal, pair_id, risk_decision.size_usd, decision_id)

    await session.commit()


async def process_watched_pairs_pipeline(ctx):
    """Run intelligence pipeline for all watched pairs."""
    logger.info("Running intelligence pipeline for watched pairs")
    async with async_session_maker() as session:
        state = await _sync_bot_state(session)
        logger.warning("Intelligence pipeline bot state: %s", state)
        if state not in TRADING_ACTIVE_STATES and state != "PAUSED":
            logger.info("Bot state %s - skipping intelligence pipeline", state)
            return
        watched_pairs = await PairService.get_watched_pairs(session)
        logger.warning("Intelligence pipeline found %d watched pair(s)", len(watched_pairs))
        for pair in watched_pairs:
            try:
                await _run_intelligence_pipeline(session, pair.id)
            except Exception as e:
                logger.exception("Pipeline error for pair %s", pair.id)


async def _collect_market_data_worker(ctx):
    """Worker to collect market data for all watched pairs."""
    logger.info("Starting market data collection worker")
    
    async with async_session_maker() as session:
        # Get all watched pairs
        watched_pairs = await PairService.get_watched_pairs(session)
        logger.info(f"Found {len(watched_pairs)} watched pairs")
        
        fetch_semaphore = asyncio.Semaphore(4)

        async def fetch_pair(pair):
            async with fetch_semaphore:
                try:
                    pair_data = await dex_screener_client.get_pair_by_chain_and_address(
                        chain=pair.chain_id,
                        pair_address=pair.pair_address,
                    )
                    if pair_data:
                        return pair, pair_data
                    fallback = await gecko_terminal_client.get_pool(pair.chain_id, pair.pair_address)
                    return pair, {"pair": fallback} if fallback else None
                except Exception:
                    logger.exception("Error fetching market data for pair %s", pair.id)
                    return pair, None

        # Fetch independently from the DB session; writes remain sequential below.
        fetched_pairs = await asyncio.gather(*(fetch_pair(pair) for pair in watched_pairs))
        for pair, pair_data in fetched_pairs:
            try:
                current_pair = (pair_data or {}).get("pair")
                if not current_pair:
                    pair_candidates = (pair_data or {}).get("pairs") or []
                    current_pair = next(
                        (candidate for candidate in pair_candidates
                         if candidate.get("pairAddress") == pair.pair_address),
                        pair_candidates[0] if pair_candidates else None,
                    )
                if not current_pair:
                    logger.warning(
                        "No current market data for pair %s (%s); keeping last snapshot",
                        pair.id,
                        pair.pair_address,
                    )
                    continue
                
                normalized = (
                    current_pair if (pair_data or {}).get("pair", {}).get("provider") == "geckoterminal"
                    else DEXScreenerClient.normalize_pair_data(current_pair)
                )
                
                # Save market snapshot
                snapshot = await MarketDataService.save_market_snapshot(
                    session,
                    pair_id=pair.id,
                    price_usd=normalized.get("price_usd"),
                    price_change_1m=normalized.get("price_change", {}).get("m5"),
                    price_change_5m=normalized.get("price_change", {}).get("m5"),
                    price_change_1h=normalized.get("price_change", {}).get("h1"),
                    price_change_24h=normalized.get("price_change", {}).get("h24"),
                    volume_1m_usd=normalized.get("volume", {}).get("m5"),
                    volume_5m_usd=normalized.get("volume", {}).get("m5"),
                    volume_1h_usd=normalized.get("volume", {}).get("h1"),
                    volume_24h_usd=normalized.get("volume", {}).get("h24"),
                    liquidity_usd=normalized.get("liquidity", {}).get("usd"),
                    buy_count_24h=normalized.get("transactions", {}).get("h24", {}).get("buys"),
                    sell_count_24h=normalized.get("transactions", {}).get("h24", {}).get("sells"),
                    market_cap_usd=normalized.get("market_cap_usd"),
                    fdv_usd=normalized.get("fdv_usd"),
                )
                try:
                    latest_candles = await MarketDataService.get_candles(session, pair.id, limit=1)
                    candle_is_fresh = latest_candles and (datetime.utcnow() - latest_candles[-1].timestamp).total_seconds() < 300
                    if not candle_is_fresh:
                        candle_rows = await gecko_terminal_client.get_pool_ohlcv(pair.chain_id, pair.pair_address, timeframe="minute", limit=100)
                        if candle_rows:
                            await MarketDataService.save_candles(session, pair.id, candle_rows)
                except Exception:
                    logger.warning("Candle data unavailable for pair %s", pair.id)
                logger.info(f"Market data saved for pair {pair.id}")

                await EventPublisher.publish(
                    "MARKET_PRICE_UPDATED",
                    {
                        "pair_id": str(pair.id),
                        "price_usd": float(normalized.get("price_usd") or 0),
                        "price_change_24h": float(normalized.get("price_change", {}).get("h24") or 0),
                    },
                )
                
            except Exception:
                logger.exception("Error collecting market data for pair %s", pair.id)
                continue
    
    logger.info("Market data collection worker completed")

    # Evaluate in the same worker task after fresh snapshots are available.
    # This avoids relying on ARQ job chaining for the critical paper-trading loop.
    async with async_session_maker() as session:
        state = await _sync_bot_state(session)
        if state in TRADING_ACTIVE_STATES:
            watched_pairs = await PairService.get_watched_pairs(session)
            for pair in watched_pairs:
                try:
                    await _run_intelligence_pipeline(session, pair.id)
                except Exception:
                    logger.exception("Post-collection pipeline error for pair %s", pair.id)


async def collect_market_data_worker(ctx):
    """Run one market collection cycle; prevent overlapping cron cycles."""
    if market_collection_lock.locked():
        logger.warning("Skipping market collection: previous cycle is still running")
        return
    async with market_collection_lock:
        await _collect_market_data_worker(ctx)


async def compute_features_worker(ctx, pair_id):
    """Worker to compute ML features for a pair."""
    logger.info(f"Computing features for pair {pair_id}")
    
    async with async_session_maker() as session:
        try:
            # Get latest market snapshot
            latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
            if not latest_snapshot:
                logger.warning(f"No market data for pair {pair_id}")
                return
            
            # Compute features
            feature = await FeatureEngineering.compute_features(
                session,
                pair_id,
                latest_snapshot,
            )
            logger.info(f"Features computed for pair {pair_id}")
            
            # Enqueue risk assessment
            # await ctx.queue.enqueue(assess_risk_worker, pair_id)
            
        except Exception as e:
            logger.error(f"Error computing features for pair {pair_id}: {e}")


async def assess_risk_worker(ctx, pair_id):
    """Worker to assess token risk."""
    logger.info(f"Assessing risk for pair {pair_id}")
    
    async with async_session_maker() as session:
        try:
            # Get latest market snapshot and run the security veto before risk scoring.
            latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
            if not latest_snapshot:
                logger.warning(f"No market data for pair {pair_id}")
                return
            
            blocked, result = await assess_risk_with_security_gate(
                session, pair_id, latest_snapshot
            )
            if blocked:
                status = "BLOCKED" if result.get("blocked") else "DEFERRED"
                logger.warning(
                    "Security gate %s pair %s: %s",
                    status,
                    pair_id,
                    result.get("block_reason") or result.get("error") or "Security verification unavailable",
                )
                return
            risk_assessment = result.get("risk_assessment")
            logger.info(f"Risk assessment completed for pair {pair_id}: {risk_assessment.risk_level}")
            
            # If not blacklisted, enqueue signal generation
            # if not risk_assessment.is_blacklisted:
            #     await ctx.queue.enqueue(generate_signals_worker, pair_id)
            
        except Exception as e:
            logger.error(f"Error assessing risk for pair {pair_id}: {e}")


async def generate_signals_worker(ctx, pair_id):
    """Worker to generate trading signals."""
    logger.info(f"Generating signals for pair {pair_id}")
    
    async with async_session_maker() as session:
        try:
            # Get latest data
            latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
            if not latest_snapshot:
                return
            
            # Get latest risk assessment
            from sqlalchemy import desc, and_
            from app.models import RiskAssessment, Feature
            
            result_risk = await session.execute(
                select(RiskAssessment)
                .where(RiskAssessment.pair_id == pair_id)
                .order_by(desc(RiskAssessment.timestamp))
                .limit(1)
            )
            risk_assessment = result_risk.scalars().first()
            
            result_feature = await session.execute(
                select(Feature)
                .where(Feature.pair_id == pair_id)
                .order_by(desc(Feature.timestamp))
                .limit(1)
            )
            feature = result_feature.scalars().first()
            
            # Run all strategies
            signals_list = await strategy_runner.evaluate_all(
                pair_id,
                latest_snapshot,
                feature,
                risk_assessment,
            )
            
            # Save signals to database
            from app.models import Signal as SignalModel
            for signal in signals_list:
                db_signal = SignalModel(
                    pair_id=signal.pair_id,
                    strategy_id=signal.strategy_id,
                    signal_type=signal.signal_type,
                    confidence=signal.confidence,
                    reasons_pro=signal.reasons_pro,
                    reasons_contra=signal.reasons_contra,
                )
                session.add(db_signal)
            
            await session.commit()
            logger.info(f"Signals generated for pair {pair_id}: {len(signals_list)} signal(s)")

            for signal in signals_list:
                await EventPublisher.publish(
                    "SIGNAL_GENERATED",
                    {
                        "pair_id": str(pair_id),
                        "strategy_id": signal.strategy_id,
                        "signal_type": signal.signal_type,
                        "confidence": float(signal.confidence),
                    },
                )
            
        except Exception as e:
            logger.error(f"Error generating signals for pair {pair_id}: {e}")


async def execute_buy_signal_worker(ctx, pair_id, confidence, target_tp, target_sl):
    """Worker to execute BUY signals."""
    logger.info(f"Executing BUY signal for pair {pair_id}")
    
    async with async_session_maker() as session:
        try:
            # Final security veto immediately before constructing/sending a swap.
            latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
            if not latest_snapshot:
                logger.warning("No latest snapshot; refusing BUY for pair %s", pair_id)
                return
            pair = await session.get(Pair, pair_id)
            token = await session.get(Token, pair.base_token_id) if pair else None
            if not pair or not token:
                logger.warning("Cannot resolve pair/token; refusing BUY for pair %s", pair_id)
                return
            liquidity_usd = latest_snapshot.liquidity_usd if latest_snapshot.liquidity_usd is not None else pair.liquidity_usd
            gate_result = await security_gate_service.evaluate_token(
                chain=pair.chain_id,
                token_address=token.address,
                pair_address=pair.pair_address or "",
                market_snapshot={
                    "liquidity_usd": float(liquidity_usd) if liquidity_usd is not None else None,
                    "buy_count_24h": latest_snapshot.buy_count_24h or 0,
                    "sell_count_24h": latest_snapshot.sell_count_24h or 0,
                    "volume_24h_usd": float(latest_snapshot.volume_24h_usd or 0),
                    "price_usd": float(latest_snapshot.price_usd or 0),
                    "trading_mode": settings.TRADING_MODE,
                },
                # This ARQ entrypoint receives no explicit size; the execution
                # engine applies the configured default after the final veto.
                position_size_usd=None,
            )
            if gate_result.is_blocked or gate_result.is_deferred:
                logger.warning(
                    "Final security veto %s BUY for pair %s: %s",
                    gate_result.status,
                    pair_id,
                    gate_result.reason,
                )
                return

            from app.services.trading.engine import ExecutionEngine
            from app.adapters.blockchain import SolanaJupiterAdapter
            
            # Get first wallet for now (Phase 3 simplified)
            from app.models import Wallet
            result = await session.execute(select(Wallet).limit(1))
            wallet = result.scalars().first()
            if not wallet:
                logger.warning("No wallet found")
                return
            
            # Initialize execution engine
            blockchain_adapter = SolanaJupiterAdapter()
            execution_engine = ExecutionEngine(
                blockchain_adapter,
                blockchain_adapter,
                None,  # Wallet adapter
                blockchain_adapter,
            )
            
            # Execute BUY
            position = await execution_engine.execute_buy(
                session,
                pair_id,
                wallet.id,
                confidence,
                target_tp,
                target_sl,
            )
            
            if position:
                logger.info(f"BUY executed successfully: position {position.id}")
                await EventPublisher.publish(
                    "ORDER_STATUS_CHANGED",
                    {
                        "pair_id": str(pair_id),
                        "position_id": str(position.id),
                        "status": "CONFIRMED",
                        "type": "BUY",
                    },
                )
            else:
                logger.warning(f"BUY execution failed for pair {pair_id}")
            
        except Exception as e:
            logger.error(f"Error executing BUY signal: {e}")


async def monitor_positions_worker(ctx):
    """Worker to monitor open positions and check for TP/SL."""
    logger.warning("Monitoring open positions")
    
    async with async_session_maker() as session:
        try:
            from app.models import Position
            from app.services.portfolio.service import PortfolioService
            from app.services.trading.engine import ExecutionEngine
            from app.adapters.blockchain import SolanaJupiterAdapter

            await _sync_bot_state(session)

            result = await session.execute(
                select(Position).where(Position.status == "OPEN")
            )
            open_positions = result.scalars().all()

            adapter = SolanaJupiterAdapter()
            engine = ExecutionEngine(adapter, adapter, None, adapter)
            
            for position in open_positions:
                try:
                    updated, should_close, reason, exit_fraction = await PortfolioService.update_position_prices(
                        session, position.id
                    )
                    if updated:
                        await EventPublisher.publish(
                            "POSITION_UPDATED",
                            {
                                "position_id": str(position.id),
                                "pair_id": str(position.pair_id),
                                "pnl_usd": float(position.pnl_usd or 0),
                                "pnl_percent": float(position.pnl_percent or 0),
                                "current_price": float(position.current_price or 0),
                            },
                        )

                    if should_close:
                        logger.info("Closing position %s: %s", position.id, reason)
                        trade = await engine.execute_sell(session, position.id, exit_fraction, reason)
                        if trade:
                            await EventPublisher.publish(
                                "ORDER_STATUS_CHANGED",
                                {
                                    "position_id": str(position.id),
                                    "pair_id": str(position.pair_id),
                                    "status": "CONFIRMED",
                                    "type": "SELL",
                                    "reason": reason,
                                },
                            )
                except Exception as e:
                    await session.rollback()
                    logger.exception("Error monitoring position %s", position.id)
            
            logger.warning("Monitored %d open position(s)", len(open_positions))
            
        except Exception:
            logger.exception("Error in position monitor worker")


async def discover_tokens_worker(ctx):
    """Worker to discover new tokens from DEX Screener."""
    logger.info("Starting token discovery worker")
    
    async with async_session_maker() as session:
        try:
            trending_data = await dex_screener_client.get_trending_pairs(chain="solana")
            if not trending_data or not trending_data.get("pairs"):
                gecko_pairs = await gecko_terminal_client.get_trending_pools("solana")
                trending_data = {"pairs": gecko_pairs}
            
            if not trending_data or "pairs" not in trending_data:
                logger.warning("No trending pairs received")
                return
            
            pairs_data = [
                pair for pair in trending_data["pairs"]
                if pair.get("provider") == "geckoterminal"
                or DEXScreenerClient.is_meme_pair_candidate(pair, "solana")
            ][:50]
            logger.info(f"Found {len(pairs_data)} trending pairs")
            
            discovered = 0
            for pair_data in pairs_data:
                try:
                    normalized = (
                        pair_data if pair_data.get("provider") == "geckoterminal"
                        else DEXScreenerClient.normalize_pair_data(pair_data)
                    )
                    
                    chain_id = normalized.get("chain")
                    pair_address = normalized.get("pair_address")
                    base_address = normalized.get("base_token", {}).get("address")
                    quote_address = normalized.get("quote_token", {}).get("address")
                    if not chain_id or not pair_address or not base_address or not quote_address:
                        logger.warning("Skipping incomplete discovered pair: %s", normalized.get("pair_address"))
                        continue
                    
                    await ChainService.create_or_get_chain(session, chain_id)
                    
                    base_token = await TokenService.create_or_get_token(
                        session,
                        chain_id=chain_id,
                        address=normalized["base_token"].get("address", ""),
                        symbol=normalized["base_token"].get("symbol", "UNKNOWN"),
                        name=normalized["base_token"].get("name"),
                        decimals=9 if chain_id == "solana" else 18,
                    )
                    
                    quote_token = await TokenService.create_or_get_token(
                        session,
                        chain_id=chain_id,
                        address=normalized["quote_token"].get("address", ""),
                        symbol=normalized["quote_token"].get("symbol", "UNKNOWN"),
                        name=normalized["quote_token"].get("name"),
                        decimals=9 if chain_id == "solana" else 18,
                    )
                    
                    pair = await PairService.create_or_get_pair(
                        session,
                        chain_id=chain_id,
                        base_token_id=base_token.id,
                        quote_token_id=quote_token.id,
                        dex_name=normalized.get("dex", "unknown"),
                        pair_address=normalized.get("pair_address"),
                        price_usd=normalized.get("price_usd"),
                        liquidity_usd=normalized.get("liquidity", {}).get("usd"),
                    )

                    scan_liquidity = normalized.get("liquidity", {}).get("usd")
                    if scan_liquidity is None or scan_liquidity < settings.SECURITY_SCAN_MIN_LIQUIDITY_USD:
                        logger.info(
                            "Skipping discovered pair %s: Dexscreener liquidity %s below scan minimum $%.2f",
                            pair_address,
                            scan_liquidity,
                            settings.SECURITY_SCAN_MIN_LIQUIDITY_USD,
                        )
                        # Do not watch low-liquidity discovery results. The
                        # pair is retained for history, but never enters the
                        # active trading pipeline.
                        pair.is_watched = False
                        await session.commit()
                        continue

                    if normalized.get("price_usd"):
                        await MarketDataService.save_market_snapshot(
                            session,
                            pair_id=pair.id,
                            price_usd=normalized.get("price_usd"),
                            price_change_5m=normalized.get("price_change", {}).get("m5"),
                            price_change_1h=normalized.get("price_change", {}).get("h1"),
                            price_change_24h=normalized.get("price_change", {}).get("h24"),
                            volume_5m_usd=normalized.get("volume", {}).get("m5"),
                            volume_1h_usd=normalized.get("volume", {}).get("h1"),
                            volume_24h_usd=normalized.get("volume", {}).get("h24"),
                            liquidity_usd=normalized.get("liquidity", {}).get("usd"),
                            buy_count_24h=(normalized.get("transactions", {}).get("h24") or {}).get("buys"),
                            sell_count_24h=(normalized.get("transactions", {}).get("h24") or {}).get("sells"),
                            market_cap_usd=normalized.get("market_cap_usd"),
                            fdv_usd=normalized.get("fdv_usd"),
                        )
                    
                    discovered += 1
                    logger.info(f"Discovered pair {pair.id}: {base_token.symbol}/{quote_token.symbol}")

                    await EventPublisher.publish(
                        "NEW_TOKEN_DISCOVERED",
                        {
                            "pair_id": str(pair.id),
                            "symbol": base_token.symbol,
                            "chain_id": chain_id,
                            "liquidity_usd": float(normalized.get("liquidity", {}).get("usd") or 0),
                        },
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing pair: {e}")
                    await session.rollback()
                    continue

            logger.info("Token discovery completed: %d pairs saved", discovered)
            
        except Exception as e:
            logger.error(f"Error in token discovery worker: {e}")
            await session.rollback()


class WorkerSettings:
    """ARQ worker settings."""

    functions = [
        collect_market_data_worker,
        compute_features_worker,
        assess_risk_worker,
        generate_signals_worker,
        execute_buy_signal_worker,
        monitor_positions_worker,
        discover_tokens_worker,
        process_watched_pairs_pipeline,
    ]

    cron_jobs = [
        cron(collect_market_data_worker, second=0, minute=list(range(60))),
        cron(monitor_positions_worker, second=0, minute=list(range(60))),
        cron(discover_tokens_worker, second=0, minute=list(range(0, 60, 30))),
        cron(process_watched_pairs_pipeline, second=30, minute=list(range(0, 60, 5))),
    ]

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    on_startup = None
    on_shutdown = None
    handle_signals = True
    allow_abort_jobs = True
    job_timeout = 180
    keep_result_ttl = 86400
