from typing import Sequence
from fastapi import HTTPException, status
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.core.security import hash_password

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def get_users(self, skip: int = 0, limit: int = 100):
        return await self.user_repo.get_all(skip=skip, limit=limit)

    async def get_user_by_id(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user
    
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

    async def update_user(self, user_id: str, user_in: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)

        if user_in.email and user_in.email != user.email:
            existing_email = await self.user_repo.get_by_email(user_in.email)

            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is existing"
                )
        

        if user_in.password:
            user.hashed_password = hash_password(user_in.password)

        return await self.user_repo.update(user, user_in)

    async def delete_user(self, user_id: str) -> None:
        user = await self.get_user_by_id(user_id)
        await self.user_repo.delete(user)