from fastapi import HTTPException,  status
from app.repositories.user import UserRepository
from app.core.security import verify_password, create_access_token

class AuthService:
    def __int__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, email: str, password: str) -> str:
        user = await self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalids Credentials"
            )
        return create_access_token(data={"sub": user.email})