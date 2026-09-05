from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import HTTPException, status

from app.core.config import settings

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False

def create_jwt_token(data: dict, expire_data: timedelta, token_type: Literal["access", "refresh"]):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expire_data

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": token_type
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
def create_access_token(data: dict) -> str:
    return create_jwt_token(
        data=data,
        expire_data=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access"
    )

def create_refresh_token(data: dict):
    return create_jwt_token(
        data=data,
        expire_data=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh"
    )

def decode_acces_token(token: str, expected_type: Literal["access", "refresh"]) -> Optional[dict]:
    try:
        payload = jwt.decode( 
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token type is invalid. Is expected {expected_type}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError:
        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid",
            headers={"WWWW-Autheticate", "Bearer"}
        )