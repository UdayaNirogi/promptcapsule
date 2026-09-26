"""Exception hierarchy for PromptCapsule.

Clear, typed exceptions make debugging easier and allow callers
to handle different failure modes appropriately.
"""


class PromptCapsuleError(Exception):
    """Base exception for all PromptCapsule errors."""

    pass


class IntegrityError(PromptCapsuleError, ValueError):
    """
    Raised when capsule integrity verification fails.
    
    This is the fail-closed signal: the capsule string was tampered with,
    corrupted, or does not match its claimed checksum/signature.
    
    In strict=True mode (default), decompression raises this immediately.
    Callers should treat this as "unsafe to use" and never fall back to
    the returned text.
    """

    pass


class FormatError(PromptCapsuleError, ValueError):
    """
    Raised when a capsule string has invalid format.
    
    Examples:
    - Missing or malformed prefix (cap_i_, cap_v_)
    - Invalid Base85 encoding
    - Checksum prefix wrong length or invalid characters
    - Vault key format violation
    """

    pass


class VaultError(PromptCapsuleError):
    """
    Raised when vault backend operations fail.
    
    Examples:
    - Key not found in vault
    - Network/auth failure reaching remote vault (S3, Gist)
    - Vault storage quota exceeded
    - Vault backend misconfiguration
    """

    pass


class SizeLimitError(PromptCapsuleError, ValueError):
    """
    Raised when input/output exceeds configured size limits.
    
    Examples:
    - Prompt text > MAX_PROMPT_SIZE before compress
    - Decompressed payload > MAX_DECOMPRESSED_SIZE (zip bomb protection)
    - Compressed zlib blob > MAX_PROMPT_SIZE
    """

    pass


class SignatureError(IntegrityError):
    """
    Raised when HMAC signature verification fails.
    
    Subclass of IntegrityError for callers who treat all integrity
    failures the same, but allows specific handling of signature issues
    (e.g., key rotation, missing PROMPT_CAPSULE_HMAC_KEY).
    """

    pass
