# Technical Design Document — PromptCapsule

**Version:** 0.1.4  
**Audience:** C-batch / technical review  
**Repository:** https://github.com/UdayaNirogi/promptcapsule  
**Package:** `pip install promptcapsule`

---

## 1. Purpose

PromptCapsule provides a **deterministic, lossless** path from prompt text → portable capsule → exact original text, with:

1. Automatic **inline** compression for small prompts  
2. **Vault** indirection for large prompts  
3. **SHA-256** integrity verification on every decompress  

The design prioritizes honesty (hybrid = compress *or* retrieve), portability of the capsule string, and pluggable storage.

---

## 2. Problem Statement

Teams need to:

- Share the *exact* system/user prompts used in LLM apps  
- Version-control prompts without pasting multi‑KB blobs into tickets  
- Reconstruct prompts across machines with a proof of integrity  

“Prompt compression” in industry often means **lossy semantic reduction**. That is a different problem. PromptCapsule targets **exact reconstruction**, which requires either true compression (entropy-limited) or storage-backed keys.

### 2.1 Agent-to-agent communication (potential)

PromptCapsule is not an agent runtime. The capsule string is still a natural **inter-agent payload**:

```
Agent A                         shared channel                    Agent B
  prompt ──compress──► capsule ──────────────► capsule ──decompress──► prompt
                              (inline: self-contained)
                              (vault: both use same backend)
                                              verified == True → act
                                              verified == False → reject
```

| Handoff type | What moves between agents | Shared state | Fits |
|--------------|---------------------------|--------------|------|
| Inline | Full capsule (`cap_i_…`) | None | Short instructions, tool args, system snippets ≤500 bytes |
| Vault | Short key (`cap_v_…`) | Same `VaultBackend` | Long RAG context, transcripts, multi-agent memory |

**Why it matters:** the receiving agent does not need the multi‑KB prompt inside the chat message. It fetches or decodes the capsule and gets a byte-for-byte copy plus a SHA-256 check.

**Boundaries:**

- No confidentiality by default (integrity only).
- Vault handoff fails if Agent B cannot reach the same store.
- Key length is backend-specific. **27+** in project docs means **test cases**, not capsule size.

---

## 3. Design Principles

| Principle | Implication |
|-----------|-------------|
| Lossless | Output text must equal input UTF-8 bytes after decompress |
| Hybrid honesty | Inline when small; vault when large—no fake “8-char magic” without storage |
| Integrity first | Checksum embedded; `verified` flag on every result |
| Minimal core deps | Core uses only Python stdlib (`zlib`, `base64`, `hashlib`) |
| Pluggable vault | `VaultBackend` interface: `store` / `retrieve` |

---

## 4. Quantified System Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `INLINE_THRESHOLD` | **500 bytes** (UTF-8) | Practical bound for portable inline payloads |
| `COMPRESSION_LEVEL` | **9** (zlib max) | Favor size over CPU for infrequent packaging |
| `MAX_PROMPT_SIZE` / `MAX_DECOMPRESSED_SIZE` | **10 MiB** | DoS / zip-bomb guards (0.1.2+) |
| Checksum | **SHA-256**, first **8 hex** chars in capsule | Integrity signal — **not** a MAC (F09) |
| Capsule prefix | `cap_` | Easy format detection |
| Inline marker | `cap_i_<checksum8>_<base85>` | Self-contained; Base85 must round-trip (0.1.4) |
| Vault marker | `cap_v_<checksum8>_<backend_key>` | Opaque key; bind failure redacts text (0.1.4) |
| `decompress(strict=True)` | default | Raises `IntegrityError` on verify failure |

### Measured packaging sizes (v0.1.0)

| Case | Input | Capsule | Mode | Capsule / Input |
|------|-------|---------|------|-----------------|
| Short system prompt | 251 B | 248 | inline | 98.8% |
| Near threshold | 307 B | 288 | inline | 93.8% |
| Long RAG context | 2,996 B | short vault key | vault | **~1%** |
| Multi-shot | 2,250 B | short vault key | vault | **~1%** |

**Interpretation:** Inline mode packages small prompts for portability (size may not shrink much). Vault mode shrinks the *shareable handle* to a short backend key (length depends on backend naming—not a fixed magic number) while the full text lives in storage.

**Note:** **27+** refers to **automated test cases** in the suite—not the character length of vault capsules.

---

## 5. Architecture

```
                    ┌─────────────────────┐
   prompt text ───► │    PromptCapsule    │
                    │  (compress/decompress)│
                    └──────────┬──────────┘
                               │
              len(utf8) ≤ 500? │
                    ┌──────────┴──────────┐
                    │ YES                 │ NO
                    ▼                     ▼
           ┌────────────────┐    ┌────────────────────┐
           │ Inline path    │    │ Vault path         │
           │ zlib → Base85  │    │ backend.store()    │
           │ embed checksum │    │ emit short key     │
           └────────┬───────┘    └─────────┬──────────┘
                    │                      │
                    ▼                      ▼
              cap_i_...              cap_v_...
                    │                      │
                    └──────────┬───────────┘
                               ▼
                    ┌─────────────────────┐
                    │ CapsuleResult       │
                    │ text, verified,     │
                    │ mode, sizes, hash   │
                    └─────────────────────┘
```

### Module map

| Module | Responsibility |
|--------|----------------|
| `promptcapsule.core` | `PromptCapsule`, `CapsuleResult`, `VaultBackend` ABC |
| `promptcapsule.backends` | InMemory, SQLite, GitHubGist, S3 |
| `promptcapsule.integrity` | Hash helpers / signature utilities |

---

## 6. Data Formats

### 6.1 Inline capsule

```
cap_i_{sha256[:8]}_{base85(zlib(utf8(text)))}
```

**Decompress:** strip prefix → Base85 decode → zlib decompress → recompute SHA-256 → compare prefix → set `verified`.

### 6.2 Vault capsule

```
cap_v_{sha256[:8]}_{backend_key}
```

**Compress:** `backend.store(text, checksum)` → returns key.  
**Decompress:** `backend.retrieve(key)` → verify checksum → `verified`.

---

## 7. Vault Backend Design

```python
class VaultBackend:
    def store(self, text: str, checksum: str) -> str: ...
    def retrieve(self, key: str) -> str: ...
```

| Backend | Persistence | Typical use | Key shape (examples) |
|---------|-------------|-------------|----------------------|
| InMemory | Process RAM | Tests | `mem_00000001` |
| SQLite | Local file | Dev / single host | `sql_YYYYMMDD_HHMMSS_0000` |
| GitHub Gist | Cloud gist | Team share | Gist ID |
| S3 | Object store | Production | `prefix/timestamp_checksum8.txt` |

Optional install: `pip install promptcapsule[vault]` → `boto3`, `PyGithub`.

---

## 8. Integrity Model

1. On compress: `checksum = SHA256(utf8(text)).hexdigest()`  
2. Capsule carries `checksum[:8]`  
3. On decompress: recompute full hash; match prefix → `verified=True`  
4. Caller should treat `verified=False` as hard failure in production  

**Threat note:** Capsules are **not encrypted**. Integrity ≠ confidentiality. Use vault ACLs / private gists / S3 encryption for secrets.

---

## 9. API Surface (minimal)

```python
from promptcapsule import PromptCapsule
from promptcapsule.backends import SQLiteBackend  # or InMemory, Gist, S3

pc = PromptCapsule()
capsule = pc.compress(prompt, vault_backend=backend)  # backend optional if ≤500B
result = pc.decompress(capsule, vault_backend=backend)
assert result.verified and result.text == prompt
```

`CapsuleResult` fields: `text`, `verified`, `mode` (`inline`|`vault`), `checksum`, `original_size`, `capsule_size`.

---

## 10. Non-Goals (v0.1)

- Semantic / lossy token compression  
- End-to-end encryption of capsule payloads  
- Multi-tenant access control inside the library (delegated to backends)  
- Guaranteeing size reduction in inline mode for high-entropy short strings  

---

## 11. Quality & Delivery

| Item | Status |
|------|--------|
| Unit / integration tests | 27+ tests via `run_tests.py` / pytest |
| Security scan (Bandit) | 0 high-severity findings in core |
| Distribution | PyPI `promptcapsule` 0.1.0 |
| License | MIT |

---

## 12. Comparison Snapshot

| Approach | Exact rebuild? | Needs storage? | Primary benefit |
|----------|----------------|----------------|-----------------|
| gzip alone | Yes | No | File compression |
| LLMLingua-style | No (lossy) | No | Token cost reduction |
| Prompt hub / gist paste | Yes | Yes | Sharing |
| **PromptCapsule** | **Yes** | **Only if >500B** | Unified capsule + verify |

---

## 13. Future Extensions (roadmap)

- Configurable threshold  
- Encrypted vault payloads  
- Max size / rate limits for DoS hardening  
- CLI (`promptcapsule pack/unpack`)  

---

*Document aligned with codebase in `promptcapsule/core.py` and `promptcapsule/backends.py`.*
