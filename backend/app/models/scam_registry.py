"""Curated addresses associated with confirmed scam activity."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ScamRegistry(Base):
    __tablename__ = "scam_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String(255), nullable=False, unique=True, index=True)
    address_type = Column(String(30), nullable=False, index=True)
    scam_type = Column(String(50), nullable=False)
    reported_by = Column(String(100))
    confidence = Column(Numeric(3, 2), nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
