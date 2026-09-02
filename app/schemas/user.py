from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserReponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    