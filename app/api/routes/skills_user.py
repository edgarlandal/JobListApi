from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_skill_user_service, require_role
from app.models.user import User, UserRole
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.schemas.skill import SkillUserCreate, SkillUserResponse, SkillUserUpdate
from app.services.skill_user import UserSkillService

router = APIRouter(prefix="")


@router.post(
    "/me/skills", response_model=SkillUserResponse, status_code=status.HTTP_201_CREATED
)
async def add_skill_to_user(
    skill_in: SkillUserCreate,
    actor: Annotated[User, Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
    service: Annotated[UserSkillService, Depends(get_skill_user_service)],
):
    return await service.add_skill_user(skill_in, actor.id)


@router.get("/me/skills", response_model=PaginateResponse[SkillUserResponse])
async def get_skill_by_user_id(
    actor: Annotated[User, Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
    service: Annotated[UserSkillService, Depends(get_skill_user_service)],
    pagination: Annotated[PaginationParams, Depends()],
):
    return await service.get_skills_by_user(actor.id, pagination)


@router.patch(
    "/me/{skill_id}/skills",
    response_model=SkillUserResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_level(
    skill_id: UUID,
    actor: Annotated[User, Depends(require_role([UserRole.ADMIN, UserRole.USER]))],
    service: Annotated[UserSkillService, Depends(get_skill_user_service)],
    skill_in: SkillUserUpdate,
):
    return await service.update_level_skill(
        user_id=actor.id, skill_id=skill_id, skill_in=skill_in
    )


@router.delete("/me/{skill_id}/skills", status_code=status.HTTP_204_NO_CONTENT)
async def remove_skill(
    skill_id: UUID,
    actor: Annotated[User, Depends(require_role([UserRole.ADMIN, UserRole.USER]))],
    service: Annotated[UserSkillService, Depends(get_skill_user_service)],
):
    await service.remove_skill_user(user_id=actor.id, skill_id=skill_id)
