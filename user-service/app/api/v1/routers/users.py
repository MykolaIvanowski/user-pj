from fastapi import APIRouter

from app.api.v1.controllers.user_controller import (
    create_user,
    delete_user,
    get_user,
    list_users,
    update_user,
)

router = APIRouter(prefix="/users", tags=["users"])

# Support both /users and /users/ (Starlette does 307 redirect otherwise)
router.post("", response_model=None, status_code=201)(create_user)
router.post("/", response_model=None, status_code=201)(create_user)
router.get("", response_model=None)(list_users)
router.get("/", response_model=None)(list_users)
router.get("/{user_id}", response_model=None)(get_user)
router.patch("/{user_id}", response_model=None)(update_user)
router.delete("/{user_id}", response_model=None)(delete_user)
