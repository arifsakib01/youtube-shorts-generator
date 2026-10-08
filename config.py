"""Application configuration and environment-variable handling."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent


def _read_int(name: str, default: int, *, minimum: int = 1) -> int:
    """Read a positive integer from the environment with a useful error."""
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw_value!r}") from exc

    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    """Validated settings used by the generation pipeline."""

    gemini_api_key: str
    gemini_model: str
    pexels_api_key: str
    output_dir: Path
    temp_dir: Path
    video_width: int
    video_height: int
    video_fps: int
    max_scenes: int
    voice: str
    log_level: str
    ffmpeg_binary: str

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load settings from ``.env`` and the process environment."""
        load_dotenv(PROJECT_ROOT / ".env")

        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
            or "gemini-2.0-flash",
            pexels_api_key=os.getenv("PEXELS_API_KEY", "").strip(),
            output_dir=_resolve_path(os.getenv("OUTPUT_DIR", "output")),
            temp_dir=_resolve_path(os.getenv("TEMP_DIR", ".tmp")),
            video_width=_read_int("VIDEO_WIDTH", 1080),
            video_height=_read_int("VIDEO_HEIGHT", 1920),
            video_fps=_read_int("VIDEO_FPS", 30),
            max_scenes=_read_int("MAX_SCENES", 8, minimum=3),
            voice=os.getenv("VOICE", "en-US-AriaNeural").strip()
            or "en-US-AriaNeural",
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
            ffmpeg_binary=os.getenv("FFMPEG_BINARY", "ffmpeg").strip() or "ffmpeg",
        )

    def validate_api_keys(self) -> None:
        """Raise a clear error if credentials required by the pipeline are absent."""
        missing = []
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        if not self.pexels_api_key:
            missing.append("PEXELS_API_KEY")

        if missing:
            names = ", ".join(missing)
            raise RuntimeError(
                f"Missing required environment variable(s): {names}. "
                "Copy .env.example to .env and add your API keys."
            )

    def ensure_directories(self) -> None:
        """Create directories used for temporary files and rendered videos."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


def _resolve_path(value: str) -> Path:
    """Resolve a configured path relative to the project root when necessary."""
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


settings = Settings.from_environment()
