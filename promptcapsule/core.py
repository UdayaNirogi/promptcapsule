"""Core compression and decompression logic for PromptCapsule."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import warnings
import zlib
from dataclasses import dataclass
from typing import NamedTuple

from .exceptions import (
    FormatError,
    IntegrityError,
    SignatureError,
    SizeLimitError,
    VaultError,
)
from .integrity import IntegrityChecker


class CapsuleResult(NamedTuple):
    """Result from compress/decompress operations."""

    text: str
    verified: bool
    mode: str  # "inline" or "vault"
    checksum: str
    original_size: int
    capsule_size: int


_HEX8 = re.compile(r"^[0-9a-f]{8}$")


@dataclass
class PromptCapsule:
    """
    Compress and decompress LLM prompts using a hybrid approach.

    - Short prompts (≤ INLINE_THRESHOLD bytes): zlib + Base85 inline
    - Long prompts: vault storage, referenced by an unguessable key

    Security defaults (v0.1.4+):
    - decompress(strict=True) raises IntegrityError on checksum failure
    - empty / malformed checksum prefixes are rejected
    - Base85 payloads must round-trip (rejects trailing junk / malleability)
    - vault bind failures never return retrieved plaintext
    - zlib decompression is bounded (max_length)
    - compress rejects oversized inputs
    """

    INLINE_THRESHOLD = 500
    COMPRESSION_LEVEL = 9
    CHECKSUM_PREFIX_LEN = 8
    # ~10 MiB prompt / expand limit — blocks zip bombs and huge vault payloads
    MAX_PROMPT_SIZE = 10 * 1024 * 1024
    MAX_DECOMPRESSED_SIZE = 10 * 1024 * 1024

    def compress(
        self,
        text: str,
        vault_backend: VaultBackend | None = None,
        *,
        sign: bool | str | None = None,
    ) -> str:
        """
        Compress a prompt into a capsule string.

        Args:
            text: The prompt text to compress
            vault_backend: Optional vault backend for prompts > INLINE_THRESHOLD
            sign: Optional HMAC signing:
                - None (default): No signature
                - True: Sign using PROMPT_CAPSULE_HMAC_KEY environment variable
                - str: Sign using provided secret key

        Raises:
            TypeError: Input is not a string
            SizeLimitError: Input exceeds MAX_PROMPT_SIZE
            VaultError: Vault backend required but not provided
            SignatureError: Signing requested but no key available
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        if not text:
            raise FormatError("Input text cannot be empty")

        text_bytes = text.encode("utf-8")
        if len(text_bytes) > self.MAX_PROMPT_SIZE:
            raise SizeLimitError(f"Prompt exceeds maximum size of {self.MAX_PROMPT_SIZE} bytes")

        checksum = self._compute_checksum(text)

        # Determine signature key if requested
        signature_key = self._get_signature_key(sign)

        if len(text_bytes) <= self.INLINE_THRESHOLD:
            capsule = self._compress_inline(text, checksum)
        else:
            if vault_backend is None:
                raise VaultError(
                    f"Prompt exceeds {self.INLINE_THRESHOLD} bytes and no vault backend provided"
                )
            capsule = self._compress_vault(text, vault_backend, checksum)

        # Add signature if requested
        if signature_key:
            capsule = self._add_signature(capsule, text, signature_key)

        return capsule

    def decompress(
        self,
        capsule: str,
        vault_backend: VaultBackend | None = None,
        *,
        strict: bool = True,
        verify_signature: bool | str | None = None,
    ) -> CapsuleResult:
        """
        Decompress a capsule string back to the original prompt.

        Args:
            capsule: Capsule string (must start with ``cap_``)
            vault_backend: Required for vault capsules
            strict: If True (default), raise IntegrityError when verification fails
                    instead of returning plaintext with verified=False.
            verify_signature: Optional HMAC signature verification:
                - None (default): Auto-verify if signature present
                - True: Verify using PROMPT_CAPSULE_HMAC_KEY environment variable
                - False: Skip signature verification (not recommended)
                - str: Verify using provided secret key

        Warning:
            Using strict=False is discouraged and may be deprecated in a future release.
            Fail-closed verification (strict=True) is the recommended practice for
            agent-to-agent handoff and security-sensitive applications.
        """
        if not strict:
            warnings.warn(
                "Using strict=False is discouraged. Fail-closed verification (strict=True) "
                "is recommended for agent handoffs and security-sensitive applications. "
                "This parameter may be deprecated in a future release.",
                DeprecationWarning,
                stacklevel=2,
            )

        if not isinstance(capsule, str):
            raise TypeError("Capsule must be a string")

        if not capsule.startswith("cap_"):
            raise FormatError("Invalid capsule format: must start with 'cap_'")

        if len(capsule.encode("utf-8")) > self.MAX_PROMPT_SIZE:
            raise SizeLimitError("Capsule exceeds maximum allowed size")

        # Check for signature and verify if present
        has_signature = "_sig_" in capsule
        if has_signature:
            capsule, expected_sig = self._extract_signature(capsule)
            # Get verification key (auto-detect or explicit)
            if verify_signature is False:
                # User explicitly disabled signature verification
                pass
            else:
                sig_key = self._get_signature_key(verify_signature if verify_signature else True)
                if not sig_key:
                    raise SignatureError(
                        "Capsule has signature but no key provided for verification. "
                        "Set PROMPT_CAPSULE_HMAC_KEY environment variable or pass verify_signature parameter."
                    )

        capsule_data = capsule[4:]

        if capsule_data.startswith("i_"):
            result = self._decompress_inline(capsule_data)
        elif capsule_data.startswith("v_"):
            if vault_backend is None:
                raise VaultError("Vault capsule requires vault_backend")
            result = self._decompress_vault(capsule_data, vault_backend)
        else:
            raise FormatError("Unknown capsule type")

        # Verify signature if present and not explicitly disabled
        if has_signature and verify_signature is not False:
            sig_key = self._get_signature_key(verify_signature if verify_signature else True)
            if sig_key:
                # Expand short signature back to full length for verification
                # Our _add_signature uses first 32 hex chars, but verify_signature expects full 64
                computed_sig_full = IntegrityChecker.create_signature(result.text, sig_key)
                computed_sig_short = computed_sig_full[:32]

                # Never include the computed signature in the error: it would leak a valid MAC.
                if not hmac.compare_digest(computed_sig_short, expected_sig):
                    raise SignatureError("Signature verification failed")

        if strict and not result.verified:
            raise IntegrityError(
                "Capsule integrity verification failed "
                "(checksum mismatch or empty/invalid prefix)"
            )
        return result

    def _compress_inline(self, text: str, checksum: str) -> str:
        """Compress using zlib + Base85."""
        text_bytes = text.encode("utf-8")
        compressed = zlib.compress(text_bytes, level=self.COMPRESSION_LEVEL)
        encoded = base64.b85encode(compressed).decode("ascii")
        return f"cap_i_{checksum[: self.CHECKSUM_PREFIX_LEN]}_{encoded}"

    def _compress_vault(
        self,
        text: str,
        vault_backend: VaultBackend,
        checksum: str,
    ) -> str:
        """Store in vault and return reference."""
        key = vault_backend.store(text, checksum)
        return f"cap_v_{checksum[: self.CHECKSUM_PREFIX_LEN]}_{key}"

    def _safe_zlib_decompress(self, compressed: bytes) -> bytes:
        """Decompress with an expansion cap (zip-bomb guard) and trailing junk rejection.

        Security hardening (F13 residual):
        - Rejects zlib streams with trailing unused bytes
        - Ensures complete decompression (EOF reached)
        - Blocks malleability via concatenated or partial streams

        ``zlib.decompress(..., max_length=)`` exists only on Python 3.11+.
        Older versions use ``decompressobj`` with the same limit.
        """
        max_length = self.MAX_DECOMPRESSED_SIZE

        # Python 3.11+ path: simpler but need manual trailing check
        try:
            decompressed = zlib.decompress(compressed, max_length=max_length)
            # Verify no trailing junk: re-compress and check exact match
            recompressed = zlib.compress(decompressed, level=self.COMPRESSION_LEVEL)
            if recompressed != compressed:
                raise FormatError("zlib stream has trailing junk or non-canonical compression")
            return decompressed
        except TypeError:
            # Python < 3.11: use decompressobj for granular control
            pass
        except zlib.error as e:
            raise FormatError(f"zlib decompress failed: {e}") from e

        # Python < 3.11 path: decompressobj with EOF verification
        deco = zlib.decompressobj()
        try:
            out = deco.decompress(compressed, max_length)
        except zlib.error as e:
            raise FormatError(f"zlib decompress failed: {e}") from e

        # Check for size limit violations
        if deco.unconsumed_tail:
            raise SizeLimitError(f"Decompressed data exceeds maximum size of {max_length} bytes")

        out += deco.flush()

        if len(out) > max_length:
            raise SizeLimitError(f"Decompressed data exceeds maximum size of {max_length} bytes")

        # F13 hardening: reject if decompressor didn't reach EOF
        # unused_data contains bytes after a valid zlib stream
        if deco.unused_data:
            raise FormatError(
                f"zlib stream has {len(deco.unused_data)} trailing bytes (malleability attempt)"
            )

        # Verify EOF flag is set (stream completed cleanly)
        if not deco.eof:
            raise FormatError("zlib stream incomplete or malformed")

        return out

    @staticmethod
    def _b85decode_strict(encoded: str) -> bytes:
        """Decode Base85 and reject trailing junk / non-canonical encodings (F13)."""
        try:
            compressed = base64.b85decode(encoded)
        except Exception as e:
            raise FormatError(f"Invalid Base85 payload: {e}") from e
        # Round-trip: ignores of trailing junk would yield a different re-encode
        if base64.b85encode(compressed).decode("ascii") != encoded:
            raise FormatError("Invalid Base85 payload: trailing junk or non-canonical encoding")
        return compressed

    def _decompress_inline(self, capsule_data: str) -> CapsuleResult:
        """Decompress inline capsule."""
        try:
            parts = capsule_data.split("_", 2)
            if len(parts) != 3:
                raise FormatError("Invalid inline capsule format")

            _, checksum_prefix, encoded = parts
            self._validate_checksum_prefix(checksum_prefix)

            compressed = self._b85decode_strict(encoded)
            text_bytes = self._safe_zlib_decompress(compressed)
            text = text_bytes.decode("utf-8")

            computed_checksum = self._compute_checksum(text)
            verified = computed_checksum.startswith(checksum_prefix)

            return CapsuleResult(
                text=text,
                verified=verified,
                mode="inline",
                checksum=computed_checksum,
                original_size=len(text.encode("utf-8")),
                capsule_size=len(encoded),
            )
        except (IntegrityError, FormatError, SizeLimitError):
            raise
        except Exception as e:
            raise FormatError(f"Failed to decompress inline capsule: {e}") from e

    def _decompress_vault(
        self,
        capsule_data: str,
        vault_backend: VaultBackend,
    ) -> CapsuleResult:
        """Decompress vault capsule with key↔checksum binding."""
        try:
            parts = capsule_data.split("_", 2)
            if len(parts) != 3:
                raise FormatError("Invalid vault capsule format")

            _, checksum_prefix, key = parts
            self._validate_checksum_prefix(checksum_prefix)
            if not key:
                raise FormatError("Invalid vault capsule: empty key")

            text, stored_checksum = vault_backend.retrieve_with_checksum(key)
            computed_checksum = self._compute_checksum(text)

            # Bind key → stored checksum → content; then match capsule prefix
            bound_ok = (
                bool(stored_checksum)
                and computed_checksum == stored_checksum
                and computed_checksum.startswith(checksum_prefix)
            )

            # F07: never return another agent's plaintext on bind failure,
            # even when strict=False.
            safe_text = text if bound_ok else ""

            return CapsuleResult(
                text=safe_text,
                verified=bound_ok,
                mode="vault",
                checksum=computed_checksum if bound_ok else stored_checksum or computed_checksum,
                original_size=len(text.encode("utf-8")) if bound_ok else 0,
                capsule_size=len(key),
            )
        except (IntegrityError, FormatError, VaultError):
            raise
        except Exception as e:
            raise VaultError(f"Failed to decompress vault capsule: {e}") from e

    @classmethod
    def _validate_checksum_prefix(cls, prefix: str) -> None:
        """Reject empty or malformed prefixes (prevents startswith('') bypass)."""
        if not prefix or not _HEX8.match(prefix):
            raise IntegrityError(
                "Invalid checksum prefix: expected exactly 8 lowercase hex characters"
            )

    @staticmethod
    def _compute_checksum(text: str) -> str:
        """Compute SHA256 checksum of text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _get_signature_key(sign: bool | str | None) -> str | None:
        """Get HMAC signature key from parameter or environment.

        Args:
            sign: bool (use env), str (explicit key), or None (no signing)

        Returns:
            Key string if available, None otherwise

        Raises:
            SignatureError: If signing explicitly requested but no key available
        """
        if sign is None or sign is False:
            return None

        if isinstance(sign, str):
            return sign

        # sign is True: use environment variable
        key = os.environ.get("PROMPT_CAPSULE_HMAC_KEY")
        if sign is True and not key:
            raise SignatureError(
                "Signing requested but PROMPT_CAPSULE_HMAC_KEY environment variable not set"
            )
        return key

    @staticmethod
    def _add_signature(capsule: str, text: str, key: str) -> str:
        """Add HMAC-SHA256 signature to capsule.

        Format: cap_X_..._sig_<hmac64>
        Uses first 32 hex chars (16 bytes) of HMAC for compactness.
        """
        signature = IntegrityChecker.create_signature(text, key)
        # Use first 32 hex chars (16 bytes) for compactness
        sig_short = signature[:32]
        return f"{capsule}_sig_{sig_short}"

    @staticmethod
    def _extract_signature(capsule: str) -> tuple[str, str]:
        """Extract signature from signed capsule.

        Returns:
            (unsigned_capsule, signature) tuple

        Raises:
            FormatError: If signature format is invalid
        """
        if "_sig_" not in capsule:
            raise FormatError("Capsule does not contain signature")

        parts = capsule.rsplit("_sig_", 1)
        if len(parts) != 2:
            raise FormatError("Invalid signature format")

        unsigned, signature = parts

        # Validate signature format (32 hex chars = 16 bytes)
        if len(signature) != 32 or not all(c in "0123456789abcdef" for c in signature):
            raise FormatError(
                f"Invalid signature format: expected 32 hex chars, got {len(signature)}"
            )

        return unsigned, signature


class VaultBackend:
    """Abstract base class for vault backends."""

    def store(self, text: str, checksum: str) -> str:
        """Store text and return a key."""
        raise NotImplementedError

    def retrieve(self, key: str) -> str:
        """Retrieve text by key."""
        raise NotImplementedError

    def retrieve_with_checksum(self, key: str) -> tuple:
        """
        Retrieve text and the checksum stored with it.

        Default: text via retrieve(); checksum recomputed (weaker binding).
        Concrete backends that persist checksum should override this.
        """
        text = self.retrieve(key)
        checksum = PromptCapsule._compute_checksum(text)
        return text, checksum
