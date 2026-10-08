"""Generate paced, conversational narration and scene timing metadata with Edge TTS."""

from __future__ import annotations

import asyncio
import logging
import re
import subprocess
from pathlib import Path
from typing import Any

import edge_tts

from config import Settings

logger = logging.getLogger(__name__)


class VoiceGenerationError(RuntimeError):
    """Raised when narration audio cannot be generated or measured."""


def generate_voiceover(script: dict[str, Any], settings: Settings) -> dict[str, Any]:
    """Generate a paced narration track and estimated scene timings."""
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("The script must contain at least one scene.")

    output_path = settings.temp_dir / "voiceover.mp3"
    narration_parts = [_prepare_narration(str(scene["narration"])) for scene in scenes]
    narration = "  ".join(narration_parts)
    if not narration.strip():
        raise ValueError("The script contains no narration.")

    try:
        asyncio.run(_save_speech(narration, settings.voice, output_path))
        duration = _probe_duration(output_path, settings.ffmpeg_binary)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        logger.exception("Voiceover generation failed.")
        raise VoiceGenerationError(
            "Could not generate or measure the voiceover. Ensure edge-tts and FFmpeg are installed."
        ) from exc

    weights = [max(1, len(str(scene["narration"]).split())) for scene in scenes]
    total_weight = sum(weights)
    timings = []
    cursor = 0.0
    for index, weight in enumerate(weights):
        scene_duration = duration * weight / total_weight
        timings.append({
            "scene_number": index + 1,
            "start": round(cursor, 3),
            "end": round(cursor + scene_duration, 3),
        })
        cursor += scene_duration

    return {"audio_path": output_path, "duration": duration, "scene_timings": timings}


def _prepare_narration(text: str) -> str:
    """Add human-friendly breathing room without inserting unnatural filler."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"\s*([,;:])\s*", r"\1 ", cleaned)
    cleaned = re.sub(r"\s*([.!?])\s*", r"\1  ", cleaned)
    return cleaned


async def _save_speech(text: str, voice: str, output_path: Path) -> None:
    communicate = edge_tts.Communicate(text, voice, rate="-8%", pitch="+1Hz", volume="+0%")
    await communicate.save(str(output_path))


def _probe_duration(path: Path, ffmpeg_binary: str) -> float:
    configured_path = Path(ffmpeg_binary)
    probe = str(configured_path.with_name("ffprobe" + configured_path.suffix))
    command = [probe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(f"{ffmpeg_binary} and ffprobe are required.") from exc
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("FFprobe returned an invalid audio duration.") from exc
    if duration <= 0:
        raise RuntimeError("Generated audio has no measurable duration.")
    return duration
