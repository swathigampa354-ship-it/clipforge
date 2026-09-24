from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from api.core.database import get_db
from api.core.auth import get_current_user
from api.schemas.common import ApiResponse
from api.models.user import User

router = APIRouter()


@router.get("", response_model=ApiResponse)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(data={
        "credits_used": 0,
        "credits_balance": 100,
        "processing_minutes_used": 0,
        "rendering_minutes_used": 0,
        "ai_calls_used": 0,
        "storage_used_mb": 0,
    }, message="Usage retrieved")


@router.get("/overview", response_model=ApiResponse)
async def get_usage_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(data={
        "this_month": {
            "processing_minutes": 0,
            "rendering_minutes": 0,
            "ai_calls": 0,
            "credits_consumed": 0,
        },
        "last_month": {
            "processing_minutes": 0,
            "rendering_minutes": 0,
            "ai_calls": 0,
            "credits_consumed": 0,
        },
        "plan": {"name": "Free", "credits_total": 100, "reset_date": "2026-10-01"},
    }, message="Usage overview")


@router.get("/history")
async def get_usage_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    return ApiResponse(data=[], message="Usage history")