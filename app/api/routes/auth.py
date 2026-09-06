from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import TokenRespose, RefreshTokenRequest, LogoutRequest
from app.services.auth import AuthService
from app.api.dependencies import get_auth_service
from app.schemas.user import UserCreate, UserReponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenRespose)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.authenticate_user(form_data.username, form_data.password)
    return tokens

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    data: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.logout(refresh_token=data.refresh_token)
    return {
        "detail": "Successfully logged out"
    }

@router.post("/refresh", response_model=TokenRespose)
async def refresh_token(
    body: RefreshTokenRequest, 
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.refresh_access_token(body.refresh_token)
    return tokens

@router.post("/register", response_model=UserReponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    created_user = await auth_service.register_user(user_data)
    return created_user