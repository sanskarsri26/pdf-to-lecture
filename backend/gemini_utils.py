import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from dotenv import load_dotenv


class GeminiUnavailableError(Exception):
    """Raised when Gemini is not configured or cannot be called."""


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None,
                 metrics_sink: Optional[Callable[..., None]] = None):
        load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._model = None
        self._load_error: Optional[str] = None
        self.metrics_sink = metrics_sink

        if not self.api_key:
            self._load_error = "GEMINI_API_KEY is not set."
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        except Exception as exc:
            self._load_error = str(exc)

    @property
    def available(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def generate_text(self, prompt: str, temperature: float = 0.45) -> str:
        if not self._model:
            raise GeminiUnavailableError(self._load_error or "Gemini is unavailable.")

        started = time.perf_counter()
        try:
            response = self._model.generate_content(
                prompt,
                generation_config={"temperature": temperature},
            )
            text = getattr(response, "text", None)
            if not text:
                raise GeminiUnavailableError("Gemini returned an empty response.")
            usage = getattr(response, "usage_metadata", None)
            prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
            completion_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
            self._record(started, prompt_tokens, completion_tokens, True)
            return text.strip()
        except Exception as exc:
            self._record(started, 0, 0, False, {"error": type(exc).__name__})
            raise GeminiUnavailableError(f"Gemini request failed: {exc}") from exc

    def _record(self, started: float, prompt_tokens: int, completion_tokens: int,
                success: bool, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not self.metrics_sink:
            return
        input_rate = float(os.getenv("GEMINI_INPUT_USD_PER_MILLION", "0"))
        output_rate = float(os.getenv("GEMINI_OUTPUT_USD_PER_MILLION", "0"))
        cost = (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000
        self.metrics_sink(
            operation="llm_generate", model=self.model_name,
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            estimated_cost_usd=cost, success=success, metadata=metadata,
        )
