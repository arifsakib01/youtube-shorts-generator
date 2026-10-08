from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
logger = logging.getLogger(__name__)
FEEDS = {
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
    "Microsoft AI": "https://blogs.microsoft.com/ai/feed/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
}

def fetch_daily_news(hours: int = 36, limit: int = 8) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stories = []
    for source, url in FEEDS.items():
        try:
            request = Request(url, headers={"User-Agent": "daily-ai-shorts/1.0"})
            with urlopen(request, timeout=15) as response:
                root = ET.fromstring(response.read())
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                date_text = item.findtext("pubDate") or ""
                try:
                    published = parsedate_to_datetime(date_text).astimezone(timezone.utc)
                except (TypeError, ValueError, OverflowError):
                    published = datetime.now(timezone.utc)
                if title and link and published >= cutoff:
                    stories.append((published, source, title, link))
        except (OSError, ET.ParseError) as exc:
            logger.warning("Could not read AI news feed %s: %s", source, exc)
    stories.sort(reverse=True)
    if not stories:
        raise RuntimeError("No recent AI news was available from the configured RSS feeds.")
    return "DAILY AI NEWS SOURCES (verify details against these links; do not invent facts):\\n" + "\\n".join(f"- [{source}] {title} | {link}" for _, source, title, link in stories[:limit])
