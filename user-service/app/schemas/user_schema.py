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
    preferences: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
    meta: Optional[dict] = None


class PaginationMeta(BaseModel):
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool

