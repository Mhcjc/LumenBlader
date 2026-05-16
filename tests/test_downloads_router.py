import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from server.main import create_app
from server.config import AppConfig
from server.database import Database


@pytest_asyncio.fixture
async def app(tmp_path):
    config = AppConfig(materials_root=str(tmp_path / "materials"))
    db = Database(tmp_path / "test.db")
    await db.init()
    # Seed an account
    await db.insert_account(
        platform="douyin",
        nickname="测试博主",
        url="https://www.douyin.com/user/abc123",
        sec_uid="abc123",
        folder_name="测试博主",
    )
    app = create_app(config, db)
    yield app
    await db.close()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_batch_download(client):
    accounts = (await client.get("/api/accounts")).json()
    account_id = accounts[0]["id"]

    with patch.object(
        client._transport.app.state.downloader,
        "fetch_account_videos",
        new_callable=AsyncMock,
        return_value=[
            {"aweme_id": "vid1", "desc": "视频1", "create_time": 1700000000},
            {"aweme_id": "vid2", "desc": "视频2", "create_time": 1700001000},
        ],
    ):
        resp = await client.post("/api/downloads/batch", json={
            "account_id": account_id,
            "earliest": "2025-01-01",
            "latest": "2025-12-31",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"
        assert "id" in data


@pytest.mark.asyncio
async def test_get_download_job(client):
    accounts = (await client.get("/api/accounts")).json()
    account_id = accounts[0]["id"]

    with patch.object(
        client._transport.app.state.downloader,
        "fetch_account_videos",
        new_callable=AsyncMock,
        return_value=[{"aweme_id": "vid1", "desc": "视频1", "create_time": 1700000000}],
    ):
        create_resp = await client.post("/api/downloads/batch", json={
            "account_id": account_id,
        })
        job_id = create_resp.json()["id"]

    resp = await client.get(f"/api/downloads/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


@pytest.mark.asyncio
async def test_single_download(client):
    with patch.object(
        client._transport.app.state.downloader,
        "fetch_video_detail",
        new_callable=AsyncMock,
        return_value={"aweme_id": "7438291029384756123", "desc": "单个视频", "author": {"nickname": "测试", "sec_uid": "sec123"}},
    ):
        resp = await client.post("/api/downloads/single", json={
            "url": "https://www.douyin.com/video/7438291029384756123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
