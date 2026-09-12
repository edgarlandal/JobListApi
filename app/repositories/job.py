from typing import Sequence
from uuid import UUID

from loguru import logger

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError 

from app.models.job import Job

from app.schemas.job import JobUpdate

class JobRepository:
    def __init__(self, db: AsyncSession) -> Job | None:
        self.db = db

    async def create(self, job: Job):
        try:
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
            return job
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def update(self, db_job: Job, job_in: JobUpdate) -> Job:
        job_update = job_in.model_dump(exclude_unset=True)

        for field, value in job_update.items():
            setattr(db_job, field, value)

        return await self.save(db_job)

    async def save(self, db_job: Job) -> Job:
        try:
            self.db.add(db_job)
            await self.db.commit()
            await self.db.refresh(db_job)
            return db_job
        except SQLAlchemyError:
            await self.db.rollback
            raise

    async def delete(self, db_job: Job) -> None:
        try:
            await self.db.delete(db_job)
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def get_by_id(self, job_id: str) -> Job | None:
        try:
            res = await self.db.execute(select(Job).where(Job.id == UUID(job_id)))
            return res.scalars().first()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def get_all(self, skip: int, limit: int) -> tuple[Sequence[Job], int]:
        try:
            total = await self.db.scalar(select(func.count()).select_from(Job))
            stmt = select(Job).order_by(Job.last_update_at, Job.id).offset(skip).limit(limit)
            res = await self.db.execute(stmt)
            logger.info("get_jobs",  event="user.get_jobs")

            return res.scalars().all(), total
        except SQLAlchemyError:
            await self.db.rollback()
            raise