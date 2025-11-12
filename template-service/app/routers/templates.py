from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.template_schema import TemplateCreateRequest, ApiResponse
from app.repositories.template_repository import TemplateRepository

router = APIRouter()


@router.post("/templates/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_template(template_data: TemplateCreateRequest, db: AsyncSession = Depends(get_db)):
    template_repo = TemplateRepository(db)
    existing = await template_repo.get_by_code(template_data.code)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template code already exists")
    
    template = await template_repo.create(
        code=template_data.code,
        name=template_data.name,
        description=template_data.description,
        content=template_data.content,
        language=template_data.language
    )
    
    return ApiResponse(success=True, message="Template created successfully", data=template.to_dict())


@router.get("/templates/{template_code}", response_model=ApiResponse)
async def get_template(template_code: str, db: AsyncSession = Depends(get_db)):
    template_repo = TemplateRepository(db)
    template = await template_repo.get_by_code(template_code)
    
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    return ApiResponse(success=True, message="Template retrieved successfully", data=template.to_dict())


@router.get("/templates/", response_model=ApiResponse)
async def list_templates(db: AsyncSession = Depends(get_db)):
    template_repo = TemplateRepository(db)
    templates = await template_repo.list_templates()
    return ApiResponse(success=True, message="Templates retrieved", data=[t.to_dict() for t in templates])

