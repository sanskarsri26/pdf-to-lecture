from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PARSING = "PARSING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Citation(BaseModel):
    page: int
    chunk_index: int
    section: str
    excerpt: str
    score: float = 0.0


class DocumentSummary(BaseModel):
    id: str
    filename: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    page_count: Optional[int] = None
    chunk_count: int = 0
    duplicate: bool = False
    error: Optional[str] = None
    created_at: str


class LectureSection(BaseModel):
    id: str
    title: str
    explanation: str
    key_points: List[str]
    citations: List[Citation]


class Lecture(BaseModel):
    title: str
    learning_objectives: List[str]
    prerequisites: List[str]
    sections: List[LectureSection]
    summary: str
    review_questions: List[str]


class StudyGuide(BaseModel):
    major_concepts: List[str]
    definitions: List[str]
    important_facts: List[str]
    common_mistakes: List[str]


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_index: int
    explanation: str
    difficulty: str
    citations: List[Citation]


class Quiz(BaseModel):
    questions: List[QuizQuestion]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=4, ge=1, le=10)
    similarity_threshold: float = Field(default=0.08, ge=0, le=1)


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    grounded: bool


class ExplainRequest(BaseModel):
    section_id: str
    mode: str = Field(default="simpler", pattern="^(simpler|example|analogy|deeper)$")


class ExplainResponse(BaseModel):
    explanation: str
    citations: List[Citation]

