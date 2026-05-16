import json
import pytest
from pathlib import Path
from server.config import load_config, save_config, AppConfig


def test_load_config_returns_app_config(tmp_path):
    config_data = {
        "tiktok_downloader": {
            "api_base_url": "http://127.0.0.1:5555",
            "cookie_douyin": "",
            "cookie_tiktok": "",
            "proxy": "",
            "download_threads": 5,
        },
        "ai": {
            "api_key": "test-key",
            "base_url": "https://api.anthropic.com",
            "model": "claude-sonnet-4-20250514",
            "whisper_api": True,
        },
        "server": {"host": "0.0.0.0", "port": 8080},
        "materials_root": "../materials",
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    config = load_config(config_file)
    assert isinstance(config, AppConfig)
    assert config.ai.api_key == "test-key"
    assert config.server.port == 8080


def test_save_config_writes_json(tmp_path):
    config_data = {
        "tiktok_downloader": {
            "api_base_url": "http://127.0.0.1:5555",
            "cookie_douyin": "",
            "cookie_tiktok": "",
            "proxy": "",
            "download_threads": 5,
        },
        "ai": {
            "api_key": "",
            "base_url": "https://api.anthropic.com",
            "model": "claude-sonnet-4-20250514",
            "whisper_api": True,
        },
        "server": {"host": "0.0.0.0", "port": 8080},
        "materials_root": "../materials",
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    config = load_config(config_file)
    config.ai.api_key = "new-key"
    save_config(config, config_file)

    reloaded = json.loads(config_file.read_text())
    assert reloaded["ai"]["api_key"] == "new-key"
