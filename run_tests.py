"""Standalone test runner for PromptCapsule - no pytest required."""

import sys
import traceback
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from promptcapsule.core import PromptCapsule, CapsuleResult
from promptcapsule.backends import InMemoryBackend, SQLiteBackend
from promptcapsule.integrity import IntegrityChecker
import tempfile
import os


class TestRunner:
    """Simple test runner."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def run_test(self, test_name, test_func):
        """Run a single test."""
        self.tests_run += 1
        try:
            test_func()
            self.tests_passed += 1
            print(f"✓ {test_name}")
        except Exception as e:
            self.tests_failed += 1
            self.failures.append((test_name, e))
            print(f"✗ {test_name}")
            print(f"  Error: {str(e)[:100]}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print(f"Test Results: {self.tests_passed}/{self.tests_run} passed")
        print("=" * 70)
        
        if self.tests_failed > 0:
            print(f"\n{self.tests_failed} FAILURES:\n")
            for test_name, error in self.failures:
                print(f"  {test_name}:")
                print(f"    {str(error)}\n")
        
        return self.tests_failed == 0


def test_compress_short_prompt_inline():
    """Test compressing a short prompt uses inline mode."""
    pc = PromptCapsule()
    prompt = "This is a short prompt"
    capsule = pc.compress(prompt)
    assert capsule.startswith("cap_i_"), f"Expected cap_i_ prefix, got {capsule[:20]}"


def test_compress_empty_string():
    """Test that empty strings are rejected."""
    pc = PromptCapsule()
    try:
        pc.compress("")
        raise AssertionError("Should have raised ValueError for empty string")
    except ValueError:
        pass


def test_compress_invalid_type():
    """Test that non-strings are rejected."""
    pc = PromptCapsule()
    try:
        pc.compress(123)  # type: ignore
        raise AssertionError("Should have raised TypeError for non-string")
    except TypeError:
        pass


def test_decompress_short_prompt():
    """Test decompressing a short prompt."""
    pc = PromptCapsule()
    prompt = "This is a short prompt"
    capsule = pc.compress(prompt)
    result = pc.decompress(capsule)
    assert result.text == prompt, f"Text mismatch: {result.text} != {prompt}"
    assert result.verified is True, "Verification failed"
    assert result.mode == "inline", f"Expected inline mode, got {result.mode}"


def test_compress_long_prompt_requires_vault():
    """Test that long prompts require a vault backend."""
    pc = PromptCapsule()
    long_prompt = "A" * 600
    try:
        pc.compress(long_prompt)
        raise AssertionError("Should have raised ValueError for long prompt without vault")
    except ValueError as e:
        assert "vault backend" in str(e)


def test_compress_long_prompt_with_vault():
    """Test compressing a long prompt with vault backend."""
    pc = PromptCapsule()
    backend = InMemoryBackend()
    long_prompt = "A" * 600
    capsule = pc.compress(long_prompt, vault_backend=backend)
    assert capsule.startswith("cap_v_"), f"Expected cap_v_ prefix, got {capsule[:20]}"


def test_decompress_long_prompt():
    """Test decompressing a long prompt."""
    pc = PromptCapsule()
    backend = InMemoryBackend()
    long_prompt = "A" * 600
    capsule = pc.compress(long_prompt, vault_backend=backend)
    result = pc.decompress(capsule, vault_backend=backend)
    assert result.text == long_prompt, "Text mismatch"
    assert result.verified is True, "Verification failed"
    assert result.mode == "vault", f"Expected vault mode, got {result.mode}"


def test_unicode_characters():
    """Test prompts with unicode characters."""
    pc = PromptCapsule()
    prompt = "Hello 世界 🌍 Привет مرحبا"
    capsule = pc.compress(prompt)
    result = pc.decompress(capsule)
    assert result.text == prompt, f"Unicode mismatch: {result.text} != {prompt}"
    assert result.verified is True, "Verification failed"


def test_multiline_prompt():
    """Test prompts with newlines and special formatting."""
    pc = PromptCapsule()
    prompt = """This is a multiline prompt
    
    With multiple paragraphs
    
    And some special chars: !@#$%^&*()_+-={}[]|:;<>?,.
    
    Also tabs:	here	and	there"""
    
    capsule = pc.compress(prompt)
    result = pc.decompress(capsule)
    assert result.text == prompt, "Multiline text mismatch"
    assert result.verified is True, "Verification failed"


def test_null_bytes_in_prompt():
    """Test prompts containing null bytes."""
    pc = PromptCapsule()
    prompt = "Text with null\x00byte in middle"
    capsule = pc.compress(prompt)
    result = pc.decompress(capsule)
    assert result.text == prompt, "Null byte text mismatch"
    assert result.verified is True, "Verification failed"


def test_exact_threshold_prompt():
    """Test prompt at exact 500 byte threshold."""
    pc = PromptCapsule()
    prompt = "A" * 500
    capsule = pc.compress(prompt)
    result = pc.decompress(capsule)
    assert result.text == prompt, "Threshold text mismatch"
    assert result.verified is True, "Verification failed"
    assert result.mode == "inline", f"Expected inline mode, got {result.mode}"


def test_just_over_threshold_prompt():
    """Test prompt just over 500 byte threshold."""
    pc = PromptCapsule()
    backend = InMemoryBackend()
    prompt = "A" * 501
    capsule = pc.compress(prompt, vault_backend=backend)
    result = pc.decompress(capsule, vault_backend=backend)
    assert result.text == prompt, "Over-threshold text mismatch"
    assert result.verified is True, "Verification failed"
    assert result.mode == "vault", f"Expected vault mode, got {result.mode}"


def test_multiple_short_prompts():
    """Test compressing multiple short prompts."""
    pc = PromptCapsule()
    prompts = [
        "First prompt",
        "Second prompt with more text",
        "Third one 🎉",
    ]
    
    capsules = [pc.compress(p) for p in prompts]
    results = [pc.decompress(c) for c in capsules]
    
    for original, result in zip(prompts, results):
        assert result.text == original, f"Mismatch: {result.text} != {original}"
        assert result.verified is True, "Verification failed"


def test_multiple_long_prompts():
    """Test compressing multiple long prompts."""
    pc = PromptCapsule()
    backend = InMemoryBackend()
    prompts = [
        "A" * 600,
        "B" * 700,
        "C" * 800,
    ]
    
    capsules = [pc.compress(p, vault_backend=backend) for p in prompts]
    results = [pc.decompress(c, vault_backend=backend) for c in capsules]
    
    for original, result in zip(prompts, results):
        assert result.text == original, "Mismatch"
        assert result.verified is True, "Verification failed"


def test_memory_backend_store_retrieve():
    """Test memory backend basics."""
    backend = InMemoryBackend()
    key1 = backend.store("text1", "checksum1")
    key2 = backend.store("text2", "checksum2")
    
    assert backend.retrieve(key1) == "text1", "Retrieval failed for key1"
    assert backend.retrieve(key2) == "text2", "Retrieval failed for key2"
    assert key1 != key2, "Keys should be unique"


def test_memory_backend_key_not_found():
    """Test KeyError on missing key."""
    backend = InMemoryBackend()
    try:
        backend.retrieve("nonexistent")
        raise AssertionError("Should have raised KeyError")
    except KeyError:
        pass


def test_sqlite_backend_store_retrieve():
    """Test SQLite backend basics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        backend = SQLiteBackend(db_path)
        
        text = "Test content for SQLite"
        checksum = "abc123"
        
        key = backend.store(text, checksum)
        retrieved = backend.retrieve(key)
        
        assert retrieved == text, "SQLite retrieval mismatch"
        assert key.startswith("sql_"), f"Expected sql_ prefix, got {key}"


def test_sqlite_backend_persistence():
    """Test that SQLite data persists across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        
        # Store with first instance
        backend1 = SQLiteBackend(db_path)
        key = backend1.store("persistent content", "checksum123")
        
        # Retrieve with second instance
        backend2 = SQLiteBackend(db_path)
        retrieved = backend2.retrieve(key)
        
        assert retrieved == "persistent content", "Persistence check failed"


def test_integrity_checker_consistency():
    """Test that hashing is consistent."""
    data = "test data"
    hash1 = IntegrityChecker.compute_hash(data)
    hash2 = IntegrityChecker.compute_hash(data)
    assert hash1 == hash2, "Hashes should be consistent"
    assert len(hash1) == 64, f"SHA256 should be 64 chars, got {len(hash1)}"


def test_integrity_checker_different_data():
    """Test that different data produces different hashes."""
    hash1 = IntegrityChecker.compute_hash("data1")
    hash2 = IntegrityChecker.compute_hash("data2")
    assert hash1 != hash2, "Different data should produce different hashes"


def test_integrity_verify_checksum_valid():
    """Test checksum verification with valid data."""
    original = "test content"
    checksum = IntegrityChecker.compute_hash(original)
    assert IntegrityChecker.verify_checksum(original, checksum) is True


def test_integrity_verify_checksum_invalid():
    """Test checksum verification with invalid data."""
    original = "test content"
    wrong_checksum = "0" * 64
    assert IntegrityChecker.verify_checksum(original, wrong_checksum) is False


def test_integrity_verify_checksum_prefix():
    """Test checksum prefix verification."""
    original = "test content"
    checksum = IntegrityChecker.compute_hash(original)
    prefix = checksum[:8]
    assert IntegrityChecker.verify_checksum_prefix(original, prefix) is True


def test_decompress_invalid_capsule_format():
    """Test that invalid capsule formats are rejected."""
    pc = PromptCapsule()
    try:
        pc.decompress("invalid_capsule")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "must start with" in str(e)


def test_decompress_unknown_capsule_type():
    """Test that unknown capsule types are rejected."""
    pc = PromptCapsule()
    try:
        pc.decompress("cap_x_invalid")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "Unknown capsule type" in str(e)


def test_capsule_result_metrics():
    """Test that CapsuleResult has correct metrics."""
    pc = PromptCapsule()
    prompt = "Test prompt with metrics"
    capsule = pc.compress(prompt)
    result = pc.decompress(capsule)
    
    assert result.original_size > 0
    assert result.capsule_size > 0
    assert len(result.checksum) == 64
    assert result.verified is True


def test_end_to_end_scenario():
    """Test end-to-end user scenario."""
    pc = PromptCapsule()
    
    work_prompt = """
    You are a senior software architect. Analyze this code and provide:
    1. Design patterns used
    2. Potential improvements
    3. Security concerns
    4. Performance optimizations
    
    Be thorough and constructive.
    """
    
    # Compress at work
    capsule = pc.compress(work_prompt)
    
    # Decompress on personal account
    result = pc.decompress(capsule)
    
    assert result.text == work_prompt
    assert result.verified is True


def main():
    """Run all tests."""
    runner = TestRunner()
    
    print("=" * 70)
    print("PromptCapsule - Regression Test Suite")
    print("=" * 70)
    print()
    
    # Core functionality tests
    print("Core Functionality Tests:")
    print("-" * 70)
    runner.run_test("Compress short prompt (inline mode)", test_compress_short_prompt_inline)
    runner.run_test("Reject empty strings", test_compress_empty_string)
    runner.run_test("Reject invalid types", test_compress_invalid_type)
    runner.run_test("Decompress short prompt", test_decompress_short_prompt)
    runner.run_test("Long prompt requires vault backend", test_compress_long_prompt_requires_vault)
    runner.run_test("Compress long prompt with vault", test_compress_long_prompt_with_vault)
    runner.run_test("Decompress long prompt", test_decompress_long_prompt)
    
    # Character encoding tests
    print("\nCharacter Encoding Tests:")
    print("-" * 70)
    runner.run_test("Unicode characters", test_unicode_characters)
    runner.run_test("Multiline prompts", test_multiline_prompt)
    runner.run_test("Null bytes in prompts", test_null_bytes_in_prompt)
    
    # Edge case tests
    print("\nEdge Case Tests:")
    print("-" * 70)
    runner.run_test("Exact threshold (500 bytes)", test_exact_threshold_prompt)
    runner.run_test("Just over threshold (501 bytes)", test_just_over_threshold_prompt)
    
    # Multiple operations tests
    print("\nMultiple Operations Tests:")
    print("-" * 70)
    runner.run_test("Multiple short prompts", test_multiple_short_prompts)
    runner.run_test("Multiple long prompts", test_multiple_long_prompts)
    
    # Backend tests
    print("\nBackend Tests:")
    print("-" * 70)
    runner.run_test("Memory backend store/retrieve", test_memory_backend_store_retrieve)
    runner.run_test("Memory backend key not found", test_memory_backend_key_not_found)
    runner.run_test("SQLite backend store/retrieve", test_sqlite_backend_store_retrieve)
    runner.run_test("SQLite backend persistence", test_sqlite_backend_persistence)
    
    # Integrity tests
    print("\nIntegrity Tests:")
    print("-" * 70)
    runner.run_test("Checksum consistency", test_integrity_checker_consistency)
    runner.run_test("Different data, different hashes", test_integrity_checker_different_data)
    runner.run_test("Checksum verification (valid)", test_integrity_verify_checksum_valid)
    runner.run_test("Checksum verification (invalid)", test_integrity_verify_checksum_invalid)
    runner.run_test("Checksum prefix verification", test_integrity_verify_checksum_prefix)
    
    # Error handling tests
    print("\nError Handling Tests:")
    print("-" * 70)
    runner.run_test("Invalid capsule format", test_decompress_invalid_capsule_format)
    runner.run_test("Unknown capsule type", test_decompress_unknown_capsule_type)
    
    # Metrics and metadata tests
    print("\nMetrics and Metadata Tests:")
    print("-" * 70)
    runner.run_test("CapsuleResult metrics", test_capsule_result_metrics)
    
    # End-to-end tests
    print("\nEnd-to-End Tests:")
    print("-" * 70)
    runner.run_test("User scenario: Share prompt across devices", test_end_to_end_scenario)
    
    # Print summary
    success = runner.print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
