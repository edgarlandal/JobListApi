from typing import List, Annotated
from fastapi import APIRouter, Depends, status
from app.schemas.user import UserCreate, UserReponse
from app.services.user import UserService
from app.api.dependencies import get_user_service, get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserReponse)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@router.get("", response_model=List[UserReponse])
async def list_users(service: UserService = Depends(get_user_service)):
    return await service.get_users()

@router.post("", response_model=UserReponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.register_user(user_in)
