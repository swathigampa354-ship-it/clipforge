"""
YouTube URL import service using yt-dlp
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    video_id: str
    filepath: str
    filename: str
    title: str
    duration: float
    url: str
    thumbnail_url: Optional[str] = None
    metadata: Optional[dict] = None


class YTDLPDownloader:
    """Handles YouTube video downloads using yt-dlp"""

    def __init__(self, download_dir: str = "/tmp/clipforge_downloads"):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

    async def download(self, url: str) -> ImportResult:
        """Download a YouTube video and return metadata"""
        # Get video info first
        info_cmd = [
            "yt-dlp", "--dump-json", "--no-playlist", url
        ]
        try:
            result = await asyncio.create_subprocess_exec(
                *info_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate(timeout=30)

            if result.returncode != 0:
                raise ValueError(f"yt-dlp info failed: {stderr.decode()}")

            info = json.loads(stdout.decode())
        except asyncio.TimeoutError:
            raise ValueError("yt-dlp info request timed out")
        except FileNotFoundError:
            raise ValueError("yt-dlp not installed. Install with: pip install yt-dlp or apt install yt-dlp")

        video_id = info.get("id", "unknown")
        filename = f"{video_id}.mp4"
        filepath = os.path.join(self.download_dir, filename)

        # Download the video
        dl_cmd = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", filepath,
            "--no-playlist",
            url
        ]
        try:
            result = await asyncio.create_subprocess_exec(
                *dl_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate(timeout=600)

            if result.returncode != 0:
                raise ValueError(f"yt-dlp download failed: {stderr.decode()}")
        except asyncio.TimeoutError:
            raise ValueError("Download timed out after 10 minutes")

        return ImportResult(
            video_id=video_id,
            filepath=filepath,
            filename=filename,
            title=info.get("title", ""),
            duration=float(info.get("duration", 0)),
            url=url,
            thumbnail_url=info.get("thumbnail"),
            metadata={
                "uploader": info.get("uploader"),
                "channel": info.get("channel"),
                "upload_date": info.get("upload_date"),
                "description": info.get("description"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
            }
        )


class URLValidator:
    """Validate and categorize video URLs"""

    SUPPORTED_DOMAINS = [
        "youtube.com", "youtu.be",
        "vimeo.com",
        "twitch.tv",
        "kick.com",
    ]

    @classmethod
    def validate(cls, url: str) -> dict:
        """Validate a URL and determine its type"""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc or ""

        if not domain:
            return {"valid": False, "error": "Invalid URL", "type": None}

        # Determine source type
        source_type = "other"
        if "youtube.com" in domain or "youtu.be" in domain:
            source_type = "youtube"
        elif "vimeo.com" in domain:
            source_type = "vimeo"
        elif "twitch.tv" in domain:
            source_type = "twitch"
        elif "kick.com" in domain:
            source_type = "kick"

        return {
            "valid": True,
            "type": source_type,
            "domain": domain,
            "url": url,
        }

    @classmethod
    def get_downloader(cls, url: str) -> YTDLPDownloader:
        """Get the appropriate downloader for a URL"""
        validation = cls.validate(url)
        if not validation["valid"]:
            raise ValueError(f"Unsupported URL: {url}")
        return YTDLPDownloader()