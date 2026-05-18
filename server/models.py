from datetime import datetime
from typing import Literal, Optional

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
    last_synced_at: Optional[str] = None


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
    finished_at: Optional[str] = None


class DownloadItemResponse(BaseModel):
    id: str
    job_id: str
    video_id: str
    title: str
    status: str
    error: Optional[str] = None


class AnalysisJobResponse(BaseModel):
    id: str
    video_path: str
    analysis_path: Optional[str] = None
    mode: str
    status: str
    error: Optional[str] = None
    created_at: str


class FileListItem(BaseModel):
    name: str
    path: str
    size: int
    modified: str


class SettingsUpdate(BaseModel):
    tiktok_downloader: Optional[dict] = None
    ai: Optional[dict] = None
    server: Optional[dict] = None
    materials_root: Optional[str] = None
