from backend.retrieval import cosine, embed, retrieve


def test_embedding_is_normalized_and_deterministic():
    first = embed("gradient descent minimizes a loss function")
    second = embed("gradient descent minimizes a loss function")

    assert first == second
    assert abs(cosine(first, first) - 1.0) < 0.0001


def test_retrieval_returns_relevant_chunk_first():
    chunks = [
        {"text": "Photosynthesis converts light energy into chemical energy.", "vector": embed("Photosynthesis converts light energy into chemical energy."), "page": 2, "section": "Plants", "chunk_index": 0},
        {"text": "A compiler translates source code into machine instructions.", "vector": embed("A compiler translates source code into machine instructions."), "page": 5, "section": "Software", "chunk_index": 1},
    ]

    result = retrieve(chunks, "How does a compiler translate code?", top_k=1, threshold=0)

    assert result[0]["page"] == 5


def test_retrieval_can_reject_unsupported_question():
    chunks = [{"text": "Plants use sunlight.", "vector": embed("Plants use sunlight."), "page": 1, "section": "Plants", "chunk_index": 0}]

    assert retrieve(chunks, "quantum chromodynamics", threshold=0.2) == []

