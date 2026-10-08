"""Echo / Mock and LLM (OpenAI/Anthropic compatible) translators."""

import os
from .base import BaseTranslator, register_translator

@register_translator("echo")
class EchoTranslator(BaseTranslator):
    """Echo translator for offline testing, formatting verification, and CI dry-runs."""

    def translate(self, text: str) -> str:
        return f"[ECHO:{self.tgt_lang}] {text}"


@register_translator("openai")
class OpenAITranslator(BaseTranslator):
    """OpenAI / Compatible API (Ollama, vLLM, DeepSeek) translator."""

    def __init__(self, src_lang: str = "en", tgt_lang: str = "zh", **kwargs):
        super().__init__(src_lang, tgt_lang, **kwargs)
        self.api_key = kwargs.get("api_key", os.environ.get("OPENAI_API_KEY", ""))
        self.api_base = kwargs.get("api_base", os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
        self.model = kwargs.get("model", os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))

    def translate(self, text: str) -> str:
        if not text.strip():
            return text
        import requests

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        prompt = (
            f"You are a professional technical translator. Translate the following text from {self.src_lang} to {self.tgt_lang}.\n"
            "CRITICAL: Preserve any sentinel tokens like \u2063PROTECT_x\u2063 EXACTLY as they are. Output only the translation without commentary."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.1,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
