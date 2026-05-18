from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/{folder_name}")
async def list_files(folder_name: str, request: Request):
    fm = request.app.state.file_manager
    db = request.app.state.db

    videos = fm.list_videos(folder_name)
    analysis = fm.list_analysis(folder_name)

    # Get analysis job statuses for videos in this folder
    all_jobs = await db.get_analysis_jobs()
    job_status_map = {}
    for job in all_jobs:
        if job["status"] in ("pending", "processing", "failed"):
            video_stem = job["video_path"].rsplit("/", 1)[-1].replace(".mp4", "")
            job_status_map[video_stem] = job["status"]

    return {
        "videos": videos,
        "analysis": analysis,
        "analysis_jobs": job_status_map,
    }


@router.get("/{folder_name}/analysis/{filename}")
async def get_analysis_file(folder_name: str, filename: str, request: Request):
    fm = request.app.state.file_manager
    content = fm.get_analysis_content(folder_name, filename)
    if content is None:
        raise HTTPException(404, "分析文件不存在")
    return {"content": content, "filename": filename}
