import asyncio
import os
import re
from pathlib import Path
from typing import Optional


class TTSGenerationError(Exception):
    """Raised when text-to-speech generation fails."""


class TTSGenerator:
    def __init__(self, audio_root: Path, enabled: Optional[bool] = None):
        self.audio_root = audio_root
        self.enabled = (
            enabled
            if enabled is not None
            else os.getenv("ENABLE_TTS", "true").lower() not in {"0", "false", "no"}
        )
        self.provider = os.getenv("TTS_PROVIDER", "edge").lower()
        self.voice = os.getenv("TTS_VOICE", "en-US-GuyNeural")
        self.rate = os.getenv("TTS_RATE", "-6%")
        self.pitch = os.getenv("TTS_PITCH", "-2Hz")
        self.language = os.getenv("TTS_LANG", "en")

    def synthesize(self, script: str, lecture_id: str, slide_number: int) -> Optional[str]:
        if not self.enabled:
            return None

        lecture_dir = self.audio_root / lecture_id
        lecture_dir.mkdir(parents=True, exist_ok=True)
        filename = f"slide_{slide_number}.mp3"
        output_path = lecture_dir / filename
        speech_text = _prepare_speech_text(script)

        try:
            if self.provider == "edge":
                self._synthesize_with_edge(speech_text, output_path)
            else:
                self._synthesize_with_gtts(speech_text, output_path)
            return f"/audio/{lecture_id}/{filename}"
        except Exception as exc:
            if self.provider == "edge":
                try:
                    self._synthesize_with_gtts(speech_text, output_path)
                    return f"/audio/{lecture_id}/{filename}"
                except Exception:
                    pass
            raise TTSGenerationError(f"Could not generate audio: {exc}") from exc

    def _synthesize_with_edge(self, text: str, output_path: Path) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch,
        )
        asyncio.run(communicate.save(str(output_path)))

    def _synthesize_with_gtts(self, text: str, output_path: Path) -> None:
        from gtts import gTTS

        gTTS(text=text, lang=self.language, slow=False).save(str(output_path))


def _prepare_speech_text(text: str) -> str:
    replacements = {
        "α": "alpha",
        "β": "beta",
        "⁻¹": " inverse",
        "−": " minus ",
        "×": " by ",
        "·": " times ",
    }

    prepared = text
    for source, target in replacements.items():
        prepared = prepared.replace(source, target)

    prepared = re.sub(r"\b(\d+)\s*x\s*(\d+)\b", r"\1 by \2", prepared, flags=re.IGNORECASE)
    prepared = re.sub(r"\b([A-Z])\s*\^\s*k\b", r"\1 to the k", prepared)
    prepared = re.sub(r"\b([A-Z])\s*\^\s*-?1\b", r"\1 inverse", prepared)
    prepared = re.sub(r"\s=\s", " equals ", prepared)
    prepared = re.sub(r"\s+", " ", prepared)
    return prepared.strip()
