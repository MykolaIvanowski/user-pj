from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.events.producer import publish_event

logger = get_logger("user-service")


class UserService:
    def __init__(self, repo) -> None:
        self.repo = repo

    async def create_user(
        self,
        email: str,
        full_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        password: str | None = None,
        hashed_password: str | None = None,
    ):
        logger.info("creating_user", email=email)

        existing = await self.repo.get_by_email(email)
        if existing:
            logger.warning("email_already_exists", email=email)
            raise ValueError("email_exists")

        # Resolve hashed_password: prefer explicit hashed_password, else hash plain password.
        if hashed_password is None and password is not None:
            from app.core.security import hash_password

            hashed_password = hash_password(password)
        if hashed_password is None:
            # Keeps backward compat with callers that pass no password (e.g. tests / OAuth)
            # but the User model requires a password; use empty hash placeholder
            # and let DB/validation reject if strict.
            hashed_password = ""

        user = await self.repo.create(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            metadata=metadata,
        )

        logger.info("user_created", user_id=user.id, email=user.email)

        await publish_event("user.created", {"id": user.id, "email": user.email})

        return user

    async def get_user(self, user_id: int):
        logger.info("get_user", user_id=user_id)
        return await self.repo.get(user_id)

    async def list_users(self, limit: int = 20, offset: int = 0):
        # Clamp to sane bounds to avoid DB abuse
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        logger.info("list_users", limit=limit, offset=offset)
        return await self.repo.list(limit, offset)

    async def update_user(self, user_id: int, patch: dict[str, Any]):
        logger.info("update_user", user_id=user_id, patch_keys=list(patch.keys()))

        user = await self.repo.get(user_id)
        if not user:
            logger.warning("user_not_found", user_id=user_id)
            return None

        updated = await self.repo.update(user, patch)

        logger.info("user_updated", user_id=updated.id)

        await publish_event("user.updated", {"id": updated.id})

        return updated

    async def delete_user(self, user_id: int, hard: bool = False):
        logger.info("delete_user", user_id=user_id, hard=hard)

        user = await self.repo.get(user_id)
        if not user:
            logger.warning("user_not_found", user_id=user_id)
            return None

        if hard:
            await self.repo.hard_delete(user)
            logger.info("user_hard_deleted", user_id=user_id)
            await publish_event("user.deleted.hard", {"id": user_id})
        else:
            await self.repo.soft_delete(user)
            logger.info("user_soft_deleted", user_id=user_id)
            await publish_event("user.deleted.soft", {"id": user_id})

        return True
