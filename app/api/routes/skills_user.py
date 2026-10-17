from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_skill_user_service, require_role
from app.models.user import User, UserRole
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.schemas.skill import SkillUserCreate, SkillUserResponse
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
    return await service.add_skill_user(skill_in, str(actor.id))


@router.get("/me/skills", response_model=PaginateResponse[SkillUserResponse])
async def get_skill_by_user_id(
    actor: Annotated[User, Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
    service: Annotated[UserSkillService, Depends(get_skill_user_service)],
    pagination: Annotated[PaginationParams, Depends()],
):
    return await service.get_skills_by_user(actor.id, pagination)
