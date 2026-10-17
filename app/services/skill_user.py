from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger

from app.models.skill import UserSkill
from app.repositories.skill_user import UserSkillRepository
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.schemas.skill import SkillUserCreate, SkillUserResponse, SkillUserUpdate


class UserSkillService:
    def __init__(self, skill_user_repo: UserSkillRepository):
        self.skill_user_repo = skill_user_repo

    async def add_skill_user(
        self,
        skill_user_data: SkillUserCreate,
        user_id: UUID,
    ) -> UserSkill:
        await self._ensure_skill_not_assigned(
            user_id=user_id, skill_id=skill_user_data.skill_id
        )
        await self._ensure_skill_exists(skill_user_data.skill_id)

        new_skill_user = UserSkill(
            user_id=user_id,
            skill_id=skill_user_data.skill_id,
            level=skill_user_data.level,
        )

        created_skill = await self.skill_user_repo.create(new_skill_user)

        logger.info(
            "skill_user_added",
            extra={"event": "skill_user.add_skill"},
        )

        return created_skill

    async def get_skills_by_user(
        self, user_id: UUID, params: PaginationParams
    ) -> PaginateResponse[SkillUserResponse]:
        skills, total = await self.skill_user_repo.get_skills_by_user_id(
            user_id, skip=params.offset, limit=params.limit
        )

        user_skill_schema = [SkillUserResponse.model_validate(u) for u in skills]

        return PaginateResponse[SkillUserResponse](
            items=user_skill_schema,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    async def get_skill_user_by_id(self, user_id: UUID, skill_id: UUID) -> UserSkill:
        skill_user = await self.skill_user_repo.get_by_user_and_skill(
            user_id=user_id, skill_id=skill_id
        )

        if skill_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La habilidad no está asignada al usuario.",
            )

        return skill_user

    async def remove_skill_user(self, user_id: UUID, skill_id: UUID) -> None:
        skill_user = await self.get_skill_user_by_id(user_id=user_id, skill_id=skill_id)
        await self.skill_user_repo.delete(skill_user)

    async def update_level_skill(
        self, user_id: UUID, skill_id: UUID, skill_in: SkillUserUpdate
    ) -> UserSkill:
        skill_user = await self.get_skill_user_by_id(user_id=user_id, skill_id=skill_id)
        return await self.skill_user_repo.update(skill_user, skill_in)

    async def _ensure_skill_not_assigned(self, user_id: UUID, skill_id: UUID) -> None:
        existing_skill = await self.skill_user_repo.get_by_user_and_skill(
            user_id=user_id, skill_id=skill_id
        )
        if existing_skill is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta habilidad ya está asignada al usuario.",
            )

    async def _ensure_skill_exists(self, skill_id: UUID) -> None:
        if not await self.skill_user_repo.skill_exists(skill_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La habilidad no existe en el catálogo.",
            )
