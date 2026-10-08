"""Generate human-sounding structured Shorts scripts with Gemini."""
from __future__ import annotations
import json
import logging
from typing import Any
from google import genai
from google.genai import types
from config import Settings
logger = logging.getLogger(__name__)
class ScriptGenerationError(RuntimeError):
    """Raised when Gemini cannot return a valid script."""
def generate_script(topic: str, settings: Settings) -> dict[str, Any]:
    topic = topic.strip()
    if not topic: raise ValueError("The topic must not be empty.")
    if not settings.gemini_api_key: raise ScriptGenerationError("GEMINI_API_KEY is missing. Add it to your .env file.")
    try:
        response = genai.Client(api_key=settings.gemini_api_key).models.generate_content(model=settings.gemini_model, contents=_build_prompt(topic, settings.max_scenes), config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.9))
    except Exception as exc:
        logger.exception("Gemini script generation failed.")
        raise ScriptGenerationError("Gemini could not generate the script. Check the API key, model name, network connection, and API quota.") from exc
    try:
        text = response.text
        if not text: raise ValueError("Gemini returned an empty response.")
        return _validate_script(json.loads(_strip_code_fences(text)), settings.max_scenes)
    except (AttributeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("Invalid Gemini script response: %s", exc)
        raise ScriptGenerationError("Gemini returned an invalid script format. Please retry the request.") from exc
def _build_prompt(topic: str, max_scenes: int) -> str:
    return f"""You write natural, human-sounding YouTube Shorts for one viewer. Create a warm, curious vertical video about {topic!r}.
Return ONLY valid JSON with title, description, and scenes. Each scene must contain scene_number, narration, pexels_query, and duration_hint_seconds.
Rules:
- Use between 3 and {max_scenes} scenes and 30 to 55 seconds total narration.
- Open with a specific surprising hook. Speak like a qurious person, not a documentary, advertisement, essay, or AI assistant.
- Address the viewer naturally with you. Use contractions like it's, you'll, and don't. Vary sentence length and rhythm.
- Use commas, ellipses, or em dashes for natural pauses. Avoid filler such as In this video, Did you know, Welcome back, and Let's dive in.
- Give every scene a distinct concrete English Pexels query. Use integer durations from 2 to 12.
- Be factual, accessible, and safe. Do not use copyrighted lyrics or unsupported claims.
""".strip()
def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        return "\n".join(lines[1:-1]).strip() if len(lines) >= 3 else cleaned
    return cleaned
def _validate_script(script: Any, max_scenes: int) -> dict[str, Any]:
    if not isinstance(script, dict): raise TypeError("The response root must be a JSON object.")
    title, description, scenes = script.get("title"), script.get("description"), script.get("scenes")
    if not isinstance(title, str) or not title.strip() or not isinstance(description, str) or not description.strip(): raise ValueError("title and description must be non-empty strings.")
    if not isinstance(scenes, list) or not 3 <= len(scenes) <= max_scenes: raise ValueError(f"scenes must contain between 3 and {max_scenes} items.")
    normalized = []
    for number, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict): raise TypeError(f"Scene {number} must be an object.")
        narration, query, duration = scene.get("narration"), scene.get("pexels_query"), scene.get("duration_hint_seconds")
        if not isinstance(narration, str) or not narration.strip() or not isinstance(query, str) or not query.strip(): raise ValueError(f"Scene {number} has invalid narration or Pexels query.")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 2 <= duration <= 12: raise ValueError(f"Scene {number} duration must be 2 to 12 seconds.")
        normalized.append({"scene_number": number, "narration": narration.strip(), "pexels_query": query.strip(), "duration_hint_seconds": int(duration))}
    return {"title": title.strip(), "description": description.strip(), "scenes": normalized}
