from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession) -> User | None:
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        res = await self.db.execute(select(User).where(User.id == user_id))
        return res.scalars().first()
    
    async def get_all(self) -> Sequence[User]:
        stmt = select(User)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create(self, user: User) -> User:
        try:
            self.db.add(User)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError:
            await self.db.rollback()
            raise
    