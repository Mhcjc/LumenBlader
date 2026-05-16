import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from server.main import create_app
from server.config import AppConfig
from server.database import Database


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
async def test_start_analysis(client):
    with patch.object(
        client._transport.app.state.analyzer,
        "generate_summary",
        new_callable=AsyncMock,
        return_value="# 分析报告\n\n这是摘要",
    ):
        resp = await client.post("/api/analysis/start", json={
            "video_path": "/path/to/video.mp4",
            "mode": "summary",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"
        assert data["mode"] == "summary"


@pytest.mark.asyncio
async def test_get_analysis_job(client):
    with patch.object(
        client._transport.app.state.analyzer,
        "generate_summary",
        new_callable=AsyncMock,
        return_value="摘要内容",
    ):
        create_resp = await client.post("/api/analysis/start", json={
            "video_path": "/path/to/video.mp4",
            "mode": "summary",
        })
        job_id = create_resp.json()["id"]

    resp = await client.get(f"/api/analysis/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id
