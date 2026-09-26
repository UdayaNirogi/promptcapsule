"""Unit tests for PromptCapsule core functionality."""

import pytest
import tempfile
import os
from promptcapsule.core import PromptCapsule, CapsuleResult
from promptcapsule.backends import InMemoryBackend, SQLiteBackend
from promptcapsule.exceptions import VaultError


class TestPromptCapsuleBasics:
    """Test basic compress/decompress functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
        self.short_prompt = "This is a short prompt"
        self.long_prompt = "A" * 600  # Exceeds 500 char threshold
    
    def test_compress_short_prompt_inline(self):
        """Test compressing a short prompt uses inline mode."""
        capsule = self.pc.compress(self.short_prompt)
        
        assert capsule.startswith("cap_i_")
        # Short non-repetitive text may not shrink; format is what matters
        assert "_".join(capsule.split("_")[:2]) == "cap_i"
    
    def test_compress_long_prompt_requires_vault(self):
        """Test that long prompts require a vault backend."""
        with pytest.raises(VaultError, match="vault backend"):
            self.pc.compress(self.long_prompt)
    
    def test_compress_long_prompt_with_vault(self):
        """Test compressing a long prompt with vault backend."""
        backend = InMemoryBackend()
        capsule = self.pc.compress(self.long_prompt, vault_backend=backend)
        
        assert capsule.startswith("cap_v_")
    
    def test_compress_empty_string(self):
        """Test that empty strings are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            self.pc.compress("")
    
    def test_compress_invalid_type(self):
        """Test that non-strings are rejected."""
        with pytest.raises(TypeError):
            self.pc.compress(123)  # type: ignore
    
    def test_decompress_short_prompt(self):
        """Test decompressing a short prompt."""
        capsule = self.pc.compress(self.short_prompt)
        result = self.pc.decompress(capsule)
        
        assert result.text == self.short_prompt
        assert result.verified is True
        assert result.mode == "inline"
    
    def test_decompress_long_prompt(self):
        """Test decompressing a long prompt."""
        backend = InMemoryBackend()
        capsule = self.pc.compress(self.long_prompt, vault_backend=backend)
        result = self.pc.decompress(capsule, vault_backend=backend)
        
        assert result.text == self.long_prompt
        assert result.verified is True
        assert result.mode == "vault"
    
    def test_decompress_invalid_capsule_format(self):
        """Test that invalid capsule formats are rejected."""
        with pytest.raises(ValueError, match="must start with"):
            self.pc.decompress("invalid_capsule")
    
    def test_decompress_unknown_capsule_type(self):
        """Test that unknown capsule types are rejected."""
        with pytest.raises(ValueError, match="Unknown capsule type"):
            self.pc.decompress("cap_x_invalid")
    
    def test_decompress_vault_without_backend(self):
        """Test that vault capsules require a backend."""
        with pytest.raises(VaultError, match="vault_backend"):
            self.pc.decompress("cap_v_abc12345_somekey")


class TestPromptCapsuleEdgeCases:
    """Test edge cases and special characters."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
    
    def test_unicode_characters(self):
        """Test prompts with unicode characters."""
        prompt = "Hello 世界 🌍 Привет مرحبا"
        capsule = self.pc.compress(prompt)
        result = self.pc.decompress(capsule)
        
        assert result.text == prompt
        assert result.verified is True
    
    def test_multiline_prompt(self):
        """Test prompts with newlines and special formatting."""
        prompt = """This is a multiline prompt
        
        With multiple paragraphs
        
        And some special chars: !@#$%^&*()_+-={}[]|:;<>?,.
        
        Also tabs:	here	and	there"""
        
        capsule = self.pc.compress(prompt)
        result = self.pc.decompress(capsule)
        
        assert result.text == prompt
        assert result.verified is True
    
    def test_very_short_prompt(self):
        """Test single character prompt."""
        prompt = "x"
        capsule = self.pc.compress(prompt)
        result = self.pc.decompress(capsule)
        
        assert result.text == prompt
        assert result.verified is True
    
    def test_null_bytes_in_prompt(self):
        """Test prompts containing null bytes."""
        prompt = "Text with null\x00byte in middle"
        capsule = self.pc.compress(prompt)
        result = self.pc.decompress(capsule)
        
        assert result.text == prompt
        assert result.verified is True
    
    def test_exact_threshold_prompt(self):
        """Test prompt at exact 500 byte threshold."""
        # Create a prompt exactly 500 bytes
        prompt = "A" * 500
        capsule = self.pc.compress(prompt)
        result = self.pc.decompress(capsule)
        
        assert result.text == prompt
        assert result.verified is True
        assert result.mode == "inline"
    
    def test_just_over_threshold_prompt(self):
        """Test prompt just over 500 byte threshold."""
        backend = InMemoryBackend()
        # Create a prompt of 501 bytes
        prompt = "A" * 501
        capsule = self.pc.compress(prompt, vault_backend=backend)
        result = self.pc.decompress(capsule, vault_backend=backend)
        
        assert result.text == prompt
        assert result.verified is True
        assert result.mode == "vault"


class TestCompressionEfficiency:
    """Test compression efficiency metrics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
    
    def test_compression_ratio_short_prompt(self):
        """Test compression ratio for short prompts."""
        prompt = "This is a test prompt with some repetitive content. " * 3
        capsule = self.pc.compress(prompt)
        result = self.pc.decompress(capsule)
        
        original_size = result.original_size
        capsule_size = result.capsule_size
        
        # For highly compressible content, we should get good compression
        compression_ratio = capsule_size / original_size
        assert compression_ratio < 0.95  # At least 5% improvement
    
    def test_capsule_result_metrics(self):
        """Test that CapsuleResult has correct metrics."""
        prompt = "Test prompt with metrics"
        capsule = self.pc.compress(prompt)
        result = self.pc.decompress(capsule)
        
        assert result.original_size > 0
        assert result.capsule_size > 0
        assert len(result.checksum) == 64  # SHA256 is 64 hex chars
        assert result.verified is True


class TestInterleavedOperations:
    """Test multiple compress/decompress operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
        self.backend = InMemoryBackend()
    
    def test_multiple_short_prompts(self):
        """Test compressing multiple short prompts."""
        prompts = [
            "First prompt",
            "Second prompt with more text",
            "Third one 🎉",
        ]
        
        capsules = [self.pc.compress(p) for p in prompts]
        results = [self.pc.decompress(c) for c in capsules]
        
        for original, result in zip(prompts, results):
            assert result.text == original
            assert result.verified is True
    
    def test_multiple_long_prompts(self):
        """Test compressing multiple long prompts."""
        prompts = [
            "A" * 600,
            "B" * 700,
            "C" * 800,
        ]
        
        capsules = [
            self.pc.compress(p, vault_backend=self.backend)
            for p in prompts
        ]
        results = [
            self.pc.decompress(c, vault_backend=self.backend)
            for c in capsules
        ]
        
        for original, result in zip(prompts, results):
            assert result.text == original
            assert result.verified is True
    
    def test_mixed_short_and_long(self):
        """Test mix of short and long prompts."""
        short_prompts = ["short" for _ in range(3)]
        long_prompts = ["A" * 600 for _ in range(3)]
        
        short_capsules = [self.pc.compress(p) for p in short_prompts]
        long_capsules = [
            self.pc.compress(p, vault_backend=self.backend)
            for p in long_prompts
        ]
        
        all_capsules = short_capsules + long_capsules
        all_originals = short_prompts + long_prompts
        
        # Decompress shorts
        short_results = [self.pc.decompress(c) for c in short_capsules]
        # Decompress longs
        long_results = [
            self.pc.decompress(c, vault_backend=self.backend)
            for c in long_capsules
        ]
        
        all_results = short_results + long_results
        
        for original, result in zip(all_originals, all_results):
            assert result.text == original
            assert result.verified is True


class TestSQLiteBackend:
    """Test SQLite backend functionality."""
    
    def test_sqlite_backend_store_retrieve(self):
        """Test storing and retrieving from SQLite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path)
            
            text = "Test content for SQLite"
            checksum = "abc123"
            
            key = backend.store(text, checksum)
            retrieved = backend.retrieve(key)
            
            assert retrieved == text
            assert key.startswith("sql_")
    
    def test_sqlite_backend_with_promptcapsule(self):
        """Test SQLite backend integration with PromptCapsule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path)
            pc = PromptCapsule()
            
            prompt = "A" * 600
            capsule = pc.compress(prompt, vault_backend=backend)
            result = pc.decompress(capsule, vault_backend=backend)
            
            assert result.text == prompt
            assert result.verified is True
    
    def test_sqlite_backend_key_not_found(self):
        """Test error handling for missing keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLiteBackend(db_path)
            
            with pytest.raises(KeyError):
                backend.retrieve("nonexistent_key")


class TestMemoryBackend:
    """Test in-memory backend functionality."""
    
    def test_memory_backend_basics(self):
        """Test basic memory backend operations."""
        backend = InMemoryBackend()
        
        key1 = backend.store("text1", "checksum1")
        key2 = backend.store("text2", "checksum2")
        
        assert backend.retrieve(key1) == "text1"
        assert backend.retrieve(key2) == "text2"
    
    def test_memory_backend_key_not_found(self):
        """Test error handling for missing keys."""
        backend = InMemoryBackend()
        
        with pytest.raises(KeyError):
            backend.retrieve("nonexistent")


class TestChecksumVerification:
    """Test checksum and integrity verification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
    
    def test_checksum_consistency(self):
        """Test that checksums are consistent."""
        prompt = "Test prompt"
        checksum1 = self.pc._compute_checksum(prompt)
        checksum2 = self.pc._compute_checksum(prompt)
        
        assert checksum1 == checksum2
    
    def test_different_prompts_different_checksums(self):
        """Test that different prompts have different checksums."""
        checksum1 = self.pc._compute_checksum("prompt1")
        checksum2 = self.pc._compute_checksum("prompt2")
        
        assert checksum1 != checksum2
    
    def test_verification_fails_on_corrupted_data(self):
        """Tampered checksum must fail closed (IntegrityError) by default."""
        from promptcapsule import IntegrityError

        prompt = "Original prompt"
        capsule = self.pc.compress(prompt)
        parts = capsule.split("_")
        wrong = f"cap_i_deadbeef_{parts[-1]}"
        with pytest.raises(IntegrityError):
            self.pc.decompress(wrong)
        result = self.pc.decompress(wrong, strict=False)
        assert result.verified is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
