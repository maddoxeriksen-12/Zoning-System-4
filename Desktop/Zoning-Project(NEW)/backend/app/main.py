"""
Zoning Project API - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from .core.config import settings
from .core.database import create_tables, get_db
from .core.security import (
    RateLimitMiddleware,
    CSRFMiddleware,
    SecurityHeadersMiddleware,
    GrokRateLimitMiddleware,
    rate_limit_exceeded_handler
)
# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format=settings.LOG_FORMAT
)

logger = logging.getLogger(__name__)

try:
    from .api.documents import router as documents_router
    logger.info("Documents router imported successfully")
except Exception as e:
    logger.error(f"Failed to import documents router: {e}")
    documents_router = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Zoning Project API...")

    # Create database tables on startup
    try:
        create_tables()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    logger.info("Shutting down Zoning Project API...")


# Create FastAPI app
app = FastAPI(
    title="Zoning Project API",
    description="AI-powered zoning document processing and search API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Add security middlewares (commented out for local development)
# app.add_middleware(SecurityHeadersMiddleware)
# app.add_middleware(GrokRateLimitMiddleware)
# app.add_middleware(RateLimitMiddleware)
# app.add_middleware(CSRFMiddleware)

# Rate limiting error handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Include API routers
if documents_router:
    app.include_router(
        documents_router,
        prefix=settings.API_V1_STR,
        tags=["Documents"]
    )
    logger.info(f"Documents router included with prefix: {settings.API_V1_STR}")
else:
    logger.error("Documents router not available, skipping inclusion")


@app.get("/health")
async def health_check(db=Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Zoning Project API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )