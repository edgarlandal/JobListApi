from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import Token
from app.services.auth import AuthService
from app.api.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    auth_service: AuthService = Depends(get_auth_service)
):
    token = await auth_service.authenticate_user(form_data.username, form_data.password)
    return {"access_token": token, "token_type": "bearer"} 