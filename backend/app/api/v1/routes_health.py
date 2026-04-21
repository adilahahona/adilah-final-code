"""
Health and metadata endpoints.
"""
from fastapi import APIRouter
from datetime import datetime

from app.models.common import HealthResponse, MetaResponse
from app.core.config import settings


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service health status and current timestamp.
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow()
    )


@router.get("/api/v1/meta", response_model=MetaResponse, tags=["Meta"])
async def get_metadata():
    """
    Get service metadata.
    
    Returns service name, version, git SHA, and environment.
    """
    return MetaResponse(
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        git_sha=settings.GIT_SHA,
        environment=settings.ENVIRONMENT
    )
