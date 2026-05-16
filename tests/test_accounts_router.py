import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from server.main import create_app
from server.config import AppConfig
from server.database import Database
from pathlib import Path


@pytest_asyncio.fixture
async def app(tmp_path):
    config = AppConfig(materials_root=str(tmp_path / "materials"))
    db = Database(tmp_path / "test.db")
    await db.init()
    app = create_app(config, db)
    yield app
    await db.close()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_list_accounts_empty(client):
    resp = await client.get("/api/accounts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_account(client):
    resp = await client.post("/api/accounts", json={
        "url": "https://www.douyin.com/user/abc123",
        "platform": "douyin",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["platform"] == "douyin"
    assert data["sec_uid"] == "abc123"
    assert data["nickname"] != ""


@pytest.mark.asyncio
async def test_create_account_auto_detect_platform(client):
    resp = await client.post("/api/accounts", json={
        "url": "https://www.tiktok.com/@testuser",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["platform"] == "tiktok"


@pytest.mark.asyncio
async def test_delete_account(client):
    create_resp = await client.post("/api/accounts", json={
        "url": "https://www.douyin.com/user/abc123",
    })
    account_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/accounts/{account_id}")
    assert del_resp.status_code == 200

    list_resp = await client.get("/api/accounts")
    assert len(list_resp.json()) == 0
