from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.repositories.user import UserRepository
from app.services.user import UserService
from app.services.auth import AuthService

from app.models.user import User
from app.core.security import decode_acces_token

from app.repositories.refresh_token import RefreshTokenRepository

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_user_repository(db: AsyncSession = Depends(get_async_db)) -> UserRepository:
    return UserRepository(db=db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)

def get_auth_service(repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(repo)

async def get_current_user(
        token: Annotated[str, Depends(oauth_scheme)], 
        db: Annotated[AsyncSession, Depends(get_async_db)]
) -> User:
    payload = decode_acces_token(token, expected_type="access")

    email: str = payload.get("sub")
    if email is None: 
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token not contain user id"
    )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not fouund"
        )

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if getattr(current_user, "disabled", False) or not getattr(current_user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User inactive o disabled"
        )
    
    return current_user

def get_refresh_token_repository(db: AsyncSession = Depends(get_async_db)) -> RefreshTokenRepository:
    return RefreshTokenRepository(db=db)

def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
    refresh_repo: RefreshTokenRepository = Depends(get_refresh_token_repository)
):
    return AuthService(user_repo=repo, refresh_repo=refresh_repo)