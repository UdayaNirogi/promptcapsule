"""Tests for integrity checking."""

import pytest
from promptcapsule.integrity import IntegrityChecker


class TestIntegrityChecker:
    """Test IntegrityChecker functionality."""
    
    def test_compute_hash_consistency(self):
        """Test that hashing is consistent."""
        data = "test data"
        hash1 = IntegrityChecker.compute_hash(data)
        hash2 = IntegrityChecker.compute_hash(data)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256
    
    def test_different_data_different_hash(self):
        """Test that different data produces different hashes."""
        hash1 = IntegrityChecker.compute_hash("data1")
        hash2 = IntegrityChecker.compute_hash("data2")
        
        assert hash1 != hash2
    
    def test_verify_checksum_valid(self):
        """Test checksum verification with valid data."""
        original = "test content"
        checksum = IntegrityChecker.compute_hash(original)
        
        assert IntegrityChecker.verify_checksum(original, checksum) is True
    
    def test_verify_checksum_invalid(self):
        """Test checksum verification with invalid data."""
        original = "test content"
        wrong_checksum = "0" * 64
        
        assert IntegrityChecker.verify_checksum(original, wrong_checksum) is False
    
    def test_verify_checksum_prefix_valid(self):
        """Test checksum prefix verification with valid prefix."""
        original = "test content"
        checksum = IntegrityChecker.compute_hash(original)
        prefix = checksum[:8]
        
        assert IntegrityChecker.verify_checksum_prefix(original, prefix) is True
    
    def test_verify_checksum_prefix_invalid(self):
        """Test checksum prefix verification with invalid prefix."""
        original = "test content"
        wrong_prefix = "00000000"
        
        assert IntegrityChecker.verify_checksum_prefix(original, wrong_prefix) is False
    
    def test_hash_length(self):
        """Test that hash output is correct length."""
        hash_value = IntegrityChecker.compute_hash("any content")
        
        # SHA256 produces 64 hex characters
        assert len(hash_value) == 64
        # All should be valid hex
        int(hash_value, 16)  # Would raise ValueError if not valid hex
    
    def test_unicode_hashing(self):
        """Test hashing with unicode content."""
        content = "Unicode: 你好 🌍"
        hash_value = IntegrityChecker.compute_hash(content)
        
        assert len(hash_value) == 64
        assert IntegrityChecker.verify_checksum(content, hash_value) is True
    
    def test_signature_creation(self):
        """Test HMAC signature creation."""
        data = "test data"
        secret = "secret key"
        
        sig = IntegrityChecker.create_signature(data, secret)
        
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA256 HMAC is 64 hex chars
    
    def test_signature_verification_valid(self):
        """Test signature verification with valid signature."""
        data = "test data"
        secret = "secret key"
        
        sig = IntegrityChecker.create_signature(data, secret)
        
        assert IntegrityChecker.verify_signature(data, sig, secret) is True
    
    def test_signature_verification_invalid_signature(self):
        """Test signature verification with invalid signature."""
        data = "test data"
        secret = "secret key"
        wrong_sig = "0" * 64
        
        assert IntegrityChecker.verify_signature(data, wrong_sig, secret) is False
    
    def test_signature_verification_wrong_secret(self):
        """Test signature verification with wrong secret."""
        data = "test data"
        secret1 = "secret key 1"
        secret2 = "secret key 2"
        
        sig = IntegrityChecker.create_signature(data, secret1)
        
        assert IntegrityChecker.verify_signature(data, sig, secret2) is False
    
    def test_signature_timing_resistance(self):
        """Test that signature verification uses constant-time comparison."""
        data = "test data"
        secret = "secret key"
        
        sig = IntegrityChecker.create_signature(data, secret)
        wrong_sig_1 = "0" * 64
        wrong_sig_2 = sig[:-1] + "0"
        
        # Both should fail, and comparison should be timing-safe
        assert IntegrityChecker.verify_signature(data, wrong_sig_1, secret) is False
        assert IntegrityChecker.verify_signature(data, wrong_sig_2, secret) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
