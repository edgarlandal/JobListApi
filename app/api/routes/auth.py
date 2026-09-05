from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import TokenRespose, RefreshTokenRequest
from app.services.auth import AuthService
from app.api.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenRespose)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.authenticate_user(form_data.username, form_data.password)
    return tokens

@router.post("/refresh", response_model=TokenRespose)
async def refresh_token(
    body: RefreshTokenRequest, 
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.refresh_access_token(body.refresh_token)
    return tokens