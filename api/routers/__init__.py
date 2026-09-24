"""
Update router aggregator to include reframe router
"""
from fastapi import APIRouter
from api.routers import auth_router, projects_router, videos_router, clips_router, renders_router, ai_router, usage_router, api_keys_router, subscriptions_router, reframe_router
from api.routers.captions import router as captions_router

api_router = APIRouter()

api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(projects_router, tags=["Projects"])
api_router.include_router(videos_router, tags=["Videos"])
api_router.include_router(clips_router, tags=["Clips"])
api_router.include_router(reframe_router, tags=["Reframe"])
api_router.include_router(renders_router, tags=["Renders"])
api_router.include_router(ai_router, tags=["AI"])
api_router.include_router(captions_router, tags=["Captions"])
api_router.include_router(usage_router, tags=["Usage"])
api_router.include_router(api_keys_router, tags=["API Keys"])
api_router.include_router(subscriptions_router, tags=["Subscriptions"])

from api.models import (
    User, Organization, Member, Project, Video, Transcript,
    ClipCandidate, Clip, CaptionStyle, RenderJob, RenderOutput,
    AIJob, UsageRecord, Subscription, APIKey, ScheduledPost,
    CameraPathData, SpeakerData, FaceDetectionData, ReframeJob,
)