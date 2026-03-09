from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from .config import KEYWORDS_DIR, REMOVED_JOBS_FILE, RESUME_DIR, RSS_RESULTS_DIR, STATE_FILE, ensure_directories


async def save_resume_file(upload_file: UploadFile) -> Path:
    """Store only one uploaded resume in input/resume."""
    ensure_directories()

    for existing_file in RESUME_DIR.glob("*"):
        if existing_file.is_file():
            existing_file.unlink()

    safe_name = Path(upload_file.filename or "resume").name
    destination = RESUME_DIR / safe_name
    destination.write_bytes(await upload_file.read())
    await upload_file.close()
    return destination


def save_keywords(resume_filename: str, keywords: list[str]) -> Path:
    ensure_directories()
    payload = {
        "resume_filename": resume_filename,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "keywords": keywords,
    }

    keyword_file = KEYWORDS_DIR / "latest_keywords.json"
    keyword_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return keyword_file


def load_latest_keywords() -> dict[str, object]:
    keyword_file = KEYWORDS_DIR / "latest_keywords.json"
    if not keyword_file.exists():
        return {"resume_filename": None, "keywords": []}
    return json.loads(keyword_file.read_text(encoding="utf-8"))


def save_rss_results(jobs: list[dict[str, str]]) -> Path:
    ensure_directories()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_file = RSS_RESULTS_DIR / f"rss_results_{timestamp}.json"
    output_file.write_text(json.dumps({"jobs": jobs}, indent=2), encoding="utf-8")
    return output_file


def _load_state() -> dict[str, object]:
    if not STATE_FILE.exists():
        return {"job_ids": [], "last_run_utc": None}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def _save_state(state: dict[str, object]) -> None:
    ensure_directories()
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def update_job_state(jobs: list[dict[str, str]]) -> dict[str, object]:
    previous_state = _load_state()
    previous_ids = set(previous_state.get("job_ids", []))
    current_ids = {job["id"] for job in jobs}
    new_ids = current_ids - previous_ids

    for job in jobs:
        job["is_new"] = job["id"] in new_ids

    now_utc = datetime.now(timezone.utc).isoformat()
    _save_state({"job_ids": sorted(current_ids), "last_run_utc": now_utc})

    return {
        "fetched_count": len(jobs),
        "new_count": len(new_ids),
        "last_run_utc": now_utc,
    }


def load_removed_job_ids() -> set[str]:
    if not REMOVED_JOBS_FILE.exists():
        return set()

    payload = json.loads(REMOVED_JOBS_FILE.read_text(encoding="utf-8"))
    removed_ids = payload.get("removed_job_ids", [])
    return {item for item in removed_ids if isinstance(item, str) and item.strip()}


def add_removed_job_id(job_id: str) -> int:
    job_id = job_id.strip()
    if not job_id:
        return len(load_removed_job_ids())

    removed_job_ids = load_removed_job_ids()
    removed_job_ids.add(job_id)

    ensure_directories()
    REMOVED_JOBS_FILE.write_text(
        json.dumps(
            {
                "removed_job_ids": sorted(removed_job_ids),
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return len(removed_job_ids)
