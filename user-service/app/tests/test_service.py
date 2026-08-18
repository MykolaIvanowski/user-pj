import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.user_service import UserService


def make_user(**kw):
    m = MagicMock()
    m.id = kw.get("id", 1)
    m.email = kw.get("email", "test@example.com")
    m.full_name = kw.get("full_name", "Test")
    m.avatar_url = kw.get("avatar_url", None)
    m.user_metadata = kw.get("user_metadata", None)
    m.is_deleted = kw.get("is_deleted", False)
    return m


@pytest.mark.asyncio
async def test_service_create_success(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get_by_email.return_value = None
    fake_user = make_user(email="new@test.com")
    repo.create.return_value = fake_user
    svc = UserService(repo)
    user = await svc.create_user("new@test.com", "New", password="S3curePass!123")
    assert user.email == "new@test.com"
    repo.create.assert_awaited_once()
    # password should be hashed
    call_kwargs = repo.create.call_args.kwargs
    assert call_kwargs["hashed_password"] != "S3curePass!123"
    assert call_kwargs["hashed_password"] != ""


@pytest.mark.asyncio
async def test_service_create_duplicate(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get_by_email.return_value = make_user()
    svc = UserService(repo)
    with pytest.raises(ValueError, match="email_exists"):
        await svc.create_user("dup@test.com")


@pytest.mark.asyncio
async def test_service_create_with_hashed_password(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get_by_email.return_value = None
    repo.create.return_value = make_user()
    svc = UserService(repo)
    await svc.create_user("a@test.com", hashed_password="alreadyhashed")
    assert repo.create.call_args.kwargs["hashed_password"] == "alreadyhashed"


@pytest.mark.asyncio
async def test_service_get_user(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get.return_value = make_user(id=5)
    svc = UserService(repo)
    u = await svc.get_user(5)
    assert u.id == 5
    repo.get.assert_awaited_once_with(5)


@pytest.mark.asyncio
async def test_service_list_users_clamps(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.list.return_value = []
    svc = UserService(repo)
    await svc.list_users(limit=1000, offset=-5)
    # should clamp limit to 100 and offset to 0
    repo.list.assert_awaited_once_with(100, 0)


@pytest.mark.asyncio
async def test_service_update_success(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get.return_value = make_user(id=1, email="old@test.com")
    repo.get_by_email.return_value = None
    updated = make_user(id=1, full_name="Updated")
    repo.update.return_value = updated
    svc = UserService(repo)
    result = await svc.update_user(1, {"full_name": "Updated"})
    assert result.full_name == "Updated"


@pytest.mark.asyncio
async def test_service_update_not_found(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get.return_value = None
    svc = UserService(repo)
    assert await svc.update_user(999, {"full_name": "x"}) is None


@pytest.mark.asyncio
async def test_service_update_duplicate_email(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get.return_value = make_user(id=1, email="a@test.com")
    repo.get_by_email.return_value = make_user(id=2, email="b@test.com")
    svc = UserService(repo)
    with pytest.raises(ValueError, match="email_exists"):
        await svc.update_user(1, {"email": "b@test.com"})


@pytest.mark.asyncio
async def test_service_delete_soft(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get.return_value = make_user(id=1)
    svc = UserService(repo)
    result = await svc.delete_user(1, hard=False)
    assert result is True
    repo.soft_delete.assert_awaited_once()
    repo.hard_delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_service_delete_hard(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get.return_value = make_user(id=1)
    svc = UserService(repo)
    result = await svc.delete_user(1, hard=True)
    assert result is True
    repo.hard_delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_service_delete_not_found(monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    repo = AsyncMock()
    repo.get.return_value = None
    svc = UserService(repo)
    assert await svc.delete_user(999) is None
