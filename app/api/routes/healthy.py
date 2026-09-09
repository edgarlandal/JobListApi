from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

from app.api.dependencies import get_async_db

router = APIRouter(tags=["Health"])

@router.get("/health", status_code=status.HTTP_200_OK, )
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service"
    }

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_async_db)):
    try:
        await db.execute(text("SELECT 1"))

        logger.debug("Readlines check passed: Database connection active", event="HEALTH_CHECK_SUCCESS")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "dependencies": {
                    "database": "connected"
                }
            }
        )
    except Exception as exc:
        logger.error(
            f"Readiness check failed: Database unreachable - Details: {str(exc)}",
            event="HEALTH_CHECK_FAILURE",
            reason="database_unreachable"
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unready",
                "dependencies": {
                    "database": "disconnected"
                },
                "error": "Database service is not responding"
            }
        )