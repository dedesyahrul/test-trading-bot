import logging
from arq import cron
from app.core.config import settings
from app.core.database import async_session_maker
from app.services import PairService, MarketDataService, TokenService, ChainService
from app.adapters.dexscreener import DEXScreenerClient
from app.services.features.engine import FeatureEngineering
from app.services.risk.engine import RiskEngine
from app.services.strategy.engine import strategy_runner
from sqlalchemy import select
from app.models import Pair, Signal
import asyncio

logger = logging.getLogger(__name__)

dex_screener_client = DEXScreenerClient()


async def collect_market_data_worker(ctx):
    """Worker to collect market data for all watched pairs."""
    logger.info("Starting market data collection worker")
    
    async with async_session_maker() as session:
        # Get all watched pairs
        watched_pairs = await PairService.get_watched_pairs(session)
        logger.info(f"Found {len(watched_pairs)} watched pairs")
        
        for pair in watched_pairs:
            try:
                # Get pair details from DEX Screener
                pair_data = await dex_screener_client.get_pair_by_chain_and_address(
                    chain=pair.chain_id,
                    pair_address=pair.pair_address,
                )
                
                if not pair_data or "pair" not in pair_data:
                    logger.warning(f"No data received for pair {pair.id}")
                    continue
                
                normalized = DEXScreenerClient.normalize_pair_data(pair_data["pair"])
                
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
                logger.info(f"Market data saved for pair {pair.id}")
                
                # Enqueue feature computation
                # (In production, would enqueue to ARQ job queue)
                # await ctx.queue.enqueue(compute_features_worker, pair.id)
                
            except Exception as e:
                logger.error(f"Error collecting market data for pair {pair.id}: {e}")
                continue
    
    logger.info("Market data collection worker completed")


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
            # Get latest market snapshot and features
            latest_snapshot = await MarketDataService.get_latest_snapshot(session, pair_id)
            if not latest_snapshot:
                logger.warning(f"No market data for pair {pair_id}")
                return
            
            # Assess risk
            risk_assessment = await RiskEngine.assess_risk(
                session,
                pair_id,
                latest_snapshot,
            )
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
            
        except Exception as e:
            logger.error(f"Error generating signals for pair {pair_id}: {e}")


async def discover_tokens_worker(ctx):
    """Worker to discover new tokens from DEX Screener."""
    logger.info("Starting token discovery worker")
    
    async with async_session_maker() as session:
        try:
            # Get trending pairs from DEX Screener
            trending_data = await dex_screener_client.get_trending_pairs()
            
            if not trending_data or "pairs" not in trending_data:
                logger.warning("No trending pairs received")
                return
            
            pairs_data = trending_data["pairs"][:50]  # Limit to 50 for now
            logger.info(f"Found {len(pairs_data)} trending pairs")
            
            for pair_data in pairs_data:
                try:
                    normalized = DEXScreenerClient.normalize_pair_data(pair_data)
                    
                    chain_id = normalized.get("chain")
                    if not chain_id:
                        continue
                    
                    # Get or create tokens
                    base_token = await TokenService.create_or_get_token(
                        session,
                        chain_id=chain_id,
                        address=normalized["base_token"].get("address", ""),
                        symbol=normalized["base_token"].get("symbol", "UNKNOWN"),
                        name=normalized["base_token"].get("name"),
                    )
                    
                    quote_token = await TokenService.create_or_get_token(
                        session,
                        chain_id=chain_id,
                        address=normalized["quote_token"].get("address", ""),
                        symbol=normalized["quote_token"].get("symbol", "UNKNOWN"),
                        name=normalized["quote_token"].get("name"),
                    )
                    
                    # Create or get pair
                    pair = await PairService.create_or_get_pair(
                        session,
                        chain_id=chain_id,
                        base_token_id=base_token.id,
                        quote_token_id=quote_token.id,
                        dex_name=normalized.get("dex", "unknown"),
                        price_usd=normalized.get("price_usd"),
                        liquidity_usd=normalized.get("liquidity", {}).get("usd"),
                    )
                    
                    logger.info(f"Discovered pair {pair.id}: {base_token.symbol}/{quote_token.symbol}")
                    
                except Exception as e:
                    logger.error(f"Error processing pair: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in token discovery worker: {e}")
    
    logger.info("Token discovery worker completed")


class WorkerSettings:
    """ARQ worker settings."""
    
    functions = [
        collect_market_data_worker,
        compute_features_worker,
        assess_risk_worker,
        generate_signals_worker,
        discover_tokens_worker,
    ]
    
    cron_jobs = [
        cron(collect_market_data_worker, second=0, minute=range(0, 60, 1)),  # Every minute
        cron(discover_tokens_worker, second=0, minute=range(0, 60, 30)),  # Every 30 minutes
    ]
    
    on_startup = None
    on_shutdown = None
    handle_signals = True
    allow_abort_jobs = True
    job_timeout = 600
    keep_result_ttl = 86400


class WorkerSettings:
    """ARQ worker settings."""
    
    functions = [
        collect_market_data_worker,
        discover_tokens_worker,
    ]
    
    cron_jobs = [
        cron(collect_market_data_worker, second=0, minute=range(0, 60, 1)),  # Every minute
        cron(discover_tokens_worker, second=0, minute=range(0, 60, 30)),  # Every 30 minutes
    ]
    
    on_startup = None
    on_shutdown = None
    handle_signals = True
    allow_abort_jobs = True
    job_timeout = 600
    keep_result_ttl = 86400
