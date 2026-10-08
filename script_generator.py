"""Generate structured short-form video scripts with Google Gemini."""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai import types

from config import Settings


logger = logging.getLogger(__name__)


class ScriptGenerationError(RuntimeError):
    """Raised when Gemini cannot return a valid short-form script."""


def generate_script(topic: str, settings: Settings) -> dict[str, Any]:
    """Generate and validate a scene-based script for ``topic``.

    The returned object has this shape::

        {
            "title": "...",
            "description": "...",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "...",
                    "pexels_query": "...",
                    "duration_hint_seconds": 4
                }
            ]
        }

    Gemini is explicitly instructed to return JSON, but parsing and validation
    remain local so malformed model output never reaches later pipeline stages.
    """
    topic = topic.strip()
    if not topic:
        raise ValueError("The topic must not be empty.")
    if not settings.gemini_api_key:
        raise ScriptGenerationError(
            "GEMINI_API_KEY is missing. Add it to your .env file."
        )

    prompt = _build_prompt(topic, settings.max_scenes)

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8,
            ),
        )
    except Exception as exc:
        logger.exception("Gemini script generation failed.")
        raise ScriptGenerationError(
            "Gemini could not generate the script. Check the API key, model name, "
            "network connection, and API quota."
        ) from exc

    try:
        raw_text = response.text
        if not raw_text:
            raise ValueError("Gemini returned an empty response.")
        script = json.loads(_strip_code_fences(raw_text))
        return _validate_script(script, max_scenes=settings.max_scenes)
    except (AttributeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("Invalid Gemini script response: %s", exc)
        raise ScriptGenerationError(
            "Gemini returned an invalid script format. Please retry the request."
        ) from exc


def _build_prompt(topic: str, max_scenes: int) -> str:
    """Build a strict prompt for a concise, visually searchable short."""
    return f"""
You are a professional YouTube Shorts writer and visual producer.
Create one engaging vertical video script about: {topic!r}

Return ONLY valid JSON. Do not use Markdown, code fences, or additional keys.
Use exactly this structure:
{{
  "title": "short title, maximum 70 characters",
  "description": "one-sentence description",
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "spoken narration for this scene",
      "pexels_query": "2 to 5 concrete English words describing the visuals",
      "duration_hint_seconds": 4
    }}
  ]
}}

Rules:
- Use between 3 and {max_scenes} scenes.
- Make the total narration approximately 30 to 55 seconds.
- Make every scene narration natural, factual, and suitable for a general audience.
- Use one distinct, literal English Pexels search query per scene.
- Use integer duration_hint_seconds between 2 and 12.
- Do not include unsupported claims, dangerous instructions, or copyrighted lyrics.
""".strip()


def _strip_code_fences(text: str) -> str:
    """Accept accidental Markdown fences without accepting arbitrary prose."""
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return cleaned


def _validate_script(script: Any, *, max_scenes: int) -> dict[str, Any]:
    """Validate the minimal contract consumed by downstream modules."""
    if not isinstance(script, dict):
        raise TypeError("The response root must be a JSON object.")

    title = script.get("title")
    description = script.get("description")
    scenes = script.get("scenes")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("The script title must be a non-empty string.")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("The script description must be a non-empty string.")
    if not isinstance(scenes, list) or not 3 <= len(scenes) <= max_scenes:
        raise ValueError(f"scenes must contain between 3 and {max_scenes} items.")

    normalized_scenes = []
    for expected_number, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise TypeError(f"Scene {expected_number} must be an object.")

        narration = scene.get("narration")
        pexels_query = scene.get("pexels_query")
        duration = scene.get("duration_hint_seconds")
        if not isinstance(narration, str) or not narration.strip():
            raise ValueError(f"Scene {expected_number} has invalid narration.")
        if not isinstance(pexels_query, str) or not pexels_query.strip():
            raise ValueError(f"Scene {expected_number} has an invalid Pexels query.")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError(f"Scene {expected_number} has an invalid duration.")
        if not 2 <= duration <= 12:
            raise ValueError(f"Scene {expected_number} duration must be 2 to 12 seconds.")

        normalized_scenes.append(
            {
                "scene_number": expected_number,
                "narration": narration.strip(),
                "pexels_query": pexels_query.strip(),
                "duration_hint_seconds": int(duration),
            }
        )

    return {
        "title": title.strip(),
        "description": description.strip(),
        "scenes": normalized_scenes,
    }
