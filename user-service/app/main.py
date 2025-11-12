from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import users, health
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events"""
    logger.info("Starting User Service")
    yield
    logger.info("Shutting down User Service")


app = FastAPI(
    title="User Service",
    version="1.0.0",
    description="User management service for notification system",
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

# Routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])


@app.get("/")
async def root():
    return {
        "service": "User Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

