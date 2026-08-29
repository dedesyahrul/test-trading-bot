from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token, create_access_token, verify_password
from app.schemas import UserCreate, UserResponse
from app.services import UserService
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_db_session)):
    """Register new user."""
    # Check if user exists
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
    logger.info(f"New user registered: {user.username}")
    return user


@router.post("/auth/login")
async def login(username: str, password: str, session: AsyncSession = Depends(get_db_session)):
    """Login user and return access token."""
    user = await UserService.get_user_by_username(session, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=timedelta(minutes=60),
    )
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
