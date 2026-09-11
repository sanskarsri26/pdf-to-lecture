from backend.tts_utils import _prepare_speech_text


def test_prepare_speech_text_expands_common_math_notation():
    text = "A⁻¹ works for a 2x2 matrix, and αA = βB."

    prepared = _prepare_speech_text(text)

    assert "A inverse" in prepared
    assert "2 by 2" in prepared
    assert "alpha" in prepared
    assert "beta" in prepared
    assert "equals" in prepared
