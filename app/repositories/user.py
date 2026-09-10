from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

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
    
    async def get_all(self, skip: int, limit: int) -> Sequence[User]:
        stmt = select(User)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create(self, user: User) -> User:
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def save(self, db_user: User) -> User:
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update(self, db_user: User, user_in: UserUpdate) -> User:
        update_data = user_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_user, field, value)

        return self.save(db_user)

    async def delete(self, db_user: User) -> None:
        await self.db.delete(db_user)
        await self.db.commit()

    