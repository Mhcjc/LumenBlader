from fastapi import APIRouter, HTTPException, Request

from ..models import AccountCreate, AccountResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


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

    sec_user_id = downloader.extract_sec_user_id(body.url)
    if not sec_user_id:
        raise HTTPException(400, "无法从 URL 提取用户 ID")

    folder_name = fm.sanitize_folder_name(sec_user_id)
    fm.ensure_account_dir(folder_name)

    account = await db.insert_account(
        platform=platform,
        nickname=sec_user_id,
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
