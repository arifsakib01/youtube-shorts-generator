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
    if not topic:
        raise ValueError("The topic must not be empty.")
    if not settings.gemini_api_key:
        raise ScriptGenerationError("GEMINI_API_KEY is missing. Add it to your .env file.")
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(model=settings.gemini_model, contents=_build_prompt(topic, settings.max_scenes), config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.9))
    except Exception as exc:
        logger.exception("Gemini script generation failed.")
        raise ScriptGenerationError("Gemini could not generate the script. Check the API key, model name, network connection, and API quota.") from exc
    try:
        text = response.text
        if not text:
            raise ValueError("Gemini returned an empty response.")
        return _validate_script(json.loads(_strip_code_fences(text)), settings.max_scenes)
    except (AttributeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("Invalid Gemini script response: %s", exc)
        raise ScriptGenerationError("Gemini returned an invalid script format. Please retry the request.") from exc

def _build_prompt(topic: str, max_scenes: int) -> str:
    return f"""You are an elite YouTube Shorts showrunner and fact-checking writer. Create a premium, highly shareable vertical short about {topic!r} for one curious viewer.
Return ONLY valid JSON with title, description, and scenes. Each scene must contain scene_number, narration, pexels_query, and duration_hint_seconds.

RETENTION STRUCTURE:
- Scene 1: a concrete pattern interrupt and irresistible question in the first 3 seconds.
- Middle scenes: reveal information in escalating steps, then pay off the early open loop.
- Final scene: a memorable takeaway and a natural question inviting comments. Never beg for likes.

QUALITY RULES:
- Use 4 to {max_scenes} scenes and 35 to 55 seconds total narration; each scene 4 to 10 seconds.
- Use tight spoken English, contractions, direct second-person language, vivid details, and varied rhythm.
- Sound like a confident human creator. Avoid greetings, filler, fake suspense, and exaggerated promises.
- Keep claims factual and defensible; never invent statistics, studies, quotes, medical advice, or guarantees.
- Give every scene one dominant visual idea and a distinct cinematic vertical Pexels query with subject, action, and setting.
- Use a short curiosity-driven title, one-sentence description, integer duration hints from 4 to 10, and no markdown or extra JSON fields.
""".strip()
def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        return "\n".join(lines[1:-1]).strip() if len(lines) >= 3 else cleaned
    return cleaned

def _validate_script(script: Any, max_scenes: int) -> dict[str, Any]:
    if not isinstance(script, dict):
        raise TypeError("The response root must be a JSON object.")
    title, description, scenes = script.get("title"), script.get("description"), script.get("scenes")
    if not isinstance(title, str) or not title.strip() or not isinstance(description, str) or not description.strip():
        raise ValueError("title and description must be non-empty strings.")
    if not isinstance(scenes, list) or not 3 <= len(scenes) <= max_scenes:
        raise ValueError(f"scenes must contain between 3 and {max_scenes} items.")
    normalized = []
    for number, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise TypeError(f"Scene {number} must be an object.")
        narration, query, duration = scene.get("narration"), scene.get("pexels_query"), scene.get("duration_hint_seconds")
        if not isinstance(narration, str) or not narration.strip() or not isinstance(query, str) or not query.strip():
            raise ValueError(f"Scene {number} has invalid narration or Pexels query.")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 2 <= duration <= 12:
            raise ValueError(f"Scene {number} duration must be 2 to 12 seconds.")
        normalized.append({"scene_number": number, "narration": narration.strip(), "pexels_query": query.strip(), "duration_hint_seconds": int(duration)})
    return {"title": title.strip(), "description": description.strip(), "scenes": normalized}
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
    if not topic:
        raise ValueError("The topic must not be empty.")
    if not settings.gemini_api_key:
        raise ScriptGenerationError("GEMINI_API_KEY is missing. Add it to your .env file.")
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(model=settings.gemini_model, contents=_build_prompt(topic, settings.max_scenes), config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.9))
    except Exception as exc:
        logger.exception("Gemini script generation failed.")
        raise ScriptGenerationError("Gemini could not generate the script. Check the API key, model name, network connection, and API quota.") from exc
    try:
        text = response.text
        if not text:
            raise ValueError("Gemini returned an empty response.")
        return _validate_script(json.loads(_strip_code_fences(text)), settings.max_scenes)
    except (AttributeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("Invalid Gemini script response: %s", exc)
        raise ScriptGenerationError("Gemini returned an invalid script format. Please retry the request.") from exc

def _build_prompt(topic: str, max_scenes: int) -> str:\n    return f"""You are an elite YouTube Shorts showrunner and fact-checking writer. Create a premium, highly shareable vertical short about {topic!r} for one curious viewer.\nReturn ONLY valid JSON with title, description, and scenes. Each scene must contain scene_number, narration, pexels_query, and duration_hint_seconds.\n\nRETENTION STRUCTURE:\n- Scene 1: a concrete pattern interrupt and irresistible question in the first 3 seconds.\n- Middle scenes: reveal information in escalating steps, then pay off the early open loop.\n- Final scene: a memorable takeaway and a natural question inviting comments. Never beg for likes.\n\nQUALITY RULES:\n- Use 4 to {max_scenes} scenes and 35 to 55 seconds total narration; each scene 4 to 10 seconds.\n- Use tight spoken English, contractions, direct second-person language, vivid details, and varied rhythm.\n- Sound like a confident human creator. Avoid greetings, filler, fake suspense, and exaggerated promises.\n- Keep claims factual and defensible; never invent statistics, studies, quotes, medical advice, or guarantees.\n- Give every scene one dominant visual idea and a distinct cinematic vertical Pexels query with subject, action, and setting.\n- Use a short curiosity-driven title, one-sentence description, integer duration hints from 4 to 10, and no markdown or extra JSON fields.\n""".strip()\ndef _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        return "\n".join(lines[1:-1]).strip() if len(lines) >= 3 else cleaned
    return cleaned

def _validate_script(script: Any, max_scenes: int) -> dict[str, Any]:
    if not isinstance(script, dict):
        raise TypeError("The response root must be a JSON object.")
    title, description, scenes = script.get("title"), script.get("description"), script.get("scenes")
    if not isinstance(title, str) or not title.strip() or not isinstance(description, str) or not description.strip():
        raise ValueError("title and description must be non-empty strings.")
    if not isinstance(scenes, list) or not 3 <= len(scenes) <= max_scenes:
        raise ValueError(f"scenes must contain between 3 and {max_scenes} items.")
    normalized = []
    for number, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise TypeError(f"Scene {number} must be an object.")
        narration, query, duration = scene.get("narration"), scene.get("pexels_query"), scene.get("duration_hint_seconds")
        if not isinstance(narration, str) or not narration.strip() or not isinstance(query, str) or not query.strip():
            raise ValueError(f"Scene {number} has invalid narration or Pexels query.")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 2 <= duration <= 12:
            raise ValueError(f"Scene {number} duration must be 2 to 12 seconds.")
        normalized.append({"scene_number": number, "narration": narration.strip(), "pexels_query": query.strip(), "duration_hint_seconds": int(duration)})
    return {"title": title.strip(), "description": description.strip(), "scenes": normalized}
"""Generate retention-focused, human-sounding Shorts scripts with Gemini."""
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
        if not topic:
                    raise ValueError("The topic must not be empty.")
                if not settings.gemini_api_key:
                            raise ScriptGenerationError("GEMINI_API_KEY is missing. Add it to your .env file.")
                        try:
                                    client = genai.Client(api_key=settings.gemini_api_key)
                                    response = client.models.generate_content(model=settings.gemini_model, contents=_build_prompt(topic, settings.max_scenes), config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.85))
except Exception as exc:
        logger.exception("Gemini script generation failed.")
        raise ScriptGenerationError("Gemini could not generate the script. Check the API key, model name, network connection, and API quota.") from exc
    try:
                text = response.text
                if not text:
                                raise ValueError("Gemini returned an empty response.")
                            return _validate_script(json.loads(_strip_code_fences(text)), settings.max_scenes)
except (AttributeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("Invalid Gemini script response: %s", exc)
        raise ScriptGenerationError("Gemini returned an invalid script format. Please retry the request.") from exc

def _build_prompt(topic: str, max_scenes: int) -> str:
        return f"""You are an elite YouTube Shorts showrunner and fact-checking writer. Create a premium, highly shareable vertical short about {topic!r} for one curious viewer.
        Return ONLY valid JSON with title, description, and scenes. Each scene must contain scene_number, narration, pexels_query, and duration_hint_seconds.

        RETENTION STRUCTURE:
        - Scene 1 (0-3 seconds): a concrete pattern interrupt and irresistible question. Never start with a greeting or generic intro.
        - Middle scenes: reveal information in escalating steps. Use an open loop early, then pay it off with a surprising but accurate explanation.
        - Final scene: a memorable takeaway plus a natural comment prompt that invites an opinion or personal experience. Never beg for likes or subscriptions.

        QUALITY RULES:
        - Use 4 to {max_scenes} scenes and 35 to 55 seconds total narration; keep each scene 4 to 10 seconds.
        - Write tight spoken English: contractions, direct second-person language, vivid concrete details, varied sentence lengths, and one idea per sentence.
        - Sound like a confident human creator, not a documentary, advertisement, essay, or AI assistant. Avoid greetings, filler, fake suspense, and exaggerated promises.
        - Make every claim defensible from common knowledge or phrase uncertainty honestly. Do not invent statistics, studies, quotes, medical advice, or guaranteed outcomes.
        - Give every scene one dominant visual idea and a distinct cinematic vertical Pexels query describing subject, action, and setting. Do not request logos, text, celebrities, or copyrighted characters.
        - Titles should be short, curiosity-driven, and specific without clickbait. Description should be one sentence suitable for YouTube.
        - Use integer duration hints from 4 to 10. Do not include markdown, hashtags, emojis, or extra JSON fields.
        """.strip()

def _strip_code_fences(text: str) -> str:
        cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
                lines = cleaned.splitlines()
        return "\n".join(lines[1:-1]).strip() if len(lines) >= 3 else cleaned
    return cleaned

def _validate_script(script: Any, max_scenes: int) -> dict[str, Any]:
        if not isinstance(script, dict):
                    raise TypeError("The response root must be a JSON object.")
                title, description, scenes = script.get("title"), script.get("description"), script.get("scenes")
    if not isinstance(title, str) or not title.strip() or not isinstance(description, str) or not description.strip():
                raise ValueError("title and description must be non-empty strings.")
    if not isinstance(scenes, list) or not 4 <= len(scenes) <= max_scenes:
                raise ValueError(f"scenes must contain between 4 and {max_scenes} items.")
    normalized = []
    for number, scene in enumerate(scenes, 1):
                if not isinstance(scene, dict):
                                raise TypeError(f"Scene {number} must be an object.")
                            narration, query, duration = scene.get("narration"), scene.get("pexels_query"), scene.get("duration_hint_seconds")
        if not isinstance(narration, str) or not narration.strip() or not isinstance(query, str) or not query.strip():
                        raise ValueError(f"Scene {number} has invalid narration or Pexels query.")
                    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 4 <= duration <= 10:
                                    raise ValueError(f"Scene {number} duration must be 4 to 10 seconds.")
                                normalized.append({"scene_number": number, "narration": narration.strip(), "pexels_query": query.strip(), "duration_hint_seconds": int(duration)})
    return {"title": title.strip(), "description": description.strip(), "scenes": normalized}
