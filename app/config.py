from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
RSS_RESULTS_DIR = INPUT_DIR / "rss_results"
RESUME_DIR = INPUT_DIR / "resume"
KEYWORDS_DIR = INPUT_DIR / "keywords"
FEEDS_CONFIG_FILE = CONFIG_DIR / "rss_feeds.json"
STATE_FILE = OUTPUT_DIR / "state.json"


def ensure_directories() -> None:
    """Create required project directories if they are missing."""
    for directory in [CONFIG_DIR, INPUT_DIR, OUTPUT_DIR, RSS_RESULTS_DIR, RESUME_DIR, KEYWORDS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def load_feed_urls() -> list[str]:
    """Load RSS feed URLs from the separate config file."""
    if not FEEDS_CONFIG_FILE.exists():
        return []

    with FEEDS_CONFIG_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    feed_urls = data.get("feeds", [])
    return [feed for feed in feed_urls if isinstance(feed, str) and feed.strip()]

