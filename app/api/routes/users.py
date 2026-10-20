from typing import Annotated

from fastapi import APIRouter, Depends, status
from loguru import logger

from app.api.dependencies import get_user_service, require_role
from app.api.routes import skills_user
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserProfileUpdate, UserReponse
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserReponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.register_user(user_in)


@router.get("/me", response_model=UserReponse)
async def get_my_profile(
    curr_user: Annotated[User, Depends(require_role([UserRole.USER]))],
):
    return curr_user


@router.patch("/me", response_model=UserReponse)
async def update_profile(
    actor: Annotated[User, Depends(require_role([UserRole.USER]))],
    user_in: UserProfileUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
):
    return await service.update_my_profile(user_id=actor.id, user_in=user_in)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    actor: Annotated[User, Depends(require_role([UserRole.USER]))],
    service: Annotated[UserService, Depends(get_user_service)],
):
    await service.get_user_by_id(actor.id)
    await service.delete_user(actor.id)


router.include_router(skills_user.router)
