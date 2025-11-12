from fastapi import APIRouter, status
from datetime import datetime

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "user-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

