"""Integrity checking and verification for capsules."""

import hashlib
from typing import Tuple


class IntegrityChecker:
    """Verify capsule integrity and authenticity."""
    
    @staticmethod
    def compute_hash(data: str) -> str:
        """Compute SHA256 hash of data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_checksum(original: str, checksum: str) -> bool:
        """Verify that a checksum matches the original text."""
        computed = IntegrityChecker.compute_hash(original)
        return computed == checksum
    
    @staticmethod
    def verify_checksum_prefix(original: str, prefix: str) -> bool:
        """Verify that a checksum prefix matches the original text."""
        computed = IntegrityChecker.compute_hash(original)
        return computed.startswith(prefix)
    
    @staticmethod
    def create_signature(data: str, secret: str) -> str:
        """Create HMAC signature for data (for future auth features)."""
        import hmac
        return hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_signature(data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature."""
        expected = IntegrityChecker.create_signature(data, secret)
        return hmac.compare_digest(expected, signature)
