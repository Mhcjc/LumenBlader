import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from server.services.downloader import TikTokDownloaderClient


@pytest.fixture
def client():
    return TikTokDownloaderClient("http://127.0.0.1:5555")


def test_extract_sec_user_id_douyin(client):
    url = "https://www.douyin.com/user/MS4wLjABAAAAabc123"
    assert client.extract_sec_user_id(url) == "MS4wLjABAAAAabc123"


def test_extract_sec_user_id_douyin_with_params(client):
    url = "https://www.douyin.com/user/MS4wLjABAAAAabc123?vid=123"
    assert client.extract_sec_user_id(url) == "MS4wLjABAAAAabc123"


def test_extract_sec_user_id_tiktok(client):
    url = "https://www.tiktok.com/@username"
    result = client.extract_sec_user_id(url)
    assert result == "username"


@pytest.mark.asyncio
async def test_fetch_account_videos_calls_api(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"aweme_id": "vid1", "desc": "视频1", "create_time": 1700000000},
            {"aweme_id": "vid2", "desc": "视频2", "create_time": 1700001000},
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        videos = await client.fetch_account_videos(
            sec_user_id="abc123",
            earliest="2025-01-01",
            latest="2025-12-31",
        )
        assert len(videos) == 2
        assert videos[0]["aweme_id"] == "vid1"
