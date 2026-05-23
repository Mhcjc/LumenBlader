import asyncio
import logging

import httpx
from fastapi import APIRouter, Request

from ..config import save_config
from ..models import SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])
health_router = APIRouter(prefix="/api/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("")
async def get_settings(request: Request):
    config = request.app.state.config
    return config.model_dump()


@router.patch("")
async def update_settings(body: SettingsUpdate, request: Request):
    config = request.app.state.config
    config_path = request.app.state.config_path

    if body.tiktok_downloader:
        for k, v in body.tiktok_downloader.items():
            setattr(config.tiktok_downloader, k, v)
    if body.ai:
        for k, v in body.ai.items():
            setattr(config.ai, k, v)
    if body.server:
        for k, v in body.server.items():
            setattr(config.server, k, v)
    if body.materials_root is not None:
        config.materials_root = body.materials_root

    save_config(config, config_path)
    return config.model_dump()


@health_router.get("/cookie")
async def check_cookie_health(request: Request):
    config = request.app.state.config
    base_url = config.tiktok_downloader.api_base_url
    result = {"downloader_alive": False, "douyin": False, "tiktok": False, "message": ""}

    # Step 1: Check if TikTokDownloader is reachable
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{base_url}/token")
            resp.raise_for_status()
            result["downloader_alive"] = True
    except Exception:
        result["message"] = "TikTokDownloader 服务未运行或无法连接"
        return result

    # Step 2: Check Douyin cookie by requesting a known public video
    cookie = config.tiktok_downloader.cookie_douyin
    if not cookie:
        result["message"] = "抖音 Cookie 未配置"
    else:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{base_url}/douyin/detail",
                    json={"detail_id": "7641528685723471139", "cookie": cookie},
                )
                data = resp.json()
                if data.get("data"):
                    result["douyin"] = True
                else:
                    result["message"] = "抖音 Cookie 可能已失效，请更新"
        except httpx.TimeoutException:
            result["message"] = "抖音接口请求超时，Cookie 可能已失效"
        except Exception as e:
            result["message"] = f"抖音接口异常: {e}"

    # Step 3: Check TikTok cookie (optional, skip if empty)
    cookie_tk = config.tiktok_downloader.cookie_tiktok
    if cookie_tk:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{base_url}/tiktok/detail",
                    json={"detail_id": "7441528685723471139", "cookie": cookie_tk},
                )
                data = resp.json()
                result["tiktok"] = bool(data.get("data"))
        except Exception:
            pass
    else:
        result["tiktok"] = True  # Not configured, skip

    return result
