from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import PROJECT_ROOT, ensure_directories, load_feed_urls
from .keyword_extractor import extract_keywords_from_resume, extract_keywords_from_text
from .rss_fetcher import fetch_job_listings
from .storage import load_latest_keywords, save_keywords, save_resume_file, save_rss_results, update_job_state

app = FastAPI(title="Resume Watcher Web", version="1.0")

STATIC_DIR = PROJECT_ROOT / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup_event() -> None:
    ensure_directories()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict[str, object]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No resume file selected.")

    try:
        resume_path = await save_resume_file(file)
        keywords = extract_keywords_from_resume(resume_path)
        saved_keyword_file = save_keywords(resume_filename=resume_path.name, keywords=keywords)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {exc}") from exc

    return {
        "message": "Resume uploaded and keywords extracted.",
        "resume_file": resume_path.name,
        "keyword_file": str(saved_keyword_file.relative_to(PROJECT_ROOT)),
        "keyword_count": len(keywords),
        "keywords": keywords,
    }


@app.get("/api/resume/keywords")
def latest_keywords() -> dict[str, object]:
    return load_latest_keywords()


def _score_job_match(resume_keywords: set[str], job_text: str) -> tuple[float, int, list[str]]:
    if not resume_keywords:
        return 0.0, 0, []

    job_keywords = set(extract_keywords_from_text(job_text, keyword_limit=60))
    if not job_keywords:
        return 0.0, 0, []

    matched_keywords = sorted(resume_keywords & job_keywords)
    matched_count = len(matched_keywords)
    match_score = round((matched_count / len(resume_keywords)) * 100, 2)
    return match_score, matched_count, matched_keywords


@app.post("/api/jobs/fetch")
def fetch_jobs() -> dict[str, object]:
    feed_urls = load_feed_urls()
    if not feed_urls:
        raise HTTPException(status_code=400, detail="No RSS feeds found in config/rss_feeds.json.")

    jobs = fetch_job_listings(feed_urls)
    resume_keywords_payload = load_latest_keywords()
    resume_keywords = {
        keyword.lower()
        for keyword in resume_keywords_payload.get("keywords", [])
        if isinstance(keyword, str) and keyword.strip()
    }

    for job in jobs:
        job_text = " ".join(
            [str(job.get("title", "")), str(job.get("summary", "")), str(job.get("source", ""))]
        )
        match_score, matched_count, matched_keywords = _score_job_match(resume_keywords, job_text)
        job["match_score"] = match_score
        job["match_count"] = matched_count
        job["matched_keywords"] = matched_keywords

    jobs.sort(key=lambda job: (float(job.get("match_score", 0)), int(job.get("match_count", 0))), reverse=True)
    rss_output_file = save_rss_results(jobs)
    stats = update_job_state(jobs)

    return {
        "message": "Job listings fetched.",
        "rss_file": str(rss_output_file.relative_to(PROJECT_ROOT)),
        "fetched_count": stats["fetched_count"],
        "new_count": stats["new_count"],
        "last_run_utc": stats["last_run_utc"],
        "resume_keyword_count": len(resume_keywords),
        "jobs": jobs,
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
