from __future__ import annotations

import re
import time
from typing import Any, Dict, List

from .models import Citation, Lecture, LectureSection, Quiz, QuizQuestion, StudyGuide
from .retrieval import retrieve
from .storage import Store


def citation(chunk: Dict[str, Any]) -> Citation:
    excerpt = re.sub(r"\s+", " ", chunk["text"]).strip()[:220]
    return Citation(page=chunk["page"], chunk_index=chunk["chunk_index"],
                    section=chunk["section"], excerpt=excerpt, score=chunk.get("score", 1.0))


def sentences(text: str) -> List[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if len(part.strip()) > 25]


class LearningService:
    def __init__(self, store: Store):
        self.store = store

    def lecture(self, document_id: str) -> Lecture:
        cached = self.store.get_artifact(document_id, "lecture")
        if cached:
            return Lecture(**cached)
        started = time.perf_counter()
        doc = self.store.get_document(document_id) or {}
        chunks = self.store.get_chunks(document_id)
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for chunk in chunks:
            groups.setdefault(chunk["section"], []).append(chunk)
        sections = []
        for index, (name, items) in enumerate(list(groups.items())[:8]):
            source_sentences = sentences(" ".join(item["text"] for item in items))
            points = source_sentences[:4] or [items[0]["text"][:180]]
            sections.append(LectureSection(
                id=f"section-{index + 1}", title=name if name != "Introduction" else _title(points[0]),
                explanation=" ".join(points[:3]), key_points=[point[:180] for point in points[:4]],
                citations=[citation(item) for item in items[:3]],
            ))
        if not sections:
            raise ValueError("Document has no indexed content")
        lecture = Lecture(
            title=_clean_filename(doc.get("filename", "Document")),
            learning_objectives=[f"Explain {section.title.lower()}" for section in sections[:3]],
            prerequisites=["Familiarity with the document's introductory terminology"],
            sections=sections,
            summary=" ".join(section.explanation for section in sections)[:900],
            review_questions=[f"What is the main idea behind {section.title}?" for section in sections[:4]],
        )
        self.store.save_artifact(document_id, "lecture", lecture.model_dump())
        self.store.record_metric("lecture", "local-grounded", (time.perf_counter() - started) * 1000,
                                 metadata={"sections": len(sections)})
        return lecture

    def study_guide(self, document_id: str) -> StudyGuide:
        cached = self.store.get_artifact(document_id, "study_guide")
        if cached:
            return StudyGuide(**cached)
        lecture = self.lecture(document_id)
        concepts = [section.title for section in lecture.sections]
        facts = [point for section in lecture.sections for point in section.key_points[:2]][:10]
        guide = StudyGuide(
            major_concepts=concepts,
            definitions=[fact for fact in facts if " is " in fact.lower() or " means " in fact.lower()][:6]
                        or facts[:4],
            important_facts=facts,
            common_mistakes=[f"Confusing the definition of {name} with a related concept" for name in concepts[:4]],
        )
        self.store.save_artifact(document_id, "study_guide", guide.model_dump())
        return guide

    def quiz(self, document_id: str) -> Quiz:
        cached = self.store.get_artifact(document_id, "quiz")
        if cached:
            return Quiz(**cached)
        lecture = self.lecture(document_id)
        questions = []
        for index, section in enumerate(lecture.sections[:5]):
            answer = section.key_points[0]
            distractors = [other.title for other in lecture.sections if other.id != section.id][:3]
            while len(distractors) < 3:
                distractors.append("This is not stated in the source")
            options = [answer] + distractors
            questions.append(QuizQuestion(
                id=f"q-{index + 1}", question=f"Which statement best describes {section.title}?",
                options=options, correct_index=0, explanation=section.explanation,
                difficulty="medium" if index > 1 else "easy", citations=section.citations[:2],
            ))
        quiz = Quiz(questions=questions)
        self.store.save_artifact(document_id, "quiz", quiz.model_dump())
        return quiz

    def ask(self, document_id: str, question: str, top_k: int, threshold: float):
        started = time.perf_counter()
        matches = retrieve(self.store.get_chunks(document_id), question, top_k, threshold)
        latency = (time.perf_counter() - started) * 1000
        self.store.record_metric("retrieval", "local-feature-hash", latency,
                                 metadata={"returned": len(matches), "top_k": top_k})
        if not matches:
            return {"answer": "The uploaded document does not provide enough information to answer that question.",
                    "citations": [], "grounded": False}
        evidence = sentences(" ".join(match["text"] for match in matches))
        answer = " ".join(evidence[:4])[:1200]
        return {"answer": answer, "citations": [citation(match) for match in matches], "grounded": True}


def _title(text: str) -> str:
    words = re.sub(r"[^A-Za-z0-9 -]", "", text).split()[:8]
    return " ".join(words).strip() or "Core Concepts"


def _clean_filename(filename: str) -> str:
    return re.sub(r"[_-]+", " ", filename.rsplit(".", 1)[0]).strip().title()

