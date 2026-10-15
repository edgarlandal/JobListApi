from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.schemas.skill import SkillCreateBase


class SkillRepository:
    def __init__(self, db: AsyncSession) -> Skill | None:
        self.db = db

    async def create(self, skill: Skill):
        return await self.save(skill)

    async def update(self, db_skill: Skill, skill_in: SkillCreateBase) -> Skill:
        try:
            update_data = skill_in.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_skill, field, value)

            return await self.save(db_skill)
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def save(self, db_skill: Skill) -> Skill:
        try:
            self.db.add(db_skill)
            await self.db.commit()
            await self.db.refresh(db_skill)
            return db_skill
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def delete(self, db_skill: Skill) -> Skill | None:
        try:
            await self.db.delete(db_skill)
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def get_all(self, skip: int, limit: int) -> tuple[Sequence[Skill], int]:
        total = await self.db.scalar(select(func.count()).select_from(Skill))
        stmt = select(Skill).order_by(Skill.name, Skill.id).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all(), total
