from fastapi import HTTPException,  status
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository

from datetime import datetime, timezone, timedelta

from app.core.security import (
    verify_password, 
    create_access_token,
    create_refresh_token,
    decode_acces_token,
    hash_token
)

from app.core.config import settings

import uuid

class AuthService:
    def __int__(self, user_repo: UserRepository, refresh_repo: RefreshTokenRepository):
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo

    async def authenticate_user(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalids Credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if getattr(user, "disabled", False) or not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )

        family_id = str(uuid.uuid4())
        access_token = create_access_token({"sub" : user.email})
        refresh_token = create_refresh_token({"sub" : user.email, "family_id": family_id})

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await self.refresh_repo.create(
            user_email=user.email,
            token_hash=hash_token(refresh_token),
            family_id=family_id,
            expire_at=expires_at
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = decode_acces_token(refresh_token, expected_type="refresh")
        email = payload.get("sub")

        token_hash = hash_token(refresh_token)
        db_token = await self.refresh_repo.get_by_hash(token_hash)

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or untrusted refresh token"
            )

        if db_token.used_at is not None or db_token.revoked:
            await self.refresh_repo.revoke_family(db_token.family_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Security alert: Refresh token reuse detected. All sessions revoked."
            )

        if db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )

        user = await self.user_repo.get_by_email(email)
        if not user or getattr(user, "disabled", False) or not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        await self.refresh_repo.mark_as_used(db_token.id)

        new_access_token = create_access_token(data={"sub": user.email})
        new_refresh_token = create_refresh_token(data={"sub": user.email, "family_id": db_token.family_id})

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await self.refresh_repo.create(
            user_email=user.email,
            token_hash=hash_token(new_refresh_token),
            family_id=db_token.family_id,
            expire_at=expires_at
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }