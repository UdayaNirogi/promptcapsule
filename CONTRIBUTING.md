# Contributing to PromptCapsule

Thank you for your interest in contributing to PromptCapsule! We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code contributions.

## Getting Started

### Prerequisites
- Python 3.8+
- pip
- git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/UdayaNirogi/promptcapsule.git
   cd promptcapsule
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify setup**
   ```bash
   pytest
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run one module
pytest tests/test_simple.py -v

# Run with coverage
pytest tests/ --cov=promptcapsule --cov-report=html
```

Tests never touch your real `~/.promptcapsule` vault: `tests/conftest.py` points `PROMPT_CAPSULE_VAULT` at a temporary file.

### Code Style

CI runs these checks; run all of them together before committing:

```bash
pip install ruff "black==25.11.0" isort
isort promptcapsule/ tests/ && black promptcapsule/ tests/ && ruff check --fix promptcapsule/ tests/
ruff check promptcapsule/ tests/ && black --check promptcapsule/ tests/ && isort --check-only promptcapsule/ tests/
```

### The capsule format is frozen

[SPEC.md](SPEC.md) is a compatibility promise: every capsule ever produced must keep decoding. If a change makes `tests/test_format_v1.py` fail, fix the change, never the test vectors. A genuinely new format needs a new type letter and a spec update.

### Writing Tests

1. **Tests are required** for new features
2. **Place tests** in `tests/test_*.py`
3. **Use clear names**: `test_<feature>_<scenario>`
4. **Include docstrings**: Explain what you're testing
5. **Test edge cases**: Empty input, unicode, null bytes, etc.

Example:

```python
from promptcapsule import pack, unpack


def test_unicode_prompt_roundtrip():
    """Unicode text comes back byte-for-byte identical."""
    prompt = "Hello 世界 🌍"
    assert unpack(pack(prompt)) == prompt
```

## Submitting Changes

### For Bug Reports

Please include:
- Python version
- PromptCapsule version
- Steps to reproduce
- Expected vs. actual behavior
- Full error traceback

### For Feature Requests

Please include:
- Use case: why do you need this?
- How would you use it?
- Alternative approaches you've considered

### For Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Write tests first** (TDD preferred)
4. **Implement the feature**
5. **Run all tests and checks**: `pytest` plus the lint commands above
6. **Update README** if needed
7. **Commit with clear messages**: `git commit -m "Add: feature description"`
8. **Push and open a Pull Request**

## PR Guidelines

- **Small, focused PRs**: One feature per PR
- **Clear commit messages**: `Fix: ...`, `Add: ...`, `Docs: ...`
- **All tests must pass**
- **No external dependencies** for core functionality
- **Update docs** if adding/changing public API
- **Request review** from maintainers

## Code Organization

```
promptcapsule/
├── __init__.py          # Public API
├── simple.py            # pack() / unpack() and the default vault
├── core.py              # PromptCapsule class, capsule encoding and decoding
├── backends.py          # Vault backends (in-memory, SQLite, Gist, S3)
├── integrity.py         # Checksums and HMAC signatures
├── exceptions.py        # Error types
└── cli.py               # Command-line tool

tests/
├── conftest.py          # Fixtures (isolated default vault)
├── test_simple.py       # pack() / unpack()
├── test_format_v1.py    # Frozen format test vectors (SPEC.md)
├── test_core.py         # PromptCapsule class
├── test_signatures.py   # HMAC signing
├── test_security.py     # Security regressions
├── test_backends.py     # Vault backends
├── test_cli.py          # Command-line tool
└── test_integration.py  # End-to-end scenarios
```

## Areas We Need Help With

- [ ] **Web UI** for managing vaults
- [ ] **Async support** for backends
- [ ] **More backends**: DynamoDB, PostgreSQL, etc.
- [ ] **API documentation** in Markdown
- [ ] **Blog posts** about use cases
- [ ] **Example projects** using PromptCapsule

## Questions?

- 📖 Check existing [Issues](https://github.com/UdayaNirogi/promptcapsule/issues)
- 💬 Start a [Discussion](https://github.com/UdayaNirogi/promptcapsule/discussions)
- 📧 Email: data.pycap@gmail.com

---

## Acknowledgments

Thank you for contributing! Every contribution, no matter how small, helps make PromptCapsule better. ❤️
