import pytest
from unittest.mock import AsyncMock, MagicMock
from server.services.analyzer import ContentAnalyzer


@pytest.fixture
def analyzer():
    return ContentAnalyzer(
        api_key="test-key",
        base_url="https://api.anthropic.com",
        model="claude-sonnet-4-20250514",
    )


@pytest.mark.asyncio
async def test_generate_summary_calls_api(analyzer):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="这是一段摘要")]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    analyzer.client = mock_client

    result = await analyzer.generate_summary(
        video_title="测试视频",
        transcript="这是视频的字幕内容",
    )
    assert result == "这是一段摘要"
    mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_full_analysis_returns_dict(analyzer):
    mock_text = """## 内容摘要
这是一个测试视频。

## Rubric 打分
- 选题: 8/10
- 表达: 7/10

## 爆款预测
预计播放量: 10w+
"""
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=mock_text)]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    analyzer.client = mock_client

    result = await analyzer.generate_full_analysis(
        video_title="测试视频",
        transcript="字幕内容",
    )
    assert "摘要" in result
    assert "打分" in result


@pytest.mark.asyncio
async def test_generate_markdown_output(analyzer):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="# 视频分析\n\n内容摘要")]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    analyzer.client = mock_client

    md = await analyzer.generate_summary(
        video_title="测试",
        transcript="内容",
    )
    assert isinstance(md, str)
    assert len(md) > 0
