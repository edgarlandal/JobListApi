from fastapi import HTTPException, status
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.models.user import User
from app.core.security import hash_password

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user_in: UserCreate) -> User:
        existing = await self.user_repo.get_by_email(user_in.email)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email exist"
            )

        db_user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password)
        )

        return await self.user_repo.create(db_user)

    async def get_users(self):
        return await self.user_repo.get_all()