from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.routers import notifications, health
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events"""
    logger.info("Starting API Gateway Service")
    yield
    logger.info("Shutting down API Gateway Service")


app = FastAPI(
    title="Notification API Gateway",
    version="1.0.0",
    description="API Gateway for distributed notification system",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)

# Routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc),
            "data": None,
            "meta": None
        }
    )


@app.get("/")
async def root():
    return {
        "service": "Notification API Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

