from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.skill import JobSkill, Skill
from app.schemas.skill import SkillJobUpdate


class JobSkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, skill_job: JobSkill) -> JobSkill:
        try:
            self.db.add(skill_job)
            await self.db.commit()
            await self.db.refresh(skill_job)
            return skill_job
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def update(
        self, db_job_skill: JobSkill, skill_job_in: SkillJobUpdate
    ) -> JobSkill:
        update_data = skill_job_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_job_skill, field, value)

        return await self.save(db_job_skill)

    async def save(self, db_job_skill: JobSkill) -> JobSkill:
        self.db.add(db_job_skill)
        await self.db.commit()
        await self.db.refresh(db_job_skill)
        return db_job_skill

    async def delete(self, db_skill_job: JobSkill) -> JobSkill:
        try:
            await self.db.delete(db_skill_job)
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def skill_exists(self, skill_id: UUID) -> bool:
        stmt = select(exists().where(Skill.id == skill_id))

        return bool(await self.db.scalar(stmt))

    async def get_by_job_and_skill(self, skill_id: UUID, job_id: UUID):
        stmt = select(JobSkill).where(
            JobSkill.job_id == job_id, JobSkill.skill_id == skill_id
        )

        res = await self.db.execute(stmt)

        return res.scalar_one_or_none()

    async def get_skills_by_job_id(
        self, job_id: UUID, skip: int, limit: int
    ) -> tuple[list[JobSkill], int]:
        try:
            total = await self.db.scalar(select(func.count()).select_from(JobSkill))
            stmt = (
                select(JobSkill)
                .where(JobSkill.job_id == job_id)
                .offset(skip)
                .limit(limit)
            )
            res = await self.db.execute(stmt)
            return res.scalars().all(), total
        except SQLAlchemyError:
            self.db.rollback()
            raise

    async def get_by_id_and_user(self, job_id: UUID, user_id: UUID) -> Job:
        stmt = select(Job).where(
            Job.id == job_id,
            Job.user_id == user_id,
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()
