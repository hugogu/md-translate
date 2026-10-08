"""Model Context Protocol (MCP) Server for md-translate.

Provides Zero-Copy, Claim-Check file translation capabilities to Agents
so large Markdown documents do not penetrate or consume the LLM context window.
"""

import sys
from pathlib import Path
from .core import translate_file
from .translators.base import _TRANSLATOR_REGISTRY

def main():
    try:
        try:
            # mcp 2.x API
            from mcp.server.mcpserver import MCPServer as FastMCP
        except ImportError:
            # mcp 1.x API
            from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "Error: 'mcp' package is required to run the MCP server.\n"
            "Install it via: pip install 'md-translate-mcp[mcp]'",
            file=sys.stderr
        )
        sys.exit(1)

    mcp = FastMCP("Markdown-Translator-MCP")

    @mcp.tool()
    def translate_markdown_file(
        input_file_path: str,
        output_file_path: str,
        engine: str = "nllb",
        src_lang: str = "en",
        tgt_lang: str = "zh",
    ) -> str:
        """Translate a Markdown file while strictly protecting formulas, code blocks, tables, and URLs.

        Designed for Zero-Copy / Claim-Check pipelines: large content remains in local storage,
        consuming negligible Agent tokens.

        :param input_file_path: Absolute or relative path to the input Markdown file.
        :param output_file_path: Absolute or relative path to save the translated Markdown file.
        :param engine: Translation backend: 'nllb', 'ct2', 'openai', 'echo'. Default: 'nllb'.
        :param src_lang: Source language code (e.g., 'en', 'ja', 'fr'). Default: 'en'.
        :param tgt_lang: Target language code (e.g., 'zh', 'en', 'es'). Default: 'zh'.
        :return: Execution summary and file size statistics.
        """
        in_p = Path(input_file_path)
        out_p = Path(output_file_path)

        if not in_p.is_file():
            return f"Error: Input file does not exist: {input_file_path}"

        try:
            translate_file(
                input_path=in_p,
                output_path=out_p,
                translator=engine,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
            )
            size_kb = out_p.stat().st_size / 1024
            return (
                f"SUCCESS: Translated '{in_p.name}' -> '{out_p.name}' using engine '{engine}' "
                f"({src_lang} -> {tgt_lang}). Output size: {size_kb:.2f} KB."
            )
        except Exception as e:
            return f"Error translating file: {str(e)}"

    @mcp.tool()
    def get_supported_engines() -> dict:
        """Returns the list of available translation backends and their hardware acceleration."""
        return {
            "nllb": "PyTorch NLLB-200 with Apple Silicon Metal (MPS) and CUDA acceleration",
            "ct2": "CTranslate2 INT8 quantized translation (Ultra-fast CPU/CUDA)",
            "openai": "OpenAI / compatible API (e.g. Ollama, vLLM, DeepSeek)",
            "echo": "Fast test engine for pipeline verification without downloading weights",
        }

    mcp.run()

if __name__ == "__main__":
    main()
