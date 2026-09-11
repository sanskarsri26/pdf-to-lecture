import io
import time

import fitz
from fastapi.testclient import TestClient

from backend.main import app, learning
from backend.storage import Store


def make_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Neural Networks\nA neural network learns weights from training examples. Backpropagation computes gradients used to update those weights.")
    value = document.tobytes()
    document.close()
    return value


def test_document_ingestion_and_grounded_ask(tmp_path, monkeypatch):
    test_store = Store(tmp_path / "api.db")
    monkeypatch.setattr("backend.main.store", test_store)
    monkeypatch.setattr("backend.main.learning", type(learning)(test_store))
    client = TestClient(app)

    response = client.post("/documents", files={"file": ("lesson.pdf", io.BytesIO(make_pdf()), "application/pdf")})
    assert response.status_code == 202
    document = response.json()

    for _ in range(50):
        document = client.get(f"/documents/{document['id']}/status").json()
        if document["status"] in {"COMPLETED", "FAILED"}:
            break
        time.sleep(0.02)

    assert document["status"] == "COMPLETED"
    answer = client.post(f"/documents/{document['id']}/ask", json={"question": "What does backpropagation compute?"})
    assert answer.status_code == 200
    assert answer.json()["citations"][0]["page"] == 1


def test_upload_rejects_fake_pdf():
    response = TestClient(app).post(
        "/documents", files={"file": ("fake.pdf", io.BytesIO(b"not a pdf"), "application/pdf")}
    )
    assert response.status_code == 400

