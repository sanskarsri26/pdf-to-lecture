import re
from typing import List


def chunk_text(text: str, max_words: int = 1000) -> List[str]:
    """Split text into roughly max_words chunks while preserving paragraphs."""
    if max_words <= 0:
        raise ValueError("max_words must be greater than 0")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        words = text.split()
        return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words)]

    chunks: List[str] = []
    current: List[str] = []
    current_word_count = 0

    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            continue

        if len(words) > max_words:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_word_count = 0

            for i in range(0, len(words), max_words):
                chunks.append(" ".join(words[i : i + max_words]))
            continue

        would_exceed = current_word_count + len(words) > max_words
        if would_exceed and current:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_word_count = len(words)
        else:
            current.append(paragraph)
            current_word_count += len(words)

    if current:
        chunks.append("\n\n".join(current))

    return chunks
