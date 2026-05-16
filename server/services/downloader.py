import re
from urllib.parse import urlparse

import httpx


class TikTokDownloaderClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

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
            payload["earliest"] = earliest
        if latest:
            payload["latest"] = latest
        if cookie:
            payload["cookie"] = cookie
        if proxy:
            payload["proxy"] = proxy

        async with httpx.AsyncClient(timeout=300) as http:
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
    ) -> dict | None:
        endpoint = "/tiktok/detail" if platform == "tiktok" else "/douyin/detail"
        payload = {"detail_id": video_id}
        if cookie:
            payload["cookie"] = cookie
        if proxy:
            payload["proxy"] = proxy

        async with httpx.AsyncClient(timeout=60) as http:
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
    ) -> dict | None:
        endpoint = "/tiktok/user" if platform == "tiktok" else "/douyin/user"
        payload = {"sec_user_id": sec_user_id}
        if cookie:
            payload["cookie"] = cookie
        if proxy:
            payload["proxy"] = proxy

        async with httpx.AsyncClient(timeout=60) as http:
            resp = await http.post(f"{self.base_url}{endpoint}", json=payload)
            resp.raise_for_status()
            result = resp.json()
            if result.get("data"):
                return result["data"]
            return None

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
