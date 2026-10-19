from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_skill_job_service, require_role
from app.models.user import User, UserRole
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.schemas.skill import SkillJobCreate, SkillJobResponse, SkillJobUpdate
from app.services.skill_job import JobSkillService

router = APIRouter(prefix="")


@router.post(
    "/{job_id}/skills",
    response_model=SkillJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_skill_to_job(
    job_id: str,
    skill_in: SkillJobCreate,
    actor: Annotated[User, Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
    service: Annotated[JobSkillService, Depends(get_skill_job_service)],
):
    return await service.add_skilL_job(
        user_id=actor.id, job_id=job_id, skill_job_data=skill_in
    )


@router.get("/{job_id}/skills", response_model=PaginateResponse[SkillJobResponse])
async def get_skill_by_job(
    job_id: str,
    actor: Annotated[User, Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
    service: Annotated[JobSkillService, Depends(get_skill_job_service)],
    pagination: Annotated[PaginationParams, Depends()],
):
    return await service.get_skills_by_user(
        user_id=actor.id, job_id=job_id, params=pagination
    )


@router.patch("/{job_id}/skills/{skill_id}", response_model=SkillJobResponse)
async def update_skils_by_job(
    job_id: str,
    skill_id: str,
    skill_in: SkillJobUpdate,
    actor: Annotated[User, Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
    service: Annotated[JobSkillService, Depends(get_skill_job_service)],
):
    return await service.update_skill_by_job(
        user_id=actor.id, job_id=job_id, skill_in=skill_in, skill_id=skill_id
    )


@router.delete("/{job_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill_by_job(
    job_id: str,
    skill_id: str,
    actor: Annotated[User, Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
    service: Annotated[JobSkillService, Depends(get_skill_job_service)],
):
    await service.remove_skill_job(user_id=actor.id, job_id=job_id, skill_id=skill_id)
