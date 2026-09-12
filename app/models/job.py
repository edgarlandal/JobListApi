import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class TypeSalary(str, enum.Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Mounthly"
    YEARLY = "Yearly"

class Mode(str, enum.Enum):
    ONSITE = "On-Site"
    HYBRID = "Hybrid"
    REMOTE = "Remote"

class  StatusJob(str, enum.Enum):
    SEND = "Send"
    RH = "RH"
    IN_PROCESS = "In Process"
    TECHNICAL_IN ="Technical Interview"
    OFFER = "Job Offer"
    REJECTION = "Rejection"
    CANCELLED = "Cancelled"

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    enterprise: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    salary: Mapped[int] = mapped_column(
        nullable=True,
    )

    type_salary: Mapped[TypeSalary] = mapped_column(
        Enum(TypeSalary, name="type_salary"),
        nullable=True
    )

    mode: Mapped[Mode] = mapped_column(
        Enum(Mode, name="mode_work"),
        nullable=False
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    status_job: Mapped[StatusJob] = mapped_column(
        Enum(StatusJob, name="status_job"),
        nullable=False
    )

    last_update_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        server_default=func.now()
    )

    notes: Mapped[String] = mapped_column(
        String(255),
        nullable=True
    )

    user: Mapped["User"] = relationship(
        back_populates="jobs"
    )