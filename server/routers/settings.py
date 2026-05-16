from fastapi import APIRouter, Request

from ..config import save_config
from ..models import SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


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
