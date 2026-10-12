import uuid

from sqlalchemy import ForeignKey, String, CheckConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(50))
    
    user_skills: Mapped[list["UserSkill"]] = relationship(
        back_populates="skills",
        passive_deletes="all",
    )
    
    job_skills: Mapped[list["JobSkill"]] = relationship(
        back_populates="skill",
        passive_deletes="all",
    )

class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (
        CheckConstraint(
            "level BETWEEN 1 AND 3",
            name="ck_user_skill_level",
        ),
    )
     
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, 
        index=True
    )
    
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True, 
        index=True
    )
    
    level: Mapped[int] = mapped_column()
    
    user: Mapped["User"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="user_skills")
    
class JobSkill(Base):
    __tablename__ = "job_skills"
    __table_args__ = (
        CheckConstraint(
            "minimum_level BETWEEN 1 AND 3",
            name="ck_job_skill_level"
        ),
        CheckConstraint(
            "weight > 0",
            name="ck_job_skill_weight"
        )
    )
    
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        primary_key=True
    )
    
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True, 
        index=True
    )
    
    minimum_level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(default=True)
    weight: Mapped[int] = mapped_column(default=1)
    
    job: Mapped["Job"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="job_skills")