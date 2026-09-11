import json
import os
import re
from dataclasses import dataclass
from typing import Any, List, Optional

from .gemini_utils import GeminiClient, GeminiUnavailableError


SUMMARY_PROMPT = """Summarize the following content into concise educational teaching notes.

Rules:
- Keep only important concepts
- Preserve factual accuracy
- Remove repetition
- Organize clearly
- Preserve definitions, formulas, worked examples, and theorem statements
- When the source is math-heavy, explain what each formula is used for

Content:
{chunk}
"""

SLIDE_PLAN_PROMPT = """Convert these teaching notes into a short sequence of lecture slides.

Rules:
- Create 1 to {max_slides} slides
- Each slide should teach one focused idea
- Slide bullets must be concise, max 5 bullets
- Bullets should be visual outline points, not full explanations
- Include teaching_notes with intuition, example/use case, and likely student confusion
- For math, include a small worked example or verification idea when the source provides one
- Do not invent facts that are not supported by the notes
- Return only valid JSON using this exact shape:
  {{
    "slides": [
      {{
        "title": "Slide title",
        "bullets": ["Short point", "Short point"],
        "teaching_notes": "What a professor should explain beyond the bullets."
      }}
    ]
  }}

Teaching notes:
{summary}
"""

SCRIPT_PROMPT = """You are a professor teaching this slide in a live class.

Write the spoken narration for this slide.

Rules:
- Do NOT read bullet points directly
- Use the teaching notes as your source of truth
- Open with the intuition behind the idea
- Explain why the idea matters before getting technical
- Include a concrete example, mini-walkthrough, or common student mistake
- Speak naturally like a real lecturer
- Use plain classroom language, not marketing language
- Do not use all-caps emphasis
- Do not use markdown, code ticks, or visual formatting
- Keep it around 90 to 150 words
- Return only the spoken script, with no markdown
- Do not say "this slide says" or "as you can see"

Bad Example:
"Matrix multiplication is associative."

Good Example:
"The useful thing about associativity is that it lets us regroup a product without changing the result. So if we have A times B times C, we can multiply A and B first, or B and C first, as long as the dimensions fit."

Slide:
Title: {title}

Bullets:
{bullets}

Teaching notes:
{teaching_notes}

Broader source context:
{summary}
"""


@dataclass
class PlannedSlide:
    title: str
    bullets: List[str]
    teaching_notes: str


@dataclass
class GeneratedSlide:
    title: str
    bullets: List[str]
    script: str


class LectureGenerator:
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini = gemini_client or GeminiClient()
        self.warnings: List[str] = []
        self.max_slides_per_chunk = _env_int("MAX_SLIDES_PER_CHUNK", default=3)

    def generate_from_chunks(self, chunks: List[str]) -> List[GeneratedSlide]:
        slides: List[GeneratedSlide] = []
        for chunk in chunks:
            summary = self.summarize(chunk)
            planned_slides = self.create_slides(summary)
            for planned_slide in planned_slides:
                script = self.create_script(
                    title=planned_slide.title,
                    bullets=planned_slide.bullets,
                    teaching_notes=planned_slide.teaching_notes,
                    summary=summary,
                )
                slides.append(
                    GeneratedSlide(
                        title=planned_slide.title,
                        bullets=planned_slide.bullets,
                        script=script,
                    )
                )
        return slides

    def summarize(self, chunk: str) -> str:
        prompt = SUMMARY_PROMPT.format(chunk=chunk)
        fallback = _fallback_summary(chunk)
        return self._generate_or_fallback(prompt, fallback, temperature=0.3)

    def create_slide(self, summary: str) -> tuple:
        planned_slide = self.create_slides(summary)[0]
        return planned_slide.title, planned_slide.bullets

    def create_slides(self, summary: str) -> List[PlannedSlide]:
        fallback_slides = _fallback_planned_slides(summary, max_slides=self.max_slides_per_chunk)
        prompt = SLIDE_PLAN_PROMPT.format(
            summary=summary,
            max_slides=self.max_slides_per_chunk,
        )

        raw = self._generate_or_fallback(
            prompt,
            json.dumps(
                {
                    "slides": [
                        {
                            "title": slide.title,
                            "bullets": slide.bullets,
                            "teaching_notes": slide.teaching_notes,
                        }
                        for slide in fallback_slides
                    ]
                }
            ),
            temperature=0.35,
        )

        try:
            data = _extract_json(raw)
            items = data.get("slides") if isinstance(data, dict) else data
            if not isinstance(items, list):
                raise ValueError("Slide plan JSON must contain a slides list.")

            planned_slides: List[PlannedSlide] = []
            for item in items[: self.max_slides_per_chunk]:
                if not isinstance(item, dict):
                    continue

                title = _clean_title(item.get("title") or "Lecture Topic")
                bullets = _clean_bullets(item.get("bullets") or [])
                teaching_notes = _clean_teaching_notes(
                    item.get("teaching_notes")
                    or item.get("speaker_notes")
                    or item.get("notes")
                    or summary
                )
                planned_slides.append(
                    PlannedSlide(title=title, bullets=bullets, teaching_notes=teaching_notes)
                )

            if planned_slides:
                return planned_slides
            raise ValueError("Slide plan JSON did not include usable slides.")
        except Exception:
            self._warn_once("Gemini slide-plan JSON was invalid; used local slide formatting.")
            return fallback_slides

    def create_script(
        self,
        title: str,
        bullets: List[str],
        teaching_notes: str = "",
        summary: str = "",
    ) -> str:
        bullet_text = "\n".join(f"- {bullet}" for bullet in bullets)
        prompt = SCRIPT_PROMPT.format(
            title=title,
            bullets=bullet_text,
            teaching_notes=teaching_notes or summary,
            summary=summary,
        )
        fallback = _fallback_script(title, bullets, teaching_notes or summary)
        script = self._generate_or_fallback(prompt, fallback, temperature=0.7)
        return _clean_script(script)

    def _generate_or_fallback(self, prompt: str, fallback: str, temperature: float) -> str:
        if not self.gemini.available:
            reason = self.gemini.load_error or "Gemini is unavailable."
            self._warn_once(f"{reason} Used local fallback lecture generation.")
            return fallback

        try:
            return self.gemini.generate_text(prompt, temperature=temperature)
        except GeminiUnavailableError as exc:
            self._warn_once(f"{exc} Used local fallback lecture generation.")
            return fallback

    def _warn_once(self, warning: str) -> None:
        if warning not in self.warnings:
            self.warnings.append(warning)


def _extract_json(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        object_start = cleaned.find("{")
        object_end = cleaned.rfind("}")
        array_start = cleaned.find("[")
        array_end = cleaned.rfind("]")

        if array_start != -1 and array_end > array_start:
            return json.loads(cleaned[array_start : array_end + 1])

        if object_start == -1 or object_end == -1 or object_end <= object_start:
            raise
        return json.loads(cleaned[object_start : object_end + 1])


def _clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", str(title)).strip()
    return title[:90] or "Lecture Topic"


def _clean_bullets(bullets: List[str]) -> List[str]:
    cleaned = []
    for bullet in bullets:
        bullet_text = re.sub(r"\s+", " ", str(bullet)).strip(" -•\t")
        if bullet_text:
            cleaned.append(bullet_text[:140])
        if len(cleaned) == 5:
            break
    return cleaned or ["Key concept", "Supporting detail", "Example or implication"]


def _clean_teaching_notes(notes: str) -> str:
    notes = re.sub(r"\s+", " ", str(notes)).strip()
    return notes[:1200] or "Explain the intuition, show how the idea is used, and warn about a common mistake."


def _clean_script(script: str) -> str:
    script = re.sub(r"^```(?:text)?\s*", "", script.strip())
    script = re.sub(r"\s*```$", "", script)
    script = re.sub(r"^\s*(Script|Narration)\s*:\s*", "", script, flags=re.IGNORECASE)
    script = script.replace("`", "")
    script = script.strip().strip('"')
    return re.sub(r"\s+", " ", script).strip()


def _sentences(text: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]


def _fallback_summary(chunk: str) -> str:
    sentences = _sentences(chunk)
    return " ".join(sentences[:8]) if sentences else chunk[:1200]


def _fallback_slide(summary: str) -> tuple:
    sentences = _sentences(summary)
    if not sentences:
        return "Lecture Topic", ["Key concept", "Supporting detail", "Example or implication"]

    title_words = re.sub(r"[^A-Za-z0-9 ]", "", sentences[0]).split()[:8]
    title = " ".join(title_words) or "Lecture Topic"

    bullets = []
    for sentence in sentences[:5]:
        words = sentence.split()
        bullets.append(" ".join(words[:16]).rstrip("."))

    return _clean_title(title), _clean_bullets(bullets)


def _fallback_planned_slides(summary: str, max_slides: int = 3) -> List[PlannedSlide]:
    sentences = _sentences(summary)
    if not sentences:
        title, bullets = _fallback_slide(summary)
        return [
            PlannedSlide(
                title=title,
                bullets=bullets,
                teaching_notes=summary[:1200],
            )
        ]

    slide_count = min(max(1, max_slides), max(1, (len(sentences) + 2) // 3))
    planned_slides: List[PlannedSlide] = []
    group_size = max(1, (len(sentences) + slide_count - 1) // slide_count)

    for start in range(0, len(sentences), group_size):
        group = sentences[start : start + group_size]
        if not group:
            continue

        title, bullets = _fallback_slide(" ".join(group))
        teaching_notes = (
            " ".join(group[:4])
            + " Explain how these facts connect, why the definition matters, and what mistake a student might make."
        )
        planned_slides.append(
            PlannedSlide(
                title=title,
                bullets=bullets,
                teaching_notes=_clean_teaching_notes(teaching_notes),
            )
        )
        if len(planned_slides) == max_slides:
            break

    return planned_slides or [
        PlannedSlide(
            title="Lecture Topic",
            bullets=["Key concept", "Supporting detail", "Example or implication"],
            teaching_notes=summary[:1200],
        )
    ]


def _fallback_script(title: str, bullets: List[str], teaching_notes: str = "") -> str:
    if not bullets:
        return f"Let's unpack {title}. The main goal is to understand the central idea and why it matters."

    notes_sentences = _sentences(teaching_notes)
    source_hint = notes_sentences[0] if notes_sentences else bullets[0]

    parts = [
        f"Let's unpack {title}. The goal is not to memorize the bullet points, but to see how the idea works in practice.",
        f"The anchor is this: {source_hint}. Think of that as the reason the rest of the slide is useful.",
    ]

    if len(bullets) > 1:
        parts.append(
            "From there, the next step is to connect the rule to an example. "
            f"When you see {bullets[1].lower()}, ask what operation is being allowed and what dimensions or assumptions make it legal."
        )

    if len(bullets) > 2:
        parts.append(
            "A common mistake is to treat every familiar algebra rule as automatic. "
            f"The point about {bullets[2].lower()} is a reminder to check the condition before applying the rule."
        )

    parts.append(
        "By the end, you should be able to explain the rule in your own words and recognize when it can actually be used."
    )

    return " ".join(parts)


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return max(1, value)
