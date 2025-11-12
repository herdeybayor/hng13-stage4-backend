from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from uuid import UUID, uuid4


class NotificationType(str, Enum):
    email = "email"
    push = "push"


class NotificationRequest(BaseModel):
    notification_type: NotificationType
    user_id: UUID
    template_code: str
    variables: Dict[str, Any]
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    priority: int = Field(default=5, ge=1, le=10)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "notification_type": "email",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "template_code": "welcome_email",
                "variables": {
                    "name": "John Doe",
                    "link": "https://example.com/verify"
                },
                "request_id": "req_123abc",
                "priority": 5,
                "metadata": {"campaign_id": "summer_2024"}
            }
        }

