"""PromptCapsule: lossless prompt capsules for sharing and agent-to-agent handoff."""

from .backends import GitHubGistBackend, InMemoryBackend, S3Backend, SQLiteBackend
from .core import CapsuleResult, PromptCapsule
from .exceptions import (
    FormatError,
    IntegrityError,
    PromptCapsuleError,
    SignatureError,
    SizeLimitError,
    VaultError,
)
from .integrity import IntegrityChecker

__version__ = "0.1.7"
__author__ = "Udaya Nirogi"
__all__ = [
    "PromptCapsule",
    "CapsuleResult",
    # Exceptions
    "PromptCapsuleError",
    "IntegrityError",
    "FormatError",
    "VaultError",
    "SizeLimitError",
    "SignatureError",
    # Utilities
    "IntegrityChecker",
    # Backends
    "InMemoryBackend",
    "SQLiteBackend",
    "GitHubGistBackend",
    "S3Backend",
]
