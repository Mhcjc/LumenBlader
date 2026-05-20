import re
from pathlib import Path
from datetime import datetime
from typing import Optional


class FileManager:
    def __init__(self, materials_root: Path):
        self.root = materials_root

    def ensure_account_dir(self, folder_name: str) -> Path:
        account_dir = self.root / folder_name
        (account_dir / "videos").mkdir(parents=True, exist_ok=True)
        (account_dir / "analysis").mkdir(parents=True, exist_ok=True)
        return account_dir

    def list_videos(self, folder_name: str) -> list[dict]:
        videos_dir = self.root / folder_name / "videos"
        if not videos_dir.exists():
            return []
        return self._list_dir(videos_dir, ".mp4")

    def list_analysis(self, folder_name: str) -> list[dict]:
        analysis_dir = self.root / folder_name / "analysis"
        if not analysis_dir.exists():
            return []
        return self._list_dir(analysis_dir, ".md")

    def get_analysis_content(self, folder_name: str, filename: str) -> Optional[str]:
        analysis_dir = self.root / folder_name / "analysis"
        path = analysis_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        # Fuzzy match: find file starting with the same video ID
        video_id = filename.split("_")[0] if "_" in filename else filename.replace(".md", "")
        for f in analysis_dir.iterdir():
            if f.is_file() and f.name.startswith(video_id) and f.suffix == ".md":
                return f.read_text(encoding="utf-8")
        return None

    def write_analysis(self, folder_name: str, filename: str, content: str) -> Path:
        analysis_dir = self.root / folder_name / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        path = analysis_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def detect_platform(url: str) -> str:
        if "douyin.com" in url or "iesdouyin.com" in url:
            return "douyin"
        if "tiktok.com" in url or "vm.tiktok.com" in url:
            return "tiktok"
        return ""

    @staticmethod
    def sanitize_folder_name(name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', "", name)
        return name.strip()

    def _list_dir(self, directory: Path, suffix: str) -> list[dict]:
        items = []
        for f in sorted(directory.iterdir()):
            if f.is_file() and f.suffix == suffix:
                stat = f.stat()
                items.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        return items
