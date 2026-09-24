"""Example 2: Working with long prompts using vault backends (v0.1.5)."""

from promptcapsule import PromptCapsule, IntegrityError
from promptcapsule.backends import InMemoryBackend, SQLiteBackend
import os

# Create a PromptCapsule instance
pc = PromptCapsule()

# Create a long, realistic prompt (simulating a carefully crafted system prompt)
long_prompt = """
SYSTEM PROMPT FOR AI CODE REVIEW ASSISTANT

You are an expert software engineer with 20+ years of experience in:
- Systems design and architecture
- Python, Go, Rust, JavaScript/TypeScript
- Security, performance, and testing
- Open source best practices

Your task is to review code and provide constructive feedback on:

1. Design Patterns & Architecture
   - Identify patterns used
   - Suggest improvements
   - Point out anti-patterns

2. Code Quality
   - Readability and maintainability
   - Naming conventions
   - DRY principle adherence
   - SOLID principles

3. Performance
   - Algorithmic complexity
   - Memory usage
   - Database query optimization
   - Caching opportunities

4. Security
   - Input validation
   - SQL injection risks
   - Authentication/authorization
   - Cryptography usage
   - Secrets management

5. Testing
   - Coverage gaps
   - Edge cases
   - Mock/fixture usage
   - Integration test design

6. Documentation
   - Docstring completeness
   - README clarity
   - API documentation
   - Comment clarity

Guidelines:
- Be constructive and respectful
- Explain WHY, not just WHAT
- Provide code examples when possible
- Prioritize issues by severity
- Acknowledge good practices
""" * 3  # Simulate a very long prompt

print(f"Original prompt length: {len(long_prompt)} bytes")
print()

# Example 1: Using InMemoryBackend (good for testing)
print("=" * 70)
print("Example 1: InMemoryBackend (testing)")
print("=" * 70)

memory_backend = InMemoryBackend()
capsule_memory = pc.compress(long_prompt, vault_backend=memory_backend)

print(f"Capsule: {capsule_memory}")
print(f"Capsule size: {len(capsule_memory)} characters")
print()

# Decompress with fail-closed integrity (default strict=True)
try:
    result_memory = pc.decompress(capsule_memory, vault_backend=memory_backend)
    assert result_memory.text == long_prompt
    print(f"✓ Decompressed successfully from memory backend")
    print(f"  Verified: {result_memory.verified}")
    print(f"  Compression ratio: {len(capsule_memory) / result_memory.original_size:.2%}")
except IntegrityError as e:
    print(f"❌ Integrity verification failed: {e}")
    raise
print()

# Example 2: Using SQLiteBackend (good for persistent storage)
print("=" * 70)
print("Example 2: SQLiteBackend (persistent storage)")
print("=" * 70)

db_path = "prompts_example.db"
sqlite_backend = SQLiteBackend(db_path)

capsule_sqlite = pc.compress(long_prompt, vault_backend=sqlite_backend)
print(f"Capsule: {capsule_sqlite}")
print(f"Database file: {db_path}")
print()

# Close and reopen to simulate persistence
result_sqlite = pc.decompress(capsule_sqlite, vault_backend=sqlite_backend)
assert result_sqlite.text == long_prompt
print(f"✓ Decompressed successfully from SQLite backend")
print(f"  Verified: {result_sqlite.verified}")
print(f"  Database file size: {os.path.getsize(db_path)} bytes")
print()

# Example 3: Compress multiple versions (version control scenario)
print("=" * 70)
print("Example 3: Version Control with Multiple Prompts")
print("=" * 70)

versions = {
    "v1.0": long_prompt,
    "v1.1": long_prompt + "\n\nUpdated: Added emphasis on error handling",
    "v1.2": long_prompt + "\n\nUpdated: Added emphasis on error handling and documentation",
}

capsules = {}
for version, prompt_text in versions.items():
    capsule = pc.compress(prompt_text, vault_backend=sqlite_backend)
    capsules[version] = capsule
    print(f"{version}: {capsule}")

print()

# Retrieve a specific version
print("Retrieving v1.1...")
result_v11 = pc.decompress(capsules["v1.1"], vault_backend=sqlite_backend)
print(f"✓ Successfully retrieved v1.1")
print(f"  Verified: {result_v11.verified}")
print(f"  Length: {len(result_v11.text)} bytes")
print()

# Cleanup
os.remove(db_path)
print("Cleaned up database file")
