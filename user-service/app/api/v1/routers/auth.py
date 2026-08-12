from fastapi import APIRouter
from app.api.v1.controllers.auth_controller import login
from app.api.v1.schemas.auth import Login, Token

router = APIRouter(prefix="/auth", tags=["auth"])

router.post("/login", response_model=Token)(login)
