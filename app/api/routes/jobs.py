from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from loguru import logger

from app.api.dependencies import get_current_user, require_role, get_job_service

from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.services.job import JobService

from app.models.user import UserRole, User
from app.models.job import Job

from app.schemas.pagination import PaginateResponse, PaginationParams

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    actor: Annotated[User, Depends(require_role([UserRole.USER]))],
    service: Annotated[JobService, Depends(get_job_service)]
):
    return await service.create_job(job_in, actor.id)

@router.get("", response_model=PaginateResponse[JobResponse])
async def list_jobs(
    actor: Annotated[User, Depends(require_role(UserRole.USER))],
    service: Annotated[JobService, Depends(get_job_service)],
    pagination: PaginationParams = Depends()
):
    result = await service.get_jobs(pagination)
    logger.info("jobs_listed",  event="user.jobs_listed", actor_id=str(actor.id))
    return result

@router.get("/{job_id}", response_model=JobResponse, dependencies=[Depends(require_role(UserRole.USER))])
async def get_job(
    job_id: str,
    service: Annotated[JobService, Depends(get_job_service)],
):
    return await service.get_job_by_id(job_id)

@router.patch("/{job_id}", response_model=JobResponse, dependencies=[Depends(require_role([UserRole.USER]))])
async def update_job(
    job_id: str,
    job_in: JobUpdate,
    service: Annotated[JobService, Depends(get_job_service)]
):
    result = await service.update_job(job_id=job_id, job_in=job_in)
    logger.info("job_updated", event="user.job_updated")
    return result

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(UserRole.USER))])
async def delete_job(
    job_id: str,
    service: Annotated[JobService, Depends(get_job_service)]
):
    target = await service.get_job_by_id(job_id)
    await service.delete_job(job_id)
    logger.info("job_deleted", event="user.job_deleted", target_id=str(target.id))