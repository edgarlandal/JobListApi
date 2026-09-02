from fastapi import FastAPI
from app.core.config import settings
from app.core.database import async_engine, Base
from app.api.routes import users, auth

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def stardup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok"}

