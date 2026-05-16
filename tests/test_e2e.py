import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from server.main import create_app
from server.config import AppConfig
from server.database import Database


@pytest_asyncio.fixture
async def app(tmp_path):
    materials = tmp_path / "materials"
    materials.mkdir()
    config = AppConfig(materials_root=str(materials))
    db = Database(tmp_path / "test.db")
    await db.init()
    app = create_app(config, db)
    app.state.config_path = tmp_path / "config.json"
    yield app
    await db.close()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_full_workflow(client):
    """Test: add account -> batch download -> analyze"""

    # 1. Add account
    with patch.object(
        client._transport.app.state.downloader,
        "extract_sec_user_id",
        return_value="abc123",
    ):
        resp = await client.post("/api/accounts", json={
            "url": "https://www.douyin.com/user/abc123",
        })
        assert resp.status_code == 200
        account = resp.json()
        account_id = account["id"]

    # 2. Batch download
    with patch.object(
        client._transport.app.state.downloader,
        "fetch_account_videos",
        new_callable=AsyncMock,
        return_value=[
            {"aweme_id": "v1", "desc": "视频1", "create_time": 1700000000},
            {"aweme_id": "v2", "desc": "视频2", "create_time": 1700001000},
        ],
    ):
        resp = await client.post("/api/downloads/batch", json={
            "account_id": account_id,
            "earliest": "2025-01-01",
        })
        assert resp.status_code == 200
        job = resp.json()
        assert job["total_videos"] == 2

    # 3. Verify job exists
    resp = await client.get(f"/api/downloads/{job['id']}")
    assert resp.status_code == 200

    # 4. Verify account listing
    resp = await client.get("/api/accounts")
    assert len(resp.json()) == 1

    # 5. Settings round-trip
    resp = await client.get("/api/settings")
    assert resp.status_code == 200

    resp = await client.patch("/api/settings", json={
        "ai": {"api_key": "test-key-123"},
    })
    assert resp.json()["ai"]["api_key"] == "test-key-123"
