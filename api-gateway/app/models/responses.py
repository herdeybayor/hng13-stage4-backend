from pydantic import BaseModel
from typing import Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class PaginationMeta(BaseModel):
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[PaginationMeta] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Notification queued successfully",
                "data": {
                    "notification_id": "notif_123abc",
                    "status": "pending"
                },
                "error": None,
                "meta": None
            }
        }


class NotificationResponse(BaseModel):
    notification_id: str
    status: str
    created_at: datetime
    estimated_delivery: Optional[datetime] = None

