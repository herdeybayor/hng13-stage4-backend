from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Tuple
from uuid import UUID

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        push_token: Optional[str] = None,
        preferences: dict = None
    ) -> User:
        """Create a new user"""
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            push_token=push_token,
            preferences=preferences or {"email": True, "push": True}
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def list_users(
        self,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[User], int]:
        """List users with pagination"""
        offset = (page - 1) * limit
        
        # Get total count
        count_result = await self.db.execute(select(User))
        total = len(count_result.all())
        
        # Get paginated results
        result = await self.db.execute(
            select(User)
            .offset(offset)
            .limit(limit)
        )
        users = result.scalars().all()
        
        return list(users), total
    
    async def update(self, user_id: UUID, update_data: dict) -> User:
        """Update user"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete user"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self.db.delete(user)
        await self.db.commit()
        return True

