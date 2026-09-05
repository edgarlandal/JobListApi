from fastapi import HTTPException,  status
from app.repositories.user import UserRepository
from app.core.security import (
    verify_password, 
    create_access_token,
    create_refresh_token,
    decode_acces_token
)

class AuthService:
    def __int__(self, user_repo: UserRepository):
        self.user_repo = user_repo

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


        data = {"sub" : user.email}

        return {
            "access_token": create_access_token(data),
            "refresh_token": create_access_token(data),
            "token_type": "bearer"
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = decode_acces_token(refresh_token, expected_type="refresh")
        email = payload.get("sub")

        user = await self.user_repo.get_by_email(email)
        if not user or getattr(user, "disabled", False) or not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        new_access_token = create_access_token(data={"sub": user.email})

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }