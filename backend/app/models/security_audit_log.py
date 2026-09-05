"""SecurityAuditLog Model for tracking security gate decisions

Tambahkan ini ke backend/app/models/__init__.py atau models.py
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base


class SecurityAuditLog(Base):
    """
    Audit log untuk security gate decisions.
    Mencatat setiap token yang di-BLOCK oleh security gate
    untuk monitoring, debugging, dan analytics.
    """
    __tablename__ = 'security_audit_log'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_id = Column(UUID(as_uuid=True), ForeignKey('pairs.id'), nullable=True, index=True)
    block_reason = Column(String(255), nullable=True)
    block_details = Column(Text, nullable=True)  # JSON string dengan full findings
    security_score = Column(Integer, nullable=True)  # 0-100 score
    blocked_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    auto_unblock_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<SecurityAuditLog pair_id={self.pair_id} reason={self.block_reason} score={self.security_score}>"
