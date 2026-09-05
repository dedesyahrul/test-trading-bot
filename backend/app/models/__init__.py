import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Integer, Text, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Chain(Base):
    __tablename__ = "chains"

    id = Column(String(20), primary_key=True)  # e.g., "solana", "ethereum"
    name = Column(String(100), nullable=False)
    native_token = Column(String(10), nullable=False)
    rpc_url = Column(String(255), nullable=False)
    explorer_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    chain_id = Column(String(20), ForeignKey("chains.id"), nullable=False)
    address = Column(String(255), nullable=False)
    label = Column(String(100))
    is_active = Column(Boolean, default=True)
    max_trade_amount = Column(Numeric(20, 8))
    daily_loss_limit = Column(Numeric(20, 8))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("user_id", "chain_id", name="uq_wallet_user_chain"),
    )


class Token(Base):
    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chain_id = Column(String(20), ForeignKey("chains.id"), nullable=False)
    address = Column(String(255), nullable=False)
    symbol = Column(String(20), nullable=False)
    name = Column(String(255))
    decimals = Column(Integer, default=18)
    developer_address = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("chain_id", "address", name="uq_token_chain_address"),
    )


class Pair(Base):
    __tablename__ = "pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chain_id = Column(String(20), ForeignKey("chains.id"), nullable=False)
    base_token_id = Column(UUID(as_uuid=True), ForeignKey("tokens.id"), nullable=False)
    quote_token_id = Column(UUID(as_uuid=True), ForeignKey("tokens.id"), nullable=False)
    dex_name = Column(String(50), nullable=False)
    pair_address = Column(String(255))
    liquidity_usd = Column(Numeric(20, 2))
    price_usd = Column(Numeric(20, 8))
    is_watched = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("chain_id", "base_token_id", "quote_token_id", "dex_name", name="uq_pair_unique"),
    )


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("pairs.id"), nullable=False, index=True)
    price_usd = Column(Numeric(20, 8), nullable=False)
    price_change_1m = Column(Numeric(10, 4))
    price_change_5m = Column(Numeric(10, 4))
    price_change_1h = Column(Numeric(10, 4))
    price_change_24h = Column(Numeric(10, 4))
    volume_1m_usd = Column(Numeric(20, 2))
    volume_5m_usd = Column(Numeric(20, 2))
    volume_1h_usd = Column(Numeric(20, 2))
    volume_24h_usd = Column(Numeric(20, 2))
    liquidity_usd = Column(Numeric(20, 2))
    buy_volume_24h = Column(Numeric(20, 2))
    sell_volume_24h = Column(Numeric(20, 2))
    buy_count_24h = Column(Integer)
    sell_count_24h = Column(Integer)
    market_cap_usd = Column(Numeric(20, 2))
    fdv_usd = Column(Numeric(20, 2))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        UniqueConstraint("pair_id", "timestamp", name="uq_snapshot_pair_timestamp"),
    )


class Candle(Base):
    """Timestamped OHLCV candle used for chart intelligence."""
    __tablename__ = "candles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("pairs.id"), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, default="minute")
    open = Column(Numeric(20, 8), nullable=False)
    high = Column(Numeric(20, 8), nullable=False)
    low = Column(Numeric(20, 8), nullable=False)
    close = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 2))
    timestamp = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("pair_id", "timeframe", "timestamp", name="uq_candle_pair_timeframe_timestamp"),
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("pairs.id"), nullable=False, index=True)
    risk_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    liquidity_risk = Column(Numeric(5, 2))
    holder_risk = Column(Numeric(5, 2))
    contract_risk = Column(Numeric(5, 2))
    developer_risk = Column(Numeric(5, 2))
    manipulation_risk = Column(Numeric(5, 2))
    volatility_risk = Column(Numeric(5, 2))
    rug_pull_risk = Column(Numeric(5, 2))
    slippage_risk = Column(Numeric(5, 2))
    execution_risk = Column(Numeric(5, 2))
    reasons = Column(JSON, default=[])
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Feature(Base):
    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("pairs.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Price features
    return_1m = Column(Numeric(10, 6))
    return_5m = Column(Numeric(10, 6))
    return_1h = Column(Numeric(10, 6))
    volatility_1h = Column(Numeric(10, 6))
    momentum_1h = Column(Numeric(10, 6))
    
    # Volume features
    volume_growth_1h = Column(Numeric(10, 6))
    volume_acceleration = Column(Numeric(10, 6))
    volume_spike = Column(Numeric(10, 6))
    
    # Transaction features
    buy_sell_ratio_1h = Column(Numeric(10, 6))
    buy_pressure = Column(Numeric(10, 6))
    
    # Liquidity features
    liquidity_change = Column(Numeric(10, 6))
    liquidity_ratio = Column(Numeric(10, 6))
    
    # Raw data
    raw_data = Column(JSON, default={})
    
    __table_args__ = (
        UniqueConstraint("pair_id", "timestamp", name="uq_feature_pair_timestamp"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("pairs.id"), nullable=False, index=True)
    model_id = Column(String(50), nullable=False)
    model_version = Column(String(20), nullable=False)
    prediction_type = Column(String(50), nullable=False)  # e.g., "price_movement_5m"
    probability = Column(Numeric(5, 4), nullable=False)  # 0.0 to 1.0
    confidence = Column(Numeric(5, 4), nullable=False)
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("pairs.id"), nullable=False, index=True)
    strategy_id = Column(String(50), nullable=False)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD, SKIP
    confidence = Column(Numeric(5, 4), nullable=False)
    reasons_pro = Column(JSON, default=[])
    reasons_contra = Column(JSON, default=[])
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Position(Base):
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("pairs.id"), nullable=False)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    entry_amount = Column(Numeric(20, 8), nullable=False)
    current_price = Column(Numeric(20, 8))
    current_amount = Column(Numeric(20, 8))
    initial_stop_loss = Column(Numeric(20, 8))
    highest_price = Column(Numeric(20, 8))
    profit_lock_price = Column(Numeric(20, 8))
    exit_pressure = Column(Numeric(5, 2), default=0)
    partial_exit_count = Column(Integer, default=0)
    entry_decision_score = Column(Numeric(5, 2))
    entry_thesis = Column(JSON, default={})
    decision_id = Column(UUID(as_uuid=True), ForeignKey("trade_decisions.id"), index=True)
    exit_reason = Column(String(40))
    mae_usd = Column(Numeric(20, 2))
    mfe_usd = Column(Numeric(20, 2))
    thesis_invalidated = Column(Boolean, default=False)
    stop_loss = Column(Numeric(20, 8))
    take_profit = Column(Numeric(20, 8))
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, ERROR
    pnl_usd = Column(Numeric(20, 2))
    pnl_percent = Column(Numeric(10, 4))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    closed_at = Column(DateTime)


class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("trade_decisions.id"), index=True)
    trade_type = Column(String(10), nullable=False)  # BUY, SELL
    price = Column(Numeric(20, 8), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    fee_usd = Column(Numeric(20, 8))
    tx_hash = Column(String(255), unique=True, nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, CONFIRMED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    confirmed_at = Column(DateTime)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    resource = Column(String(50), nullable=False)
    resource_id = Column(String(255))
    details = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    strategy_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BotState(Base):
    __tablename__ = "bot_state"

    id = Column(Integer, primary_key=True)
    state = Column(String(20), default="STOPPED")  # STOPPED, STARTING, RUNNING, PAUSED, STOPPING, ERROR, EMERGENCY_STOP
    trading_mode = Column(String(10), default="PAPER")  # PAPER, LIVE
    risk_config = Column(JSON, default={
        "max_position_size_usd": 1000,
        "max_daily_loss_usd": 500,
        "max_positions": 5,
        "min_liquidity_usd": 5000,
        "max_risk_score": 50,
    })
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text)
    circuit_state = Column(String(20), default="RUNNING")
    consecutive_failures = Column(Integer, default=0)
    daily_loss_usd = Column(Numeric(20, 2), default=0)
    last_failure_at = Column(DateTime)


class TradeDecision(Base):
    """Auditable record of each strategy/risk decision."""
    __tablename__ = "trade_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("pairs.id"), nullable=False, index=True)
    strategy_id = Column(String(50), nullable=False)
    decision = Column(String(20), nullable=False)
    signal_type = Column(String(20))
    confidence = Column(Numeric(5, 4))
    risk_score = Column(Numeric(5, 2))
    risk_level = Column(String(20))
    position_size_usd = Column(Numeric(20, 8))
    decision_score = Column(Numeric(5, 2))
    data_quality = Column(String(20))
    features = Column(JSON, default={})
    reasons = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# Register the audit model with SQLAlchemy/Alembic.
from app.models.security_audit_log import SecurityAuditLog  # noqa: E402,F401
from app.models.scam_registry import ScamRegistry  # noqa: E402,F401
