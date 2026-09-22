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
   python run_tests.py
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test module (requires pytest)
pytest tests/test_core.py -v

# Run with coverage
pytest tests/ --cov=promptcapsule --cov-report=html
```

### Code Style

We follow PEP 8. Before submitting, run:

```bash
# Format code
black promptcapsule/ tests/

# Check for style issues
flake8 promptcapsule/ tests/

# Type checking
mypy promptcapsule/
```

### Writing Tests

1. **Tests are required** for new features
2. **Place tests** in `tests/test_*.py`
3. **Use clear names**: `test_<feature>_<scenario>`
4. **Include docstrings**: Explain what you're testing
5. **Test edge cases**: Empty input, unicode, null bytes, etc.

Example:

```python
def test_unicode_prompt_compression():
    """Test that unicode characters are preserved through compression."""
    pc = PromptCapsule()
    prompt = "Hello 世界 🌍"
    capsule = pc.compress(prompt)
    result = pc.decompress(capsule)
    
    assert result.text == prompt
    assert result.verified is True
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
5. **Run all tests**: `python run_tests.py`
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
├── core.py              # Main PromptCapsule class
├── backends.py          # Storage backends
├── integrity.py         # Checksum verification
└── cli.py               # (future) Command-line tool

tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── test_core.py         # Core functionality
├── test_backends.py     # Backend tests
├── test_integrity.py    # Integrity checker tests
└── test_integration.py  # End-to-end scenarios
```

## Areas We Need Help With

- [ ] **CLI tool** (`promptcapsule compress`, `promptcapsule decompress`)
- [ ] **Web UI** for managing vaults
- [ ] **Async support** for backends
- [ ] **More backends**: DynamoDB, PostgreSQL, etc.
- [ ] **Performance benchmarks**
- [ ] **API documentation** in Markdown
- [ ] **Blog posts** about use cases
- [ ] **Example projects** using PromptCapsule

## Questions?

- 📖 Check existing [Issues](https://github.com/UdayaNirogi/promptcapsule/issues)
- 💬 Start a [Discussion](https://github.com/UdayaNirogi/promptcapsule/discussions)
- 📧 Email: udaya@example.com

---

## Acknowledgments

Thank you for contributing! Every contribution, no matter how small, helps make PromptCapsule better. ❤️
