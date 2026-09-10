import re
import uuid

from typing import Optional

from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    firstname: str
    lastname: str


    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("firstname", "lastname")
    @classmethod
    def clean_names(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("The value can't empty")

        return cleaned

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_policy(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("The password must be at least 8 character long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("It must include at least one capital letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("It must include at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("It must include at least one number")
        return v

class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    
class UserReponse(UserBase):
    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

    