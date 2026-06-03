import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request

from ..models import AccountCreate, AccountResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])
logger = logging.getLogger(__name__)


async def _fetch_nickname(downloader, sec_user_id, platform, cookie, proxy) -> str:
    """Try to fetch nickname from TikTokDownloader API. Returns empty string on failure."""
    # Fast path: use dedicated user info endpoint
    try:
        user_info = await asyncio.wait_for(
            downloader.fetch_user_info(
                sec_user_id=sec_user_id,
                platform=platform,
                cookie=cookie,
                proxy=proxy,
            ),
            timeout=15,
        )
        if user_info and user_info.get("nickname"):
            return user_info["nickname"]
    except asyncio.TimeoutError:
        logger.warning("Timeout fetching user info for nickname")
    except Exception as e:
        logger.warning(f"Failed to fetch user info for nickname: {e}")
    return ""


@router.get("", response_model=list[AccountResponse])
async def list_accounts(request: Request):
    db = request.app.state.db
    return await db.get_accounts()


@router.post("", response_model=AccountResponse)
async def create_account(body: AccountCreate, request: Request):
    db = request.app.state.db
    fm = request.app.state.file_manager
    downloader = request.app.state.downloader

    platform = body.platform
    if not platform:
        platform = fm.detect_platform(body.url)
    if not platform:
        raise HTTPException(400, "无法识别平台，请手动指定 platform")

    resolved_url = await downloader.resolve_short_url(body.url)

    sec_user_id = downloader.extract_sec_user_id(resolved_url)
    if not sec_user_id:
        raise HTTPException(400, "无法从 URL 提取用户 ID")

    # Fetch nickname from account's video list (TikTokDownloader has no dedicated user info endpoint)
    config = request.app.state.config
    cookie = config.tiktok_downloader.cookie_douyin if platform == "douyin" else config.tiktok_downloader.cookie_tiktok
    proxy = config.tiktok_downloader.proxy
    nickname = await _fetch_nickname(downloader, sec_user_id, platform, cookie, proxy)

    if not nickname:
        nickname = "未知博主"

    folder_name = fm.sanitize_folder_name(nickname)
    # Ensure unique folder name by appending short sec_uid suffix if needed
    if fm.account_dir_exists(folder_name):
        short_id = sec_user_id[:8] if len(sec_user_id) > 8 else sec_user_id
        folder_name = fm.sanitize_folder_name(f"{nickname}_{short_id}")
    fm.ensure_account_dir(folder_name)

    account = await db.insert_account(
        platform=platform,
        nickname=nickname,
        url=body.url,
        sec_uid=sec_user_id,
        folder_name=folder_name,
    )
    return account


@router.post("/{account_id}/refresh")
async def refresh_account(account_id: str, request: Request):
    db = request.app.state.db
    downloader = request.app.state.downloader
    account = await db.get_account(account_id)
    if not account:
        raise HTTPException(404, "博主不存在")

    config = request.app.state.config
    platform = account["platform"]
    cookie = config.tiktok_downloader.cookie_douyin if platform == "douyin" else config.tiktok_downloader.cookie_tiktok
    proxy = config.tiktok_downloader.proxy
    nickname = await _fetch_nickname(downloader, account["sec_uid"], platform, cookie, proxy)

    if not nickname:
        raise HTTPException(400, "无法获取博主昵称，请检查 Cookie 是否有效")

    await db.update_account_nickname(account_id, nickname)
    return {"id": account_id, "nickname": nickname}


@router.delete("/{account_id}")
async def delete_account(account_id: str, request: Request, delete_files: bool = False):
    db = request.app.state.db
    fm = request.app.state.file_manager
    account = await db.get_account(account_id)
    if not account:
        raise HTTPException(404, "博主不存在")
    if delete_files:
        fm.delete_account_dir(account["folder_name"])
    await db.delete_account(account_id)
    return {"ok": True, "files_deleted": delete_files}
