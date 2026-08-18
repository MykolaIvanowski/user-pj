import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from app.db.repositories.user_repository import UserRepository
from app.models.user import User


@pytest.mark.asyncio
async def test_repository_create_and_get(db_session):
    repo = UserRepository(db_session)
    user = await repo.create(email="a@test.com", hashed_password="hash", full_name="Alice")
    assert user.id is not None
    assert user.email == "a@test.com"
    fetched = await repo.get(user.id)
    assert fetched.email == "a@test.com"


@pytest.mark.asyncio
async def test_repository_get_by_email(db_session):
    repo = UserRepository(db_session)
    await repo.create(email="b@test.com", hashed_password="h", full_name="Bob")
    u = await repo.get_by_email("b@test.com")
    assert u is not None
    assert u.full_name == "Bob"
    assert await repo.get_by_email("missing@test.com") is None


@pytest.mark.asyncio
async def test_repository_list_pagination(db_session):
    repo = UserRepository(db_session)
    for i in range(5):
        await repo.create(email=f"list{i}@test.com", hashed_password="h")
    users = await repo.list(limit=2, offset=1)
    assert len(users) == 2
    # ordered by id
    assert users[0].id < users[1].id


@pytest.mark.asyncio
async def test_repository_list_excludes_soft_deleted(db_session):
    repo = UserRepository(db_session)
    u1 = await repo.create(email="soft1@test.com", hashed_password="h")
    u2 = await repo.create(email="soft2@test.com", hashed_password="h")
    await repo.soft_delete(u1)
    all_users = await repo.list(limit=10, include_deleted=True)
    active = await repo.list(limit=10, include_deleted=False)
    assert len(all_users) >= 2
    assert all(u.email != "soft1@test.com" for u in active)
    assert any(u.email == "soft2@test.com" for u in active)


@pytest.mark.asyncio
async def test_repository_update(db_session):
    repo = UserRepository(db_session)
    u = await repo.create(email="upd@test.com", hashed_password="h", full_name="Old")
    updated = await repo.update(u, {"full_name": "New", "avatar_url": "http://a"})
    assert updated.full_name == "New"
    assert updated.avatar_url == "http://a"


@pytest.mark.asyncio
async def test_repository_update_metadata_alias(db_session):
    repo = UserRepository(db_session)
    u = await repo.create(email="meta@test.com", hashed_password="h")
    await repo.update(u, {"metadata": {"role": "admin"}})
    assert u.user_metadata == {"role": "admin"}


@pytest.mark.asyncio
async def test_repository_soft_and_hard_delete(db_session):
    repo = UserRepository(db_session)
    u = await repo.create(email="del@test.com", hashed_password="h")
    await repo.soft_delete(u)
    assert u.is_deleted is True
    assert u.deleted_at is not None
    # get without include_deleted should return None
    assert await repo.get(u.id) is None
    assert await repo.get(u.id, include_deleted=True) is not None

    u2 = await repo.create(email="hard@test.com", hashed_password="h")
    uid = u2.id
    await repo.hard_delete(u2)
    assert await repo.get(uid, include_deleted=True) is None


@pytest.mark.asyncio
async def test_repository_create_with_metadata(db_session):
    repo = UserRepository(db_session)
    u = await repo.create(email="mdat@test.com", hashed_password="h", metadata={"k": "v"})
    assert u.user_metadata == {"k": "v"}
    fetched = await repo.get(u.id)
    assert fetched.user_metadata == {"k": "v"}
