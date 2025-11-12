from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from uuid import UUID

from app.database import get_db
from app.schemas.user_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    ApiResponse,
    PaginationMeta
)
from app.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()


@router.post(
    "/users/",
    response_model=ApiResponse,
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
        data=user.to_dict()
    )


@router.get(
    "/users/{user_id}",
    response_model=ApiResponse
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
        data=user.to_dict()
    )


@router.get(
    "/users/",
    response_model=ApiResponse
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
        data=[user.to_dict() for user in users],
        meta=meta.model_dump()
    )


@router.patch(
    "/users/{user_id}",
    response_model=ApiResponse
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
    if "preferences" in update_data and update_data["preferences"]:
        update_data["preferences"] = update_data["preferences"].model_dump()
    
    updated_user = await user_repo.update(user_id, update_data)
    
    return ApiResponse(
        success=True,
        message="User updated successfully",
        data=updated_user.to_dict()
    )

