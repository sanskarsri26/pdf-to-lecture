from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List

from .pdf_utils import ExtractedDocument, extract_pdf_text
from .retrieval import embed


HEADING_PATTERN = re.compile(r"^(?:chapter\s+\d+|\d+(?:\.\d+)*\s+)?[A-Z][^.!?]{2,80}$", re.I)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_and_chunk(path: Path, max_pages: int, chunk_words: int = 260,
                      overlap_words: int = 45) -> tuple[ExtractedDocument, List[Dict[str, Any]]]:
    document = extract_pdf_text(path, max_pages=max_pages)
    chunks: List[Dict[str, Any]] = []
    current_section = "Introduction"
    for page_number, page_text in enumerate(document.pages, start=1):
        page_words: List[str] = []
        for line in (part.strip() for part in page_text.splitlines() if part.strip()):
            if HEADING_PATTERN.match(line) and len(line.split()) <= 12:
                current_section = line[:100]
                continue
            page_words.extend(line.split())
        step = max(1, chunk_words - overlap_words)
        for start in range(0, len(page_words), step):
            words = page_words[start:start + chunk_words]
            if not words:
                continue
            text = " ".join(words)
            chunks.append({"chunk_index": len(chunks), "page": page_number,
                           "section": current_section, "text": text, "vector": embed(text)})
            if start + chunk_words >= len(page_words):
                break
    return document, chunks
