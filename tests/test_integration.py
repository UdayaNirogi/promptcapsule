"""Integration and regression tests for PromptCapsule."""

import os
import tempfile

import pytest

from promptcapsule import PromptCapsule, VaultError
from promptcapsule.backends import InMemoryBackend, SQLiteBackend


class TestRegressionCases:
    """Regression tests to catch previously found bugs."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
    
    def test_regression_empty_compression(self):
        """Regression: empty prompts should be rejected."""
        with pytest.raises(ValueError):
            self.pc.compress("")
    
    def test_regression_type_safety(self):
        """Regression: non-string inputs should be rejected."""
        with pytest.raises(TypeError):
            self.pc.compress(None)  # type: ignore
        
        with pytest.raises(TypeError):
            self.pc.compress([1, 2, 3])  # type: ignore
    
    def test_regression_vault_missing_backend(self):
        """Regression: vault decompression without backend should fail."""
        with pytest.raises(VaultError):
            self.pc.decompress("cap_v_abc123_key")


class TestEndToEndScenarios:
    """End-to-end user scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
    
    def test_scenario_share_prompt_across_devices(self):
        """Scenario: User wants to copy a prompt from work to personal account."""
        work_prompt = """
        You are a senior software architect. Analyze this code and provide:
        1. Design patterns used
        2. Potential improvements
        3. Security concerns
        4. Performance optimizations
        
        Be thorough and constructive.
        """
        
        # At work, user compresses the prompt
        capsule = self.pc.compress(work_prompt)
        
        # User copies the capsule string (e.g., via email, message, etc.)
        # Later, on personal account, user decompresses it
        result = self.pc.decompress(capsule)
        
        assert result.text == work_prompt
        assert result.verified is True
    
    def test_scenario_version_control_prompts(self):
        """Scenario: User wants to version control their prompts in git."""
        InMemoryBackend()
        
        # V1 of the prompt
        prompt_v1 = "Generate a poem about mountains"
        capsule_v1 = self.pc.compress(prompt_v1)
        
        # V2 - iterated based on results
        prompt_v2 = "Generate a haiku about mountains with vivid imagery"
        capsule_v2 = self.pc.compress(prompt_v2)
        
        # User stores both in git
        config = {
            "version": "1.0",
            "prompts": {
                "v1": capsule_v1,
                "v2": capsule_v2,
            }
        }
        
        # Later, retrieve from git and decompress
        result_v1 = self.pc.decompress(config["prompts"]["v1"])
        result_v2 = self.pc.decompress(config["prompts"]["v2"])
        
        assert result_v1.text == prompt_v1
        assert result_v2.text == prompt_v2
    
    def test_scenario_long_prompt_with_vault(self):
        """Scenario: User has a very long, carefully crafted prompt."""
        backend = InMemoryBackend()
        
        # Simulate a 50-page prompt document
        long_prompt = """
        SYSTEM PROMPT FOR CODE GENERATION AI
        
        You are an expert software engineer with 20+ years of experience.
        """ + ("This section provides detailed context and guidelines. " * 200)
        
        capsule = self.pc.compress(long_prompt, vault_backend=backend)
        result = self.pc.decompress(capsule, vault_backend=backend)
        
        assert result.text == long_prompt
        assert result.verified is True
        assert result.mode == "vault"


class TestCrossVersionCompatibility:
    """Test compatibility between different use patterns."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
    
    def test_multiple_decompressions_same_capsule(self):
        """Test that the same capsule can be decompressed multiple times."""
        prompt = "Reusable prompt capsule"
        capsule = self.pc.compress(prompt)
        
        # Decompress multiple times
        results = [self.pc.decompress(capsule) for _ in range(5)]
        
        for result in results:
            assert result.text == prompt
            assert result.verified is True
    
    def test_different_backends_same_long_prompt(self):
        """Test using different backends for same prompt."""
        prompt = "A" * 600
        
        # With memory backend
        mem_backend = InMemoryBackend()
        capsule_mem = self.pc.compress(prompt, vault_backend=mem_backend)
        result_mem = self.pc.decompress(capsule_mem, vault_backend=mem_backend)
        
        # With SQLite backend
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            sqlite_backend = SQLiteBackend(db_path)
            capsule_sql = self.pc.compress(prompt, vault_backend=sqlite_backend)
            result_sql = self.pc.decompress(capsule_sql, vault_backend=sqlite_backend)
        
        # Both should work
        assert result_mem.text == prompt
        assert result_sql.text == prompt
        assert result_mem.verified is True
        assert result_sql.verified is True
    
    def test_capsule_format_stability(self):
        """Test that capsule format is stable and parseable."""
        prompt = "Test for format stability"
        capsule = self.pc.compress(prompt)
        
        # Format should be: cap_i_<8chars>_<data>
        assert capsule.startswith("cap_i_")
        parts = capsule.split('_')
        assert len(parts) >= 3
        assert parts[0] == "cap"
        assert parts[1] == "i"
        # Checksum should be 8 chars
        assert len(parts[2]) == 8


class TestPerformanceCharacteristics:
    """Test performance characteristics and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
    
    def test_compression_ratio_repetitive_content(self):
        """Test that repetitive content compresses well in inline mode."""
        # Stay under INLINE_THRESHOLD (500 bytes) so compress stays inline
        repetitive = ("hello " * 80)[:480]
        capsule = self.pc.compress(repetitive)
        result = self.pc.decompress(capsule)
        
        assert result.text == repetitive
        original_size = len(repetitive.encode('utf-8'))
        capsule_size = len(capsule)
        ratio = capsule_size / original_size
        
        assert ratio < 0.5  # Should achieve >50% compression
    
    def test_compression_ratio_random_content(self):
        """Test compression on mostly random content (worst case)."""
        import random
        import string
        
        random_content = ''.join(
            random.choices(string.ascii_letters + string.digits, k=500)
        )
        capsule = self.pc.compress(random_content)
        result = self.pc.decompress(capsule)
        
        assert result.text == random_content
        # Random content might not compress as well, but should still work


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pc = PromptCapsule()
    
    def test_malformed_capsule_handling(self):
        """Test handling of various malformed capsules."""
        malformed_capsules = [
            "not_a_capsule",
            "cap_",
            "cap_i_",
            "cap_x_abc123_data",  # unknown type
            "cap_i_toolongchecksum_data",  # wrong checksum length
        ]
        
        for malformed in malformed_capsules:
            with pytest.raises(ValueError):
                self.pc.decompress(malformed)
    
    def test_backend_error_propagation(self):
        """Test that backend errors are properly propagated."""
        backend = InMemoryBackend()
        
        prompt = "A" * 600
        capsule = self.pc.compress(prompt, vault_backend=backend)
        
        # Create a failing backend
        class FailingBackend:
            def retrieve(self, key):
                raise RuntimeError("Backend failure")
            
            def retrieve_with_checksum(self, key):
                raise RuntimeError("Backend failure")
        
        failing_backend = FailingBackend()
        
        with pytest.raises(VaultError):
            self.pc.decompress(capsule, vault_backend=failing_backend)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
