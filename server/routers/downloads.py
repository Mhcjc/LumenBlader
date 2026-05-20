import logging
from datetime import datetime
from pathlib import Path
from typing import Set

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..models import BatchDownloadRequest, DownloadJobResponse, SingleDownloadRequest

router = APIRouter(prefix="/api/downloads", tags=["downloads"])
logger = logging.getLogger(__name__)

# Track cancelled job IDs so background tasks can check
_cancelled_jobs: Set[str] = set()


def _is_cancelled(job_id: str) -> bool:
    return job_id in _cancelled_jobs


async def _process_single_item(app_state, job_id: str, item_id: str, video_id: str, platform: str, folder_name: str):
    """Background task: download a single item (used by both single download and retry)."""
    db = app_state.db
    downloader = app_state.downloader
    config = app_state.config

    if _is_cancelled(job_id):
        return

    try:
        await db.update_download_item(item_id, status="downloading")
        await db.update_download_job(job_id, status="downloading")

        cookie = config.tiktok_downloader.cookie_douyin if platform == "douyin" else config.tiktok_downloader.cookie_tiktok
        detail = await downloader.fetch_video_detail(
            video_id=video_id,
            platform=platform,
            cookie=cookie,
            proxy=config.tiktok_downloader.proxy,
        )

        if _is_cancelled(job_id):
            return

        if not detail:
            raise Exception("获取视频详情失败")

        if isinstance(detail, list):
            detail = detail[0] if detail else {}

        download_url = detail.get("downloads", "")
        if isinstance(download_url, list):
            download_url = download_url[0] if download_url else ""

        if not download_url:
            raise Exception("未找到下载链接")

        desc = detail.get("desc", video_id)
        safe_desc = "".join(c for c in desc if c.isalnum() or c in " _-").strip()[:64]
        filename = f"{video_id}_{safe_desc}.mp4"

        materials_root = Path(config.materials_root)
        if not materials_root.is_absolute():
            materials_root = (Path(__file__).parent.parent.parent / materials_root).resolve()

        dest = materials_root / folder_name / "videos" / filename
        await downloader.download_file(download_url, dest)

        if _is_cancelled(job_id):
            return

        await db.update_download_item(item_id, status="completed")
        await _update_job_counts(db, job_id)

    except Exception as e:
        if _is_cancelled(job_id):
            return
        logger.error(f"Download failed for {video_id}: {e}")
        await db.update_download_item(item_id, status="failed", error=str(e))
        await _update_job_counts(db, job_id)


async def _process_single_download(app_state, job_id: str, item_id: str, video_id: str, platform: str, folder_name: str):
    """Background task: fetch detail and download a single video."""
    db = app_state.db
    downloader = app_state.downloader
    config = app_state.config

    if _is_cancelled(job_id):
        return

    try:
        await db.update_download_item(item_id, status="downloading")
        await db.update_download_job(job_id, status="downloading")

        cookie = config.tiktok_downloader.cookie_douyin if platform == "douyin" else config.tiktok_downloader.cookie_tiktok
        detail = await downloader.fetch_video_detail(
            video_id=video_id,
            platform=platform,
            cookie=cookie,
            proxy=config.tiktok_downloader.proxy,
        )

        if _is_cancelled(job_id):
            return

        if not detail:
            raise Exception("获取视频详情失败")

        # detail may be a list or dict
        if isinstance(detail, list):
            detail = detail[0] if detail else {}

        download_url = detail.get("downloads", "")
        if isinstance(download_url, list):
            download_url = download_url[0] if download_url else ""

        if not download_url:
            raise Exception("未找到下载链接")

        # Determine filename
        desc = detail.get("desc", video_id)
        safe_desc = "".join(c for c in desc if c.isalnum() or c in " _-").strip()[:64]
        filename = f"{video_id}_{safe_desc}.mp4"

        materials_root = Path(config.materials_root)
        if not materials_root.is_absolute():
            materials_root = (Path(__file__).parent.parent.parent / materials_root).resolve()

        dest = materials_root / folder_name / "videos" / filename
        await downloader.download_file(download_url, dest)

        if _is_cancelled(job_id):
            return

        await db.update_download_item(item_id, status="completed")
        await _update_job_counts(db, job_id)

    except Exception as e:
        if _is_cancelled(job_id):
            return
        logger.error(f"Download failed for {video_id}: {e}")
        await db.update_download_item(item_id, status="failed", error=str(e))
        await _update_job_counts(db, job_id)


async def _process_batch_download(app_state, job_id: str, account_id: str, videos: list[dict]):
    """Background task: download all videos in a batch job."""
    db = app_state.db
    downloader = app_state.downloader
    config = app_state.config

    account = await db.get_account(account_id)
    if not account:
        await db.update_download_job(job_id, status="failed")
        return

    platform = account["platform"]
    folder_name = account["folder_name"]
    cookie = config.tiktok_downloader.cookie_douyin if platform == "douyin" else config.tiktok_downloader.cookie_tiktok

    await db.update_download_job(job_id, status="downloading")
    items = await db.get_download_items(job_id)

    for item in items:
        if _is_cancelled(job_id):
            await db.update_download_job(job_id, status="cancelled", finished_at=datetime.utcnow().isoformat())
            return

        video_id = item["video_id"]
        item_id = item["id"]
        try:
            await db.update_download_item(item_id, status="downloading")

            detail = await downloader.fetch_video_detail(
                video_id=video_id,
                platform=platform,
                cookie=cookie,
                proxy=config.tiktok_downloader.proxy,
            )

            if _is_cancelled(job_id):
                await db.update_download_job(job_id, status="cancelled", finished_at=datetime.utcnow().isoformat())
                return

            if not detail:
                raise Exception("获取视频详情失败")

            if isinstance(detail, list):
                detail = detail[0] if detail else {}

            download_url = detail.get("downloads", "")
            if isinstance(download_url, list):
                download_url = download_url[0] if download_url else ""

            if not download_url:
                raise Exception("未找到下载链接")

            desc = detail.get("desc", video_id)
            safe_desc = "".join(c for c in desc if c.isalnum() or c in " _-").strip()[:64]
            filename = f"{video_id}_{safe_desc}.mp4"

            materials_root = Path(config.materials_root)
            if not materials_root.is_absolute():
                materials_root = (Path(__file__).parent.parent.parent / materials_root).resolve()

            dest = materials_root / folder_name / "videos" / filename
            await downloader.download_file(download_url, dest)

            if _is_cancelled(job_id):
                await db.update_download_job(job_id, status="cancelled", finished_at=datetime.utcnow().isoformat())
                return

            await db.update_download_item(item_id, status="completed")
            await _update_job_counts(db, job_id)

        except Exception as e:
            if _is_cancelled(job_id):
                await db.update_download_job(job_id, status="cancelled", finished_at=datetime.utcnow().isoformat())
                return
            logger.error(f"Batch download failed for {video_id}: {e}")
            await db.update_download_item(item_id, status="failed", error=str(e))

    if not _is_cancelled(job_id):
        await _update_job_counts(db, job_id)


async def _update_job_counts(db, job_id: str):
    """Recalculate job counts and mark as completed if all items are done."""
    items = await db.get_download_items(job_id)
    downloaded = sum(1 for i in items if i["status"] == "completed")
    failed = sum(1 for i in items if i["status"] == "failed")
    total = len(items)
    pending = sum(1 for i in items if i["status"] in ("pending", "downloading"))

    updates = {"downloaded": downloaded, "failed": failed, "total_videos": total}
    if pending == 0:
        updates["status"] = "completed"
        updates["finished_at"] = datetime.utcnow().isoformat()

    await db.update_download_job(job_id, **updates)


@router.post("/batch", response_model=DownloadJobResponse)
async def batch_download(body: BatchDownloadRequest, request: Request, background_tasks: BackgroundTasks):
    db = request.app.state.db
    downloader = request.app.state.downloader
    config = request.app.state.config

    account = await db.get_account(body.account_id)
    if not account:
        raise HTTPException(404, "博主不存在")

    try:
        videos = await downloader.fetch_account_videos(
            sec_user_id=account["sec_uid"],
            platform=account["platform"],
            earliest=body.earliest,
            latest=body.latest,
            cookie=config.tiktok_downloader.cookie_douyin if account["platform"] == "douyin" else config.tiktok_downloader.cookie_tiktok,
            proxy=config.tiktok_downloader.proxy,
        )
    except Exception as e:
        raise HTTPException(502, f"无法连接 TikTokDownloader 服务: {e}")

    job = await db.insert_download_job(
        account_id=body.account_id,
        earliest=body.earliest,
        latest=body.latest,
    )

    for video in videos:
        await db.insert_download_item(
            job_id=job["id"],
            video_id=video.get("id", ""),
            title=video.get("desc", ""),
        )

    await db.update_download_job(
        job["id"],
        total_videos=len(videos),
        status="pending",
    )

    background_tasks.add_task(_process_batch_download, request.app.state, job["id"], body.account_id, videos)

    updated_job = await db.get_download_job(job["id"])
    return updated_job


@router.post("/single", response_model=DownloadJobResponse)
async def single_download(body: SingleDownloadRequest, request: Request, background_tasks: BackgroundTasks):
    db = request.app.state.db
    downloader = request.app.state.downloader
    fm = request.app.state.file_manager
    config = request.app.state.config

    # Resolve short URLs (e.g. v.douyin.com) to full URLs before extracting video ID
    resolved_url = await downloader.resolve_short_url(body.url)
    video_id = downloader.extract_video_id(resolved_url)
    if not video_id:
        raise HTTPException(400, "无法从 URL 提取视频 ID")

    platform = fm.detect_platform(resolved_url)
    if not platform:
        raise HTTPException(400, "无法识别平台")

    detail = await downloader.fetch_video_detail(
        video_id=video_id,
        platform=platform,
        cookie=config.tiktok_downloader.cookie_douyin if platform == "douyin" else config.tiktok_downloader.cookie_tiktok,
        proxy=config.tiktok_downloader.proxy,
    )

    if not detail:
        raise HTTPException(502, "获取视频详情失败")

    if isinstance(detail, list):
        detail = detail[0] if detail else {}

    # Find or create account - nickname/sec_uid are top-level in TikTokDownloader response
    sec_uid = detail.get("sec_uid", "unknown")
    nickname = detail.get("nickname", "") or sec_uid
    folder_name = fm.sanitize_folder_name(nickname)
    fm.ensure_account_dir(folder_name)

    accounts = await db.get_accounts()
    account = next((a for a in accounts if a["sec_uid"] == sec_uid), None)
    if not account:
        account = await db.insert_account(
            platform=platform,
            nickname=nickname,
            url=body.url.rsplit("/", 1)[0],
            sec_uid=sec_uid,
            folder_name=folder_name,
        )

    job = await db.insert_download_job(account_id=account["id"])
    item = await db.insert_download_item(
        job_id=job["id"],
        video_id=video_id,
        title=detail.get("desc", ""),
    )
    await db.update_download_job(job["id"], total_videos=1)

    background_tasks.add_task(
        _process_single_download,
        request.app.state, job["id"], item["id"], video_id, platform, folder_name,
    )

    return await db.get_download_job(job["id"])


@router.get("")
async def list_download_jobs(request: Request):
    db = request.app.state.db
    jobs = await db.get_download_jobs()
    accounts = {a["id"]: a for a in await db.get_accounts()}
    for job in jobs:
        account = accounts.get(job.get("account_id"))
        if account:
            job["account_name"] = account["nickname"]
            job["platform"] = account["platform"]
        items = await db.get_download_items(job["id"])
        job["items"] = items
    return jobs


@router.get("/{job_id}", response_model=DownloadJobResponse)
async def get_download_job(job_id: str, request: Request):
    db = request.app.state.db
    job = await db.get_download_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return job


@router.get("/{job_id}/items")
async def get_download_items(job_id: str, request: Request):
    db = request.app.state.db
    job = await db.get_download_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return await db.get_download_items(job_id)


@router.post("/{job_id}/cancel")
async def cancel_download_job(job_id: str, request: Request):
    """Cancel an in-progress download job."""
    db = request.app.state.db
    job = await db.get_download_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    if job["status"] not in ("pending", "downloading"):
        raise HTTPException(400, "任务已结束，无法取消")

    _cancelled_jobs.add(job_id)
    await db.update_download_job(job_id, status="cancelled", finished_at=datetime.utcnow().isoformat())

    # Mark any pending/downloading items as cancelled
    items = await db.get_download_items(job_id)
    for item in items:
        if item["status"] in ("pending", "downloading"):
            await db.update_download_item(item["id"], status="cancelled")

    return {"ok": True, "status": "cancelled"}


@router.post("/{job_id}/retry")
async def retry_failed_items(job_id: str, request: Request, background_tasks: BackgroundTasks):
    """Retry all failed items in a download job."""
    db = request.app.state.db
    job = await db.get_download_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")

    items = await db.get_download_items(job_id)
    failed_items = [i for i in items if i["status"] == "failed"]
    if not failed_items:
        raise HTTPException(400, "没有失败的下载项")

    # Get account info for platform and folder_name
    account = await db.get_account(job["account_id"])
    if not account:
        raise HTTPException(404, "博主不存在")

    platform = account["platform"]
    folder_name = account["folder_name"]

    # Remove from cancelled set if it was cancelled
    _cancelled_jobs.discard(job_id)

    # Reset failed items to pending
    for item in failed_items:
        await db.update_download_item(item["id"], status="pending", error=None)

    # Update job status
    await db.update_download_job(job_id, status="downloading", finished_at=None)

    # Start background task for each failed item
    for item in failed_items:
        background_tasks.add_task(
            _process_single_item,
            request.app.state, job_id, item["id"], item["video_id"], platform, folder_name,
        )

    return {"ok": True, "retrying": len(failed_items)}


@router.delete("/{job_id}")
async def delete_download_job(job_id: str, request: Request):
    """Delete a download job and its items."""
    db = request.app.state.db
    job = await db.get_download_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")

    # Cancel if still running
    if job["status"] in ("pending", "downloading"):
        _cancelled_jobs.add(job_id)

    await db.delete_download_job(job_id)
    return {"ok": True}
