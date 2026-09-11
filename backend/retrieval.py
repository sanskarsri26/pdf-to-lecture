from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any, Dict, List


VECTOR_SIZE = 384


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def embed(text: str, size: int = VECTOR_SIZE) -> List[float]:
    """Dependency-free signed feature hashing for reproducible local retrieval."""
    counts = Counter(tokenize(text))
    vector = [0.0] * size
    for token, count in counts.items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % size
        sign = 1 if digest[4] % 2 else -1
        vector[index] += sign * (1 + math.log(count))
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]


def cosine(left: List[float], right: List[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def retrieve(chunks: List[Dict[str, Any]], query: str, top_k: int = 4,
             threshold: float = 0.08) -> List[Dict[str, Any]]:
    query_vector = embed(query)
    ranked = []
    query_terms = set(tokenize(query))
    for chunk in chunks:
        semantic = cosine(query_vector, chunk["vector"])
        terms = set(tokenize(chunk["text"]))
        lexical = len(query_terms & terms) / max(1, len(query_terms))
        score = max(0.0, 0.75 * semantic + 0.25 * lexical)
        if score >= threshold:
            ranked.append({**chunk, "score": round(score, 4)})
    return sorted(ranked, key=lambda item: item["score"], reverse=True)[:top_k]

