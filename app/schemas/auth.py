from pydantic import BaseModel

class TokenRespose(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenData(BaseModel):
    email: str | None = None

    