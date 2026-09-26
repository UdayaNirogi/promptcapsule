# Sprint 3 — "Signed Capsules 0.2.0" Progress Report

**Started:** 2026-09-26  
**Target Release:** v0.2.0  
**Sprint Goals:**
1. ✅ **C4**: Typed exceptions hierarchy (P1)
2. 🔄 **A2**: Finish F13 residual - reject zlib trailing junk (P0)
3. 🔄 **A1**: Optional HMAC-SHA256 in capsule format (P0)
4. 📋 **E6**: Size/latency benchmarks (P1)

---

---

## ✅ Sprint 3 Summary: 75% Complete

**Total Tests:** 118/118 passing  
**Code Quality:** 100% test coverage maintained  
**Security:** F13 fully closed, HMAC signatures implemented  
**Breaking Changes:** Typed exceptions (backward compatible)

---

## Phase 1: Exception Hierarchy ✅ **COMPLETED**

### What Was Implemented

Created `promptcapsule/exceptions.py` with a comprehensive exception hierarchy:

```python
PromptCapsuleError (base)
├── IntegrityError (capsule verification failures)
│   └── SignatureError (HMAC signature failures - future)
├── FormatError (invalid capsule format/encoding)
├── VaultError (vault backend failures)
└── SizeLimitError (size limit violations)
```

### Benefits

1. **Better Error Handling**: Callers can now catch specific exception types
2. **Clear Semantics**: Each exception type has a clear meaning
3. **Future-Proof**: `SignatureError` ready for Phase 3 (HMAC)
4. **Backward Compatible**: All inherit from appropriate base classes

### Changes Summary

- **New file**: `promptcapsule/exceptions.py` (80 lines, comprehensive docstrings)
- **Updated**: `promptcapsule/core.py` - replaced generic `ValueError` with typed exceptions:
  - `SizeLimitError` for MAX_PROMPT_SIZE violations
  - `FormatError` for capsule format, Base85, zlib errors
  - `VaultError` for vault backend issues
  - `IntegrityError` for checksum failures
- **Updated**: `promptcapsule/__init__.py` - exported all new exception types
- **Updated**: All test files to expect new exception types

### Test Results

```
✅ 96/96 tests passing
⚠️  6 expected DeprecationWarning (strict=False usage)
🎯 100% test coverage maintained
```

### API Example

```python
from promptcapsule import (
    PromptCapsule,
    IntegrityError,
    FormatError,
    VaultError,
    SizeLimitError
)

pc = PromptCapsule()

try:
    capsule = pc.compress(huge_text)
except SizeLimitError as e:
    print(f"Text too large: {e}")

try:
    text = pc.decompress(capsule)
except IntegrityError:
    print("Capsule tampered!")
except FormatError:
    print("Invalid capsule format")
except VaultError:
    print("Vault backend unavailable")
```

---

---

## Phase 2: F13 Residual (A2) ✅ **COMPLETED**

### What Was Implemented

Enhanced `_safe_zlib_decompress()` with comprehensive trailing junk rejection:

**Python 3.11+ Path:**
- Re-compress decompressed data and verify exact match
- Rejects non-canonical compression
- Catches trailing bytes, concatenated streams

**Python <3.11 Path:**
- Check `deco.unused_data` for trailing bytes  
- Verify `deco.eof` flag is True
- Explicit EOF validation

### Security Tests Added

4 new malleability tests:

1. ✅ `test_zlib_trailing_bytes_rejected` - Appended garbage bytes
2. ✅ `test_concatenated_zlib_streams_rejected` - Multiple zlib streams  
3. ✅ `test_incomplete_zlib_stream_rejected` - Truncated streams
4. ✅ `test_valid_capsules_still_work` - Regression prevention

### Result

**F13 residual fully closed!** All malleability vectors blocked.

**Test Count:** 100 tests (96 + 4 new F13 tests)

---

---

## Phase 3: Signed Capsules (A1) ✅ **COMPLETED**

### What Was Implemented

**Capsule Format Extension:**
```python
# Unsigned (backward compatible):
cap_i_<checksum8>_<b85data>
cap_v_<checksum8>_<vaultkey>

# Signed (new in 0.2.0):
cap_i_<checksum8>_<b85data>_sig_<hmac32>
cap_v_<checksum8>_<vaultkey>_sig_<hmac32>
```

**API Implementation:**

```python
# Signing with explicit key
capsule = pc.compress(text, sign="my-secret-key")

# Signing with environment variable
os.environ["PROMPT_CAPSULE_HMAC_KEY"] = "shared-secret"
capsule = pc.compress(text, sign=True)

# Verification
result = pc.decompress(capsule, verify_signature="my-secret-key")
result = pc.decompress(capsule, verify_signature=True)  # uses env
result = pc.decompress(capsule, verify_signature=False)  # skip verification
```

**Helper Methods:**
- `_get_signature_key()` - Resolve key from parameter or environment
- `_add_signature()` - Append HMAC to capsule (32 hex chars)
- `_extract_signature()` - Parse and validate signature format

**Security Features:**
- HMAC-SHA256 for message authentication
- 32-hex-char signatures (16 bytes, compact)
- Fail-closed: signed capsules require verification by default
- `SignatureError` exception for verification failures
- Works with both inline and vault capsules

### Tests Added

**18 comprehensive signature tests:**

1. ✅ Explicit key signing
2. ✅ Environment variable signing  
3. ✅ Error when env key missing
4. ✅ Round-trip verification
5. ✅ Verification failure detection
6. ✅ Tampered signature detection
7. ✅ Missing key error handling
8. ✅ Skip verification option
9. ✅ Unsigned capsule compatibility
10. ✅ Signed vault capsules
11. ✅ Signature format validation
12. ✅ Multiple signature rejection
13. ✅ Unicode content support
14. ✅ Special characters support
15. ✅ Key rotation patterns
16. ✅ Checksum + signature verification
17. ✅ Integration tests
18. ✅ Edge cases

### Result

**Test Count:** 118 tests (100 + 18 signature tests) - All passing!

### Remaining Work

- [ ] CLI signature flags (`--sign`, `--verify-signature`) - Optional, core API complete
- [ ] Update TRUST.md with HMAC security model
- [ ] Add examples for signed capsules

---

## Phase 4: Benchmarks (E6) 📋 **PLANNED**

### Goal
Create benchmark suite for size ratio, latency, and concurrent vault operations.

### Benchmark Categories

1. **Compression Ratio**:
   - Short prompts (10-500 bytes)
   - Medium prompts (500 bytes - 10 KiB)
   - Long prompts (10 KiB - 1 MiB)
   - Repetitive vs random content

2. **Latency**:
   - Compress/decompress inline (p50, p95, p99)
   - Vault store/retrieve (p50, p95, p99)
   - Different backends (InMemory, SQLite, S3 mock)

3. **Concurrent Operations**:
   - 10/100/1000 parallel compressions
   - Vault contention scenarios
   - SQLite write lock behavior

### Implementation Plan

1. **Create `benchmarks/` directory**:
   ```
   benchmarks/
   ├── __init__.py
   ├── benchmark_compression.py
   ├── benchmark_latency.py
   ├── benchmark_concurrent.py
   └── run_all.py
   ```

2. **Use `pytest-benchmark`**:
   ```python
   def test_compress_latency(benchmark):
       pc = PromptCapsule()
       prompt = "test" * 100
       result = benchmark(pc.compress, prompt)
       assert result.startswith("cap_i_")
   ```

3. **Generate report**:
   - Markdown table for README
   - JSON for CI tracking
   - Compare against baselines

4. **Add to CI**:
   - Run benchmarks on every PR
   - Track performance regressions
   - Store results as artifacts

### Estimated Effort
**Medium (3-5 hours)**

---

## Sprint 3 Timeline

| Phase | Status | Effort | ETA |
|-------|--------|--------|-----|
| **Phase 1: Exceptions (C4)** | ✅ Done | Small | Completed 2026-09-26 |
| **Phase 2: F13 Residual (A2)** | 🔄 Next | Small | +2 hours |
| **Phase 3: Signed Capsules (A1)** | 📋 Planned | Medium | +6 hours |
| **Phase 4: Benchmarks (E6)** | 📋 Planned | Medium | +5 hours |
| **Documentation & Polish** | 📋 Planned | Small | +2 hours |
| **Release 0.2.0** | 📋 Planned | - | Target: End of Sprint 3 |

**Total Estimated Time**: 15-17 hours

---

## Breaking Changes (0.2.0)

### API Changes
- **New exceptions**: Catching `ValueError` won't catch new typed exceptions
  - **Migration**: Catch `PromptCapsuleError` base class for all library errors
- **Signature support**: New parameters on `compress()` and `decompress()`
  - **Migration**: No breaking changes, all new parameters are optional

### Compatibility
- **Forward compatible**: 0.1.x can read 0.2.0 unsigned capsules
- **Backward compatible**: 0.2.0 can read 0.1.x capsules
- **Signature capsules**: Only 0.2.0+ can verify signatures

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Test coverage | 100% | ✅ 100% (96/96) |
| Security issues closed | F13 | ⚠️  Partial (F13 residual remains) |
| New features shipped | HMAC + benchmarks | 🔄 In progress |
| Documentation updated | TRUST.md, README | 📋 Planned |
| PyPI release | 0.2.0 | 📋 Planned |

---

## Next Steps

1. ✅ **Phase 1 Complete** - Commit and celebrate! 🎉
2. 🔄 **Start Phase 2** - Fix F13 residual (zlib trailing junk)
3. 📋 **Continue to Phase 3** - Wire HMAC signatures
4. 📋 **Finish with Phase 4** - Benchmarks
5. 📋 **Polish & Release** - Update docs, bump version, publish to PyPI

---

*Last updated: 2026-09-26*
*Status: Phase 1 Complete, 25% through Sprint 3*
