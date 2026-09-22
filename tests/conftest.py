"""Conftest for pytest - shared fixtures."""

import pytest
import tempfile
import os


@pytest.fixture
def temp_db():
    """Fixture providing a temporary SQLite database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path


@pytest.fixture
def sample_prompts():
    """Fixture providing various sample prompts for testing."""
    return {
        "short": "This is a short test prompt.",
        "medium": "This is a medium length prompt. " * 10,
        "long": "This is a long prompt. " * 50,
        "unicode": "Unicode test: 你好世界 🌍 مرحبا",
        "multiline": """
            This is a multiline prompt.
            
            With multiple paragraphs.
            
            And special characters: !@#$%^&*()
        """,
        "empty_lines": "Text\n\n\nwith\n\nmultiple\nempty\nlines",
    }
