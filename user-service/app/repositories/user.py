from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.models.user import User


class UserRepository:
    """Persistence layer for User. Kept separate from app.core.security."""

    def __init__(self, session) -> None:
        self.session = session

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, limit: int = 20, offset: int = 0) -> list[User]:
        stmt = select(User).limit(limit).offset(offset).order_by(User.id)
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
        # metadata is a reserved attr on some base classes; set via setattr if needed
        if metadata is not None:
            # Try common field names; fallback to direct attribute
            if hasattr(user, "user_metadata"):
                setattr(user, "user_metadata", metadata)
            elif hasattr(user, "extra_data"):
                setattr(user, "extra_data", metadata)
            else:
                # SQLAlchemy JSON column named `metadata` may be accessible via __dict__
                # Use setattr to avoid shadowing Base metadata
                object.__setattr__(user, "metadata", metadata) if hasattr(user, "metadata") else None
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, patch: dict[str, Any]) -> User:
        for key, value in patch.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def soft_delete(self, user: User) -> None:
        # Assumes model has is_deleted / deleted_at; fallback to flag
        if hasattr(user, "is_deleted"):
            setattr(user, "is_deleted", True)
        if hasattr(user, "deleted_at"):
            from datetime import datetime, timezone

            setattr(user, "deleted_at", datetime.now(timezone.utc))
        await self.session.commit()

    async def hard_delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
