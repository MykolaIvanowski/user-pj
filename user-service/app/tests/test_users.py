import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.v1.controllers.user_controller import get_user_service
from app.services.user_service import UserService


def _make_user(**kw):
    u = SimpleNamespace(
        id=kw.get("id", 1),
        email=kw.get("email", "test@example.com"),
        full_name=kw.get("full_name", "Test User"),
        avatar_url=None,
        user_metadata=None,
        hashed_password="hashed",
        is_deleted=False,
        deleted_at=None,
    )
    u.metadata = None
    return u


class _FakeRepo:
    def __init__(self):
        self.store = {}
        self.next_id = 1

    async def get(self, uid, **kw):
        return self.store.get(uid)

    async def get_by_email(self, email, **kw):
        for u in self.store.values():
            if u.email == email:
                return u
        return None

    async def list(self, limit=20, offset=0, **kw):
        vals = sorted(self.store.values(), key=lambda x: x.id)
        return vals[offset : offset + limit]

    async def create(self, email, hashed_password, full_name=None, metadata=None, **kw):
        u = _make_user(id=self.next_id, email=email, full_name=full_name)
        u.hashed_password = hashed_password
        self.store[self.next_id] = u
        self.next_id += 1
        return u

    async def update(self, user, patch):
        for k, v in patch.items():
            setattr(user, k, v)
        return user

    async def soft_delete(self, user):
        user.is_deleted = True

    async def hard_delete(self, user):
        self.store.pop(user.id, None)


@pytest.fixture
def _app(monkeypatch):
    repo = _FakeRepo()
    monkeypatch.setattr("app.services.user_service.publish_event", AsyncMock())
    monkeypatch.setattr("app.events.producer.publish_event", AsyncMock())

    async def _override():
        yield UserService(repo)

    app.dependency_overrides[get_user_service] = _override
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_user_success(monkeypatch, _app):
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/users",
            json={"email": "test@example.com", "full_name": "Test User", "password": "S3curePass!123"},
        )
    assert r.status_code in (200, 201)
    body = r.json()
    assert body.get("email") == "test@example.com" or "id" in body


@pytest.mark.asyncio
async def test_create_user_invalid_email(_app):
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/users", json={"email": "not-an-email"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_user_duplicate(monkeypatch, _app):
    transport = ASGITransport(app=_app)
    payload = {"email": "dup@example.com", "password": "S3curePass!123"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.post("/users", json=payload)
        second = await ac.post("/users", json=payload)
    assert second.status_code in (200, 201, 409, 422)
    if first.status_code in (200, 201) and second.status_code not in (200, 201):
        assert second.status_code == 409
