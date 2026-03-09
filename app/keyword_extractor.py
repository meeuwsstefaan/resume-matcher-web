from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#\-.]{1,}")
STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "any",
    "are",
    "been",
    "but",
    "can",
    "did",
    "for",
    "from",
    "have",
    "her",
    "him",
    "his",
    "how",
    "into",
    "its",
    "job",
    "jobs",
    "our",
    "resume",
    "she",
    "that",
    "the",
    "their",
    "them",
    "there",
    "they",
    "this",
    "use",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "you",
    "your",
}


def _extract_text(resume_path: Path) -> str:
    suffix = resume_path.suffix.lower()

    if suffix in {".txt", ".md", ".rst"}:
        return resume_path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError("PDF parsing dependency is missing. Install requirements first.") from exc

        reader = PdfReader(str(resume_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    if suffix == ".docx":
        try:
            import docx2txt
        except ImportError as exc:
            raise ValueError("DOCX parsing dependency is missing. Install requirements first.") from exc

        return docx2txt.process(str(resume_path)) or ""

    raise ValueError("Unsupported resume format. Use .txt, .md, .pdf, or .docx.")


def _extract_keywords(text: str, limit: int = 40) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    tokens = [token for token in tokens if token not in STOPWORDS and len(token) > 2]
    frequencies = Counter(tokens)
    return [word for word, _ in frequencies.most_common(limit)]


def extract_keywords_from_text(text: str, keyword_limit: int = 40) -> list[str]:
    return _extract_keywords(text=text, limit=keyword_limit)


def extract_keywords_from_resume(resume_path: Path, keyword_limit: int = 40) -> list[str]:
    text = _extract_text(resume_path)
    return extract_keywords_from_text(text=text, keyword_limit=keyword_limit)
