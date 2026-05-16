import pytest
from pathlib import Path
from server.services.file_manager import FileManager


@pytest.fixture
def fm(tmp_path):
    materials = tmp_path / "materials"
    materials.mkdir()
    return FileManager(materials)


def test_ensure_account_dir_creates_folders(fm):
    path = fm.ensure_account_dir("测试博主")
    assert path.exists()
    assert (path / "videos").exists()
    assert (path / "analysis").exists()


def test_ensure_account_dir_idempotent(fm):
    p1 = fm.ensure_account_dir("测试博主")
    p2 = fm.ensure_account_dir("测试博主")
    assert p1 == p2


def test_list_videos(fm):
    account_dir = fm.ensure_account_dir("博主A")
    (account_dir / "videos" / "video1.mp4").write_bytes(b"fake")
    (account_dir / "videos" / "video2.mp4").write_bytes(b"fake")
    videos = fm.list_videos("博主A")
    assert len(videos) == 2
    assert all(v["name"].endswith(".mp4") for v in videos)


def test_list_analysis(fm):
    account_dir = fm.ensure_account_dir("博主A")
    (account_dir / "analysis" / "video1.md").write_text("# Analysis")
    analysis = fm.list_analysis("博主A")
    assert len(analysis) == 1
    assert analysis[0]["name"] == "video1.md"


def test_get_analysis_content(fm):
    account_dir = fm.ensure_account_dir("博主A")
    (account_dir / "analysis" / "video1.md").write_text("# 标题\n\n内容")
    content = fm.get_analysis_content("博主A", "video1.md")
    assert content == "# 标题\n\n内容"


def test_get_analysis_content_not_found(fm):
    content = fm.get_analysis_content("博主A", "nonexistent.md")
    assert content is None


def test_detect_platform_from_url_douyin(fm):
    assert fm.detect_platform("https://www.douyin.com/user/abc123") == "douyin"


def test_detect_platform_from_url_tiktok(fm):
    assert fm.detect_platform("https://www.tiktok.com/@username") == "tiktok"


def test_sanitize_folder_name(fm):
    assert fm.sanitize_folder_name("博主/Name") == "博主Name"
    assert fm.sanitize_folder_name("  spaces  ") == "spaces"
