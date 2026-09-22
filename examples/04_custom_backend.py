"""Example 4: Creating a custom vault backend."""

from promptcapsule import PromptCapsule
from promptcapsule.core import VaultBackend
import json
import os
from pathlib import Path

# Custom backend: JSON file-based storage
class JSONBackend(VaultBackend):
    """Store capsules in a JSON file."""
    
    def __init__(self, filepath: str = "capsule_vault.json"):
        self.filepath = filepath
        self.data = self._load()
        self.counter = len(self.data)
    
    def _load(self):
        """Load existing data or create new file."""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {}
    
    def _save(self):
        """Save data to file."""
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def store(self, text: str, checksum: str) -> str:
        """Store text and return a key."""
        self.counter += 1
        key = f"json_{self.counter:06d}"
        self.data[key] = {
            "text": text,
            "checksum": checksum,
        }
        self._save()
        return key
    
    def retrieve(self, key: str) -> str:
        """Retrieve text by key."""
        if key not in self.data:
            raise KeyError(f"Key not found: {key}")
        return self.data[key]["text"]

# Usage example
print("=" * 70)
print("Example: Custom JSON File Backend")
print("=" * 70)
print()

pc = PromptCapsule()
backend = JSONBackend("my_vault.json")

# Compress some prompts
prompts = [
    "Write a Python function that sorts a list",
    "Explain quantum computing in simple terms",
    "Generate creative product names for a new todo app",
]

capsules = []
print("Compressing prompts...")
for i, prompt in enumerate(prompts, 1):
    capsule = pc.compress(prompt, vault_backend=backend)
    capsules.append(capsule)
    print(f"  {i}. {prompt[:40]}...")
    print(f"     Capsule: {capsule}")

print()

# Show the vault file
print("Vault file contents (my_vault.json):")
print("-" * 70)
with open("my_vault.json", "r") as f:
    vault_content = json.load(f)
    for key, value in vault_content.items():
        print(f"  {key}:")
        print(f"    text: {value['text'][:40]}...")
        print(f"    checksum: {value['checksum'][:8]}...")

print()

# Decompress a prompt
print("Decompressing first prompt...")
result = pc.decompress(capsules[0], vault_backend=backend)
print(f"  Original: {result.text}")
print(f"  Verified: {result.verified}")

print()

# Create a new backend instance and verify persistence
print("Testing persistence (create new backend instance)...")
backend2 = JSONBackend("my_vault.json")
result2 = pc.decompress(capsules[1], vault_backend=backend2)
print(f"  Successfully retrieved from new backend instance")
print(f"  Text: {result2.text}")
print(f"  Verified: {result2.verified}")

print()

# Cleanup
os.remove("my_vault.json")
print("Cleaned up example files")

print()
print("=" * 70)
print("How to create your own backend:")
print("=" * 70)
print("""
1. Inherit from VaultBackend
2. Implement two methods:
   - store(text: str, checksum: str) -> str
     * Save the text somewhere
     * Return a key (string) that identifies it
   
   - retrieve(key: str) -> str
     * Fetch the text by key
     * Raise KeyError if not found

3. Use it:
   capsule = pc.compress(prompt, vault_backend=my_backend)
   result = pc.decompress(capsule, vault_backend=my_backend)

Examples:
- Database backend: store in PostgreSQL, return row ID
- Redis backend: store in Redis, return cache key
- S3 backend: store in S3, return object key
- Google Cloud Storage: store in GCS, return blob name
""")
