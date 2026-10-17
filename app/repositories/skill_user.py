from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, UserSkill
from app.schemas.skill import SkillUserUpdate


class UserSkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, skill_user: UserSkill) -> UserSkill:
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

    async def skill_exists(
        self,
        skill_id: UUID,
    ) -> bool:
        stmt = select(
            exists().where(
                Skill.id == skill_id,
            )
        )

        return bool(await self.db.scalar(stmt))

    async def get_by_user_and_skill(
        self,
        skill_id: UUID,
        user_id: UUID,
    ) -> UserSkill | None:
        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
        )
        res = await self.db.execute(stmt)

        return res.scalar_one_or_none()

    async def get_skills_by_user_id(
        self, user_id: UUID, skip: int, limit: int
    ) -> tuple[list[UserSkill], int]:
        try:
            total = await self.db.scalar(select(func.count()).select_from(UserSkill))
            stmt = (
                select(UserSkill)
                .where(UserSkill.user_id == user_id)
                .offset(skip)
                .limit(limit)
            )
            res = await self.db.execute(stmt)
            return res.scalars().all(), total
        except SQLAlchemyError:
            self.db.rollback()
            raise
