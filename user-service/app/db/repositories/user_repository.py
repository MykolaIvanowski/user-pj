from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.models.user import User


class UserRepository:
    """Persistence layer for User."""

    def __init__(self, session) -> None:
        self.session = session

    async def get(self, user_id: int, *, include_deleted: bool = False) -> User | None:
        user = await self.session.get(User, user_id)
        if user is None:
            return None
        if not include_deleted and getattr(user, "is_deleted", False):
            return None
        return user

    async def get_by_email(
        self, email: str, *, include_deleted: bool = False
    ) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is not None and not include_deleted and getattr(user, "is_deleted", False):
            return None
        return user

    async def list(
        self, limit: int = 20, offset: int = 0, *, include_deleted: bool = False
    ) -> list[User]:
        stmt = select(User).order_by(User.id).limit(limit).offset(offset)
        if not include_deleted:
            stmt = stmt.where(User.is_deleted == False)  # noqa: E712
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        **extra: Any,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            **extra,
        )
        if metadata is not None:
            user.user_metadata = metadata
        # handle avatar_url or other extra fields passed via **extra already, but ensure metadata alias
        if "avatar_url" in extra:
            user.avatar_url = extra["avatar_url"]
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, patch: dict[str, Any]) -> User:
        for key, value in patch.items():
            # map alias `metadata` -> `user_metadata`
            if key == "metadata":
                key = "user_metadata"
            if hasattr(user, key):
                setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def soft_delete(self, user: User) -> None:
        if hasattr(user, "is_deleted"):
            setattr(user, "is_deleted", True)
        if hasattr(user, "deleted_at"):
            setattr(user, "deleted_at", datetime.now(timezone.utc))
        await self.session.commit()

    async def hard_delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
