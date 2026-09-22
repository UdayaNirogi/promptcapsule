# PromptCapsule - Quick Start Guide

**Version**: 0.1.0  
**Status**: ✅ Production Ready

---

## Installation

```bash
# Basic installation
pip install promptcapsule

# With cloud storage support
pip install promptcapsule[vault]
```

---

## 60-Second Quick Start

```python
from promptcapsule import PromptCapsule

# Create an instance
pc = PromptCapsule()

# Compress a prompt
prompt = "You are a helpful assistant. Be concise and accurate."
capsule = pc.compress(prompt)
print(f"Capsule: {capsule}")

# Decompress anywhere
result = pc.decompress(capsule)
assert result.text == prompt  # ✓ Exact match
assert result.verified is True  # ✓ Integrity verified

print(result.text)  # Prints original prompt
```

---

## For Long Prompts

```python
from promptcapsule import PromptCapsule
from promptcapsule.backends import SQLiteBackend

pc = PromptCapsule()
vault = SQLiteBackend("prompts.db")

# Compress long prompt
long_prompt = "..." * 200  # >500 bytes
capsule = pc.compress(long_prompt, vault_backend=vault)

# Decompress later
result = pc.decompress(capsule, vault_backend=vault)
print(result.text)  # Original prompt reconstructed
```

---

## Run Tests

```bash
python run_tests.py
# Expected: Test Results: 27/27 passed ✅
```

---

## Examples

See `/examples/` directory:
- `01_basic_usage.py` - Simple compress/decompress
- `02_long_prompts.py` - Vault backends
- `03_version_control.py` - Git integration
- `04_custom_backend.py` - Custom backends

---

## Documentation

- 📖 [`README.md`](README.md) - Full documentation
- 🧪 [`TEST_RESULTS.md`](TEST_RESULTS.md) - Test analysis
- 🔧 [`CONTRIBUTING.md`](CONTRIBUTING.md) - Contributing guide
- 🏗️ [`BUILD_SUMMARY.md`](BUILD_SUMMARY.md) - Build details
- ✅ [`PROJECT_COMPLETION_REPORT.md`](PROJECT_COMPLETION_REPORT.md) - Final report

---

## Key Features

✨ **Hybrid Compression**
- Short prompts: Portable, self-contained
- Long prompts: Scalable with pluggable backends

🔒 **Integrity Verification**
- SHA256 checksums
- Byte-for-byte reconstruction

🎯 **Automatic Mode Selection**
- <500 bytes → inline compression
- >500 bytes → vault backend

🌍 **Pluggable Backends**
- In-Memory (testing)
- SQLite (local)
- GitHub Gist (cloud)
- S3 (enterprise)

---

## API Reference

### `PromptCapsule`

```python
pc = PromptCapsule()

# Compress
capsule = pc.compress(text, vault_backend=None)

# Decompress
result = pc.decompress(capsule, vault_backend=None)
# Returns: CapsuleResult(text, verified, mode, checksum, original_size, capsule_size)
```

### Backends

```python
from promptcapsule.backends import (
    InMemoryBackend,      # For testing
    SQLiteBackend,        # Local storage
    GitHubGistBackend,    # GitHub Gist (requires token)
    S3Backend,            # AWS S3 (requires credentials)
)

backend = SQLiteBackend("prompts.db")
```

---

## Common Use Cases

### 1. Share Across Devices
```python
# On device A
capsule = pc.compress(my_prompt)

# Share the capsule string (email, message, etc.)

# On device B
result = pc.decompress(capsule)
print(result.text)  # Original prompt
```

### 2. Version Control
```python
import json

prompts = {
    "v1.0": pc.compress(prompt_v1),
    "v1.1": pc.compress(prompt_v1_1),
}

# Commit to git
with open("prompts.json", "w") as f:
    json.dump(prompts, f)

# Later, retrieve any version
result = pc.decompress(prompts["v1.0"])
```

### 3. Vault Storage
```python
vault = SQLiteBackend("vault.db")

# Store long prompts
capsule = pc.compress(long_prompt, vault_backend=vault)

# Retrieve anywhere with access to vault
result = pc.decompress(capsule, vault_backend=vault)
```

---

## Troubleshooting

### ❌ "vault backend" error
```python
# ✓ Short prompts don't need a backend
pc.compress("short prompt")

# ✗ Long prompts (>500 bytes) require a backend
# pc.compress("A" * 600)  # Error!

# ✓ Provide a backend for long prompts
pc.compress("A" * 600, vault_backend=SQLiteBackend("db.sqlite"))
```

### ❌ "cannot decompressivault capsule"
```python
# ✓ Provide the same backend used for compression
result = pc.decompress(capsule, vault_backend=vault)

# ✗ Missing backend
# result = pc.decompress(capsule)  # Error for vault capsules
```

---

## Performance

| Operation | Time |
|-----------|------|
| Inline compress | 1-5ms |
| Inline decompress | <1ms |
| Vault store | 1-10ms |
| Vault retrieve | 1-10ms |

---

## Limits

- **Max inline**: 500 bytes
- **Max vault key**: 64 bytes (SHA256)
- **Compression**: Up to 90% for repetitive content
- **Python**: 3.8+

---

## Support

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/UdayaNirogi/promptcapsule/issues)
- 💬 [Discussions](https://github.com/UdayaNirogi/promptcapsule/discussions)

---

**Made with ❤️ for developers who care about their prompts.**
