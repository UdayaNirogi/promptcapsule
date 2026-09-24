"""Core compression and decompression logic for PromptCapsule."""

import base64
import hashlib
import re
import warnings
import zlib
from dataclasses import dataclass
from typing import NamedTuple, Optional


class IntegrityError(ValueError):
    """Raised when capsule integrity verification fails (fail-closed)."""


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
        vault_backend: Optional["VaultBackend"] = None,
    ) -> str:
        """
        Compress a prompt into a capsule string.

        Raises:
            TypeError / ValueError: invalid or oversized input
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        if not text:
            raise ValueError("Input text cannot be empty")

        text_bytes = text.encode("utf-8")
        if len(text_bytes) > self.MAX_PROMPT_SIZE:
            raise ValueError(
                f"Prompt exceeds maximum size of {self.MAX_PROMPT_SIZE} bytes"
            )

        checksum = self._compute_checksum(text)

        if len(text_bytes) <= self.INLINE_THRESHOLD:
            return self._compress_inline(text, checksum)

        if vault_backend is None:
            raise ValueError(
                f"Prompt exceeds {self.INLINE_THRESHOLD} bytes and no vault backend provided"
            )

        return self._compress_vault(text, vault_backend, checksum)

    def decompress(
        self,
        capsule: str,
        vault_backend: Optional["VaultBackend"] = None,
        *,
        strict: bool = True,
    ) -> CapsuleResult:
        """
        Decompress a capsule string back to the original prompt.

        Args:
            capsule: Capsule string (must start with ``cap_``)
            vault_backend: Required for vault capsules
            strict: If True (default), raise IntegrityError when verification fails
                    instead of returning plaintext with verified=False.
                    
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
                stacklevel=2
            )
        
        if not isinstance(capsule, str):
            raise TypeError("Capsule must be a string")

        if not capsule.startswith("cap_"):
            raise ValueError("Invalid capsule format: must start with 'cap_'")

        if len(capsule.encode("utf-8")) > self.MAX_PROMPT_SIZE:
            raise ValueError("Capsule exceeds maximum allowed size")

        capsule_data = capsule[4:]

        if capsule_data.startswith("i_"):
            result = self._decompress_inline(capsule_data)
        elif capsule_data.startswith("v_"):
            if vault_backend is None:
                raise ValueError("Vault capsule requires vault_backend")
            result = self._decompress_vault(capsule_data, vault_backend)
        else:
            raise ValueError("Unknown capsule type")

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
        vault_backend: "VaultBackend",
        checksum: str,
    ) -> str:
        """Store in vault and return reference."""
        key = vault_backend.store(text, checksum)
        return f"cap_v_{checksum[: self.CHECKSUM_PREFIX_LEN]}_{key}"

    def _safe_zlib_decompress(self, compressed: bytes) -> bytes:
        """Decompress with an expansion cap (zip-bomb guard).

        ``zlib.decompress(..., max_length=)`` exists only on Python 3.11+.
        Older versions use ``decompressobj`` with the same limit.
        """
        max_length = self.MAX_DECOMPRESSED_SIZE
        try:
            return zlib.decompress(compressed, max_length=max_length)
        except TypeError:
            # Python < 3.11
            pass
        except zlib.error as e:
            raise ValueError(f"zlib decompress failed: {e}") from e

        deco = zlib.decompressobj()
        try:
            out = deco.decompress(compressed, max_length)
        except zlib.error as e:
            raise ValueError(f"zlib decompress failed: {e}") from e
        if deco.unconsumed_tail:
            raise ValueError(
                f"Decompressed data exceeds maximum size of {max_length} bytes"
            )
        out += deco.flush()
        if len(out) > max_length:
            raise ValueError(
                f"Decompressed data exceeds maximum size of {max_length} bytes"
            )
        return out

    @staticmethod
    def _b85decode_strict(encoded: str) -> bytes:
        """Decode Base85 and reject trailing junk / non-canonical encodings (F13)."""
        try:
            compressed = base64.b85decode(encoded)
        except Exception as e:
            raise ValueError(f"Invalid Base85 payload: {e}") from e
        # Round-trip: ignores of trailing junk would yield a different re-encode
        if base64.b85encode(compressed).decode("ascii") != encoded:
            raise ValueError(
                "Invalid Base85 payload: trailing junk or non-canonical encoding"
            )
        return compressed

    def _decompress_inline(self, capsule_data: str) -> CapsuleResult:
        """Decompress inline capsule."""
        try:
            parts = capsule_data.split("_", 2)
            if len(parts) != 3:
                raise ValueError("Invalid inline capsule format")

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
        except IntegrityError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to decompress inline capsule: {e}") from e

    def _decompress_vault(
        self,
        capsule_data: str,
        vault_backend: "VaultBackend",
    ) -> CapsuleResult:
        """Decompress vault capsule with key↔checksum binding."""
        try:
            parts = capsule_data.split("_", 2)
            if len(parts) != 3:
                raise ValueError("Invalid vault capsule format")

            _, checksum_prefix, key = parts
            self._validate_checksum_prefix(checksum_prefix)
            if not key:
                raise ValueError("Invalid vault capsule: empty key")

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
        except IntegrityError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to decompress vault capsule: {e}") from e

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
