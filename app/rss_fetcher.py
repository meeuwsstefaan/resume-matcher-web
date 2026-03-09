from __future__ import annotations

import hashlib
from html import unescape
from typing import Any

import feedparser


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return unescape(str(value)).strip()


def fetch_job_listings(feed_urls: list[str]) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for feed_url in feed_urls:
        parsed_feed = feedparser.parse(feed_url)
        source_name = _clean_text(parsed_feed.feed.get("title")) or feed_url

        for entry in parsed_feed.entries:
            title = _clean_text(entry.get("title")) or "Untitled role"
            link = _clean_text(entry.get("link"))
            published = _clean_text(entry.get("published") or entry.get("updated"))
            summary = _clean_text(entry.get("summary") or entry.get("description"))

            entry_unique_value = (
                _clean_text(entry.get("id"))
                or _clean_text(entry.get("guid"))
                or link
                or f"{title}:{published}:{source_name}"
            )

            job_id = hashlib.sha256(entry_unique_value.encode("utf-8", errors="ignore")).hexdigest()
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            jobs.append(
                {
                    "id": job_id,
                    "title": title,
                    "link": link,
                    "published": published,
                    "summary": summary,
                    "source": source_name,
                }
            )

    return jobs

