from fastapi import APIRouter
from app.api.v1.controllers.user_controller import (
    create_user, get_user, list_users, update_user, delete_user
)

router = APIRouter(prefix="/users", tags=["users"])

router.post("/", response_model=None)(create_user)
router.get("/", response_model=None)(list_users)
router.get("/{user_id}", response_model=None)(get_user)
router.patch("/{user_id}", response_model=None)(update_user)
router.delete("/{user_id}", response_model=None)(delete_user)
