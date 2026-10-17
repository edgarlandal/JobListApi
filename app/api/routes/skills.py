from typing import Annotated

from fastapi import APIRouter, Depends, status
from loguru import logger

from app.api.dependencies import get_skill_service, require_role
from app.models.user import User, UserRole
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.schemas.skill import SkillCreateBase, SkillResponseBase, SkillUpdateBase
from app.services.skill import SkillService

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.post(
    "",
    response_model=SkillResponseBase,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def create_skill(
    skill_in: SkillCreateBase,
    service: Annotated[SkillService, Depends(get_skill_service)],
):
    return await service.create_skill(skill_data=skill_in)


@router.get("", response_model=PaginateResponse[SkillResponseBase])
async def list_skills(
    actor: Annotated[User, Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
    service: Annotated[SkillService, Depends(get_skill_service)],
    pagination: Annotated[PaginationParams, Depends()],
):
    result = await service.get_skills(pagination)
    return result


@router.get(
    "/{skill_id}",
    response_model=SkillResponseBase,
    dependencies=[Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
)
async def get_skill(
    skill_id: str, service: Annotated[SkillService, Depends(get_skill_service)]
):
    return await service.get_skill_by_id(skill_id)


@router.patch(
    "/{skill_id}",
    response_model=SkillResponseBase,
    dependencies=[Depends(require_role([UserRole.USER, UserRole.ADMIN]))],
)
async def update_skill(
    skill_id: str,
    skill_in: SkillUpdateBase,
    service: Annotated[SkillService, Depends(get_skill_service)],
):
    res = await service.update_skill(skill_id=skill_id, skill_in=skill_in)
    logger.info("skill_update", event="skil.skill_updated")
    return res


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def delete_skill(
    skill_id: str, service: Annotated[SkillService, Depends(get_skill_service)]
):
    target = await service.get_skill_by_id(skill_id)
    await service.delete_skill(target)
    logger.info("skill_deleted", event="skill.skill_deleted", target_id=str(target.id))
