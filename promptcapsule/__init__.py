"""PromptCapsule: Open-source prompt compression & retrieval library."""

from .core import PromptCapsule, CapsuleResult
from .integrity import IntegrityChecker

__version__ = "0.1.0"
__author__ = "Udaya Nirogi"
__all__ = ["PromptCapsule", "CapsuleResult", "IntegrityChecker"]
