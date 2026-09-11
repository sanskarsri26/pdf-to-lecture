from backend.chunking import chunk_text


def test_chunk_text_respects_max_words_for_plain_text():
    text = " ".join(f"word{i}" for i in range(25))

    chunks = chunk_text(text, max_words=10)

    assert len(chunks) == 3
    assert all(len(chunk.split()) <= 10 for chunk in chunks)


def test_chunk_text_keeps_paragraphs_when_possible():
    text = "First paragraph has a few words.\n\nSecond paragraph stays together."

    chunks = chunk_text(text, max_words=20)

    assert chunks == [text]
