from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from api.core.database import get_db
from api.core.auth import get_current_user
from api.schemas.common import ApiResponse
from api.models.user import User

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(data={"key": "ck_live_placeholder", "name": key_data.get("name")}, message="API key created")


@router.get("", response_model=ApiResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(data=[], message="API keys listed")


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(message="API key deleted")


@router.get("/{key_id}/usage")
async def get_key_usage(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(data={"requests": 0, "limit": 100}, message="Key usage")