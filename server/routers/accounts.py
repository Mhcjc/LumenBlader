import logging

from fastapi import APIRouter, HTTPException, Request

from ..models import AccountCreate, AccountResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])
logger = logging.getLogger(__name__)


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

    # Fetch real nickname from TikTokDownloader
    config = request.app.state.config
    cookie = config.tiktok_downloader.cookie_douyin if platform == "douyin" else config.tiktok_downloader.cookie_tiktok
    try:
        user_info = await downloader.fetch_user_info(
            sec_user_id=sec_user_id,
            platform=platform,
            cookie=cookie,
            proxy=config.tiktok_downloader.proxy,
        )
        nickname = user_info.get("nickname", sec_user_id) if user_info else sec_user_id
    except Exception as e:
        logger.warning(f"Failed to fetch user info: {e}")
        nickname = sec_user_id

    folder_name = fm.sanitize_folder_name(nickname)
    fm.ensure_account_dir(folder_name)

    account = await db.insert_account(
        platform=platform,
        nickname=nickname,
        url=body.url,
        sec_uid=sec_user_id,
        folder_name=folder_name,
    )
    return account


@router.delete("/{account_id}")
async def delete_account(account_id: str, request: Request):
    db = request.app.state.db
    account = await db.get_account(account_id)
    if not account:
        raise HTTPException(404, "博主不存在")
    await db.delete_account(account_id)
    return {"ok": True}
