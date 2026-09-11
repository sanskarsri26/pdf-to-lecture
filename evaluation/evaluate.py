"""Run the deterministic retrieval benchmark: python -m evaluation.evaluate."""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from backend.retrieval import embed, retrieve


ROOT = Path(__file__).resolve().parents[1]
CORPUS = [
    (1, "Spaced Practice", "Spaced practice distributes study sessions over time. The spacing effect improves long-term retention compared with cramming."),
    (2, "Retrieval Practice", "Retrieval practice strengthens memory by requiring active recall. Practice tests reveal gaps and make later recall easier."),
    (3, "Interleaving", "Interleaving means mixing different problem types during one practice session. Learners must choose an approach instead of repeating one procedure."),
]


def run() -> dict:
    cases = json.loads((ROOT / "evaluation" / "benchmark.json").read_text())
    chunks = [{"page": page, "section": section, "text": text, "chunk_index": index, "vector": embed(text)} for index, (page, section, text) in enumerate(CORPUS)]
    hits = 0
    citation_hits = 0
    relevance_hits = 0
    latencies = []
    rows = []
    for case in cases:
        started = time.perf_counter()
        matches = retrieve(chunks, case["question"], top_k=3, threshold=0)
        latencies.append((time.perf_counter() - started) * 1000)
        pages = [item["page"] for item in matches]
        hit = case["expected_page"] in pages
        top_correct = bool(matches and matches[0]["page"] == case["expected_page"])
        answer = matches[0]["text"].lower() if matches else ""
        relevant = all(term in answer for term in case["expected_terms"])
        hits += int(hit); citation_hits += int(top_correct); relevance_hits += int(relevant)
        rows.append({"question": case["question"], "retrieved_pages": pages, "hit": hit, "top_citation_correct": top_correct})
    count = len(cases)
    return {
        "cases": count, "retrieval_hit_at_3": round(hits / count, 3),
        "top_citation_accuracy": round(citation_hits / count, 3),
        "answer_criteria_pass_rate": round(relevance_hits / count, 3),
        "median_retrieval_latency_ms": round(statistics.median(latencies), 3), "details": rows,
        "note": "Small deterministic smoke benchmark; not a claim of general RAG quality.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

