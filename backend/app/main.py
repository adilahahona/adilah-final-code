"""
FastAPI application entry point for ESG Analytics System.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from app.core.config import settings
from app.core.logging import setup_logging,RequestIDMiddleware, request_id_ctx
from app.api.v1 import routes_health, routes_orgs, routes_mapping, routes_ingestion, routes_coverage, routes_features, routes_ml, routes_documents, routes_nlp


# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)


# Create FastAPI application
app = FastAPI(
    title="ESG Analytics System",
    description="End-to-end ESG data ingestion, mapping, ML pipeline, and scoring system",
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Add request ID middleware first (executes last)
app.add_middleware(RequestIDMiddleware)

# Configure CORS - added last so it executes first
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-request-id"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with consistent format."""
    request_id = request_id_ctx.get()
    errors = []
    
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"])
        errors.append({
            "code": "VALIDATION_ERROR",
            "message": error["msg"],
            "field": field
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": errors[0] if len(errors) == 1 else {
                "code": "VALIDATION_ERROR",
                "message": f"{len(errors)} validation errors",
                "details": errors
            },
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with consistent format."""
    request_id = request_id_ctx.get()
    logger.exception("Unhandled exception", extra={"request_id": request_id})
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            },
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


# Include routers
app.include_router(routes_health.router)
app.include_router(routes_orgs.router)
app.include_router(routes_mapping.router)
app.include_router(routes_ingestion.router)
app.include_router(routes_coverage.router)
app.include_router(routes_features.router)
app.include_router(routes_ml.router)
app.include_router(routes_documents.router)
app.include_router(routes_nlp.router)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(
        "Starting ESG Analytics System",
        extra={
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "environment": settings.ENVIRONMENT,
            "git_sha": settings.GIT_SHA
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down ESG Analytics System")
