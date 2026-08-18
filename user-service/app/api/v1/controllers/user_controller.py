from __future__ import annotations

from fastapi import Depends, HTTPException

from app.db.repositories.user_repository import UserRepository
from app.db.session import AsyncSessionLocal
from app.api.v1.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService


async def get_user_service():
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        yield UserService(repo)


async def create_user(payload: UserCreate, service: UserService = Depends(get_user_service)):
    try:
        user = await service.create_user(
            payload.email,
            payload.full_name,
            payload.user_metadata,
            password=payload.password,
        )
    except ValueError as e:
        if "email_exists" in str(e):
            raise HTTPException(status_code=409, detail="Email already exists")
        raise
    return UserOut.model_validate(user)


async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


async def list_users(
    limit: int = 50, offset: int = 0, service: UserService = Depends(get_user_service)
):
    users = await service.list_users(limit, offset)
    return [UserOut.model_validate(u) for u in users]


async def update_user(
    user_id: int, payload: UserUpdate, service: UserService = Depends(get_user_service)
):
    patch = payload.model_dump(exclude_unset=True, by_alias=False)
    # map user_metadata -> metadata for service/repo layer
    if "user_metadata" in patch:
        patch["metadata"] = patch.pop("user_metadata")
    try:
        user = await service.update_user(user_id, patch)
    except ValueError as e:
        if "email_exists" in str(e):
            raise HTTPException(status_code=409, detail="Email already exists")
        raise
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


async def delete_user(
    user_id: int, hard: bool = False, service: UserService = Depends(get_user_service)
):
    result = await service.delete_user(user_id, hard)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted", "hard": hard}
