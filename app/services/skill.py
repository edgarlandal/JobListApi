from fastapi import HTTPException, status
from loguru import logger

from app.models.skill import Skill
from app.repositories.skill import SkillRepository
from app.schemas.pagination import PaginateResponse, PaginationParams
from app.schemas.skill import SkillCreateBase, SkillResponseBase, SkillUpdateBase


class SkillService:
    def __init__(self, skill_repo: SkillRepository):
        self.skill_repo = skill_repo

    async def create_skill(
        self,
        skill_data: SkillCreateBase,
    ) -> Skill:
        existing_skill = await self.skill_repo.get_by_slug(skill_data.slug)

        if existing_skill:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Skill is register"
            )

        new_skill = Skill(
            name=skill_data.name, slug=skill_data.slug, category=skill_data.category
        )

        created_skill = await self.skill_repo.create(new_skill)
        logger.info("registration_succeeded", event="skill.create_skill")

        return created_skill

    async def update_skill(self, skill_id: str, skill_in: SkillUpdateBase) -> Skill:
        skill = await self.get_skill_by_id(skill_id)

        if skill_in.slug is not None and skill_in.slug != skill.slug:
            existing_skill = await self.skill_repo.get_by_slug(skill_in.slug)

            if existing_skill and existing_skill.id != skill.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Slug is existing"
                )

        return await self.skill_repo.update(skill=skill, skill_in=skill_in)

    async def delete_skill(self, skill_id: str) -> None:
        skill = await self.get_skill_by_id(skill_id)
        await self.skill_repo.delete(skill)

    async def get_skills(self, params: PaginationParams) -> PaginateResponse:
        skills, total = await self.skill_repo.get_all(
            skip=params.offset, limit=params.limit
        )

        skill_schema = [SkillResponseBase.model_validate(u) for u in skills]

        return PaginateResponse[SkillResponseBase](
            items=skill_schema, total=total, limit=params.limit, offset=params.offset
        )

    async def get_skill_by_id(self, skill_id: str) -> Skill:
        skill = await self.skill_repo.get_by_id(skill_id)

        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found"
            )

        return skill
