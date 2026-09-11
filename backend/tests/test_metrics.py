from backend.gemini_utils import GeminiClient


def test_gemini_cost_uses_configured_token_rates(monkeypatch):
    captured = {}
    monkeypatch.setenv("GEMINI_INPUT_USD_PER_MILLION", "2")
    monkeypatch.setenv("GEMINI_OUTPUT_USD_PER_MILLION", "8")
    client = GeminiClient(api_key="", metrics_sink=lambda **values: captured.update(values))

    client._record(0, prompt_tokens=1_000_000, completion_tokens=500_000, success=True)

    assert captured["estimated_cost_usd"] == 6
    assert captured["prompt_tokens"] == 1_000_000
