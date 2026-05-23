import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..models import AnalysisStartRequest, AnalysisBatchRequest, AnalysisJobResponse

router = APIRouter(prefix="/api/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)


@router.post("/start", response_model=AnalysisJobResponse)
async def start_analysis(body: AnalysisStartRequest, request: Request, background_tasks: BackgroundTasks):
    db = request.app.state.db
    analyzer = request.app.state.analyzer
    fm = request.app.state.file_manager
    transcriber = request.app.state.transcriber

    job = await db.insert_analysis_job(
        video_path=body.video_path,
        mode=body.mode,
    )

    background_tasks.add_task(
        _run_analysis, db, analyzer, fm, transcriber, job["id"], body.video_path, body.mode
    )

    return job


@router.post("/batch")
async def batch_analysis(body: AnalysisBatchRequest, request: Request, background_tasks: BackgroundTasks):
    db = request.app.state.db
    analyzer = request.app.state.analyzer
    fm = request.app.state.file_manager
    transcriber = request.app.state.transcriber
    account = await db.get_account(body.account_id)
    if not account:
        raise HTTPException(404, "博主不存在")

    videos = fm.list_videos(account["folder_name"])

    # Skip videos that already have active (non-completed) jobs with same mode
    all_jobs = await db.get_analysis_jobs()
    active = set()
    for job in all_jobs:
        if job["status"] in ("pending", "processing") and job.get("mode") == body.mode:
            active.add(Path(job["video_path"]).stem)

    jobs = []
    for video in videos:
        video_stem = Path(video["name"]).stem
        if video_stem not in active:
            job = await db.insert_analysis_job(
                video_path=video["path"],
                mode=body.mode,
            )
            jobs.append(job)

    background_tasks.add_task(
        _run_batch_analysis, db, analyzer, fm, transcriber, jobs, body.mode
    )

    return {"created": len(jobs), "job_ids": [j["id"] for j in jobs]}


@router.get("/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job(job_id: str, request: Request):
    db = request.app.state.db
    job = await db.get_analysis_job(job_id)
    if not job:
        raise HTTPException(404, "分析任务不存在")
    return job


async def _run_analysis(db, analyzer, fm, transcriber, job_id, video_path, mode):
    try:
        await db.update_analysis_job(job_id, status="processing")

        video_p = Path(video_path)
        video_name = video_p.stem
        title = video_name

        # Transcribe video audio if transcriber is available
        transcript = ""
        if transcriber.is_available():
            try:
                transcript = await transcriber.transcribe(video_p)
                # Save transcript alongside video
                transcript_path = video_p.parent / f"{video_name}_transcript.txt"
                transcript_path.write_text(transcript, encoding="utf-8")
                logger.info(f"Transcript saved to {transcript_path}")
            except Exception as e:
                logger.warning(f"Transcription failed for {video_path}: {e}")
                transcript = ""
        else:
            logger.info("Transcriber not available, skipping transcription")

        if mode == "full":
            result = await analyzer.generate_full_prediction(
                video_title=title,
                transcript=transcript,
            )
        else:
            result = await analyzer.generate_score_report(
                video_title=title,
                transcript=transcript,
                video_path=video_path,
            )

        # Find account folder from video path
        account_folder = video_p.parent.parent.name
        suffix = "_full" if mode == "full" else ""
        analysis_path = fm.write_analysis(account_folder, f"{video_name}{suffix}.md", result)

        await db.update_analysis_job(
            job_id,
            status="completed",
            analysis_path=str(analysis_path),
        )
    except Exception as e:
        logger.error(f"Analysis failed for {video_path}: {e}")
        await db.update_analysis_job(job_id, status="failed", error=str(e))


async def _run_batch_analysis(db, analyzer, fm, transcriber, jobs, mode):
    for job in jobs:
        await _run_analysis(db, analyzer, fm, transcriber, job["id"], job["video_path"], mode)
