from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .chunking import chunk_text
from .ingestion import extract_and_chunk, file_hash
from .learning import LearningService
from .gemini_utils import GeminiClient
from .models import (AskRequest, AskResponse, DocumentSummary, ExplainRequest,
                     ExplainResponse, Lecture, Quiz, StudyGuide)
from .pdf_utils import NoExtractableTextError, PDFProcessingError, PDFTooLongError
from .storage import Store
from .slide_generator import LectureGenerator
from .tts_utils import TTSGenerationError, TTSGenerator


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
BASE_DIR = Path(__file__).resolve().parent
AUDIO_ROOT = BASE_DIR / "audio"
AUDIO_ROOT.mkdir(parents=True, exist_ok=True)
MAX_PAGES = int(os.getenv("MAX_PDF_PAGES", "100"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024
CHUNK_WORDS = int(os.getenv("CHUNK_WORDS", "260"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "45"))

store = Store()
learning = LearningService(store)
workers = ThreadPoolExecutor(max_workers=max(1, int(os.getenv("JOB_WORKERS", "2"))))


class LegacySlide(BaseModel):
    title: str
    bullets: List[str]
    script: str
    audio_url: Optional[str] = None


class LegacyLecture(BaseModel):
    slides: List[LegacySlide]
    warnings: List[str] = Field(default_factory=list)

app = FastAPI(
    title="PDF to Lecture API",
    version="1.0.0",
    description="Document ingestion, grounded learning artifacts, retrieval, and observability.",
)
allowed_origins = [item.strip() for item in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/audio", StaticFiles(directory=AUDIO_ROOT), name="audio")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "version": app.version, "storage": "sqlite"}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    return store.metrics_summary()


@app.post("/generate-lecture", response_model=LegacyLecture, deprecated=True)
async def legacy_generate_lecture(file: UploadFile = File(...)) -> LegacyLecture:
    """Compatibility endpoint for the original slide-and-narration client."""
    path = await _save_validated_upload(file)
    try:
        document, _ = extract_and_chunk(path, min(MAX_PAGES, 30), 1000, 0)
        generator = LectureGenerator(GeminiClient(metrics_sink=store.record_metric))
        generated = generator.generate_from_chunks(chunk_text(document.text, max_words=1000))
        lecture_id = uuid.uuid4().hex
        tts = TTSGenerator(AUDIO_ROOT)
        slides = []
        warnings = list(document.warnings) + list(generator.warnings)
        for index, slide in enumerate(generated, start=1):
            audio_url = None
            try:
                audio_url = tts.synthesize(slide.script, lecture_id, index)
            except TTSGenerationError as exc:
                warnings.append(str(exc))
            slides.append(LegacySlide(title=slide.title, bullets=slide.bullets,
                                      script=slide.script, audio_url=audio_url))
        return LegacyLecture(slides=slides, warnings=warnings)
    finally:
        path.unlink(missing_ok=True)


@app.get("/documents", response_model=List[DocumentSummary])
def list_documents() -> List[DocumentSummary]:
    return [_document_response(item) for item in store.list_documents()]


@app.post("/documents", response_model=DocumentSummary, status_code=202)
async def upload_document(file: UploadFile = File(...)) -> DocumentSummary:
    filename = _safe_filename(file.filename)
    path = await _save_validated_upload(file)
    digest = file_hash(path)
    duplicate = store.find_by_hash(digest)
    if duplicate:
        path.unlink(missing_ok=True)
        return _document_response(duplicate, duplicate=True)

    document_id = uuid.uuid4().hex
    record = store.create_document(document_id, filename, digest)
    workers.submit(_process_document, document_id, path)
    return _document_response(record)


@app.get("/documents/{document_id}", response_model=DocumentSummary)
def get_document(document_id: str) -> DocumentSummary:
    return _document_response(_require_document(document_id))


@app.get("/documents/{document_id}/status", response_model=DocumentSummary)
def document_status(document_id: str) -> DocumentSummary:
    return get_document(document_id)


@app.get("/documents/{document_id}/events")
async def document_events(document_id: str) -> StreamingResponse:
    _require_document(document_id)

    async def stream():
        last = None
        while True:
            item = _require_document(document_id)
            payload = _document_response(item).model_dump()
            payload["status"] = payload["status"].value
            encoded = json.dumps(payload)
            if encoded != last:
                yield f"event: status\ndata: {encoded}\n\n"
                last = encoded
            if item["status"] in {"COMPLETED", "FAILED"}:
                break
            await asyncio.sleep(0.7)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})


@app.get("/documents/{document_id}/lecture", response_model=Lecture)
def get_lecture(document_id: str) -> Lecture:
    _require_ready(document_id)
    return learning.lecture(document_id)


@app.get("/documents/{document_id}/study-guide", response_model=StudyGuide)
def get_study_guide(document_id: str) -> StudyGuide:
    _require_ready(document_id)
    return learning.study_guide(document_id)


@app.get("/documents/{document_id}/quiz", response_model=Quiz)
def get_quiz(document_id: str) -> Quiz:
    _require_ready(document_id)
    return learning.quiz(document_id)


@app.post("/documents/{document_id}/ask", response_model=AskResponse)
def ask_document(document_id: str, request: AskRequest) -> AskResponse:
    _require_ready(document_id)
    return AskResponse(**learning.ask(document_id, request.question, request.top_k,
                                       request.similarity_threshold))


@app.post("/documents/{document_id}/explain", response_model=ExplainResponse)
def explain_section(document_id: str, request: ExplainRequest) -> ExplainResponse:
    lecture = get_lecture(document_id)
    section = next((item for item in lecture.sections if item.id == request.section_id), None)
    if not section:
        raise HTTPException(status_code=404, detail="Lecture section not found.")
    prefixes = {
        "simpler": "In simpler terms: ", "example": "A concrete way to apply this is: ",
        "analogy": "Think of this like a map: each idea gives you a landmark for the next one. ",
        "deeper": "Looking more closely at the source: ",
    }
    return ExplainResponse(explanation=prefixes[request.mode] + section.explanation,
                           citations=section.citations)


def _process_document(document_id: str, path: Path) -> None:
    started = time.perf_counter()
    try:
        store.update_document(document_id, status="PARSING", progress=18)
        document, chunks = extract_and_chunk(path, MAX_PAGES, CHUNK_WORDS, CHUNK_OVERLAP)
        store.update_document(document_id, status="CHUNKING", progress=48,
                              page_count=document.page_count)
        if not chunks:
            raise NoExtractableTextError("No usable text was found in the PDF.")
        store.update_document(document_id, status="EMBEDDING", progress=72)
        store.replace_chunks(document_id, chunks)
        store.update_document(document_id, status="GENERATING", progress=88,
                              chunk_count=len(chunks), warnings=document.warnings)
        learning.lecture(document_id)
        store.update_document(document_id, status="COMPLETED", progress=100)
        store.record_metric("ingestion", "local", (time.perf_counter() - started) * 1000,
                            metadata={"pages": document.page_count, "chunks": len(chunks)})
    except (PDFTooLongError, NoExtractableTextError, PDFProcessingError, ValueError) as exc:
        store.update_document(document_id, status="FAILED", progress=100, error=str(exc))
        store.record_metric("ingestion", "local", (time.perf_counter() - started) * 1000,
                            success=False, metadata={"error": type(exc).__name__})
    except Exception:
        store.update_document(document_id, status="FAILED", progress=100,
                              error="Document processing failed. Check server logs for details.")
        store.record_metric("ingestion", "local", (time.perf_counter() - started) * 1000,
                            success=False, metadata={"error": "unexpected"})
    finally:
        path.unlink(missing_ok=True)


async def _save_validated_upload(file: UploadFile) -> Path:
    header = await file.read(5)
    if header != b"%PDF-":
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")
    suffix = Path(_safe_filename(file.filename)).suffix.lower()
    if suffix != ".pdf":
        raise HTTPException(status_code=400, detail="Upload a file with a .pdf extension.")
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    size = len(header)
    try:
        temp.write(header)
        while True:
            block = await file.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail=f"PDF exceeds the {MAX_UPLOAD_BYTES // 1024 // 1024} MB limit.")
            temp.write(block)
        temp.close()
        return Path(temp.name)
    except Exception:
        temp.close()
        Path(temp.name).unlink(missing_ok=True)
        raise


def _safe_filename(filename: Optional[str]) -> str:
    raw = Path(filename or "document.pdf").name
    safe = re.sub(r"[^A-Za-z0-9._ -]", "_", raw)[:120]
    return safe or "document.pdf"


def _require_document(document_id: str) -> Dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9]{32}", document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    item = store.get_document(document_id)
    if not item:
        raise HTTPException(status_code=404, detail="Document not found.")
    return item


def _require_ready(document_id: str) -> Dict[str, Any]:
    item = _require_document(document_id)
    if item["status"] != "COMPLETED":
        raise HTTPException(status_code=409, detail=f"Document is {item['status'].lower()}.")
    return item


def _document_response(item: Dict[str, Any], duplicate: bool = False) -> DocumentSummary:
    return DocumentSummary(id=item["id"], filename=item["filename"], status=item["status"],
                           progress=item["progress"], page_count=item.get("page_count"),
                           chunk_count=item.get("chunk_count", 0), duplicate=duplicate,
                           error=item.get("error"), created_at=item["created_at"])
