from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_admin: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    settings: Optional[dict] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChainResponse(BaseModel):
    id: str
    name: str
    native_token: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    id: UUID
    chain_id: str
    address: str
    symbol: str
    name: Optional[str]
    decimals: int

    class Config:
        from_attributes = True


class PairResponse(BaseModel):
    id: UUID
    chain_id: str
    base_token_id: UUID
    quote_token_id: UUID
    dex_name: str
    price_usd: Optional[Decimal]
    liquidity_usd: Optional[Decimal]
    is_watched: bool

    class Config:
        from_attributes = True


class MarketSnapshotResponse(BaseModel):
    id: UUID
    pair_id: UUID
    price_usd: Decimal
    price_change_1h: Optional[Decimal]
    price_change_24h: Optional[Decimal]
    volume_24h_usd: Optional[Decimal]
    liquidity_usd: Optional[Decimal]
    timestamp: datetime

    class Config:
        from_attributes = True


class RiskAssessmentResponse(BaseModel):
    id: UUID
    pair_id: UUID
    risk_score: Decimal
    risk_level: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SignalResponse(BaseModel):
    id: UUID
    pair_id: UUID
    signal_type: str
    confidence: Decimal
    reasons_pro: List[str]
    reasons_contra: List[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    id: UUID
    pair_id: UUID
    entry_price: Decimal
    entry_amount: Decimal
    current_price: Optional[Decimal]
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    status: str
    pnl_usd: Optional[Decimal]
    pnl_percent: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    id: UUID
    position_id: UUID
    trade_type: str
    price: Decimal
    amount: Decimal
    tx_hash: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BotStateResponse(BaseModel):
    state: str
    trading_mode: str
    last_update: datetime
    error_message: Optional[str]

    class Config:
        from_attributes = True
