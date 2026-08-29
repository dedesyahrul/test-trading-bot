import logging
from arq import cron
from app.core.config import settings
from app.core.database import async_session_maker
from app.services import PairService, MarketDataService, TokenService, ChainService
from app.adapters.dexscreener import DEXScreenerClient
from sqlalchemy import select
from app.models import Pair
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
                await MarketDataService.save_market_snapshot(
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
                    market_cap_usd=normalized.get("market_cap_usd"),
                    fdv_usd=normalized.get("fdv_usd"),
                )
                logger.info(f"Market data saved for pair {pair.id}")
                
            except Exception as e:
                logger.error(f"Error collecting market data for pair {pair.id}: {e}")
                continue
    
    logger.info("Market data collection worker completed")


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
