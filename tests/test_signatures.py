"""Tests for HMAC signature support in capsules (A1 - Sprint 3)."""

import os
import pytest
from promptcapsule import PromptCapsule, SignatureError, IntegrityError
from promptcapsule.backends import InMemoryBackend


class TestSignedCapsules:
    """Test HMAC-SHA256 signature support."""

    def test_compress_with_explicit_key(self):
        """Compress with explicit signature key."""
        pc = PromptCapsule()
        text = "secret message"
        key = "my-secret-key-123"
        
        capsule = pc.compress(text, sign=key)
        
        # Should contain signature marker
        assert "_sig_" in capsule
        # Signature should be 32 hex chars
        assert capsule.count("_sig_") == 1
        sig = capsule.split("_sig_")[1]
        assert len(sig) == 32
        assert all(c in "0123456789abcdef" for c in sig)

    def test_compress_with_env_key(self):
        """Compress using PROMPT_CAPSULE_HMAC_KEY environment variable."""
        os.environ["PROMPT_CAPSULE_HMAC_KEY"] = "env-secret-key"
        try:
            pc = PromptCapsule()
            text = "environment signed"
            
            capsule = pc.compress(text, sign=True)
            
            assert "_sig_" in capsule
        finally:
            del os.environ["PROMPT_CAPSULE_HMAC_KEY"]

    def test_compress_sign_true_without_env_raises(self):
        """sign=True without env key should raise SignatureError."""
        if "PROMPT_CAPSULE_HMAC_KEY" in os.environ:
            del os.environ["PROMPT_CAPSULE_HMAC_KEY"]
        
        pc = PromptCapsule()
        
        with pytest.raises(SignatureError, match="PROMPT_CAPSULE_HMAC_KEY"):
            pc.compress("test", sign=True)

    def test_compress_without_signature(self):
        """Default compress should not add signature."""
        pc = PromptCapsule()
        capsule = pc.compress("unsigned message")
        
        assert "_sig_" not in capsule

    def test_roundtrip_with_signature(self):
        """Signed capsule round-trip with verification."""
        pc = PromptCapsule()
        text = "authenticated message"
        key = "shared-secret"
        
        # Compress with signature
        capsule = pc.compress(text, sign=key)
        
        # Decompress with verification
        result = pc.decompress(capsule, verify_signature=key)
        
        assert result.text == text
        assert result.verified

    def test_roundtrip_with_env_key(self):
        """Signed capsule round-trip using environment variable."""
        key = "env-roundtrip-key"
        os.environ["PROMPT_CAPSULE_HMAC_KEY"] = key
        try:
            pc = PromptCapsule()
            text = "env authenticated"
            
            # Compress with sign=True
            capsule = pc.compress(text, sign=True)
            
            # Decompress with verify_signature=True
            result = pc.decompress(capsule, verify_signature=True)
            
            assert result.text == text
            assert result.verified
        finally:
            del os.environ["PROMPT_CAPSULE_HMAC_KEY"]

    def test_signature_verification_failure(self):
        """Wrong key should fail signature verification."""
        pc = PromptCapsule()
        text = "tamper me"
        
        # Sign with one key
        capsule = pc.compress(text, sign="key1")
        
        # Try to verify with different key
        with pytest.raises(SignatureError, match="Signature verification failed"):
            pc.decompress(capsule, verify_signature="key2")

    def test_tampered_signature_detected(self):
        """Modifying signature should be detected."""
        pc = PromptCapsule()
        text = "original"
        key = "detection-key"
        
        capsule = pc.compress(text, sign=key)
        
        # Tamper with signature (flip one hex digit)
        tampered = capsule[:-1] + ("0" if capsule[-1] != "0" else "1")
        
        with pytest.raises(SignatureError):
            pc.decompress(tampered, verify_signature=key)

    def test_signature_without_key_raises(self):
        """Signed capsule without verification key should raise."""
        if "PROMPT_CAPSULE_HMAC_KEY" in os.environ:
            del os.environ["PROMPT_CAPSULE_HMAC_KEY"]
        
        pc = PromptCapsule()
        
        capsule = pc.compress("signed", sign="key123")
        
        # Try to decompress without providing key
        with pytest.raises(SignatureError, match="PROMPT_CAPSULE_HMAC_KEY|no key"):
            pc.decompress(capsule)

    def test_verify_signature_false_skips_check(self):
        """verify_signature=False should skip verification."""
        pc = PromptCapsule()
        text = "skip verification"
        
        capsule = pc.compress(text, sign="key1")
        
        # Should succeed even with wrong key if verification disabled
        result = pc.decompress(capsule, verify_signature=False)
        assert result.text == text

    def test_unsigned_capsule_no_error(self):
        """Unsigned capsule should decompress without verification params."""
        pc = PromptCapsule()
        
        capsule = pc.compress("unsigned")
        result = pc.decompress(capsule)
        
        assert result.text == "unsigned"
        assert result.verified

    def test_signed_vault_capsule(self):
        """Vault capsules can also be signed."""
        pc = PromptCapsule()
        backend = InMemoryBackend()
        text = "long " * 200  # > 500 bytes
        key = "vault-sign-key"
        
        # Compress long text with vault and signature
        capsule = pc.compress(text, vault_backend=backend, sign=key)
        
        assert "_sig_" in capsule
        assert capsule.startswith("cap_v_")
        
        # Decompress with verification
        result = pc.decompress(capsule, vault_backend=backend, verify_signature=key)
        
        assert result.text == text
        assert result.verified
        assert result.mode == "vault"

    def test_signature_format_validation(self):
        """Invalid signature format should be rejected."""
        pc = PromptCapsule()
        
        # Create capsule with invalid signature
        valid = pc.compress("test")
        invalid = f"{valid}_sig_INVALID"
        
        with pytest.raises(Exception):  # FormatError
            pc.decompress(invalid, verify_signature=False)

    def test_multiple_sig_markers_rejected(self):
        """Capsule with multiple _sig_ should fail."""
        pc = PromptCapsule()
        
        capsule = pc.compress("test", sign="key")
        # Add second signature marker
        evil = capsule + "_sig_" + "a" * 32
        
        # Should fail during parsing
        with pytest.raises(Exception):
            pc.decompress(evil, verify_signature="key")


class TestSignatureIntegration:
    """Integration tests for signature feature."""

    def test_signature_with_unicode(self):
        """Signatures work with unicode content."""
        pc = PromptCapsule()
        text = "你好世界 🎉 مرحبا בשלום"
        key = "unicode-key"
        
        capsule = pc.compress(text, sign=key)
        result = pc.decompress(capsule, verify_signature=key)
        
        assert result.text == text

    def test_signature_with_special_chars(self):
        """Signatures work with special characters in text."""
        pc = PromptCapsule()
        text = "line1\nline2\ttab\r\nspecial: !@#$%^&*()"
        key = "special-key"
        
        capsule = pc.compress(text, sign=key)
        result = pc.decompress(capsule, verify_signature=key)
        
        assert result.text == text

    def test_signature_key_rotation(self):
        """Demonstrate key rotation pattern."""
        pc = PromptCapsule()
        text = "sensitive data"
        
        old_key = "old-key-v1"
        new_key = "new-key-v2"
        
        # Old capsule with old key
        old_capsule = pc.compress(text, sign=old_key)
        
        # Can still verify with old key
        result = pc.decompress(old_capsule, verify_signature=old_key)
        assert result.text == text
        
        # New capsules use new key
        new_capsule = pc.compress(text, sign=new_key)
        result = pc.decompress(new_capsule, verify_signature=new_key)
        assert result.text == text
        
        # Cross-verification should fail
        with pytest.raises(SignatureError):
            pc.decompress(old_capsule, verify_signature=new_key)

    def test_checksum_and_signature_both_verified(self):
        """Both checksum and signature provide integrity."""
        pc = PromptCapsule()
        text = "double verified"
        key = "double-key"
        
        capsule = pc.compress(text, sign=key)
        
        # Tamper with checksum prefix (8 hex chars after cap_i_)
        # Format: cap_i_<checksum8>_<base85>_sig_<signature>
        parts = capsule.split("_")
        # parts[0] = "cap", parts[1] = "i", parts[2] = checksum, etc.
        tampered_checksum = parts[2][:-1] + ("0" if parts[2][-1] != "0" else "1")
        parts[2] = tampered_checksum
        tampered = "_".join(parts)
        
        # Should fail on checksum verification
        with pytest.raises(IntegrityError):
            pc.decompress(tampered, verify_signature=key, strict=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
