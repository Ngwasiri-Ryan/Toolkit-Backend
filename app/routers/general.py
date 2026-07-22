from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.config import settings

router = APIRouter(tags=["general"])

@router.get("/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION
        }
    )
