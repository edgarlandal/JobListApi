from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.repositories.user import UserRepository
from app.services.user import UserService
from app.services.auth import AuthService

from app.models.user import User
from app.core.security import decode_acces_token

oauth_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_user_repository(db: AsyncSession = Depends(get_async_db)) -> UserRepository:
    return UserRepository(db=db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)

def get_auth_service(repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(repo)

async def get_current_user(
        token: str = Depends(oauth_scheme), 
        user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    payload = decode_acces_token(token, expected_type="access")

    user_id = payload.get("sub")
    if not user_id: raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token not contain user id"
    )

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not fouund"
        )

    if getattr(user, "disabled", False) or not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User inactive o disabled"
        )

    return user