# md-translate

> Production-grade, zero-leak Markdown translation engine designed for **CLI, CI/CD, and Autonomous AI Agents (MCP)**.
> Inspired by the architecture of [PDFMathTranslate](https://github.com/PDFMathTranslate/PDFMathTranslate).

---

## 🌟 Key Features

1. **Strict Markdown & LaTeX Protection**:
   - **Formulas preserved**: `$...$` (inline math) and `$$...$$` (display math) are shielded.
   - **Code & Syntax**: Fenced code blocks (```` ``` ````), inline code (`` ` ``), and image syntax are untouched.
   - **Tables intact**: Cell borders (`|`), dividers, and alignments remain 100% valid CommonMark.
2. **Local Hardware Acceleration (Apple Silicon / CUDA)**:
   - Built-in support for **Apple Silicon Metal (MPS)** on Mac M2/M3/M4 Max chips.
   - Powered by Meta's open-source `facebook/nllb-200-distilled-600M` and `CTranslate2` (INT8 quantized).
   - Zero API subscription fees, 100% offline and confidential.
3. **Zero-Copy / Claim-Check Architecture for AI Agents (MCP)**:
   - Provides a native **Model Context Protocol (MCP)** server.
   - AI Agents only exchange file handles (`input_path` $\rightarrow$ `output_path`), meaning **no large Markdown texts pollute the LLM's context window**, saving 99% of prompt tokens.
4. **Multi-Interface Usability**:
   - **Python Library**: Clean API for scripts and microservices.
   - **Command Line (CLI)**: Single files or batch directory translation with recursive scanning.
   - **CI/CD Integration**: Ready for automated GitHub Actions documentation sync.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/hugogu/md-translate.git
cd md-translate

# Install core CLI
pip install -e .

# Install with Local Hardware Acceleration (PyTorch + MPS/CUDA)
pip install -e ".[nllb]"

# Install with MCP Server support
pip install -e ".[mcp]"

# Or install everything
pip install -e ".[all]"
```

---

## 🛠️ Usage

### 1. Command-Line (CLI)

#### Translate a single Markdown file:
```bash
# Translates README.md to README.zh.md using local NLLB model
md-translate README.md -o README.zh.md --from en --to zh
```

#### Batch translate an entire docs directory:
```bash
md-translate ./docs -o ./docs_zh --from en --to zh --recursive
```

#### Dry-run / Offline test (without downloading model weights):
```bash
md-translate README.md -o README.test.md --engine echo
```

---

### 2. Model Context Protocol (MCP) for AI Agents

`md-translate` exposes a standard MCP server for Claude Desktop, Cursor, Roo-Code, or any MCP-compatible Agent runtime.

#### Configure in Claude Desktop / Agent (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "md-translate": {
      "command": "python3",
      "args": ["-m", "md_translate.mcp_server"]
    }
  }
}
```

#### How the Agent interacts with it (Zero Token Waste):
```
Agent: translate_markdown_file(
  input_file_path="/tmp/kb/architecture.md",
  output_file_path="/tmp/kb/architecture_zh.md",
  engine="nllb",
  src_lang="en",
  tgt_lang="zh"
)
```
> The entire document is processed on your **Mac M2 GPU** and saved directly to the file system. The agent only receives the status and file size summary, ensuring massive knowledge bases can be migrated seamlessly.

---

### 3. Python API

```python
from md_translate import translate_markdown, translate_file

# Translate in-memory string
markdown_text = "# Machine Learning\n\nLoss formula: $L = (y - \\hat{y})^2$"
translated = translate_markdown(markdown_text, translator="nllb", src_lang="en", tgt_lang="zh")
print(translated)

# Translate files
translate_file("input.md", "output.md", translator="nllb", src_lang="en", tgt_lang="zh")
```

---

## 🏛️ Architecture

```
                          ┌────────────────────────┐
                          │   Raw Markdown Document│
                          └───────────┬────────────┘
                                      │
                         [MarkdownProtector]
                 (Extract Math, Code, Tables, URLs)
                                      │
                     ┌────────────────┴───────────────┐
                     │                                │
             Protected Sentinels               Pure Prose Slices
             (U+2063 Shields)                  (Sentence Split)
                     │                                │
                     │                 [Translation Engine]
                     │                 (NLLB on M2 MPS / CT2 / LLM)
                     │                                │
                     └────────────────┬───────────────┘
                                      │
                             [Restore & Assemble]
                                      │
                          ┌───────────▼────────────┐
                          │ Well-Formed Markdown   │
                          └────────────────────────┘
```

---

## 📄 License

MIT License. Free forever for personal and commercial use.
