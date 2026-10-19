from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger

from app.models.job import Job
from app.models.skill import JobSkill
from app.repositories.skill_job import JobSkillRepository
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.schemas.skill import SkillJobCreate, SkillJobResponse, SkillJobUpdate


class JobSkillService:
    def __init__(self, skill_job_repo: JobSkillRepository):
        self.skill_job_repo = skill_job_repo

    async def add_skilL_job(
        self,
        user_id: str | UUID,
        job_id: str | UUID,
        skill_job_data: SkillJobCreate,
    ) -> JobSkill:

        job = await self.get_owned_job(user_id=user_id, job_id=job_id)

        await self._ensure_skill_not_assigned(
            job_id=job.id, skill_id=skill_job_data.skill_id
        )

        await self._ensure_skill_exists(skill_job_data.skill_id)

        new_skill_job = JobSkill(
            job_id=job.id,
            skill_id=skill_job_data.skill_id,
            minimum_level=skill_job_data.minimum_level,
        )

        created_skill = await self.skill_job_repo.create(new_skill_job)

        logger.info("skill_job_added", extra={"event": "skill_job.add_skill"})

        return created_skill

    async def get_skills_by_user(
        self, user_id: UUID, job_id: UUID, params: PaginationParams
    ) -> PaginateResponse[SkillJobResponse]:

        job = await self.skill_job_repo.get_by_id_and_user(
            job_id=job_id,
            user_id=user_id,
        )

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The role is not exist",
            )

        skills, total = await self.skill_job_repo.get_skills_by_job_id(
            job_id, skip=params.offset, limit=params.limit
        )

        job_skill_schema = [SkillJobResponse.model_validate(u) for u in skills]

        return PaginateResponse[SkillJobResponse](
            items=job_skill_schema,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    async def get_skill_job_by_id(
        self, user_id: UUID, job_id: UUID, skill_id: UUID
    ) -> JobSkill:

        job = await self.skill_job_repo.get_by_id_and_user(
            job_id=job_id,
            user_id=user_id,
        )

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The role is not exist",
            )

        skill_job = await self.skill_job_repo.get_by_job_and_skill(
            skill_id=skill_id, job_id=job_id
        )

        if skill_job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The skill is not assigned in job.",
            )

        return skill_job

    async def remove_skill_job(
        self, user_id: str | UUID, job_id: str | UUID, skill_id: str | UUID
    ) -> None:

        job = await self.get_owned_job(user_id=user_id, job_id=job_id)

        await self._ensure_skill_not_assigned(job_id=job.id, skill_id=skill_id)

        skill_job = await self.get_skill_job_by_id(
            job_id=job_id,
            skill_id=skill_id,
        )

        await self.skill_job_repo.delete(skill_job)

    async def update_skill_by_job(
        self,
        user_id: str | UUID,
        job_id: str | UUID,
        skill_id: str | UUID,
        skill_in: SkillJobUpdate,
    ) -> JobSkill:
        job = await self.get_owned_job(user_id=user_id, job_id=job_id)

        skill_job = await self.get_skill_job_by_id(
            user_id=user_id,
            job_id=job.id,
            skill_id=skill_id,
        )

        return await self.skill_job_repo.update(skill_job, skill_in)

    async def _ensure_skill_not_assigned(self, job_id: UUID, skill_id: UUID) -> None:
        existing_skill = await self.skill_job_repo.get_by_job_and_skill(
            skill_id=skill_id, job_id=job_id
        )

        if existing_skill is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This skill is assigned in job",
            )

    async def _ensure_skill_exists(self, skill_id: UUID) -> None:
        if not await self.skill_job_repo.skill_exists(skill_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This skill not exist in the catalog",
            )

    async def get_owned_job(self, user_id: UUID, job_id: UUID) -> Job:
        job = await self.skill_job_repo.get_by_id_and_user(
            job_id=job_id,
            user_id=user_id,
        )

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The role is not exist",
            )

        return job
