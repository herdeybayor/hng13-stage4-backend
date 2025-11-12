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
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "language": self.language,
            "version": self.version,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

