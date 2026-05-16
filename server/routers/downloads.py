from fastapi import APIRouter, HTTPException, Request

from ..models import BatchDownloadRequest, SingleDownloadRequest, DownloadJobResponse

router = APIRouter(prefix="/api/downloads", tags=["downloads"])


@router.post("/batch", response_model=DownloadJobResponse)
async def batch_download(body: BatchDownloadRequest, request: Request):
    db = request.app.state.db
    downloader = request.app.state.downloader
    config = request.app.state.config

    account = await db.get_account(body.account_id)
    if not account:
        raise HTTPException(404, "博主不存在")

    videos = await downloader.fetch_account_videos(
        sec_user_id=account["sec_uid"],
        platform=account["platform"],
        earliest=body.earliest,
        latest=body.latest,
        cookie=config.tiktok_downloader.cookie_douyin if account["platform"] == "douyin" else config.tiktok_downloader.cookie_tiktok,
        proxy=config.tiktok_downloader.proxy,
    )

    job = await db.insert_download_job(
        account_id=body.account_id,
        earliest=body.earliest,
        latest=body.latest,
    )

    for video in videos:
        await db.insert_download_item(
            job_id=job["id"],
            video_id=video.get("aweme_id", ""),
            title=video.get("desc", ""),
        )

    await db.update_download_job(
        job["id"],
        total_videos=len(videos),
        status="pending",
    )

    updated_job = await db.get_download_job(job["id"])
    return updated_job


@router.post("/single", response_model=DownloadJobResponse)
async def single_download(body: SingleDownloadRequest, request: Request):
    db = request.app.state.db
    downloader = request.app.state.downloader
    fm = request.app.state.file_manager
    config = request.app.state.config

    video_id = downloader.extract_video_id(body.url)
    if not video_id:
        raise HTTPException(400, "无法从 URL 提取视频 ID")

    platform = fm.detect_platform(body.url)
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

    # Find or create account
    author = detail.get("author", {})
    sec_uid = author.get("sec_uid", "unknown")
    nickname = author.get("nickname", sec_uid)
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
    await db.insert_download_item(
        job_id=job["id"],
        video_id=video_id,
        title=detail.get("desc", ""),
    )
    await db.update_download_job(job["id"], total_videos=1)

    return await db.get_download_job(job["id"])


@router.get("", response_model=list[DownloadJobResponse])
async def list_download_jobs(request: Request):
    db = request.app.state.db
    return await db.get_download_jobs()


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
