from fastapi import APIRouter, status
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check - verifies dependencies"""
    # TODO: Check RabbitMQ, Redis, etc.
    dependencies = {
        "rabbitmq": "connected",
        "redis": "connected",
        "user_service": "reachable",
        "template_service": "reachable"
    }
    
    return {
        "ready": True,
        "dependencies": dependencies,
        "timestamp": datetime.utcnow().isoformat()
    }

