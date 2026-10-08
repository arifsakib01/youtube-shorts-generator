"""Download portrait stock clips from the Pexels video API."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from config import Settings

logger = logging.getLogger(__name__)
PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"


class StockFetchError(RuntimeError):
    """Raised when a suitable stock clip cannot be downloaded."""


def fetch_scene_clips(
    script: dict[str, Any], settings: Settings
) -> list[dict[str, Any]]:
    """Download one suitable clip per scene and return local paths."""
    if not settings.pexels_api_key:
        raise StockFetchError("PEXELS_API_KEY is missing. Add it to your .env file.")

    clips = []
    for scene in script.get("scenes", []):
        query = str(scene["pexels_query"]).strip()
        try:
            video_url = _find_video_url(query, settings.pexels_api_key)
            target = settings.temp_dir / f"scene_{scene['scene_number']:02d}.mp4"
            _download(video_url, target)
        except (OSError, requests.RequestException, ValueError) as exc:
            logger.exception("Could not fetch stock video for query %r.", query)
            raise StockFetchError(
                f"Could not download a Pexels clip for scene {scene['scene_number']} "
                f"({query!r})."
            ) from exc
        clips.append({"scene_number": scene["scene_number"], "path": target})
    if not clips:
        raise StockFetchError("The script contains no scenes to fetch.")
    return clips


def _find_video_url(query: str, api_key: str) -> str:
    response = requests.get(
        PEXELS_SEARCH_URL,
        headers={"Authorization": api_key},
        params={"query": query, "orientation": "portrait", "per_page": 15},
        timeout=30,
    )
    response.raise_for_status()
    videos = response.json().get("videos", [])
    if not videos:
        raise ValueError(f"No Pexels videos found for {query!r}.")

    # Prefer portrait files with enough resolution for a 1080x1920 output.
    candidates = []
    for video in videos:
        for file in video.get("video_files", []):
            width = int(file.get("width") or 0)
            height = int(file.get("height") or 0)
            link = file.get("link")
            if link and height >= width and height >= 720:
                candidates.append((width * height, link))
    if not candidates:
        raise ValueError(f"No portrait Pexels file found for {query!r}.")
    return max(candidates, key=lambda item: item[0])[1]


def _download(url: str, target: Path) -> None:
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with target.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
    if not target.exists() or target.stat().st_size == 0:
        raise OSError(f"Downloaded clip is empty: {target}")
