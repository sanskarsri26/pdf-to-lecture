from backend.slide_generator import _extract_json, _fallback_slide


def test_extract_json_from_code_fence():
    raw = '```json\n{"title": "Topic", "bullets": ["A", "B"]}\n```'

    parsed = _extract_json(raw)

    assert parsed["title"] == "Topic"
    assert parsed["bullets"] == ["A", "B"]


def test_fallback_slide_limits_bullets():
    title, bullets = _fallback_slide(
        "This is the opening concept. Second idea matters. Third idea matters. "
        "Fourth idea matters. Fifth idea matters. Sixth idea should not appear."
    )

    assert title
    assert len(bullets) == 5
