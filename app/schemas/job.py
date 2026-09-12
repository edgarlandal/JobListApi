from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.job import TypeSalary, Mode, StatusJob

class JobCreate(BaseModel):
    enterprise: str
    role: str
    salary: Optional[int] = None
    type_salary: Optional[TypeSalary] = None
    mode: Mode 
    location: str
    status_job: StatusJob
    notes: Optional[str] = None
    last_update_at: datetime


class JobUpdate(BaseModel):
    enterprise: Optional[str] = None
    role: Optional[str] = None
    salary: Optional[int] = None
    type_salary: Optional[TypeSalary] = None
    mode: Optional[Mode] = None
    location: Optional[str] = None
    status_job: Optional[str] = None
    notes: Optional[str] = None
    last_update_at: Optional[datetime] = None

class JobResponse(BaseModel):
    id: UUID
    enterprise: str
    role: str
    salary: int
    type_salary: TypeSalary
    mode: Mode 
    location: str
    status_job: StatusJob
    notes: str
    last_update_at: datetime

    model_config = ConfigDict(from_attributes=True)