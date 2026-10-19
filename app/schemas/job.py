from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.job import Mode, StatusJob, TypeSalary


class JobCreate(BaseModel):
    enterprise: str
    role: str
    salary: int | None
    type_salary: TypeSalary | None
    mode: Mode
    location: str
    status_job: StatusJob
    notes: str | None
    last_update_at: datetime


class JobUpdate(BaseModel):
    enterprise: str | None
    role: str | None
    salary: int | None
    type_salary: TypeSalary | None
    mode: Mode | None
    location: str | None
    status_job: str | None
    notes: str | None
    last_update_at: datetime | None


class JobResponse(BaseModel):
    id: UUID
    enterprise: str
    role: str
    salary: int | None
    type_salary: TypeSalary | None
    mode: Mode
    location: str
    status_job: StatusJob
    notes: str
    last_update_at: datetime

    model_config = ConfigDict(from_attributes=True)
