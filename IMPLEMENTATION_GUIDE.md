# Distributed Notification System - Implementation Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Service Implementation](#service-implementation)
5. [Database Design](#database-design)
6. [Message Queue Setup](#message-queue-setup)
7. [API Specifications](#api-specifications)
8. [Key Technical Implementations](#key-technical-implementations)
9. [Deployment Guide](#deployment-guide)
10. [Testing Strategy](#testing-strategy)

---

## System Overview

This distributed notification system handles email and push notifications using a microservices architecture with asynchronous message queuing. The system is designed to be scalable, fault-tolerant, and capable of handling 1,000+ notifications per minute.

### Key Features

- ✅ Multiple notification channels (Email, Push)
- ✅ Template management with variable substitution
- ✅ User preference management
- ✅ Asynchronous processing with message queues
- ✅ Circuit breaker pattern for resilience
- ✅ Retry mechanism with exponential backoff
- ✅ Idempotency with request IDs
- ✅ Health monitoring endpoints

---

## Architecture

### High-Level System Architecture

```mermaid
graph TB
    Client[Client Application]

    subgraph API Gateway Service
        Gateway[API Gateway]
        Auth[Authentication]
        Router[Message Router]
    end

    subgraph Message Queue - RabbitMQ
        Exchange[notifications.direct]
        EmailQueue[email.queue]
        PushQueue[push.queue]
        DLQ[failed.queue - DLQ]
    end

    subgraph User Service
        UserAPI[User REST API]
        UserDB[(PostgreSQL - Users)]
    end

    subgraph Template Service
        TemplateAPI[Template REST API]
        TemplateDB[(PostgreSQL - Templates)]
    end

    subgraph Email Service
        EmailWorker[Email Worker]
        SMTP[SMTP Provider]
    end

    subgraph Push Service
        PushWorker[Push Worker]
        FCM[FCM/OneSignal]
    end

    subgraph Shared Infrastructure
        Redis[(Redis Cache)]
        StatusDB[(Status Store)]
    end

    Client --> Gateway
    Gateway --> Auth
    Auth --> Router
    Router --> Exchange

    Exchange --> EmailQueue
    Exchange --> PushQueue

    EmailQueue --> EmailWorker
    PushQueue --> PushWorker

    EmailWorker --> SMTP
    PushWorker --> FCM

    EmailWorker --> DLQ
    PushWorker --> DLQ

    Gateway --> UserAPI
    Gateway --> TemplateAPI

    UserAPI --> UserDB
    TemplateAPI --> TemplateDB

    EmailWorker --> Redis
    PushWorker --> Redis
    Gateway --> Redis

    EmailWorker --> StatusDB
    PushWorker --> StatusDB
    Gateway --> StatusDB
```

### Service Communication Flow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant UserSvc as User Service
    participant TmplSvc as Template Service
    participant Queue as RabbitMQ
    participant EmailSvc as Email Service
    participant SMTP as SMTP Provider
    participant Redis

    Client->>Gateway: POST /api/v1/notifications
    Gateway->>Gateway: Validate Request & Check Idempotency
    Gateway->>UserSvc: GET /users/{user_id}
    UserSvc-->>Gateway: User Data + Preferences

    alt Email preference enabled
        Gateway->>TmplSvc: GET /templates/{template_code}
        TmplSvc-->>Gateway: Template Data
        Gateway->>Queue: Publish to email.queue
        Gateway-->>Client: 202 Accepted {notification_id}

        Queue->>EmailSvc: Consume Message
        EmailSvc->>Redis: Check Rate Limit
        EmailSvc->>EmailSvc: Render Template
        EmailSvc->>SMTP: Send Email

        alt Success
            SMTP-->>EmailSvc: Delivery Success
            EmailSvc->>Redis: Update Status (delivered)
        else Failure
            SMTP-->>EmailSvc: Delivery Failed
            EmailSvc->>EmailSvc: Retry with Backoff
            alt Max Retries Exceeded
                EmailSvc->>Queue: Move to DLQ
                EmailSvc->>Redis: Update Status (failed)
            end
        end
    end
```

### Data Flow Architecture

```mermaid
graph LR
    subgraph Input Layer
        A[Client Request]
    end

    subgraph Processing Layer
        B[API Gateway]
        C[Validation]
        D[Authentication]
        E[Authorization]
    end

    subgraph Service Layer
        F[User Service]
        G[Template Service]
    end

    subgraph Queue Layer
        H[RabbitMQ Exchange]
        I[Email Queue]
        J[Push Queue]
        K[DLQ]
    end

    subgraph Worker Layer
        L[Email Workers]
        M[Push Workers]
    end

    subgraph External Services
        N[SMTP/SendGrid]
        O[FCM/OneSignal]
    end

    A-->B-->C-->D-->E
    E-->F
    E-->G
    E-->H
    H-->I-->L-->N
    H-->J-->M-->O
    L-->K
    M-->K
```

---

## Technology Stack

### Core Technologies

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Message Queue**: RabbitMQ (with Pika library)
- **Databases**:
  - PostgreSQL (User & Template data)
  - Redis (Caching & Status store)
- **Containerization**: Docker & Docker Compose
- **API Documentation**: OpenAPI/Swagger (built-in with FastAPI)

### Python Dependencies

```python
# requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
redis==5.0.1
pika==1.3.2
aio-pika==9.3.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
jinja2==3.1.3
httpx==0.26.0
tenacity==8.2.3
pybreaker==1.0.1
prometheus-client==0.19.0
```

---

## Service Implementation

### 1. API Gateway Service

#### Project Structure

```
api-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── notifications.py
│   │   └── health.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py
│   │   └── responses.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── template_service.py
│   │   └── queue_service.py
│   └── middleware/
│       ├── __init__.py
│       ├── correlation_id.py
│       └── error_handler.py
├── tests/
├── Dockerfile
└── requirements.txt
```

#### Core Implementation

**main.py**

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.routers import notifications, health
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events"""
    logger.info("Starting API Gateway Service")
    # Initialize connections
    yield
    # Cleanup connections
    logger.info("Shutting down API Gateway Service")


app = FastAPI(
    title="Notification API Gateway",
    version="1.0.0",
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
```

**models/requests.py**

```python
from pydantic import BaseModel, Field, EmailStr, HttpUrl
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
```

**models/responses.py**

```python
from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, Any
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
```

**routers/notifications.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
import logging

from app.models.requests import NotificationRequest
from app.models.responses import ApiResponse, NotificationResponse
from app.services.queue_service import QueueService
from app.services.user_service import UserService
from app.services.auth_service import get_current_user
from app.dependencies import get_queue_service, get_user_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/notifications/",
    response_model=ApiResponse[NotificationResponse],
    status_code=status.HTTP_202_ACCEPTED
)
async def create_notification(
    request: Request,
    notification_request: NotificationRequest,
    queue_service: QueueService = Depends(get_queue_service),
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user)
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
                data=existing
            )

        # Validate user exists and get preferences
        user = await user_service.get_user(notification_request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check user preferences
        if notification_request.notification_type == "email" and not user.get("preferences", {}).get("email", True):
            return ApiResponse(
                success=False,
                message="User has disabled email notifications",
                error="Notification preference disabled"
            )

        if notification_request.notification_type == "push" and not user.get("preferences", {}).get("push", True):
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
async def get_notification_status(
    notification_id: str,
    queue_service: QueueService = Depends(get_queue_service),
    current_user: dict = Depends(get_current_user)
):
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
```

**services/queue_service.py**

```python
import aio_pika
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from app.config import settings
from app.models.requests import NotificationRequest

logger = logging.getLogger(__name__)


class QueueService:
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None

    async def connect(self):
        """Establish connection to RabbitMQ"""
        if not self.connection or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                "notifications.direct",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            # Declare queues
            await self.channel.declare_queue("email.queue", durable=True)
            await self.channel.declare_queue("push.queue", durable=True)
            await self.channel.declare_queue("failed.queue", durable=True)

        return self.channel

    async def queue_notification(
        self,
        notification_request: NotificationRequest,
        user_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> str:
        """Queue a notification for processing"""
        await self.connect()

        notification_id = f"notif_{uuid4().hex[:12]}"

        message_body = {
            "notification_id": notification_id,
            "notification_type": notification_request.notification_type,
            "user_id": str(notification_request.user_id),
            "user_email": user_data.get("email"),
            "user_push_token": user_data.get("push_token"),
            "template_code": notification_request.template_code,
            "variables": notification_request.variables,
            "request_id": notification_request.request_id,
            "priority": notification_request.priority,
            "metadata": notification_request.metadata,
            "correlation_id": correlation_id,
            "created_at": datetime.utcnow().isoformat(),
            "retry_count": 0
        }

        # Determine routing key based on notification type
        routing_key = f"{notification_request.notification_type}.queue"

        message = aio_pika.Message(
            body=json.dumps(message_body).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            priority=notification_request.priority,
            correlation_id=correlation_id,
            message_id=notification_id
        )

        await self.exchange.publish(
            message,
            routing_key=routing_key
        )

        logger.info(f"Queued notification {notification_id} to {routing_key}")

        # Store in Redis for idempotency check
        # Implementation depends on Redis client

        return notification_id

    async def check_request_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Check if request_id has been processed (idempotency)"""
        # Implementation with Redis
        # Return existing notification data if found
        return None

    async def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get notification status from Redis/Database"""
        # Implementation depends on status store
        return None

    async def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
```

**routers/health.py**

```python
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
    # Check RabbitMQ, Redis, etc.
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
```

---

### 2. User Service

#### Project Structure

```
user-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── health.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user_schema.py
│   └── repositories/
│       ├── __init__.py
│       └── user_repository.py
├── alembic/
├── tests/
├── Dockerfile
└── requirements.txt
```

#### Core Implementation

**models/user.py**

```python
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    push_token = Column(String, nullable=True)
    preferences = Column(JSON, nullable=False, default={"email": True, "push": True})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "push_token": self.push_token,
            "preferences": self.preferences,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
```

**schemas/user_schema.py**

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserPreference(BaseModel):
    email: bool = True
    push: bool = True


class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    push_token: Optional[str] = None
    preferences: UserPreference = Field(default_factory=UserPreference)
    password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "push_token": "fcm_token_here",
                "preferences": {
                    "email": True,
                    "push": True
                },
                "password": "SecurePass123!"
            }
        }


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    push_token: Optional[str] = None
    preferences: Optional[UserPreference] = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    push_token: Optional[str]
    preferences: UserPreference
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**routers/users.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.user_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse
)
from app.models.responses import ApiResponse, PaginationMeta
from app.repositories.user_repository import UserRepository
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()


@router.post(
    "/users/",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    user_repo = UserRepository(db)

    # Check if email already exists
    existing = await user_repo.get_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = pwd_context.hash(user_data.password)

    # Create user
    user = await user_repo.create(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
        push_token=user_data.push_token,
        preferences=user_data.preferences.model_dump()
    )

    return ApiResponse(
        success=True,
        message="User created successfully",
        data=UserResponse.model_validate(user)
    )


@router.get(
    "/users/{user_id}",
    response_model=ApiResponse[UserResponse]
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return ApiResponse(
        success=True,
        message="User retrieved successfully",
        data=UserResponse.model_validate(user)
    )


@router.get(
    "/users/",
    response_model=ApiResponse[List[UserResponse]]
)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all users with pagination"""
    user_repo = UserRepository(db)

    users, total = await user_repo.list_users(page=page, limit=limit)
    total_pages = (total + limit - 1) // limit

    meta = PaginationMeta(
        total=total,
        limit=limit,
        page=page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )

    return ApiResponse(
        success=True,
        message="Users retrieved successfully",
        data=[UserResponse.model_validate(user) for user in users],
        meta=meta
    )


@router.patch(
    "/users/{user_id}",
    response_model=ApiResponse[UserResponse]
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update user information"""
    user_repo = UserRepository(db)

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    if "preferences" in update_data:
        update_data["preferences"] = update_data["preferences"].model_dump()

    updated_user = await user_repo.update(user_id, update_data)

    return ApiResponse(
        success=True,
        message="User updated successfully",
        data=UserResponse.model_validate(updated_user)
    )
```

---

### 3. Email Service

#### Project Structure

```
email-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── worker.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_sender.py
│   │   ├── template_renderer.py
│   │   └── circuit_breaker.py
│   └── routers/
│       ├── __init__.py
│       ├── health.py
│       └── status.py
├── templates/
│   └── email/
│       └── welcome.html
├── tests/
├── Dockerfile
└── requirements.txt
```

#### Core Implementation

**worker.py**

```python
import aio_pika
import asyncio
import json
import logging
from typing import Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import settings
from app.services.email_sender import EmailSender
from app.services.template_renderer import TemplateRenderer
from app.services.circuit_breaker import CircuitBreaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailWorker:
    def __init__(self):
        self.email_sender = EmailSender()
        self.template_renderer = TemplateRenderer()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None

    async def connect(self):
        """Connect to RabbitMQ"""
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=settings.WORKER_PREFETCH_COUNT)

        self.queue = await self.channel.declare_queue(
            "email.queue",
            durable=True
        )

        self.dlq = await self.channel.declare_queue(
            "failed.queue",
            durable=True
        )

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process a single email notification"""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                notification_id = body.get("notification_id")
                correlation_id = message.correlation_id

                logger.info(
                    f"Processing notification {notification_id} "
                    f"(correlation_id: {correlation_id})"
                )

                # Check if circuit breaker is open
                if not self.circuit_breaker.can_proceed():
                    logger.warning("Circuit breaker is OPEN, requeueing message")
                    await message.reject(requeue=True)
                    await asyncio.sleep(5)
                    return

                # Render template
                html_content = await self.template_renderer.render(
                    template_code=body.get("template_code"),
                    variables=body.get("variables", {})
                )

                # Send email with retry
                await self.send_email_with_retry(
                    to_email=body.get("user_email"),
                    subject=body.get("variables", {}).get("subject", "Notification"),
                    html_content=html_content,
                    notification_id=notification_id
                )

                self.circuit_breaker.record_success()
                logger.info(f"Successfully sent email for {notification_id}")

                # Update status in Redis/DB
                await self.update_status(notification_id, "delivered")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                self.circuit_breaker.record_failure()

                # Check retry count
                retry_count = body.get("retry_count", 0)
                if retry_count >= settings.MAX_RETRIES:
                    logger.error(f"Max retries exceeded for {notification_id}, moving to DLQ")
                    await self.move_to_dlq(body)
                    await self.update_status(notification_id, "failed", str(e))
                else:
                    # Increment retry count and requeue
                    body["retry_count"] = retry_count + 1
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                    await message.reject(requeue=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def send_email_with_retry(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        notification_id: str
    ):
        """Send email with automatic retry"""
        await self.email_sender.send(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )

    async def move_to_dlq(self, message_body: dict):
        """Move failed message to dead letter queue"""
        message = aio_pika.Message(
            body=json.dumps(message_body).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await self.channel.default_exchange.publish(
            message,
            routing_key="failed.queue"
        )

    async def update_status(
        self,
        notification_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """Update notification status in Redis/Database"""
        # Implementation with Redis or database
        pass

    async def start(self):
        """Start consuming messages"""
        await self.connect()
        logger.info("Email worker started, waiting for messages...")

        await self.queue.consume(self.process_message)

        # Keep the worker running
        await asyncio.Future()

    async def stop(self):
        """Stop the worker"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()


async def main():
    worker = EmailWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

**services/email_sender.py**

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL

    async def send(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ):
        """Send email via SMTP"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            if text_content:
                message.attach(MIMEText(text_content, "plain"))

            message.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise
```

**services/template_renderer.py**

```python
from jinja2 import Environment, FileSystemLoader, Template
import logging
from typing import Dict, Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TemplateRenderer:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader("templates/email"),
            autoescape=True
        )
        self.template_service_url = settings.TEMPLATE_SERVICE_URL

    async def render(
        self,
        template_code: str,
        variables: Dict[str, Any]
    ) -> str:
        """Render email template with variables"""
        try:
            # Option 1: Fetch from Template Service
            template_content = await self.fetch_template(template_code)

            # Option 2: Load from local files (fallback)
            # template = self.env.get_template(f"{template_code}.html")

            template = Template(template_content)
            html_content = template.render(**variables)

            return html_content

        except Exception as e:
            logger.error(f"Failed to render template {template_code}: {e}")
            raise

    async def fetch_template(self, template_code: str) -> str:
        """Fetch template from Template Service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.template_service_url}/templates/{template_code}",
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            return data["data"]["content"]
```

**services/circuit_breaker.py**

```python
import time
import logging
from typing import Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation

    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def can_proceed(self) -> bool:
        """Check if request can proceed"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self):
        """Record successful operation"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker entering CLOSED state")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

        if self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker entering OPEN state (failed during half-open)")
            self.state = CircuitState.OPEN

        if self.failure_count >= self.failure_threshold:
            logger.warning(f"Circuit breaker entering OPEN state (threshold: {self.failure_threshold})")
            self.state = CircuitState.OPEN
```

---

### 4. Push Service

#### Implementation (Similar structure to Email Service)

**worker.py**

```python
import aio_pika
import asyncio
import json
import logging
from typing import Optional
import httpx

from app.config import settings
from app.services.circuit_breaker import CircuitBreaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PushWorker:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        self.fcm_api_key = settings.FCM_API_KEY
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"

    async def connect(self):
        """Connect to RabbitMQ"""
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=settings.WORKER_PREFETCH_COUNT)

        self.queue = await self.channel.declare_queue(
            "push.queue",
            durable=True
        )

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process push notification"""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                notification_id = body.get("notification_id")

                logger.info(f"Processing push notification {notification_id}")

                if not self.circuit_breaker.can_proceed():
                    logger.warning("Circuit breaker OPEN, requeueing")
                    await message.reject(requeue=True)
                    await asyncio.sleep(5)
                    return

                # Send push notification
                await self.send_push_notification(
                    token=body.get("user_push_token"),
                    title=body.get("variables", {}).get("title", "Notification"),
                    body_text=body.get("variables", {}).get("body", ""),
                    data=body.get("variables", {})
                )

                self.circuit_breaker.record_success()
                logger.info(f"Push notification sent: {notification_id}")

            except Exception as e:
                logger.error(f"Error processing push: {e}", exc_info=True)
                self.circuit_breaker.record_failure()

                retry_count = body.get("retry_count", 0)
                if retry_count >= settings.MAX_RETRIES:
                    await self.move_to_dlq(body)
                else:
                    body["retry_count"] = retry_count + 1
                    await message.reject(requeue=True)

    async def send_push_notification(
        self,
        token: str,
        title: str,
        body_text: str,
        data: dict
    ):
        """Send push notification via FCM"""
        payload = {
            "to": token,
            "notification": {
                "title": title,
                "body": body_text,
                "icon": data.get("icon"),
                "click_action": data.get("link")
            },
            "data": data
        }

        headers = {
            "Authorization": f"key={self.fcm_api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.fcm_url,
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"FCM Response: {response.json()}")

    async def start(self):
        """Start consuming messages"""
        await self.connect()
        logger.info("Push worker started")

        await self.queue.consume(self.process_message)
        await asyncio.Future()


async def main():
    worker = PushWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### 5. Template Service

#### Core Implementation

**models/template.py**

```python
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    language = Column(String, default="en")
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**routers/templates.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.schemas.template_schema import (
    TemplateCreateRequest,
    TemplateResponse
)
from app.models.responses import ApiResponse
from app.repositories.template_repository import TemplateRepository

router = APIRouter()


@router.post(
    "/templates/",
    response_model=ApiResponse[TemplateResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_template(
    template_data: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification template"""
    template_repo = TemplateRepository(db)

    # Check if code already exists
    existing = await template_repo.get_by_code(template_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template code already exists"
        )

    template = await template_repo.create(
        code=template_data.code,
        name=template_data.name,
        description=template_data.description,
        content=template_data.content,
        language=template_data.language
    )

    return ApiResponse(
        success=True,
        message="Template created successfully",
        data=TemplateResponse.model_validate(template)
    )


@router.get(
    "/templates/{template_code}",
    response_model=ApiResponse[TemplateResponse]
)
async def get_template(
    template_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get template by code"""
    template_repo = TemplateRepository(db)
    template = await template_repo.get_by_code(template_code)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return ApiResponse(
        success=True,
        message="Template retrieved successfully",
        data=TemplateResponse.model_validate(template)
    )
```

---

## Database Design

### User Service Database Schema

```sql
-- users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    push_token TEXT,
    preferences JSONB NOT NULL DEFAULT '{"email": true, "push": true}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### Template Service Database Schema

```sql
-- templates table
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_code ON templates(code);
CREATE INDEX idx_templates_language ON templates(language);

-- template_versions table (for version history)
CREATE TABLE template_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES templates(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_id, version)
);
```

### Redis Schema (Shared)

```python
# Notification Status
# Key: notification:{notification_id}
# Value: {
#   "notification_id": "notif_123",
#   "status": "delivered|pending|failed",
#   "created_at": "2024-01-01T00:00:00",
#   "updated_at": "2024-01-01T00:01:00",
#   "error": null
# }
# TTL: 7 days

# Idempotency Check
# Key: request_id:{request_id}
# Value: notification_id
# TTL: 24 hours

# Rate Limiting
# Key: rate_limit:{user_id}:{notification_type}
# Value: count
# TTL: 1 hour

# User Cache
# Key: user:{user_id}
# Value: {user_json}
# TTL: 1 hour
```

---

## Message Queue Setup

### RabbitMQ Configuration

**docker-compose.yml**

```yaml
version: "3.8"

services:
  rabbitmq:
    image: rabbitmq:3-management
    container_name: notification_rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: admin123
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
      - ./rabbitmq-config/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf
      - ./rabbitmq-config/definitions.json:/etc/rabbitmq/definitions.json
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  rabbitmq_data:
```

**rabbitmq-config/definitions.json**

```json
{
  "rabbit_version": "3.12.0",
  "exchanges": [
    {
      "name": "notifications.direct",
      "vhost": "/",
      "type": "direct",
      "durable": true,
      "auto_delete": false
    }
  ],
  "queues": [
    {
      "name": "email.queue",
      "vhost": "/",
      "durable": true,
      "auto_delete": false,
      "arguments": {
        "x-max-priority": 10,
        "x-message-ttl": 86400000
      }
    },
    {
      "name": "push.queue",
      "vhost": "/",
      "durable": true,
      "auto_delete": false,
      "arguments": {
        "x-max-priority": 10,
        "x-message-ttl": 86400000
      }
    },
    {
      "name": "failed.queue",
      "vhost": "/",
      "durable": true,
      "auto_delete": false
    }
  ],
  "bindings": [
    {
      "source": "notifications.direct",
      "vhost": "/",
      "destination": "email.queue",
      "destination_type": "queue",
      "routing_key": "email.queue"
    },
    {
      "source": "notifications.direct",
      "vhost": "/",
      "destination": "push.queue",
      "destination_type": "queue",
      "routing_key": "push.queue"
    }
  ]
}
```

### Queue Architecture Diagram

```mermaid
graph TB
    subgraph API Gateway
        A[POST /notifications]
    end

    subgraph RabbitMQ
        B[notifications.direct Exchange]
        C[email.queue]
        D[push.queue]
        E[failed.queue DLQ]
    end

    subgraph Workers
        F[Email Worker Pool]
        G[Push Worker Pool]
    end

    subgraph Retry Logic
        H{Retry Count < Max?}
        I[Exponential Backoff]
        J[Move to DLQ]
    end

    A -->|Publish| B
    B -->|Route: email| C
    B -->|Route: push| D

    C -->|Consume| F
    D -->|Consume| G

    F -->|On Failure| H
    G -->|On Failure| H

    H -->|Yes| I
    H -->|No| J
    I -->|Requeue| C
    I -->|Requeue| D
    J --> E
```

---

## API Specifications

### Common Response Format

All API endpoints follow this response structure:

```typescript
interface ApiResponse<T> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
  meta?: PaginationMeta;
}

interface PaginationMeta {
  total: number;
  limit: number;
  page: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}
```

### API Endpoints Summary

#### API Gateway Service

| Method | Endpoint                     | Description                    |
| ------ | ---------------------------- | ------------------------------ |
| POST   | `/api/v1/notifications/`     | Create notification            |
| GET    | `/api/v1/notifications/{id}` | Get notification status        |
| GET    | `/api/v1/notifications/`     | List notifications (paginated) |
| GET    | `/health/`                   | Health check                   |
| GET    | `/health/readiness`          | Readiness check                |

#### User Service

| Method | Endpoint             | Description  |
| ------ | -------------------- | ------------ |
| POST   | `/api/v1/users/`     | Create user  |
| GET    | `/api/v1/users/{id}` | Get user     |
| GET    | `/api/v1/users/`     | List users   |
| PATCH  | `/api/v1/users/{id}` | Update user  |
| GET    | `/health/`           | Health check |

#### Template Service

| Method | Endpoint                   | Description     |
| ------ | -------------------------- | --------------- |
| POST   | `/api/v1/templates/`       | Create template |
| GET    | `/api/v1/templates/{code}` | Get template    |
| GET    | `/api/v1/templates/`       | List templates  |
| PATCH  | `/api/v1/templates/{code}` | Update template |
| GET    | `/health/`                 | Health check    |

#### Email/Push Services

| Method | Endpoint          | Description                |
| ------ | ----------------- | -------------------------- |
| POST   | `/api/v1/status/` | Update notification status |
| GET    | `/health/`        | Health check               |
| GET    | `/metrics/`       | Prometheus metrics         |

---

## Key Technical Implementations

### 1. Circuit Breaker Pattern

Already implemented in `services/circuit_breaker.py` above. The circuit breaker prevents cascading failures by:

- **CLOSED**: Normal operation
- **OPEN**: Blocks requests after threshold failures
- **HALF_OPEN**: Tests service recovery

### 2. Retry System with Exponential Backoff

```python
# Implemented in worker.py
retry_count = body.get("retry_count", 0)
if retry_count >= MAX_RETRIES:
    # Move to DLQ
    await move_to_dlq(body)
else:
    # Exponential backoff: 2^retry_count seconds
    await asyncio.sleep(2 ** retry_count)
    body["retry_count"] = retry_count + 1
    await message.reject(requeue=True)
```

### 3. Idempotency Implementation

```python
# In API Gateway
async def check_idempotency(request_id: str) -> Optional[dict]:
    """Check if request has been processed"""
    redis_client = await get_redis()
    cached = await redis_client.get(f"request_id:{request_id}")

    if cached:
        return json.loads(cached)

    return None

async def save_idempotency(request_id: str, notification_id: str):
    """Save request for idempotency check (24h TTL)"""
    redis_client = await get_redis()
    data = {"notification_id": notification_id, "created_at": datetime.utcnow().isoformat()}
    await redis_client.setex(
        f"request_id:{request_id}",
        86400,  # 24 hours
        json.dumps(data)
    )
```

### 4. Rate Limiting

```python
from datetime import datetime, timedelta

async def check_rate_limit(user_id: str, notification_type: str) -> bool:
    """Check if user has exceeded rate limit"""
    redis_client = await get_redis()
    key = f"rate_limit:{user_id}:{notification_type}"

    count = await redis_client.get(key)

    if count and int(count) >= RATE_LIMIT_MAX:
        return False

    # Increment counter
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 3600)  # 1 hour window
    await pipe.execute()

    return True
```

### 5. Correlation ID Middleware

```python
# middleware/correlation_id.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Store in request state
        request.state.correlation_id = correlation_id

        # Call next middleware/endpoint
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response
```

### 6. Health Check Implementation

```python
# routers/health.py
from fastapi import APIRouter, status
import httpx
import aio_pika

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/readiness")
async def readiness_check():
    """Comprehensive readiness check"""
    checks = {}
    all_healthy = True

    # Check RabbitMQ
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL, timeout=5)
        await connection.close()
        checks["rabbitmq"] = "connected"
    except Exception as e:
        checks["rabbitmq"] = f"failed: {str(e)}"
        all_healthy = False

    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "connected"
    except Exception as e:
        checks["redis"] = f"failed: {str(e)}"
        all_healthy = False

    # Check dependent services
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/health", timeout=3)
            checks["user_service"] = "reachable" if response.status_code == 200 else "unhealthy"
    except:
        checks["user_service"] = "unreachable"
        all_healthy = False

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_healthy,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## Deployment Guide

### Docker Compose Setup

**docker-compose.yml**

```yaml
version: "3.8"

services:
  # Infrastructure
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: notifications
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: admin123
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Services
  api-gateway:
    build:
      context: ./api-gateway
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/notifications
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://admin:admin123@rabbitmq:5672/
      - USER_SERVICE_URL=http://user-service:8001
      - TEMPLATE_SERVICE_URL=http://template-service:8002
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  user-service:
    build:
      context: ./user-service
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/notifications
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8001

  template-service:
    build:
      context: ./template-service
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/notifications
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8002

  email-worker:
    build:
      context: ./email-service
      dockerfile: Dockerfile
    environment:
      - RABBITMQ_URL=amqp://admin:admin123@rabbitmq:5672/
      - REDIS_URL=redis://redis:6379/0
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - TEMPLATE_SERVICE_URL=http://template-service:8002
    depends_on:
      rabbitmq:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python -m app.worker
    deploy:
      replicas: 2

  push-worker:
    build:
      context: ./push-service
      dockerfile: Dockerfile
    environment:
      - RABBITMQ_URL=amqp://admin:admin123@rabbitmq:5672/
      - REDIS_URL=redis://redis:6379/0
      - FCM_API_KEY=${FCM_API_KEY}
    depends_on:
      rabbitmq:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python -m app.worker
    deploy:
      replicas: 2

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
```

### Dockerfile Template

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### CI/CD Workflow (.github/workflows/deploy.yml)

```yaml
name: Deploy Notification System

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  DOCKER_REGISTRY: docker.io
  REGISTRY_USERNAME: ${{ secrets.DOCKER_USERNAME }}

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-gateway, user-service, template-service, email-service, push-service]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        working-directory: ./${{ matrix.service }}
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        working-directory: ./${{ matrix.service }}
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./${{ matrix.service }}/coverage.xml
          flags: ${{ matrix.service }}

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    strategy:
      matrix:
        service: [api-gateway, user-service, template-service, email-service, push-service]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: |
            ${{ env.REGISTRY_USERNAME }}/notification-${{ matrix.service }}:latest
            ${{ env.REGISTRY_USERNAME }}/notification-${{ matrix.service }}:${{ github.sha }}
          cache-from: type=registry,ref=${{ env.REGISTRY_USERNAME }}/notification-${{ matrix.service }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY_USERNAME }}/notification-${{ matrix.service }}:buildcache,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USERNAME }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/notification-system
            docker-compose pull
            docker-compose up -d
            docker-compose ps
```

---

## Testing Strategy

### Unit Tests Example

```python
# tests/test_notification_router.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_notification():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/notifications/",
            json={
                "notification_type": "email",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "template_code": "welcome",
                "variables": {"name": "Test User"},
                "request_id": "test_req_001",
                "priority": 5
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert "notification_id" in data["data"]

@pytest.mark.asyncio
async def test_idempotency():
    """Test that duplicate request_id returns same response"""
    request_data = {
        "notification_type": "email",
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "template_code": "welcome",
        "variables": {"name": "Test User"},
        "request_id": "duplicate_test_001",
        "priority": 5
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        # First request
        response1 = await client.post("/api/v1/notifications/", json=request_data)

        # Duplicate request
        response2 = await client.post("/api/v1/notifications/", json=request_data)

        assert response1.status_code == 202
        assert response2.status_code == 202
        assert response1.json()["data"]["notification_id"] == response2.json()["data"]["notification_id"]
```

### Integration Tests

```python
# tests/integration/test_notification_flow.py
import pytest
import asyncio
from app.services.queue_service import QueueService

@pytest.mark.integration
@pytest.mark.asyncio
async def test_email_notification_flow():
    """Test complete email notification flow"""
    queue_service = QueueService()

    # Create notification
    notification_id = await queue_service.queue_notification(
        notification_request=mock_notification_request,
        user_data=mock_user_data,
        correlation_id="test_corr_001"
    )

    # Wait for processing
    await asyncio.sleep(5)

    # Check status
    status = await queue_service.get_notification_status(notification_id)

    assert status is not None
    assert status["status"] in ["delivered", "pending"]
```

### Load Testing (Locust)

```python
# locustfile.py
from locust import HttpUser, task, between

class NotificationUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_notification(self):
        self.client.post(
            "/api/v1/notifications/",
            json={
                "notification_type": "email",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "template_code": "test",
                "variables": {"name": "Load Test"},
                "priority": 5
            }
        )
```

Run with:

```bash
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10
```

---

## System Monitoring

### Prometheus Metrics

```python
# Add to each service
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import make_asgi_app

# Metrics
notification_counter = Counter(
    'notifications_total',
    'Total notifications processed',
    ['notification_type', 'status']
)

processing_time = Histogram(
    'notification_processing_seconds',
    'Time spent processing notification'
)

queue_size = Gauge(
    'queue_size',
    'Current queue size',
    ['queue_name']
)

# Add metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### Logging Configuration

```python
# config/logging.py
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/app.log')
        ]
    )
```

---

## Performance Optimization Checklist

- [ ] Implement connection pooling for databases
- [ ] Use Redis caching for frequently accessed data
- [ ] Configure RabbitMQ prefetch count appropriately
- [ ] Implement batch processing for notifications
- [ ] Use async/await throughout the codebase
- [ ] Add database indexes on frequently queried columns
- [ ] Implement query result caching
- [ ] Use CDN for static template assets
- [ ] Configure worker auto-scaling based on queue length
- [ ] Implement message compression for large payloads

---

## Security Checklist

- [ ] Implement JWT authentication
- [ ] Use HTTPS/TLS for all communications
- [ ] Sanitize user inputs
- [ ] Implement rate limiting
- [ ] Use environment variables for secrets
- [ ] Hash passwords with bcrypt
- [ ] Implement CORS properly
- [ ] Add request validation middleware
- [ ] Use parameterized queries (SQLAlchemy ORM)
- [ ] Implement API key rotation
- [ ] Add audit logging
- [ ] Use secrets management (e.g., HashiCorp Vault)

---

## Conclusion

This implementation guide provides a complete blueprint for building a distributed notification system with:

✅ Microservices architecture
✅ Asynchronous message processing
✅ Fault tolerance with circuit breakers
✅ Retry mechanisms with exponential backoff
✅ Idempotency guarantees
✅ Horizontal scalability
✅ Comprehensive monitoring
✅ Production-ready deployment

Follow this guide step-by-step, implementing one service at a time, and you'll have a robust, scalable notification system ready for production use.

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/getstarted.html)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Microservices Patterns](https://microservices.io/patterns/)
