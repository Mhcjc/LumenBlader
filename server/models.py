from datetime import datetime
from typing import Literal

from pydantic import BaseModel


# --- Request models ---

class AccountCreate(BaseModel):
    url: str
    platform: str = ""  # auto-detect if empty


class BatchDownloadRequest(BaseModel):
    account_id: str
    earliest: str = ""
    latest: str = ""


class SingleDownloadRequest(BaseModel):
    url: str


class AnalysisStartRequest(BaseModel):
    video_path: str
    mode: Literal["summary", "full"] = "summary"


class AnalysisBatchRequest(BaseModel):
    account_id: str
    mode: Literal["summary", "full"] = "summary"


# --- Response models ---

class AccountResponse(BaseModel):
    id: str
    platform: str
    nickname: str
    url: str
    sec_uid: str
    folder_name: str
    created_at: str
    last_synced_at: str | None = None


class DownloadJobResponse(BaseModel):
    id: str
    account_id: str
    earliest: str
    latest: str
    status: str
    total_videos: int
    downloaded: int
    failed: int
    created_at: str
    finished_at: str | None = None


class DownloadItemResponse(BaseModel):
    id: str
    job_id: str
    video_id: str
    title: str
    status: str
    error: str | None = None


class AnalysisJobResponse(BaseModel):
    id: str
    video_path: str
    analysis_path: str | None = None
    mode: str
    status: str
    error: str | None = None
    created_at: str


class FileListItem(BaseModel):
    name: str
    path: str
    size: int
    modified: str


class SettingsUpdate(BaseModel):
    tiktok_downloader: dict | None = None
    ai: dict | None = None
    server: dict | None = None
    materials_root: str | None = None
