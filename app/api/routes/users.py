from loguru import logger
from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Query
from app.schemas.user import UserCreate, UserReponse, UserUpdate
from app.services.user import UserService
from app.models.user import UserRole
from app.api.dependencies import get_user_service, get_current_active_user, require_role
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("", response_model=UserReponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, 
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.register_user(user_in)

@router.get("/me", response_model=UserReponse)
async def get_my_profile(
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN, UserRole.USER]))],
):
    return current_user

@router.get("", response_model=List[UserReponse])
async def list_users(
    actor: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
    service: Annotated[UserService, Depends(get_user_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, get=1, le=100)
):
    result = await service.get_users(skip=skip, limit=limit)
    logger.info("users_listed", event="admin.users_listed", actor_id=str(actor.id))
    return result

@router.get("/{id}", response_model=UserReponse, dependencies=[Depends(require_role([UserRole.USER]))])
async def get_user_by_id(
    id: str, 
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.get_user_by_id(id)

@router.patch("/{user_id}", response_model=UserReponse)
async def update_user(
    actor: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
    user_id: str,
    user_in: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)]
):
    result = await service.update_user(user_id=user_id, user_in=user_in)
    logger.info("user_updated", event="admin.user_updated", actor_id=str(actor.id), target_id=str(result.id))
    return result

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    actor: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)]
):
    target = await service.get_user_by_id(user_id)
    await service.delete_user(user_id)
    logger.info("user_deleted", event="admin.user_deleted", actor_id=str(actor.id), target_id=str(target.id))