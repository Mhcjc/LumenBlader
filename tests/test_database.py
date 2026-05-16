import pytest
import pytest_asyncio
from pathlib import Path
from server.database import Database


@pytest_asyncio.fixture
async def db(tmp_path):
    db = Database(tmp_path / "test.db")
    await db.init()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_init_creates_tables(db):
    async with db.connect() as conn:
        result = await conn.execute_fetchall(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = {row[0] for row in result}
        assert "accounts" in table_names
        assert "download_jobs" in table_names
        assert "download_items" in table_names
        assert "analysis_jobs" in table_names


@pytest.mark.asyncio
async def test_insert_and_get_account(db):
    account = await db.insert_account(
        platform="douyin",
        nickname="测试博主",
        url="https://www.douyin.com/user/abc123",
        sec_uid="abc123",
        folder_name="测试博主",
    )
    assert account["id"] is not None
    assert account["platform"] == "douyin"

    accounts = await db.get_accounts()
    assert len(accounts) == 1
    assert accounts[0]["nickname"] == "测试博主"


@pytest.mark.asyncio
async def test_delete_account(db):
    account = await db.insert_account(
        platform="douyin",
        nickname="测试",
        url="https://www.douyin.com/user/abc",
        sec_uid="abc",
        folder_name="测试",
    )
    await db.delete_account(account["id"])
    accounts = await db.get_accounts()
    assert len(accounts) == 0


@pytest.mark.asyncio
async def test_insert_and_get_download_job(db):
    account = await db.insert_account(
        platform="douyin",
        nickname="测试",
        url="https://www.douyin.com/user/abc",
        sec_uid="abc",
        folder_name="测试",
    )
    job = await db.insert_download_job(
        account_id=account["id"],
        earliest="2025-01-01",
        latest="2025-12-31",
    )
    assert job["status"] == "pending"
    assert job["total_videos"] == 0

    fetched = await db.get_download_job(job["id"])
    assert fetched["id"] == job["id"]


@pytest.mark.asyncio
async def test_insert_and_get_analysis_job(db):
    job = await db.insert_analysis_job(
        video_path="/path/to/video.mp4",
        mode="summary",
    )
    assert job["status"] == "pending"

    fetched = await db.get_analysis_job(job["id"])
    assert fetched["video_path"] == "/path/to/video.mp4"
