"""Compose the final 9:16 short with FFmpeg."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

from config import Settings

logger = logging.getLogger(__name__)


class VideoEditingError(RuntimeError):
    """Raised when FFmpeg cannot render the final short."""


def render_short(*, script: dict[str, Any], voiceover: dict[str, Any], clips: list[dict[str, Any]], settings: Settings) -> Path:
    """Render portrait clips, narration, and high-contrast safe-area captions."""
    output_path = (settings.output_dir / _safe_filename(script["title"])).with_suffix(".mp4")
    concat_file = settings.temp_dir / "concat.txt"
    subtitle_file = settings.temp_dir / "captions.srt"
    segment_paths = []

    if len(clips) != len(voiceover["scene_timings"]) or len(clips) != len(script.get("scenes", [])):
        raise ValueError("Each script scene must have one clip and one timing entry.")

    try:
        for clip, timing in zip(clips, voiceover["scene_timings"]):
            segment = settings.temp_dir / f"rendered_{clip['scene_number']:02d}.mp4"
            _run([settings.ffmpeg_binary, "-y", "-i", str(clip["path"]), "-t", f"{timing['end'] - timing['start']:.3f}", "-vf", f"scale={settings.video_width}:{settings.video_height}:force_original_aspect_ratio=increase,crop={settings.video_width}:{settings.video_height}", "-r", str(settings.video_fps), "-an", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(segment)], "preparing scene video")
            segment_paths.append(segment)

        _write_concat_file(concat_file, segment_paths)
        joined = settings.temp_dir / "joined.mp4"
        _run([settings.ffmpeg_binary, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(joined)], "joining scene videos")
        _write_srt(subtitle_file, script["scenes"], voiceover["scene_timings"])
        caption_filter = (f"subtitles={_filter_path(subtitle_file)}:force_style="
                          "'FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,"
                          "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,"
                          "Alignment=2,MarginV=260'")
        _run([settings.ffmpeg_binary, "-y", "-i", str(joined), "-i", str(voiceover["audio_path"]), "-vf", caption_filter, "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(output_path)], "rendering final video")
    except (OSError, subprocess.SubprocessError) as exc:
        logger.exception("Video rendering failed.")
        raise VideoEditingError("FFmpeg could not render the short. Install FFmpeg and ensure it is available on PATH.") from exc
    return output_path


def _run(command: list[str], action: str) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise OSError("FFmpeg executable was not found.") from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or "").strip()[-1000:]
        raise subprocess.SubprocessError(f"Failed while {action}: {details}") from exc


def _write_concat_file(path: Path, segments: list[Path]) -> None:
    path.write_text("".join(f"file '{segment.as_posix().replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'\n" for segment in segments), encoding="utf-8")


def _write_srt(path: Path, scenes: list[dict[str, Any]], timings: list[dict[str, Any]]) -> None:
    blocks = []
    for number, (scene, timing) in enumerate(zip(scenes, timings), start=1):
        blocks.append(f"{number}\n{_srt_time(timing['start'])} --> {_srt_time(timing['end'])}\n{_format_caption(scene['narration'])}\n")
    path.write_text("\n".join(blocks), encoding="utf-8")


def _format_caption(text: str, max_line_length: int = 34) -> str:
    """Keep captions to two balanced lines for mobile readability."""
    words = text.strip().split()
    if not words:
        return ""
    midpoint = max(1, len(words) // 2)
    best = midpoint
    best_score = None
    for split in range(1, len(words)):
        left = " ".join(words[:split])
        right = " ".join(words[split:])
        if len(left) <= max_line_length and len(right) <= max_line_length:
            score = abs(len(left) - len(right))
            if best_score is None or score < best_score:
                best, best_score = split, score
    if best_score is None:
        return " ".join(words)
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


def _srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", "\\:")


def _safe_filename(title: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in " -_" else "_" for char in title)
    return "_".join(cleaned.split())[:80] or "youtube_short"
