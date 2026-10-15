from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import UserSkill
from app.schemas.skill import SkillUserUpdate


class UserSkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, skill_user: UserSkill):
        try:
            self.db.add(skill_user)
            await self.db.commit()
            await self.db.refresh(skill_user)
            return skill_user
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def update(self, db_user_skill: UserSkill, skill_user_in: SkillUserUpdate):
        update_data = skill_user_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_user_skill, field, value)

        return await self.save(db_user_skill)

    async def save(self, db_skill_user: UserSkill) -> UserSkill:
        self.db.add(db_skill_user)
        await self.db.commit()
        await self.db.refresh(db_skill_user)
        return db_skill_user

    async def delete(self, db_skill_user: UserSkill) -> None:
        try:
            await self.db.delete(db_skill_user)
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def get_skills_by_user_id(self, user_id: str) -> list[UserSkill]:
        try:
            res = await self.db.execute(
                select(UserSkill).where(UserSkill.user_id == UUID(user_id))
            )
            return res.scalars().all()
        except SQLAlchemyError:
            self.db.rollback()
            raise
