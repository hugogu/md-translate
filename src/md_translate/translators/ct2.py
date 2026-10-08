"""CTranslate2 Translator backend for ultra-fast quantized local translation."""

import os
from .base import BaseTranslator, register_translator
from .nllb import NLLB_CODE_MAP

@register_translator("ct2")
class CTranslate2Translator(BaseTranslator):
    """Ultra-fast local CPU/GPU execution via CTranslate2."""

    def __init__(self, src_lang: str = "en", tgt_lang: str = "zh", **kwargs):
        super().__init__(src_lang, tgt_lang, **kwargs)
        self.src_nllb = NLLB_CODE_MAP.get(src_lang.lower(), src_lang)
        self.tgt_nllb = NLLB_CODE_MAP.get(tgt_lang.lower(), tgt_lang)
        self.model_path = kwargs.get("model", os.environ.get("CT2_MODEL_PATH", "OpenNMT/nllb-200-distilled-600M-ct2"))
        self._translator = None
        self._tokenizer = None

    def warm_up(self):
        if self._translator is None:
            import ctranslate2
            import transformers
            from huggingface_hub import snapshot_download

            # If model is on HuggingFace Hub, ensure it's downloaded
            local_dir = self.model_path
            if not os.path.isdir(local_dir):
                local_dir = snapshot_download(repo_id=self.model_path)

            compute_type = self.kwargs.get("compute_type", "int8")
            self._translator = ctranslate2.Translator(local_dir, device="cpu", compute_type=compute_type)
            self._tokenizer = transformers.AutoTokenizer.from_pretrained(
                "facebook/nllb-200-distilled-600M",
                src_lang=self.src_nllb
            )

    def translate(self, text: str) -> str:
        if not text.strip():
            return text
        self.warm_up()

        tokens = self._tokenizer.convert_ids_to_tokens(self._tokenizer.encode(text))
        results = self._translator.translate_batch([tokens], target_prefix=[[self.tgt_nllb]])
        target_tokens = results[0].hypotheses[0][1:]
        return self._tokenizer.decode(self._tokenizer.convert_tokens_to_ids(target_tokens))
