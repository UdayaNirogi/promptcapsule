"""Exception hierarchy for PromptCapsule.

Clear, typed exceptions make debugging easier and allow callers
to handle different failure modes appropriately.
"""


class PromptCapsuleError(Exception):
    """Base exception for all PromptCapsule errors."""


class IntegrityError(PromptCapsuleError, ValueError):
    """
    Raised when capsule integrity verification fails.

    This is the fail-closed signal: the capsule was corrupted or altered and
    does not match its checksum or signature. The unsigned checksum is not
    keyed, so it catches accidental corruption; only a signature verified with
    the key catches deliberate tampering.

    In strict=True mode (default), decompression raises this immediately.
    Callers should treat this as "unsafe to use" and never fall back to
    the returned text.
    """


class FormatError(PromptCapsuleError, ValueError):
    """
    Raised when a capsule string has invalid format.

    Examples:
    - Missing or malformed prefix (cap_i_, cap_v_)
    - Invalid Base85 encoding or zlib data
    - Empty payload or vault key

    A malformed checksum prefix raises IntegrityError, not FormatError.
    """


class VaultError(PromptCapsuleError):
    """
    Raised when vault backend operations fail.

    Examples:
    - Key not found in vault
    - Network/auth failure reaching remote vault (S3, Gist)
    - Vault backend misconfiguration
    """


class SizeLimitError(PromptCapsuleError, ValueError):
    """
    Raised when input/output exceeds configured size limits.

    Examples:
    - Prompt text > MAX_PROMPT_SIZE before compress
    - Decompressed payload > MAX_DECOMPRESSED_SIZE (zip bomb protection)
    - Compressed zlib blob > MAX_PROMPT_SIZE
    """


class SignatureError(IntegrityError):
    """
    Raised when HMAC signature verification fails.

    Subclass of IntegrityError for callers who treat all integrity
    failures the same, but allows specific handling of signature issues
    (e.g., key rotation, missing PROMPT_CAPSULE_HMAC_KEY).
    """
