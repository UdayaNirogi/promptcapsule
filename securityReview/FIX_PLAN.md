# Security Fix Plan — PromptCapsule

Source: `securityReview/Report1.txt`  
Scope: **library** first (bus is separate / not in this repo)

## Priority

### P0 — Do now (core trust)
| ID | Fix | Approach |
|----|-----|----------|
| P0.1 | Integrity fail-open | `decompress(..., strict=True)` default: raise `IntegrityError` if checksum fails |
| P0.2 | Empty checksum → verified | Reject empty / non-8-hex prefixes before verify |
| P0.3 | zlib bomb | `zlib.decompress(..., max_length=MAX_DECOMPRESSED_SIZE)` |
| P0.4 | Input size DoS | Reject compress above `MAX_PROMPT_SIZE` |
| P0.5 | HMAC `NameError` | Import `hmac` in `verify_signature` |

### P1 — Vault hardening
| ID | Fix | Approach |
|----|-----|----------|
| P1.1 | Predictable keys | Use `secrets.token_urlsafe(16)` (keep optional readable prefix) |
| P1.2 | Key↔checksum bind | On retrieve, load stored checksum; require full hash match |

### P2 — Cloud backends
| ID | Fix | Approach |
|----|-----|----------|
| P2.1 | Confused deputy | S3: reject keys outside configured `prefix`; Gist: keep as-is (IDs opaque) |

### Out of scope (this pass)
- Demo capsule bus auth / list disclosure / body limits (no bus code in repo)

## Status

| Phase | Status |
|-------|--------|
| P0 library fixes | **Done** (v0.1.2) |
| P1 vault hardening | **Done** |
| P2 S3 prefix check | **Done** |
| Demo bus | Out of scope (not in repo) |
| PyPI upload of 0.1.2 | **Published** — https://pypi.org/project/promptcapsule/0.1.2/ |
| PyPI upload of 0.1.3 | **Published** — https://pypi.org/project/promptcapsule/0.1.3/ |

## Implemented (v0.1.2)

- `decompress(strict=True)` raises `IntegrityError` on checksum failure
- Empty / non-8-hex checksum prefixes rejected
- Bounded zlib decompress (3.11 `max_length` or `decompressobj` fallback)
- `MAX_PROMPT_SIZE` on compress
- HMAC `verify_signature` fixed (`import hmac`)
- Unguessable vault keys (`secrets.token_urlsafe`)
- `retrieve_with_checksum` binds key ↔ stored checksum
- S3 retrieve refuses keys outside configured `prefix`
