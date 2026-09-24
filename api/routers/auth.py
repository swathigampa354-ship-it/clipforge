from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timedelta

from api.core.database import get_db
from api.models.user import User
from api.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from api.schemas.auth import (
    UserCreate,
    UserResponse,
    TokenResponse,
    LoginRequest,
    OAuthCallback,
)
from api.schemas.common import ApiResponse
from api.core.rate_limiter import rate_limiter

router = APIRouter()
security = HTTPBearer()


@router.post("/auth/register", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
@rate_limiter.limit("5/minute")
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, settings.JWT_EXPIRY_MINUTES)

    return ApiResponse(
        data=UserResponse.model_validate(user),
        message="User created successfully",
    ) | {"token": token}


@router.post("/auth/login", response_model=ApiResponse[TokenResponse])
@rate_limiter.limit("10/minute")
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id, settings.JWT_EXPIRY_MINUTES)
    return ApiResponse(
        data=TokenResponse(access_token=token, token_type="bearer"),
        message="Login successful",
    )


@router.get("/auth/me", response_model=ApiResponse[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return ApiResponse(data=UserResponse.model_validate(current_user))


@router.post("/auth/logout")
async def logout():
    return ApiResponse(message="Logged out successfully")


@router.post("/auth/oauth/start")
async def oauth_start():
    return ApiResponse(message="OAuth initiation URL returned")


@router.post("/auth/oauth/callback")
async def oauth_callback(payload: OAuthCallback):
    return ApiResponse(message="OAuth callback processed")


@router.post("/auth/forgot-password")
async def forgot_password(payload: dict):
    return ApiResponse(message="Password reset email sent")


@router.post("/auth/refresh")
async def refresh_token():
    return ApiResponse(message="Token refreshed")
