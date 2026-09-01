from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token, create_access_token, verify_password
from app.core.security_hardening import RateLimiter, AuditLogger, InputValidator
from app.schemas import UserCreate, UserResponse
from app.services import UserService
from app.services.audit import AuditService
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
audit_logger = AuditLogger()
login_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_db_session)):
    """Register new user."""
    if not InputValidator.validate_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username format",
        )
    if not InputValidator.validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format",
        )

    existing_user = await UserService.get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    existing_email = await UserService.get_user_by_email(session, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = await UserService.create_user(
        session,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )
    await AuditService.record(session, "REGISTER", "USER", user_id=user.id, resource_id=user.id,
                              details={"username": user.username})
    await session.commit()
    logger.info(f"New user registered: {user.username}")
    return user


@router.post("/auth/login")
async def login(
    username: str,
    password: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Login user and return access token."""
    client_ip = request.client.host if request.client else "unknown"
    if login_rate_limiter.is_rate_limited(f"login:{client_ip}"):
        audit_logger.log_auth_attempt(username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = await UserService.get_user_by_username(session, username)
    if not user:
        await AuditService.record(session, "LOGIN_FAILED", "AUTH", details={"username": username, "ip": client_ip})
        await session.commit()
        audit_logger.log_auth_attempt(username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(password, user.password_hash):
        await AuditService.record(session, "LOGIN_FAILED", "AUTH", details={"username": username, "ip": client_ip})
        await session.commit()
        audit_logger.log_auth_attempt(username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        audit_logger.log_auth_attempt(username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "is_admin": bool(user.is_admin)},
        expires_delta=timedelta(minutes=60),
    )
    await AuditService.record(session, "LOGIN", "AUTH", user_id=user.id, resource_id=user.id,
                              details={"ip": client_ip})
    await session.commit()
    audit_logger.log_auth_attempt(username, True, client_ip)
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Get current user info."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = await UserService.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
