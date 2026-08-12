from app.core.security import hash_password, verify_password, create_access_token

class AuthService:
    def __init__(self, repo):
        self.repo = repo

    async def register(self, email: str, password: str, full_name: str | None):
        hashed = hash_password(password)
        return await self.repo.create(email, hashed, full_name)

    async def login(self, email: str, password: str):
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return create_access_token({"sub": str(user.id)})
