from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .gemini_utils import GeminiClient
from .retrieval import embed


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        raise NotImplementedError

    def embed(self, text: str):
        return embed(text)


class GeminiProvider(LLMProvider):
    def __init__(self, client: Optional[GeminiClient] = None):
        self.client = client or GeminiClient()
        self.model_name = self.client.model_name

    @property
    def available(self) -> bool:
        return self.client.available

    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        return self.client.generate_text(prompt, temperature=temperature)

