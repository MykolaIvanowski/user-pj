import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.v1.controllers.user_controller import get_user_service
from app.services.user_service import UserService


def make_user(**kw):
    u = SimpleNamespace(
        id=kw.get("id", 1),
        email=kw.get("email", "test@example.com"),
        full_name=kw.get("full_name", "Test User"),
        avatar_url=kw.get("avatar_url", None),
        user_metadata=kw.get("user_metadata", None),
        hashed_password=kw.get("hashed_password", "hashed"),
        is_deleted=kw.get("is_deleted", False),
        deleted_at=kw.get("deleted_at", None),
    )
    u.metadata = u.user_metadata
    return u


class FakeRepo:
    def __init__(self):
        self.store: dict[int, SimpleNamespace] = {}
        self.next_id = 1

    async def get(self, user_id: int, **kw):
        u = self.store.get(user_id)
        if u and getattr(u, "is_deleted", False) and not kw.get("include_deleted"):
            return None
        return u

    async def get_by_email(self, email: str, **kw):
        for u in self.store.values():
            if u.email == email and not getattr(u, "is_deleted", False):
                return u
        return None

    async def list(self, limit=20, offset=0, **kw):
        active = [u for u in self.store.values() if not getattr(u, "is_deleted", False)]
        active.sort(key=lambda x: x.id)
        return active[offset : offset + limit]

    async def create(self, email, hashed_password, full_name=None, metadata=None, **extra):
        u = make_user(id=self.next_id, email=email, full_name=full_name, user_metadata=metadata)
        u.hashed_password = hashed_password
        u.avatar_url = extra.get("avatar_url")
        u.metadata = u.user_metadata
        self.store[self.next_id] = u
        self.next_id += 1
        return u

    async def update(self, user, patch):
        for k, v in patch.items():
            if k == "metadata":
                k = "user_metadata"
                user.metadata = v
            setattr(user, k, v)
            if k == "user_metadata":
                user.metadata = v
        return user

    async def soft_delete(self, user):
        user.is_deleted = True
        from datetime import datetime, timezone

        user.deleted_at = datetime.now(timezone.utc)

    async def hard_delete(self, user):
        self.store.pop(user.id, None)


@pytest.fixture
def fake_repo():
    return FakeRepo()


@pytest.fixture
def app_with_fake_repo(fake_repo, monkeypatch):
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    monkeypatch.setattr("app.events.producer.publish_event", AsyncMock())

    async def _override():
        yield UserService(fake_repo)

    app.dependency_overrides[get_user_service] = _override
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_user_success(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/users/", json={"email": "alice@example.com", "full_name": "Alice", "password": "S3curePass!123"}
        )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert body["id"] == 1
    assert body["full_name"] == "Alice"


@pytest.mark.asyncio
async def test_create_user_with_metadata(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/users/",
            json={"email": "meta@example.com", "password": "S3curePass!123", "metadata": {"role": "admin"}},
        )
    assert r.status_code == 201
    assert r.json()["metadata"] == {"role": "admin"}


@pytest.mark.asyncio
async def test_create_user_invalid_email(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/users/", json={"email": "not-an-email", "password": "S3curePass!123"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_user_short_password(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/users/", json={"email": "a@b.com", "password": "short"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_duplicate_email(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    payload = {"email": "dup@example.com", "password": "S3curePass!123"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.post("/users/", json=payload)
        r2 = await ac.post("/users/", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 409
    assert r2.json()["detail"] == "Email already exists"


@pytest.mark.asyncio
async def test_get_user_success(app_with_fake_repo, fake_repo):
    await fake_repo.create(email="get@example.com", hashed_password="h", full_name="Get Me")
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/users/1")
    assert r.status_code == 200
    assert r.json()["email"] == "get@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/users/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_users(app_with_fake_repo, fake_repo):
    for i in range(3):
        await fake_repo.create(email=f"list{i}@example.com", hashed_password="h")
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/users/?limit=2&offset=1")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert body[0]["email"] == "list1@example.com"


@pytest.mark.asyncio
async def test_list_users_default_pagination(app_with_fake_repo, fake_repo):
    await fake_repo.create(email="one@example.com", hashed_password="h")
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/users/")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_update_user_success(app_with_fake_repo, fake_repo):
    await fake_repo.create(email="upd@example.com", hashed_password="h", full_name="Old")
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.patch("/users/1", json={"full_name": "New Name", "avatar_url": "http://cdn/a.png"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "New Name"
    assert r.json()["avatar_url"] == "http://cdn/a.png"


@pytest.mark.asyncio
async def test_update_user_metadata(app_with_fake_repo, fake_repo):
    await fake_repo.create(email="upd2@example.com", hashed_password="h")
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.patch("/users/1", json={"metadata": {"x": 1}})
    assert r.status_code == 200
    assert r.json()["metadata"] == {"x": 1}


@pytest.mark.asyncio
async def test_update_user_not_found(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.patch("/users/999", json={"full_name": "Nope"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_user_duplicate_email(app_with_fake_repo, fake_repo):
    await fake_repo.create(email="a@example.com", hashed_password="h")
    await fake_repo.create(email="b@example.com", hashed_password="h")
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.patch("/users/1", json={"email": "b@example.com"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_delete_soft(app_with_fake_repo, fake_repo):
    await fake_repo.create(email="del@example.com", hashed_password="h")
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.delete("/users/1")
        assert r.status_code == 200
        assert r.json() == {"status": "deleted", "hard": False}
        r2 = await ac.get("/users/1")
        assert r2.status_code == 404
        r3 = await ac.get("/users/")
        assert len(r3.json()) == 0


@pytest.mark.asyncio
async def test_delete_hard(app_with_fake_repo, fake_repo):
    await fake_repo.create(email="hard@example.com", hashed_password="h")
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.delete("/users/1?hard=true")
        assert r.status_code == 200
        assert r.json()["hard"] is True
        assert len(fake_repo.store) == 0


@pytest.mark.asyncio
async def test_delete_not_found(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.delete("/users/999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_full_crud_lifecycle(app_with_fake_repo):
    transport = ASGITransport(app=app_with_fake_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/users/", json={"email": "life@example.com", "full_name": "Life", "password": "S3curePass!123"}
        )
        assert r.status_code == 201
        uid = r.json()["id"]
        r = await ac.get(f"/users/{uid}")
        assert r.status_code == 200
        r = await ac.patch(f"/users/{uid}", json={"full_name": "Alive"})
        assert r.json()["full_name"] == "Alive"
        r = await ac.get("/users/")
        assert len(r.json()) == 1
        r = await ac.delete(f"/users/{uid}")
        assert r.status_code == 200
        r = await ac.get(f"/users/{uid}")
        assert r.status_code == 404
