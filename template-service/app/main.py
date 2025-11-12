from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import templates
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Template Service")
    yield
    logger.info("Shutting down Template Service")


app = FastAPI(title="Template Service", version="1.0.0", description="Template management service", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(templates.router, prefix="/api/v1", tags=["Templates"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "template-service", "version": "1.0.0"}


@app.get("/")
async def root():
    return {"service": "Template Service", "version": "1.0.0", "status": "running", "docs": "/docs"}

