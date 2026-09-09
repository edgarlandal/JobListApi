# import os
# from dotenv import load_dotenv

# load_dotenv()

# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_PORT = int(os.getenv("DB_PORT", 5433))
# DB_NAME = os.getenv("DB_NAME")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")

# JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
# JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

# if not JWT_SECRET_KEY or not DB_PASSWORD:
#     raise ValueError("CRITICAL ERRORL")

# DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

from typing import Optional, List
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    PROJECT_NAME: str = "Job List"
    PORT: int = 8000
    ENVIROMENT: str = "development"
    DEBUG: bool = True

    # -------------------------------------------- #
    #           REQUIREMENTS VARIABLES             #
    # -------------------------------------------- #

    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int  = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173"
    ]

    # JWT 
    JWT_SECRET_KEY: str = Field(..., min_length=32, description="JWT Secret Key of 32 character")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # API Keys 

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Setting()
