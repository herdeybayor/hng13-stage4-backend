from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.template import Template


class TemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, code: str, name: str, content: str, description: str = None, language: str = "en") -> Template:
        template = Template(code=code, name=name, content=content, description=description, language=language)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def get_by_code(self, code: str) -> Optional[Template]:
        result = await self.db.execute(select(Template).where(Template.code == code))
        return result.scalar_one_or_none()
    
    async def list_templates(self) -> list:
        result = await self.db.execute(select(Template))
        return result.scalars().all()

