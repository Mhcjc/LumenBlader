import json
from pathlib import Path
from pydantic import BaseModel


class TikTokDownloaderConfig(BaseModel):
    api_base_url: str = "http://127.0.0.1:5555"
    cookie_douyin: str = ""
    cookie_tiktok: str = ""
    proxy: str = ""
    download_threads: int = 5


class AIConfig(BaseModel):
    api_key: str = ""
    base_url: str = "https://api.anthropic.com"
    model: str = "claude-sonnet-4-20250514"
    whisper_api: bool = True


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080


class AppConfig(BaseModel):
    tiktok_downloader: TikTokDownloaderConfig = TikTokDownloaderConfig()
    ai: AIConfig = AIConfig()
    server: ServerConfig = ServerConfig()
    materials_root: str = "../materials"


def load_config(path: Path) -> AppConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return AppConfig(**data)


def save_config(config: AppConfig, path: Path) -> None:
    path.write_text(
        config.model_dump_json(indent=2),
        encoding="utf-8",
    )
