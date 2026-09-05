import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.models import User, Chain, Token, Pair, MarketSnapshot, Candle
from app.core.security import hash_password
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import desc

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    async def create_user(session: AsyncSession, username: str, email: str, password: str, is_admin: bool = False) -> User:
        """Create new user."""
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_admin=is_admin,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        result = await session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id) -> Optional[User]:
        """Get user by ID."""
        return await session.get(User, user_id)


class ChainService:
    KNOWN_CHAINS = {
        "solana": {
            "name": "Solana",
            "native_token": "SOL",
            "rpc_url": "https://api.mainnet-beta.solana.com",
            "explorer_url": "https://solscan.io",
        },
        "base": {
            "name": "Base",
            "native_token": "ETH",
            "rpc_url": "https://mainnet.base.org",
            "explorer_url": "https://basescan.org",
        },
        "ethereum": {
            "name": "Ethereum",
            "native_token": "ETH",
            "rpc_url": "https://eth.llamarpc.com",
            "explorer_url": "https://etherscan.io",
        },
        "bsc": {
            "name": "BNB Chain",
            "native_token": "BNB",
            "rpc_url": "https://bsc-dataseed.binance.org",
            "explorer_url": "https://bscscan.com",
        },
    }

    @staticmethod
    async def create_or_get_chain(session: AsyncSession, chain_id: str) -> Chain:
        """Create chain or return existing."""
        chain = await session.get(Chain, chain_id)
        if chain:
            return chain

        meta = ChainService.KNOWN_CHAINS.get(
            chain_id,
            {
                "name": chain_id.title(),
                "native_token": "NATIVE",
                "rpc_url": "https://localhost",
                "explorer_url": None,
            },
        )
        chain = Chain(
            id=chain_id,
            name=meta["name"],
            native_token=meta["native_token"],
            rpc_url=meta["rpc_url"],
            explorer_url=meta.get("explorer_url"),
        )
        session.add(chain)
        await session.commit()
        await session.refresh(chain)
        return chain

    @staticmethod
    async def create_chain(session: AsyncSession, chain_id: str, name: str, native_token: str, rpc_url: str) -> Chain:
        """Create new chain."""
        chain = Chain(
            id=chain_id,
            name=name,
            native_token=native_token,
            rpc_url=rpc_url,
        )
        session.add(chain)
        await session.commit()
        await session.refresh(chain)
        return chain

    @staticmethod
    async def get_chain_by_id(session: AsyncSession, chain_id: str) -> Optional[Chain]:
        """Get chain by ID."""
        return await session.get(Chain, chain_id)

    @staticmethod
    async def get_all_chains(session: AsyncSession) -> list[Chain]:
        """Get all active chains."""
        result = await session.execute(select(Chain).where(Chain.is_active == True))
        return result.scalars().all()


class TokenService:
    @staticmethod
    async def create_or_get_token(
        session: AsyncSession,
        chain_id: str,
        address: str,
        symbol: str,
        name: Optional[str] = None,
        decimals: int = 18,
        developer_address: Optional[str] = None,
    ) -> Token:
        """Create token or get existing."""
        result = await session.execute(
            select(Token).where(
                (Token.chain_id == chain_id) & (Token.address == address)
            )
        )
        token = result.scalars().first()
        
        if token:
            if developer_address and token.developer_address != developer_address:
                token.developer_address = developer_address
                await session.commit()
            return token
        
        token = Token(
            chain_id=chain_id,
            address=address,
            symbol=symbol,
            name=name,
            decimals=decimals,
            developer_address=developer_address,
        )
        session.add(token)
        await session.commit()
        await session.refresh(token)
        return token


class PairService:
    @staticmethod
    async def create_or_get_pair(
        session: AsyncSession,
        chain_id: str,
        base_token_id,
        quote_token_id,
        dex_name: str,
        pair_address: Optional[str] = None,
        price_usd: Optional[Decimal] = None,
        liquidity_usd: Optional[Decimal] = None,
        is_watched: bool = False,
    ) -> Pair:
        """Create pair or get existing."""
        result = await session.execute(
            select(Pair).where(
                (Pair.chain_id == chain_id)
                & (Pair.base_token_id == base_token_id)
                & (Pair.quote_token_id == quote_token_id)
                & (Pair.dex_name == dex_name)
            )
        )
        pair = result.scalars().first()

        if pair:
            if pair_address and not pair.pair_address:
                pair.pair_address = pair_address
            if price_usd is not None:
                pair.price_usd = price_usd
            if liquidity_usd is not None:
                pair.liquidity_usd = liquidity_usd
            if is_watched:
                pair.is_watched = True
            await session.commit()
            await session.refresh(pair)
            return pair

        pair = Pair(
            chain_id=chain_id,
            base_token_id=base_token_id,
            quote_token_id=quote_token_id,
            dex_name=dex_name,
            pair_address=pair_address,
            price_usd=price_usd,
            liquidity_usd=liquidity_usd,
            is_watched=is_watched,
        )
        session.add(pair)
        await session.commit()
        await session.refresh(pair)
        return pair

    @staticmethod
    async def get_watched_pairs(session: AsyncSession, chain_id: Optional[str] = None) -> list[Pair]:
        """Get all watched pairs."""
        query = select(Pair).where(Pair.is_watched == True)
        if chain_id:
            query = query.where(Pair.chain_id == chain_id)
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def set_watched(session: AsyncSession, pair_id, is_watched: bool) -> Pair:
        """Set pair as watched/unwatched."""
        pair = await session.get(Pair, pair_id)
        if pair:
            pair.is_watched = is_watched
            await session.commit()
            await session.refresh(pair)
        return pair


class MarketDataService:
    @staticmethod
    def aggregate_candles(candles: list[Candle], minutes: int) -> list[dict]:
        """Aggregate stored one-minute OHLCV candles without inventing prices."""
        if minutes <= 1:
            return [{"timestamp": candle.timestamp, "open": candle.open, "high": candle.high, "low": candle.low, "close": candle.close, "volume": candle.volume or Decimal("0")} for candle in candles]
        buckets: dict[datetime, list[Candle]] = {}
        for candle in candles:
            timestamp = candle.timestamp.replace(second=0, microsecond=0)
            bucket = timestamp - timedelta(minutes=timestamp.minute % minutes)
            buckets.setdefault(bucket, []).append(candle)
        aggregated = []
        for bucket, rows in sorted(buckets.items()):
            rows.sort(key=lambda row: row.timestamp)
            aggregated.append({"timestamp": bucket, "open": rows[0].open, "high": max(row.high for row in rows), "low": min(row.low for row in rows), "close": rows[-1].close, "volume": sum((row.volume or Decimal("0") for row in rows), Decimal("0"))})
        return aggregated

    @staticmethod
    async def get_candles(session: AsyncSession, pair_id, timeframe: str = "minute", limit: int = 100) -> list[Candle]:
        if timeframe in {"5m", "15m", "hour", "1h"}:
            minute_candles = await MarketDataService.get_candles(session, pair_id, "minute", min(limit * (60 if timeframe in {"hour", "1h"} else int(timeframe[:-1])), 500))
            minutes = 60 if timeframe in {"hour", "1h"} else int(timeframe[:-1])
            aggregated = MarketDataService.aggregate_candles(minute_candles, minutes)
            return aggregated[-limit:]  # type: ignore[return-value]
        result = await session.execute(
            select(Candle).where(Candle.pair_id == pair_id, Candle.timeframe == timeframe)
            .order_by(Candle.timestamp.desc()).limit(limit)
        )
        return list(reversed(result.scalars().all()))

    @staticmethod
    async def save_candles(session: AsyncSession, pair_id, candles: list[dict], timeframe: str = "minute") -> int:
        """Persist valid OHLCV candles without duplicating timestamps."""
        values = []
        for row in candles:
            try:
                timestamp = datetime.utcfromtimestamp(float(row["timestamp"]))
                values.append({"pair_id": pair_id, "timeframe": timeframe, "open": Decimal(str(row["open"])), "high": Decimal(str(row["high"])), "low": Decimal(str(row["low"])), "close": Decimal(str(row["close"])), "volume": Decimal(str(row.get("volume", 0))), "timestamp": timestamp})
            except Exception:
                continue
        if not values:
            return 0
        result = await session.execute(insert(Candle).values(values).on_conflict_do_nothing(constraint="uq_candle_pair_timeframe_timestamp"))
        await session.commit()
        return result.rowcount or 0

    @staticmethod
    async def save_market_snapshot(
        session: AsyncSession,
        pair_id,
        price_usd: Decimal,
        price_change_1m: Optional[Decimal] = None,
        price_change_5m: Optional[Decimal] = None,
        price_change_1h: Optional[Decimal] = None,
        price_change_24h: Optional[Decimal] = None,
        volume_1m_usd: Optional[Decimal] = None,
        volume_5m_usd: Optional[Decimal] = None,
        volume_1h_usd: Optional[Decimal] = None,
        volume_24h_usd: Optional[Decimal] = None,
        liquidity_usd: Optional[Decimal] = None,
        buy_volume_24h: Optional[Decimal] = None,
        sell_volume_24h: Optional[Decimal] = None,
        buy_count_24h: Optional[int] = None,
        sell_count_24h: Optional[int] = None,
        market_cap_usd: Optional[Decimal] = None,
        fdv_usd: Optional[Decimal] = None,
    ) -> MarketSnapshot:
        """Save market snapshot."""
        snapshot = MarketSnapshot(
            pair_id=pair_id,
            price_usd=price_usd,
            price_change_1m=price_change_1m,
            price_change_5m=price_change_5m,
            price_change_1h=price_change_1h,
            price_change_24h=price_change_24h,
            volume_1m_usd=volume_1m_usd,
            volume_5m_usd=volume_5m_usd,
            volume_1h_usd=volume_1h_usd,
            volume_24h_usd=volume_24h_usd,
            liquidity_usd=liquidity_usd,
            buy_volume_24h=buy_volume_24h,
            sell_volume_24h=sell_volume_24h,
            buy_count_24h=buy_count_24h,
            sell_count_24h=sell_count_24h,
            market_cap_usd=market_cap_usd,
            fdv_usd=fdv_usd,
        )
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        return snapshot

    @staticmethod
    async def get_latest_snapshot(session: AsyncSession, pair_id) -> Optional[MarketSnapshot]:
        """Get latest market snapshot for pair."""
        result = await session.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.pair_id == pair_id)
            .order_by(MarketSnapshot.timestamp.desc())
            .limit(1)
        )
        return result.scalars().first()
