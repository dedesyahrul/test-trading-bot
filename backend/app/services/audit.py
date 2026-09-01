"""Persistent, redacted audit trail for security and trading operations."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog


SENSITIVE_KEYS = {"password", "password_hash", "token", "access_token", "secret", "private_key", "wallet_private_key"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else _redact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


class AuditService:
    @staticmethod
    async def record(session: AsyncSession, action: str, resource: str, user_id=None,
                     resource_id=None, details: dict | None = None) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action[:50],
            resource=resource[:50],
            resource_id=str(resource_id) if resource_id is not None else None,
            details=_redact(details or {}),
        )
        session.add(entry)
        await session.flush()
        return entry
