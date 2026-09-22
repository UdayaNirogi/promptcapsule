"""Core compression and decompression logic for PromptCapsule."""

import zlib
import base64
import hashlib
from typing import Optional, Tuple, NamedTuple
from dataclasses import dataclass


class CapsuleResult(NamedTuple):
    """Result from compress/decompress operations."""
    text: str
    verified: bool
    mode: str  # "inline" or "vault"
    checksum: str
    original_size: int
    capsule_size: int


@dataclass
class PromptCapsule:
    """
    Compress and decompress LLM prompts using hybrid approach.
    
    - Short prompts (<500 chars): zlib compressed + Base85 encoded
    - Long prompts: Stored in vault backend, referenced by hash key
    """
    
    INLINE_THRESHOLD = 500  # Max chars for inline compression
    COMPRESSION_LEVEL = 9  # Maximum zlib compression (0-9)
    
    def compress(
        self,
        text: str,
        vault_backend: Optional['VaultBackend'] = None,
    ) -> str:
        """
        Compress a prompt into a capsule string.
        
        Args:
            text: The prompt text to compress
            vault_backend: Optional backend for storing long prompts
            
        Returns:
            Compressed capsule string (starts with 'cap_' prefix)
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")
        
        if not text:
            raise ValueError("Input text cannot be empty")
        
        text_bytes = text.encode('utf-8')
        checksum = self._compute_checksum(text)
        
        # Try inline compression first
        if len(text_bytes) <= self.INLINE_THRESHOLD:
            return self._compress_inline(text, checksum)
        
        # Fall back to vault mode
        if vault_backend is None:
            raise ValueError(
                f"Prompt exceeds {self.INLINE_THRESHOLD} bytes and no vault backend provided"
            )
        
        return self._compress_vault(text, vault_backend, checksum)
    
    def decompress(
        self,
        capsule: str,
        vault_backend: Optional['VaultBackend'] = None,
    ) -> CapsuleResult:
        """
        Decompress a capsule string back to original prompt.
        
        Args:
            capsule: The capsule string to decompress
            vault_backend: Optional backend for retrieving long prompts
            
        Returns:
            CapsuleResult with decompressed text and verification status
        """
        if not isinstance(capsule, str):
            raise TypeError("Capsule must be a string")
        
        if not capsule.startswith("cap_"):
            raise ValueError("Invalid capsule format: must start with 'cap_'")
        
        capsule_data = capsule[4:]  # Remove 'cap_' prefix
        
        # Check mode
        if capsule_data.startswith("i_"):
            return self._decompress_inline(capsule_data)
        elif capsule_data.startswith("v_"):
            if vault_backend is None:
                raise ValueError("Vault capsule requires vault_backend")
            return self._decompress_vault(capsule_data, vault_backend)
        else:
            raise ValueError("Unknown capsule type")
    
    def _compress_inline(self, text: str, checksum: str) -> str:
        """Compress using zlib + Base85."""
        text_bytes = text.encode('utf-8')
        compressed = zlib.compress(
            text_bytes,
            level=self.COMPRESSION_LEVEL
        )
        
        # Encode as Base85 for better human readability than Base64
        encoded = base64.b85encode(compressed).decode('ascii')
        
        # Format: cap_i_<checksum>_<encoded_data>
        return f"cap_i_{checksum[:8]}_{encoded}"
    
    def _compress_vault(
        self,
        text: str,
        vault_backend: 'VaultBackend',
        checksum: str,
    ) -> str:
        """Store in vault and return reference."""
        key = vault_backend.store(text, checksum)
        # Format: cap_v_<checksum>_<vault_key>
        return f"cap_v_{checksum[:8]}_{key}"
    
    def _decompress_inline(self, capsule_data: str) -> CapsuleResult:
        """Decompress inline capsule."""
        try:
            parts = capsule_data.split('_', 2)
            if len(parts) != 3:
                raise ValueError("Invalid inline capsule format")
            
            _, checksum_prefix, encoded = parts
            compressed = base64.b85decode(encoded)
            text_bytes = zlib.decompress(compressed)
            text = text_bytes.decode('utf-8')
            
            # Verify integrity
            computed_checksum = self._compute_checksum(text)
            verified = computed_checksum.startswith(checksum_prefix)
            
            return CapsuleResult(
                text=text,
                verified=verified,
                mode="inline",
                checksum=computed_checksum,
                original_size=len(text.encode('utf-8')),
                capsule_size=len(encoded),
            )
        except Exception as e:
            raise ValueError(f"Failed to decompress inline capsule: {e}")
    
    def _decompress_vault(
        self,
        capsule_data: str,
        vault_backend: 'VaultBackend',
    ) -> CapsuleResult:
        """Decompress vault capsule."""
        try:
            parts = capsule_data.split('_', 2)
            if len(parts) != 3:
                raise ValueError("Invalid vault capsule format")
            
            _, checksum_prefix, key = parts
            text = vault_backend.retrieve(key)
            
            # Verify integrity
            computed_checksum = self._compute_checksum(text)
            verified = computed_checksum.startswith(checksum_prefix)
            
            return CapsuleResult(
                text=text,
                verified=verified,
                mode="vault",
                checksum=computed_checksum,
                original_size=len(text.encode('utf-8')),
                capsule_size=len(key),
            )
        except Exception as e:
            raise ValueError(f"Failed to decompress vault capsule: {e}")
    
    @staticmethod
    def _compute_checksum(text: str) -> str:
        """Compute SHA256 checksum of text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()


class VaultBackend:
    """Abstract base class for vault backends."""
    
    def store(self, text: str, checksum: str) -> str:
        """Store text and return a key."""
        raise NotImplementedError
    
    def retrieve(self, key: str) -> str:
        """Retrieve text by key."""
        raise NotImplementedError
