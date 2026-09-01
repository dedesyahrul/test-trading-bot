from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token
from app.models import AuditLog

router = APIRouter(tags=["audit"], prefix="/audit")


@router.get("/logs")
async def list_audit_logs(
    action: str | None = Query(None, max_length=50),
    resource: str | None = Query(None, max_length=50),
    limit: int = Query(50, ge=1, le=200),
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    query = select(AuditLog)
    if not payload.get("is_admin"):
        query = query.where(AuditLog.user_id == payload.get("sub"))
    if action:
        query = query.where(AuditLog.action == action)
    if resource:
        query = query.where(AuditLog.resource == resource)
    result = await session.execute(query.order_by(desc(AuditLog.created_at)).limit(limit))
    return {"logs": [
        {
            "id": str(entry.id), "user_id": str(entry.user_id) if entry.user_id else None,
            "action": entry.action, "resource": entry.resource, "resource_id": entry.resource_id,
            "details": entry.details or {}, "created_at": entry.created_at.isoformat(),
        }
        for entry in result.scalars().all()
    ]}
