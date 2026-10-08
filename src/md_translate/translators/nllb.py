"""NLLB Translator using PyTorch with Apple Silicon (MPS) & CUDA acceleration."""

import os
from .base import BaseTranslator, register_translator

# Mapping common 2-letter codes to NLLB FLORES-200 codes
NLLB_CODE_MAP = {
    "en": "eng_Latn",
    "zh": "zho_Hans",
    "zh-cn": "zho_Hans",
    "zh-tw": "zho_Hant",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "es": "spa_Latn",
    "ru": "rus_Cyrl",
}

@register_translator("nllb")
class NLLBTranslator(BaseTranslator):
    """Local NLLB translation backend optimized for Apple Silicon (Metal/MPS)."""

    def __init__(self, src_lang: str = "en", tgt_lang: str = "zh", **kwargs):
        super().__init__(src_lang, tgt_lang, **kwargs)
        self.src_nllb = NLLB_CODE_MAP.get(src_lang.lower(), src_lang)
        self.tgt_nllb = NLLB_CODE_MAP.get(tgt_lang.lower(), tgt_lang)
        self.model_name = kwargs.get("model", os.environ.get("NLLB_MODEL", "facebook/nllb-200-distilled-600M"))
        self._pipe = None

    def warm_up(self):
        if self._pipe is None:
            import torch
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

            device = "cpu"
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"

            dtype = torch.float16 if device in ("mps", "cuda") else torch.float32

            tokenizer = AutoTokenizer.from_pretrained(self.model_name, src_lang=self.src_nllb)
            model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, torch_dtype=dtype).to(device)
            model.eval()

            self._device = device
            self._tokenizer = tokenizer
            self._model = model
            self._target_id = tokenizer.lang_code_to_id.get(self.tgt_nllb)

    def translate(self, text: str) -> str:
        if not text.strip():
            return text
        self.warm_up()

        import torch
        inputs = self._tokenizer(text, return_tensors="pt", max_length=512, truncation=True).to(self._device)
        with torch.no_grad():
            generated_tokens = self._model.generate(
                **inputs,
                forced_bos_token_id=self._target_id,
                max_length=512,
            )
        decoded = self._tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        return decoded
