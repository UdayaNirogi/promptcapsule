# Sprint 3 — "Signed Capsules 0.2.0" Progress Report

**Started:** 2026-09-26  
**Target Release:** v0.2.0  
**Sprint Goals:**
1. ✅ **C4**: Typed exceptions hierarchy (P1)
2. 🔄 **A2**: Finish F13 residual - reject zlib trailing junk (P0)
3. 🔄 **A1**: Optional HMAC-SHA256 in capsule format (P0)
4. 📋 **E6**: Size/latency benchmarks (P1)

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

## Phase 2: F13 Residual (A2) 🔄 **NEXT**

### Goal
Complete rejection of zlib trailing junk to close F13 residual from security review.

### Current State
- ✅ Base85 round-trip validation implemented (0.1.4)
- ✅ Rejects non-canonical Base85 encodings
- ⚠️  zlib `unused_tail` detection exists but needs hardening

### Implementation Plan

1. **Enhance `_safe_zlib_decompress`**:
   - After decompression, check `deco.unconsumed_tail`
   - Verify `deco.eof` flag is True
   - Reject if any compressed bytes remain unused

2. **Add test cases**:
   - Capsule with extra bytes after valid zlib data
   - Multiple zlib streams concatenated
   - Partial zlib stream

3. **Update security tests**:
   - Add to `tests/test_security.py::TestCapsuleMalleability`
   - Verify rejection even with `strict=False`

### Estimated Effort
**Small (1-2 hours)**

---

## Phase 3: Signed Capsules (A1) 🔄 **PLANNED**

### Goal
Wire HMAC-SHA256 into capsule format as opt-in feature.

### Design Decisions

#### Capsule Format Extension
```
# Current (unsigned):
cap_i_<checksum8>_<b85(zlib(text))>
cap_v_<checksum8>_<vault_key>

# Proposed (signed):
cap_i_<checksum8>_<b85(zlib(text))>_sig_<hmac32>
cap_v_<checksum8>_<vault_key>_sig_<hmac32>
```

#### API Changes
```python
# Compress with signature
capsule = pc.compress(
    text,
    sign=True,  # or sign="my_secret_key"
    vault_backend=backend
)

# Decompress with signature verification
result = pc.decompress(
    capsule,
    verify_signature=True,  # or verify_signature="my_secret_key"
    vault_backend=backend
)
```

#### Environment Variable Support
```bash
export PROMPT_CAPSULE_HMAC_KEY="your-secret-key-here"
```

### Implementation Tasks

1. **Update `PromptCapsule` class**:
   - Add `sign` parameter to `compress()`
   - Add `verify_signature` parameter to `decompress()`
   - Read `PROMPT_CAPSULE_HMAC_KEY` from environment if needed

2. **Extend capsule format parser**:
   - Detect `_sig_` suffix
   - Extract HMAC from capsule
   - Verify before decompression

3. **Use `IntegrityChecker`**:
   - Wire existing `create_signature()` / `verify_signature()` methods
   - Raise `SignatureError` on mismatch

4. **Update CLI**:
   - Add `--sign` flag to `promptcapsule pack`
   - Add `--verify-signature` flag to `promptcapsule unpack`

5. **Documentation**:
   - Update `TRUST.md` with HMAC guarantees
   - Add migration guide (unsigned → signed)
   - Document key rotation strategy

6. **Tests**:
   - Round-trip with signatures
   - Signature verification failure
   - Missing key scenarios
   - Key rotation

### Estimated Effort
**Medium (4-6 hours)**

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
