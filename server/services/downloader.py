import re
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import httpx


class TikTokDownloaderClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        # Bypass proxy for local TikTokDownloader connections
        self._client_kwargs = {"trust_env": False}

    async def fetch_account_videos(
        self,
        sec_user_id: str,
        platform: str = "douyin",
        earliest: str = "",
        latest: str = "",
        cookie: str = "",
        proxy: str = "",
    ) -> list[dict]:
        endpoint = "/tiktok/account" if platform == "tiktok" else "/douyin/account"
        payload = {
            "sec_user_id": sec_user_id,
            "tab": "post",
        }
        if earliest:
            payload["earliest"] = earliest.replace("-", "/")
        if latest:
            payload["latest"] = latest.replace("-", "/")
        if cookie:
            payload["cookie"] = cookie
        if proxy:
            payload["proxy"] = proxy

        async with httpx.AsyncClient(timeout=300, trust_env=False) as http:
            resp = await http.post(f"{self.base_url}{endpoint}", json=payload)
            resp.raise_for_status()
            result = resp.json()
            if result.get("data"):
                return result["data"]
            return []

    async def fetch_video_detail(
        self,
        video_id: str,
        platform: str = "douyin",
        cookie: str = "",
        proxy: str = "",
    ) -> Optional[dict]:
        endpoint = "/tiktok/detail" if platform == "tiktok" else "/douyin/detail"
        payload = {"detail_id": video_id}
        if cookie:
            payload["cookie"] = cookie
        if proxy:
            payload["proxy"] = proxy

        async with httpx.AsyncClient(timeout=60, trust_env=False) as http:
            resp = await http.post(f"{self.base_url}{endpoint}", json=payload)
            resp.raise_for_status()
            result = resp.json()
            if result.get("data"):
                return result["data"]
            return None

    async def fetch_user_info(
        self,
        sec_user_id: str,
        platform: str = "douyin",
        cookie: str = "",
        proxy: str = "",
    ) -> Optional[dict]:
        endpoint = "/tiktok/user" if platform == "tiktok" else "/douyin/user"
        payload = {"sec_user_id": sec_user_id}
        if cookie:
            payload["cookie"] = cookie
        if proxy:
            payload["proxy"] = proxy

        async with httpx.AsyncClient(timeout=30, trust_env=False) as http:
            resp = await http.post(f"{self.base_url}{endpoint}", json=payload)
            resp.raise_for_status()
            result = resp.json()
            if result.get("data"):
                return result["data"]
            return None

    async def resolve_short_url(self, url: str) -> str:
        if "v.douyin.com" not in url and "vm.tiktok.com" not in url:
            return url
        async with httpx.AsyncClient(timeout=30, follow_redirects=False, trust_env=False) as http:
            resp = await http.get(url)
            if resp.status_code in (301, 302, 303, 307, 308):
                return str(resp.headers.get("location", url))
        return url

    async def download_file(self, url: str, dest: Path) -> Path:
        """Download a file from URL to dest path. Returns the dest path on success."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=300, follow_redirects=True, trust_env=False) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
        return dest

    @staticmethod
    def extract_sec_user_id(url: str) -> str:
        if "douyin.com" in url:
            match = re.search(r"/user/([^/?]+)", url)
            return match.group(1) if match else ""
        if "tiktok.com" in url:
            match = re.search(r"@([^/?]+)", url)
            return match.group(1) if match else ""
        return ""

    @staticmethod
    def extract_video_id(url: str) -> str:
        match = re.search(r"/video/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"/(\d{15,})", url)
        if match:
            return match.group(1)
        return ""
