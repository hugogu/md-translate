# Contributing to md-translate

Thank you for your interest in contributing to **md-translate**! We welcome bug reports, feature requests, translation engine adapters, and documentation improvements.

---

## 🛠️ Development Setup

We recommend using [`uv`](https://github.com/astral-sh/uv) for fast and deterministic local development:

```bash
# 1. Fork and clone the repository
git clone https://github.com/hugogu/md-translate.git
cd md-translate

# 2. Create virtual environment
uv venv
source .venv/bin/activate

# 3. Install in editable mode with development dependencies
uv pip install -e ".[all,dev]"
```

---

## 🧪 Running Tests

Before submitting a Pull Request, please ensure all unit tests pass:

```bash
# Run standalone verification test suite
python3 -c "import sys; sys.path.insert(0, 'src'); from tests.test_translation import test_markdown_protector_integrity, test_full_pipeline_with_echo_engine; test_markdown_protector_integrity(); test_full_pipeline_with_echo_engine(); print('ALL TESTS PASS')"
```

---

## 📐 Guidelines

1. **Markdown & LaTeX Integrity**: Any change touching `protector.py` must ensure zero degradation to LaTeX formulas, code fences, table alignment, or Markdown links.
2. **Zero-Copy MCP Contract**: When improving the MCP server, ensure file paths remain the primary communication medium to prevent token leaks into Agent context windows.
3. **Hardware Compatibility**: Use device fallbacks (`mps` -> `cuda` -> `cpu`) so code runs seamlessly across Mac and Linux/Windows environments.

---

## 📄 Pull Request Process

1. Create a descriptive feature branch: `git checkout -b feat/your-feature-name`.
2. Commit your changes with clear messages: `git commit -m "feat: add support for custom glossaries"`.
3. Push to your fork and submit a Pull Request to `main`.
