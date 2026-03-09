# Resume Watcher Web

Version: 1.0

Python web app with:
- backend RSS polling from a separate config file (`config/rss_feeds.json`),
- resume upload (single file) and keyword extraction,
- frontend job cards with counts for fetched jobs and new jobs since previous run,
- matching score per job card based on overlap between resume keywords and job post keywords,
- job cards ordered from highest matching score to lowest,
- persistent remove button per job card (removed cards are never shown again on future fetches),
- `input/` and `output/` project directories for stored artifacts.

## Open In PyCharm
1. Open PyCharm.
2. Choose **Open**.
3. Select `C:\Codex\resume-watcher-web`.
4. Create/select a Python interpreter for the project.
5. Install dependencies:
   `pip install -r requirements.txt`

## Run
From PyCharm terminal or Run Configuration:

```bash
python run.py
```

Then open `http://127.0.0.1:8000`.

## Project Structure

```text
C:\Codex\resume-watcher-web
├── app
│   ├── config.py
│   ├── keyword_extractor.py
│   ├── main.py
│   ├── rss_fetcher.py
│   └── storage.py
├── config
│   └── rss_feeds.json
├── input
│   ├── keywords
│   ├── resume
│   └── rss_results
├── output
├── static
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── requirements.txt
└── run.py
```

## Notes
- RSS feed URLs are configurable in `config/rss_feeds.json` and loaded with regular Python `json` code.
- Uploaded resume is stored in `input/resume` (previous one is replaced).
- Extracted keywords are stored in `input/keywords/latest_keywords.json`.
- Fetched RSS job results are stored in `input/rss_results/`.
- State for "new since last run" is stored in `output/state.json`.
- Permanently removed job IDs are stored in `output/removed_jobs.json`.
