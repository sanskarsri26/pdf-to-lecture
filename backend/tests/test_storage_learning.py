from backend.learning import LearningService
from backend.retrieval import embed
from backend.storage import Store


def test_learning_artifacts_are_grounded_and_cached(tmp_path):
    store = Store(tmp_path / "test.db")
    store.create_document("a" * 32, "biology.pdf", "hash")
    store.replace_chunks("a" * 32, [
        {"chunk_index": 0, "page": 3, "section": "Cell Biology", "text": "Mitochondria produce ATP through cellular respiration. ATP stores chemical energy for the cell.", "vector": embed("Mitochondria produce ATP through cellular respiration.")}
    ])
    service = LearningService(store)

    lecture = service.lecture("a" * 32)
    answer = service.ask("a" * 32, "What produces ATP?", 3, 0.01)

    assert lecture.sections[0].citations[0].page == 3
    assert answer["grounded"] is True
    assert answer["citations"][0].page == 3
    assert store.get_artifact("a" * 32, "lecture") is not None

