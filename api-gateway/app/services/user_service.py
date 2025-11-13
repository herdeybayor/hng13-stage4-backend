import httpx
import logging
from typing import Optional, Dict, Any
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
    
    async def get_user(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Fetch user data from User Service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/users/{user_id}")
                response.raise_for_status()
                data = response.json()
                
                if data.get("success") and data.get("data"):
                    return data["data"]
                
                return None
        except Exception as e:
            logger.error(f"Failed to fetch user {user_id}: {e}")
            return None

