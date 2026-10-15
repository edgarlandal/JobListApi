from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=50)


class SkillCreateBase(SkillBase):
    pass


class SkillResponseBase(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class SkillUserCreate(BaseModel):
    skill_id: UUID
    level: int = Field(ge=1, le=3)


class SkillJobCreate(BaseModel):
    skill_id: UUID
    minimum_level: int = Field(ge=1, le=3)
    is_required: bool = True
    weight: int = Field(default=1, gt=0)


class SkillUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill: SkillResponseBase
    level: int = Field(ge=1, le=3)


class SkillJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill: SkillResponseBase
    minimum_level: int = Field(ge=1, le=3)
    is_required: bool
    weight: int = Field(gt=0)


class SkillUpdateBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    category: str | None = Field(default=None, max_length=50)

    @field_validator("name", "slug")
    @classmethod
    def reject_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("This field can't be null")

        return value


class SkillUserUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1, le=3)

    @field_validator("level")
    @classmethod
    def reject_null(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("This field can't be null")

        return value


class SkillJobUpdate(BaseModel):
    minimum_level: int | None = Field(default=None, ge=1, le=3)
    is_required: bool | None = None
    weight: int | None = Field(default=None, gt=0)

    @field_validator("minimum_level", "is_required", "weight")
    @classmethod
    def reject_null(cls, value: int | bool | None) -> int | bool:
        if value is None:
            raise ValueError("This field can't be null")

        return value
