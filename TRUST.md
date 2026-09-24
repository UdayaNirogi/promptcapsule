# PromptCapsule — Trust & Threat Model

**Version:** 0.1.5  
**Last Updated:** 2026-09-24  
**Status:** Living document

---

## Purpose

This document defines what PromptCapsule **does** and **does not** guarantee from a security and trust perspective. It is intended for:

- Security reviewers evaluating the library
- Developers integrating PromptCapsule into production systems
- Teams building agent-to-agent handoff mechanisms
- Anyone making trust assumptions about capsule integrity

**Key principle:** **Honesty over marketing**. We document limitations clearly.

---

## 1. What PromptCapsule Guarantees

### ✅ 1.1 Integrity Verification

**Guarantee:** PromptCapsule detects **unintentional corruption** and **basic tampering** of capsule payloads.

**Mechanism:**
- SHA-256 checksum computed over the original prompt text
- 8-hex prefix embedded in the capsule string (visible)
- Full checksum verified on decompress
- Fail-closed by default (`strict=True` raises `IntegrityError`)

**What this protects against:**
- ✅ Accidental corruption (network errors, copy-paste mistakes)
- ✅ Naive tampering (editing capsule string manually)
- ✅ Truncation or malformed capsules
- ✅ Non-canonical Base85 encodings with trailing junk

**What this does NOT protect against (see §2):**
- ❌ Motivated attackers with knowledge of SHA-256 weaknesses
- ❌ MITM attacks without additional transport security
- ❌ Key disclosure in shared vault scenarios

### ✅ 1.2 Lossless Reconstruction

**Guarantee:** Original prompt text is reconstructed **byte-for-byte** if integrity check passes.

**Mechanism:**
- Inline mode: zlib compression + Base85 encoding (deterministic)
- Vault mode: text stored in backend; retrieved by key
- UTF-8 round-trip verified

**What this protects against:**
- ✅ Lossy semantic compression confusion
- ✅ Encoding mismatch errors
- ✅ Partial capsule transmission

### ✅ 1.3 DoS / Resource Exhaustion Protection

**Guarantee:** Capsule decompression is bounded to prevent denial-of-service.

**Limits (v0.1.5):**
| Resource | Limit | Enforcement |
|----------|-------|-------------|
| Max prompt size | 10 MiB | Checked on compress |
| Max capsule size | 10 MiB | Checked on decompress |
| Max zlib expansion | 10 MiB | zlib decompressor with `max_length` |
| Checksum prefix | 8 hex chars | Exactly 8 lowercase hex required |

**What this protects against:**
- ✅ Zip bombs (zlib expansion capped)
- ✅ Memory exhaustion attacks
- ✅ Oversized payload DoS

### ✅ 1.4 Vault Key Unpredictability

**Guarantee:** Vault keys are **unguessable**.

**Mechanism:**
- Generated using `secrets.token_urlsafe(nbytes=16)`
- Not sequential, not derived from content

**What this protects against:**
- ✅ Vault key enumeration attacks
- ✅ Predictable key guessing

### ✅ 1.5 Fail-Closed Default Behavior

**Guarantee:** By default, integrity failures **stop execution** rather than silently returning corrupted data.

**Mechanism:**
- `decompress(strict=True)` is the default (as of v0.1.2)
- Raises `IntegrityError` on checksum mismatch
- Vault key-swap returns empty text even if `strict=False`

**What this protects against:**
- ✅ Silent data corruption in agent handoffs
- ✅ Accidental use of tampered prompts

**Note:** `strict=False` is **discouraged** and emits `DeprecationWarning` (v0.1.5+).

---

## 2. What PromptCapsule Does NOT Guarantee

### ❌ 2.1 Confidentiality (No Encryption)

**Not guaranteed:** Capsule contents are **not encrypted**.

**Why:**
- Inline capsules: Base85-encoded zlib (trivially reversible)
- Vault capsules: Text stored in backend as-is (no encryption at rest by default)

**Implications:**
- ❌ Anyone with a capsule string can read inline payloads
- ❌ Anyone with vault access can read stored prompts
- ❌ Network transmission without TLS exposes plaintext

**Mitigation:**
- Use TLS for transport (HTTPS, secure WebSocket)
- Use vault backends with encryption at rest (AWS S3 SSE, SQLCipher)
- Consider out-of-band encryption if confidentiality is required
- Future: Optional AEAD encryption (Epic A8, not yet implemented)

### ❌ 2.2 Authentication (No Identity Verification)

**Not guaranteed:** Capsules do **not** prove who created them.

**Why:**
- No digital signatures (yet)
- No public key cryptography
- No identity binding

**Implications:**
- ❌ Alice cannot prove she created a capsule
- ❌ Bob can create a capsule and claim Alice made it
- ❌ Capsules can be replayed by anyone

**Mitigation:**
- Use authenticated transport channels (mTLS, API keys)
- Implement agent authentication at the application layer
- Future: Optional HMAC signing with shared secret (Epic A1, in progress)

### ❌ 2.3 Authorization (No Access Control)

**Not guaranteed:** Capsules do **not** enforce who can read them.

**Why:**
- No ACLs in the capsule format
- No per-agent permissions
- Vault backends may have ACLs, but capsules don't enforce them

**Implications:**
- ❌ Any agent with the capsule string can decompress it
- ❌ Vault backends must implement their own ACLs
- ❌ Capsules can be shared beyond intended recipients

**Mitigation:**
- Implement authorization at the vault layer (S3 IAM, Gist token scoping)
- Use short-lived capsules with TTL (Epic B6, not yet implemented)
- Treat capsules as bearer tokens (protect like passwords)

### ❌ 2.4 Message Authentication Code (MAC)

**Not guaranteed:** 8-hex checksum is **not a MAC**.

**Why:**
- Only 8 hex characters (32 bits) of SHA-256 are visible in the capsule
- Full SHA-256 is verified, but no secret key is involved
- Collision resistance is weaker with truncated hash

**Implications:**
- ❌ A determined attacker could find collisions for the 8-hex prefix
- ❌ Capsules are **not cryptographically signed**
- ❌ Integrity check is **not proof against motivated attackers**

**Mitigation:**
- Use signed capsules when available (Epic A1, HMAC with shared secret)
- Combine with authenticated transport (TLS, API keys)
- Document limitation to security reviewers
- Future: Full SHA-256 or HMAC-SHA256 in capsule format

### ❌ 2.5 Replay Protection

**Not guaranteed:** Capsules can be **replayed** indefinitely.

**Why:**
- No timestamps
- No nonces
- No expiration

**Implications:**
- ❌ Eve can capture a capsule and replay it later
- ❌ No freshness guarantee
- ❌ Capsules are valid forever by default

**Mitigation:**
- Implement TTL at the vault layer (Epic B6)
- Use application-layer replay tokens (session IDs, nonces)
- Pair capsules with out-of-band challenge-response

### ❌ 2.6 Side-Channel Resistance

**Not guaranteed:** Decompression timing is **not constant**.

**Why:**
- zlib decompression time varies with payload size
- Checksum comparison is not constant-time (except in HMAC path)
- Base85 decode timing varies

**Implications:**
- ❌ Timing attacks may reveal information about capsule contents
- ❌ Not suitable for high-security cryptographic applications

**Mitigation:**
- Use constant-time comparison for checksums (Epic A5)
- Treat capsules as low-to-medium trust boundary
- Use proper cryptographic libraries for high-security scenarios

### ❌ 2.7 Multi-Tenancy Isolation

**Not guaranteed:** Library does **not** enforce multi-tenant isolation.

**Why:**
- No built-in tenant IDs
- No namespace separation
- Shared vault backends can leak data across tenants

**Implications:**
- ❌ Agents in the same vault can read each other's capsules
- ❌ No per-tenant quota enforcement
- ❌ Vault pollution / key enumeration possible

**Mitigation:**
- Use separate vault backends per tenant
- Implement tenant isolation at the application layer
- Use vault backend ACLs (S3 bucket policies, Gist per-user tokens)

---

## 3. Threat Scenarios & Risk Assessment

### 3.1 Accidental Corruption (Low Risk)

**Scenario:** Network glitch corrupts a capsule during transmission.

**PromptCapsule Response:**
- ✅ Detected by checksum verification
- ✅ `IntegrityError` raised (fail-closed)
- ✅ Agent rejects capsule

**Risk Level:** **LOW** — Well mitigated.

---

### 3.2 Naive Tampering (Low Risk)

**Scenario:** Developer manually edits capsule string to change prompt.

**PromptCapsule Response:**
- ✅ Checksum mismatch detected
- ✅ `IntegrityError` raised

**Risk Level:** **LOW** — Well mitigated.

---

### 3.3 MITM Attack Without TLS (High Risk)

**Scenario:** Attacker intercepts capsule in transit (no TLS), modifies payload, recomputes checksum.

**PromptCapsule Response:**
- ❌ Capsule format has no signature → attacker can forge valid capsule
- ❌ Receiver accepts modified capsule

**Risk Level:** **HIGH** — **Not mitigated by library**.

**Mitigation:**
- **MUST** use TLS for transport
- Consider HMAC-signed capsules (Epic A1)
- Use authenticated channels (mTLS, API keys)

---

### 3.4 Vault Key Disclosure (High Risk)

**Scenario:** Attacker gains read access to vault backend (leaked S3 credentials, Gist token).

**PromptCapsule Response:**
- ❌ No encryption at rest → attacker reads all stored prompts
- ❌ No ACLs in capsule format → attacker can enumerate keys

**Risk Level:** **HIGH** — **Not mitigated by library**.

**Mitigation:**
- Protect vault credentials (environment variables, IAM roles)
- Use vault encryption at rest (S3 SSE, SQLCipher)
- Rotate credentials regularly
- Monitor vault access logs

---

### 3.5 Capsule Replay Attack (Medium Risk)

**Scenario:** Attacker captures valid capsule, replays it to another agent later.

**PromptCapsule Response:**
- ❌ No replay protection → capsule is valid forever
- ❌ Receiver accepts replayed capsule

**Risk Level:** **MEDIUM** — **Not mitigated by library**.

**Mitigation:**
- Implement TTL at application layer
- Use session-specific capsules (pair with nonces)
- Vault backends can implement expiry (Epic B6)

---

### 3.6 8-Hex Collision Attack (Medium Risk)

**Scenario:** Attacker finds two prompts with the same 8-hex prefix, swaps payloads.

**PromptCapsule Response:**
- ❌ 8-hex prefix collision is feasible (~2^32 attempts)
- ✅ Full SHA-256 verification catches mismatch → `IntegrityError` raised

**Risk Level:** **MEDIUM** — Partially mitigated (full checksum still verified).

**Mitigation:**
- Use HMAC-signed capsules (Epic A1)
- Document limitation to security reviewers
- Future: Increase prefix length or use full SHA-256 in format

---

### 3.7 Vault Enumeration (Low-Medium Risk)

**Scenario:** Attacker enumerates vault keys (SQLite, Gist) to discover stored prompts.

**PromptCapsule Response:**
- ✅ Vault keys are unguessable (`secrets.token_urlsafe`)
- ❌ If attacker has vault read access, enumeration is trivial

**Risk Level:** **LOW-MEDIUM** — Partially mitigated (keys unguessable, but vault ACLs required).

**Mitigation:**
- Use vault backend ACLs (S3 IAM, Gist token scoping)
- Monitor vault access patterns
- Implement rate limiting on vault reads

---

## 4. Trust Boundaries

### 4.1 Inline Capsules (`cap_i_...`)

**Trust Model:**
- ✅ Tamper-evident (checksum)
- ❌ Not confidential (Base85-encoded)
- ❌ Not authenticated (no signature)

**Recommended Use:**
- Short prompts shared between trusted agents
- Non-sensitive system instructions
- Demo / testing scenarios

**Avoid:**
- Confidential data (PII, secrets)
- High-security applications
- Untrusted network transmission without TLS

### 4.2 Vault Capsules (`cap_v_...`)

**Trust Model:**
- ✅ Short handle (key) is unguessable
- ✅ Checksum verified on retrieve
- ❌ Vault contents depend on backend security
- ❌ No built-in encryption at rest

**Recommended Use:**
- Long prompts shared between agents with shared vault access
- Multi-agent systems with trusted backend
- Version-controlled prompts in CI/CD

**Avoid:**
- Multi-tenant scenarios without vault isolation
- Untrusted vault backends
- Scenarios requiring confidentiality without vault encryption

### 4.3 Demo HTTP Bus (Out of Package)

**Trust Model:**
- ❌ No authentication (localhost only, demo-grade)
- ❌ No authorization
- ❌ No TLS by default
- ❌ Not production-ready

**Recommended Use:**
- Local development / testing
- Classroom demonstrations
- Prototype agent handoff

**Avoid:**
- Production deployments
- Shared networks
- Multi-tenant environments

---

## 5. Security Hardening Checklist

### ✅ Library-Level Mitigations (Implemented)

- [x] Fail-closed integrity by default (`strict=True`)
- [x] 10 MiB size limits (prompt, capsule, zlib expansion)
- [x] Unguessable vault keys (`secrets.token_urlsafe`)
- [x] Base85 round-trip validation (reject trailing junk)
- [x] S3 prefix validation (block path traversal)
- [x] Gist owner check + optional ID allowlist
- [x] Empty/short checksum prefix rejection
- [x] Vault key-swap returns empty text (even `strict=False`)
- [x] `DeprecationWarning` on `strict=False` usage

### 🔲 Application-Level Mitigations (Required)

- [ ] **Use TLS** for all capsule transmission (HTTPS, WSS)
- [ ] **Protect vault credentials** (IAM roles, env vars, secret managers)
- [ ] **Implement authentication** at agent layer (API keys, mTLS)
- [ ] **Use vault encryption at rest** (S3 SSE, SQLCipher, KMS)
- [ ] **Monitor vault access** (CloudTrail, audit logs)
- [ ] **Rate-limit vault operations** (prevent enumeration)
- [ ] **Implement TTL** for ephemeral capsules (application or vault layer)
- [ ] **Document threat model** for your specific deployment

### 🔮 Future Library Enhancements (Roadmap)

- [ ] HMAC-signed capsules (Epic A1, v0.2.0)
- [ ] Constant-time checksum comparison (Epic A5)
- [ ] Optional AEAD encryption (Epic A8)
- [ ] Capsule TTL / expiry metadata (Epic D7)
- [ ] Authenticated capsule bus (Epic B1-B5)

---

## 6. Coordinated Disclosure

### Reporting Security Issues

If you discover a security vulnerability in PromptCapsule:

1. **DO NOT** open a public GitHub issue
2. Email: `udaya.nirogi@example.com` (or create private security advisory)
3. Include:
   - Description of the issue
   - Steps to reproduce
   - Affected versions
   - Suggested mitigation (if any)

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial assessment:** Within 7 days
- **Fix timeline:** Depends on severity (P0: 1-2 weeks; P1: 2-4 weeks)
- **Public disclosure:** After fix is released + 90-day grace period

### Security Hall of Fame

Contributors who report valid security issues will be credited here (with permission).

---

## 7. Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.5 | 2026-09-24 | Initial TRUST.md; documents all current guarantees/limitations |
| 0.1.4 | 2026-09-22 | Added F07, F11, F13 fixes (not documented in TRUST.md at time) |
| 0.1.2 | 2026-09-20 | Added fail-closed default, size limits |

---

## 8. References

- **Security Fixes:** See `securityReview/FIX_PLAN.md` for detailed finding IDs
- **Test Coverage:** See `tests/test_security.py` for regression tests
- **Limitations:** See `README.md` § "Limitations"
- **Threat Model Standards:** Based on OWASP Threat Modeling, Microsoft STRIDE

---

**Bottom Line:**

PromptCapsule is a **tamper-evident packaging system** for prompts, not a cryptographic security boundary. It protects against **accidental corruption** and **naive tampering**, but **requires application-layer security** (TLS, authentication, vault ACLs) for production use.

**Use it to detect accidents, not to stop motivated attackers.**

For questions or clarifications, open a GitHub Discussion or email the maintainer.

---

*Last updated: 2026-09-24 by Udaya Nirogi*
