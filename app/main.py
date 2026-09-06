from fastapi import FastAPI, APIRouter
from app.core.config import settings
from app.core.database import async_engine, Base
from app.api.routes import users, auth

app = FastAPI(title=settings.PROJECT_NAME, openapi_prefix="")

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)

@api_router.on_event("startup")
async def stardup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@api_router.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok"}

app.include_router(api_router)