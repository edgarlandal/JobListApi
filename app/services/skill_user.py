from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger

from app.models.skill import UserSkill
from app.repositories.skill_user import UserSkillRepository
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.schemas.skill import SkillUserCreate, SkillUserResponse


class UserSkillService:
    def __init__(self, skill_user_repo: UserSkillRepository):
        self.skill_user_repo = skill_user_repo

    async def add_skill_user(
        self,
        skill_user_data: SkillUserCreate,
        user_id: UUID | str,
    ) -> UserSkill:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        existing_skill = await self.skill_user_repo.get_skill_existing(
            skill_id=skill_user_data.skill_id,
            user_id=user_uuid,
        )

        if existing_skill:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta habilidad ya está asignada al usuario.",
            )

        skill_exists = await self.skill_user_repo.skill_exists(skill_user_data.skill_id)

        if not skill_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La habilidad no existe en el catálogo.",
            )

        new_skill_user = UserSkill(
            user_id=user_uuid,
            skill_id=skill_user_data.skill_id,
            level=skill_user_data.level,
        )

        created_skill = await self.skill_user_repo.create(new_skill_user)

        if created_skill is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta habilidad ya está asignada al usuario.",
            )

        logger.info(
            "skill_user_added",
            extra={"event": "skill_user.add_skill"},
        )

        return created_skill

    async def get_skills_by_user(
        self, user_id: str | UUID, params: PaginationParams
    ) -> PaginateResponse:
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
