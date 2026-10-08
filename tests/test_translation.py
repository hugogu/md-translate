"""Unit tests for Markdown structure protection and translation reconstruction."""

from md_translate.protector import MarkdownProtector, parse_and_process_lines
from md_translate.core import translate_markdown

SAMPLE_COMPLEX_MARKDOWN = """# Introduction to Machine Learning

> A quick overview of neural networks.

Here is an inline math formula: $E = mc^2$ and inline code: `pip install torch`.

Check this image: ![Architecture](https://example.com/arch.png) and link: [Documentation](https://pytorch.org).

## Formula Section
$$
\\mathcal{L}_{\\theta} = \\frac{1}{N} \\sum_{i=1}^N (y_i - \\hat{y}_i)^2
$$

## Code Example
```python
def train_step(x, y):
    # Do not translate code comments inside code fence
    loss = (x - y) ** 2
    return loss
```

## Comparison Table
| Metric | Baseline | Ours | Description |
| :--- | :--- | :--- | :--- |
| Accuracy | 85.2% | **92.4%** | Higher is better |
| Latency | 45ms | `12ms` | Measured on M2 Max |

End of the document.
"""

def dummy_translate(text: str) -> str:
    """Mock translation function appending [ZH]."""
    return f"[ZH]{text}"

def test_markdown_protector_integrity():
    protector = MarkdownProtector()
    doc = protector.protect_document(SAMPLE_COMPLEX_MARKDOWN)

    # Ensure code blocks, display math, and images are protected
    assert "def train_step" not in doc
    assert "\\mathcal{L}_{\\theta}" not in doc
    assert "https://example.com/arch.png" not in doc

    # Restore and verify complete match
    restored = protector.restore(doc)
    assert restored == SAMPLE_COMPLEX_MARKDOWN

def test_full_pipeline_with_echo_engine():
    result = translate_markdown(
        SAMPLE_COMPLEX_MARKDOWN,
        translator="echo",
        src_lang="en",
        tgt_lang="zh"
    )

    # 1. Formulas and Code blocks must stay completely intact
    assert "def train_step(x, y):" in result
    assert "# Do not translate code comments inside code fence" in result
    assert "\\mathcal{L}_{\\theta} = \\frac{1}{N} \\sum_{i=1}^N (y_i - \\hat{y}_i)^2" in result
    assert "$E = mc^2$" in result
    assert "`pip install torch`" in result

    # 2. Images and Links must preserve URLs
    assert "![Architecture](https://example.com/arch.png)" in result
    assert "(https://pytorch.org)" in result

    # 3. Table pipes and alignments must be preserved
    assert "| [ECHO:zh]  Metric |" in result
    assert "| :--- | :--- | :--- | :--- |" in result
    assert "`12ms`" in result

    # 4. Prose was processed
    assert "[ECHO:zh]" in result
