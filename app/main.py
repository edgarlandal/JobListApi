from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import async_engine, Base
from app.core.rate_limit import limiter
from app.api.routes import users, auth
from app.core.middleware import SecurityHeadersMiddleware
from app.core.error_handlers import register_exception_handler

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "X-Requested-With"
    ],
    expose_headers=["Content-Disposition"]
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

register_exception_handler(app)

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