# Initial repository audit

This audit records the Phase 0 state before the product refactor.

## Current architecture

The original repository was an unversioned local prototype with a React/Vite client and a single FastAPI module. `POST /generate-lecture` copied an uploaded PDF to a temporary file, extracted all text with pdfplumber (and optional page OCR with PyMuPDF/Tesseract), split the combined text into paragraph-sized blocks, called Gemini three times per block to summarize, plan slides, and write narration, then optionally generated MP3 files through Edge TTS or gTTS. The response existed only in browser memory; generated audio remained on the local filesystem.

## What worked

- Text PDF extraction and cleanup, including de-hyphenation
- Conditional OCR for sparse scanned pages
- Paragraph-preserving text chunking
- Gemini-backed slide planning with JSON recovery and useful no-key fallbacks
- Narration generation plus Edge TTS/gTTS fallback
- A responsive, visually coherent slide/narration viewer
- Nine focused unit tests for chunking, extraction helpers, JSON parsing, and speech cleanup

## Incomplete or weak areas

- One blocking endpoint owned upload, extraction, model orchestration, and audio generation
- No upload byte limit or PDF magic-byte check; extension-only validation
- Page provenance was discarded before chunking, so citations were impossible
- No document identity, persistence, duplicate detection, library, job state, or cache
- No retrieval/vector index, grounded Q&A, study guide, quiz, or explanation workflow
- Gemini was directly coupled to lecture code; structured output used dataclasses and ad hoc JSON cleanup
- No metrics, token/cost fields, retrieval traces, benchmark, or evaluation runner
- No API integration tests, frontend build check, container, CI, or architecture document
- Failures from long requests could leave the interface waiting with simulated progress
- Audio storage had no retention policy; there was no authentication, rate limiting, or tenant boundary
- The README documented only the MVP and did not state evaluation or deployment limitations
- The directory had no `.git` metadata, so none of the existing work was versioned

## Preserved

PDF cleanup/OCR, legacy chunking, Gemini client and fallback generation, TTS providers, their tests, and the original compatibility endpoint were retained. The frontend's strong focus on an obvious upload-to-learning workflow and restrained visual treatment were preserved while the information architecture changed.

## Refactored

Upload validation and background ingestion moved into a document lifecycle. Page-aware chunks now retain citation metadata and vectors. Routes delegate to storage and learning services. Responses use Pydantic schemas. The client is a persistent learning workspace rather than an ephemeral slide player. See [architecture.md](architecture.md) for the resulting design and limitations.

## Phased plan used

1. Stabilize existing modules and define typed domain schemas.
2. Add validated ingestion, document/job persistence, deduplication, and structured chunks.
3. Add deterministic vector retrieval, citations, and insufficient-evidence behavior.
4. Build cached structured lectures and section explanations.
5. Reuse the same evidence for study guides and quizzes.
6. Add a versioned retrieval benchmark and actual measurements.
7. Record operation, latency, token, cost, success, and retrieval metadata.
8. Rebuild the client around the complete learning flow.
9. Add integration tests, containers, and CI build verification.
10. Include demo data and transparent architecture/README documentation.
