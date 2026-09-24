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
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(data={
        "plan": "free",
        "credits_total": 100,
        "credits_used": 0,
        "status": "active",
        "current_period_start": "2026-09-01",
        "current_period_end": "2026-10-01",
    }, message="Subscription retrieved")


@router.post("/checkout", response_model=ApiResponse)
async def create_checkout(
    checkout_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(data={"checkout_url": "https://checkout.stripe.com/placeholder"}, message="Checkout created")


@router.get("/portal", response_model=ApiResponse)
async def get_billing_portal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(data={"portal_url": "https://billing.stripe.com/placeholder"}, message="Billing portal URL")


@router.post("/webhook")
async def stripe_webhook(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(message="Webhook received")