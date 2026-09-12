import uuid

from datetime import datetime, timezone
from fastapi import HTTPException, status

from loguru import logger

from app.repositories.job import JobRepository
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.models.job import Job

class JobService:
    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def create_job(self, job_in: JobCreate, user_id: str) -> Job:
        new_job = Job(
            user_id=user_id,
            enterprise=job_in.enterprise,
            role=job_in.role,
            salary=job_in.salary,
            type_salary=job_in.type_salary,
            mode=job_in.mode,
            location=job_in.location,
            status_job=job_in.status_job,
            last_update_at=datetime.now(timezone.utc),
            notes=job_in.notes
        )

        created_job = await self.job_repo.create(new_job)
        logger.info("registration_succeeded", event="job.registerd", job_id=str(created_job.id))
        return created_job

    async def update_job(self, job_id: str, job_in: JobUpdate) -> Job:
        job = await self.get_job_by_id(job_id)
        return await self.job_repo.update(job, job_in)

    async def delete_job(self, job_id: str) -> None:
        job = await self.get_job_by_id(job_id)
        await self.job_repo.delete(job)
    
    async def get_jobs(self, params: PaginationParams) -> PaginateResponse:
        logger.info("get_jobs",  event="user.get_jobs")

        jobs, total = await self.job_repo.get_all(skip=params.offset, limit=params.limit)

        job_schema = [JobResponse.model_validate(j) for j in jobs]

        return PaginateResponse[JobResponse](
            items=job_schema,
            total=total,
            limit=params.limit,
            offset=params.offset
        )

    async def get_job_by_id(self, job_id: str) -> Job:
        job = await self.job_repo.get_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        return job
