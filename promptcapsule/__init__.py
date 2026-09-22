"""PromptCapsule: lossless prompt capsules for sharing and agent-to-agent handoff."""

from .core import CapsuleResult, IntegrityError, PromptCapsule
from .integrity import IntegrityChecker

__version__ = "0.1.2"
__author__ = "Udaya Nirogi"
__all__ = ["PromptCapsule", "CapsuleResult", "IntegrityChecker", "IntegrityError"]
