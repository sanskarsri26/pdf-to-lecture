from backend.pdf_utils import _env_flag, _env_int, _pages_needing_ocr, clean_pdf_text


def test_clean_pdf_text_joins_hyphenated_line_breaks():
    assert clean_pdf_text("photo-\nsynthesis") == "photosynthesis"


def test_pages_needing_ocr_uses_min_text_chars():
    pages = ["", "short", "This page has enough embedded text."]

    assert _pages_needing_ocr(pages, min_text_chars=10) == [0, 1]


def test_env_flag_accepts_false_values(monkeypatch):
    monkeypatch.setenv("ENABLE_OCR", "false")

    assert _env_flag("ENABLE_OCR", default=True) is False


def test_env_int_falls_back_for_invalid_value(monkeypatch):
    monkeypatch.setenv("OCR_DPI", "not-a-number")

    assert _env_int("OCR_DPI", default=200) == 200
