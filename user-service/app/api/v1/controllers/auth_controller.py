from fastapi import Depends, HTTPException
from app.api.v1.schemas.auth import Login, Token
from app.db.session import SessionLocal
from app.db.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

async def get_auth_service():
    async with SessionLocal() as session:
        repo = UserRepository(session)
        yield AuthService(repo)

async def login(data: Login, service: AuthService = Depends(get_auth_service)):
    token = await service.login(data.email, data.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(access_token=token)
