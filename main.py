"""Command-line entry point for the automated YouTube Shorts pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a vertical YouTube Short from a topic.")
    parser.add_argument("topic", help="The subject to turn into a short.")
    return parser.parse_args()


def generate_short(topic: str) -> Path:
    if not topic.strip():
        raise ValueError("The topic must not be empty.")

    settings.validate_api_keys()
    settings.ensure_directories()

    try:
        from script_generator import generate_script
        from stock_fetcher import fetch_scene_clips
        from video_editor import render_short
        from voice_generator import generate_voiceover
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "an optional dependency"
        raise RuntimeError(
            f"Missing Python dependency {missing_module!r}. Install dependencies with: "
            "python -m pip install -r requirements.txt"
        ) from exc

    script = generate_script(topic, settings)
    voiceover = generate_voiceover(script, settings)
    clips = fetch_scene_clips(script, settings)
    output_path = render_short(script=script, voiceover=voiceover, clips=clips, settings=settings)
    logger.info("Short rendered successfully: %s", output_path)
    return output_path


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        generate_short(args.topic)
    except (RuntimeError, ValueError, OSError) as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""Command-line entry point for the automated YouTube Shorts pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a vertical YouTube Short from a topic.")
    parser.add_argument("topic", help="The subject to turn into a short.")
    return parser.parse_args()


def generate_short(topic: str) -> Path:
    if not topic.strip():
        raise ValueError("The topic must not be empty.")

    settings.validate_api_keys()
    settings.ensure_directories()

    try:
        from script_generator import generate_script
        from stock_fetcher import fetch_scene_clips
        from video_editor import render_short
        from voice_generator import generate_voiceover
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "an optional dependency"
        raise RuntimeError(
            f"Missing Python dependency {missing_module!r}. Install dependencies with: "
            "python -m pip install -r requirements.txt"
        ) from exc

    if topic == "__DAILY_AI_NEWS__":
        from news_fetcher import fetch_daily_news
        topic = fetch_daily_news()

    script = generate_script(topic, settings)
    voiceover = generate_voiceover(script, settings)
    clips = fetch_scene_clips(script, settings)
    output_path = render_short(script=script, voiceover=voiceover, clips=clips, settings=settings)
    logger.info("Short rendered successfully: %s", output_path)
    return output_path


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        generate_short(args.topic)
    except (RuntimeError, ValueError, OSError) as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""Command-line entry point for the automated YouTube Shorts pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a vertical YouTube Short from a topic.")
    parser.add_argument("topic", help="The subject to turn into a short.")
    return parser.parse_args()


def generate_short(topic: str) -> Path:
    if not topic.strip():
        raise ValueError("The topic must not be empty.")

    settings.validate_api_keys()
    settings.ensure_directories()

    try:
        from script_generator import generate_script
        from stock_fetcher import fetch_scene_clips
        from video_editor import render_short
        from voice_generator import generate_voiceover
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "an optional dependency"
        raise RuntimeError(
            f"Missing Python dependency {missing_module!r}. Install dependencies with: "
            "python -m pip install -r requirements.txt"
        ) from exc

    script = generate_script(topic, settings)
    voiceover = generate_voiceover(script, settings)
    clips = fetch_scene_clips(script, settings)
    output_path = render_short(script=script, voiceover=voiceover, clips=clips, settings=settings)
    logger.info("Short rendered successfully: %s", output_path)
    return output_path


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        generate_short(args.topic)
    except (RuntimeError, ValueError, OSError) as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
