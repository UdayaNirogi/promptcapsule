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
from .simple import default_vault_path, pack, unpack

__version__ = "0.2.1.1"
__author__ = "Udaya Nirogi"
__all__ = [
    "CapsuleResult",
    "FormatError",
    "GitHubGistBackend",
    # Backends
    "InMemoryBackend",
    # Utilities
    "IntegrityChecker",
    "IntegrityError",
    "PromptCapsule",
    # Exceptions
    "PromptCapsuleError",
    "S3Backend",
    "SQLiteBackend",
    "SignatureError",
    "SizeLimitError",
    "VaultError",
    # Two-function API
    "default_vault_path",
    "pack",
    "unpack",
]
