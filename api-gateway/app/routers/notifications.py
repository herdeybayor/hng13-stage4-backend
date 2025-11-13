from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime
import logging

from app.models.requests import NotificationRequest
from app.models.responses import ApiResponse, NotificationResponse
from app.services.queue_service import QueueService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency injection
queue_service = QueueService()
user_service = UserService()


@router.post(
    "/notifications/",
    response_model=ApiResponse[NotificationResponse],
    status_code=status.HTTP_202_ACCEPTED
)
async def create_notification(
    request: Request,
    notification_request: NotificationRequest
):
    """
    Create and queue a new notification
    
    - **notification_type**: Type of notification (email or push)
    - **user_id**: Target user identifier
    - **template_code**: Template to use for the notification
    - **variables**: Data for template substitution
    - **request_id**: Unique identifier for idempotency
    - **priority**: Priority level (1-10, higher is more urgent)
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        # Check idempotency
        existing = await queue_service.check_request_id(notification_request.request_id)
        if existing:
            logger.info(f"Duplicate request detected: {notification_request.request_id}")
            return ApiResponse(
                success=True,
                message="Notification already processed",
                data=NotificationResponse(
                    notification_id=existing.get("notification_id"),
                    status=existing.get("status", "pending"),
                    created_at=datetime.utcnow()
                )
            )
        
        # Validate user exists and get preferences
        user = await user_service.get_user(notification_request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check user preferences
        preferences = user.get("preferences", {})
        if notification_request.notification_type == "email" and not preferences.get("email", True):
            return ApiResponse(
                success=False,
                message="User has disabled email notifications",
                error="Notification preference disabled"
            )
        
        if notification_request.notification_type == "push" and not preferences.get("push", True):
            return ApiResponse(
                success=False,
                message="User has disabled push notifications",
                error="Notification preference disabled"
            )
        
        # Queue the notification
        notification_id = await queue_service.queue_notification(
            notification_request=notification_request,
            user_data=user,
            correlation_id=correlation_id
        )
        
        response_data = NotificationResponse(
            notification_id=notification_id,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        return ApiResponse(
            success=True,
            message="Notification queued successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue notification"
        )


@router.get(
    "/notifications/{notification_id}",
    response_model=ApiResponse[dict]
)
async def get_notification_status(notification_id: str):
    """Get the status of a notification"""
    status_data = await queue_service.get_notification_status(notification_id)
    
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return ApiResponse(
        success=True,
        message="Notification status retrieved",
        data=status_data
    )

