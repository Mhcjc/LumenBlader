import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from server.main import create_app
from server.config import AppConfig
from server.database import Database


@pytest_asyncio.fixture
async def app(tmp_path):
    materials = tmp_path / "materials"
    materials.mkdir()
    # Create test files
    account_dir = materials / "测试博主"
    (account_dir / "videos").mkdir(parents=True)
    (account_dir / "analysis").mkdir(parents=True)
    (account_dir / "videos" / "test.mp4").write_bytes(b"fake")
    (account_dir / "analysis" / "test.md").write_text("# 测试分析")

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
async def test_list_files(client):
    resp = await client.get("/api/files/测试博主")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["videos"]) == 1
    assert len(data["analysis"]) == 1


@pytest.mark.asyncio
async def test_get_analysis_content(client):
    resp = await client.get("/api/files/测试博主/analysis/test.md")
    assert resp.status_code == 200
    assert "# 测试分析" in resp.json()["content"]


@pytest.mark.asyncio
async def test_get_settings(client):
    resp = await client.get("/api/settings")
    assert resp.status_code == 200
    assert "ai" in resp.json()


@pytest.mark.asyncio
async def test_update_settings(client):
    resp = await client.patch("/api/settings", json={
        "ai": {"api_key": "new-key"},
    })
    assert resp.status_code == 200
    assert resp.json()["ai"]["api_key"] == "new-key"
