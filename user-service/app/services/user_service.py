from app.core.logging import get_logger
from app.events.dispatcher import dispatch_event
from app.events.producer import publish_event

logger = get_logger("user-service")

class UserService:
    def __init__(self, repo):
        self.repo = repo

    async def create_user(self, email, full_name, metadata):
        logger.info(f"Creating user: {email}")

        existing = await self.repo.get_by_email(email)
        if existing:
            logger.warning(f"Email already exists: {email}")
            raise ValueError("email_exists")

        user = await self.repo.create(email, full_name, metadata)

        logger.info(f"User created: id={user.id}")

        await dispatch_event("user.created", {"id": user.id, "email": user.email})

        return user

    async def get_user(self, user_id):
        logger.info(f"Get user: id={user_id}")
        return await self.repo.get(user_id)

    async def list_users(self, limit, offset):
        logger.info(f"List users: limit={limit}, offset={offset}")
        return await self.repo.list(limit, offset)

    async def update_user(self, user_id, patch):
        logger.info(f"Update user: id={user_id}, patch={patch}")

        user = await self.repo.get(user_id)
        if not user:
            logger.warning(f"User not found: id={user_id}")
            return None

        updated = await self.repo.update(user, patch)

        logger.info(f"User updated: id={updated.id}")

        await dispatch_event("user.updated", {"id": updated.id})

        return updated

    async def delete_user(self, user_id, hard=False):
        logger.info(f"Delete user: id={user_id}, hard={hard}")

        user = await self.repo.get(user_id)
        if not user:
            logger.warning(f"User not found: id={user_id}")
            return None

        if hard:
            await self.repo.hard_delete(user)
            logger.info(f"Hard delete: id={user_id}")
            await dispatch_event("user.deleted.hard", {"id": user_id})
        else:
            await self.repo.soft_delete(user)
            logger.info(f"Soft delete: id={user_id}")
            await dispatch_event("user.deleted.soft", {"id": user_id})

        return True

    def __init__(self, repo):
        self.repo = repo

    async def create_user(self, email: str, full_name: str | None, metadata: dict | None):
        existing = await self.repo.get_by_email(email)
        if existing:
            raise ValueError("email_exists")

        user = await self.repo.create(email, full_name, metadata)
        await publish_event("user.created", {"id": user.id, "email": user.email})
        return user

    async def get_user(self, user_id: int):
        return await self.repo.get(user_id)

    async def list_users(self, limit: int, offset: int):
        return await self.repo.list(limit, offset)

    async def update_user(self, user_id: int, patch: dict):
        user = await self.repo.get(user_id)
        if not user:
            return None

        updated = await self.repo.update(user, patch)
        await publish_event("user.updated", {"id": updated.id})
        return updated

    async def delete_user(self, user_id: int, hard: bool = False):
        user = await self.repo.get(user_id)
        if not user:
            return None

        if hard:
            await self.repo.hard_delete(user)
            await publish_event("user.deleted.hard", {"id": user_id})
        else:
            await self.repo.soft_delete(user)
            await publish_event("user.deleted.soft", {"id": user_id})

        return True
