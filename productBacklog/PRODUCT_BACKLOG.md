# PromptCapsule — Product Owner Backlog

**Owner view:** Udaya Nirogi (maintainer)  
**Product:** [promptcapsule](https://pypi.org/project/promptcapsule/) (MIT, Alpha, Python ≥3.8)  
**Current release:** **0.1.5** (2026-09-23)  
**Repo:** https://github.com/UdayaNirogi/promptcapsule  
**Companion:** local demo + FastAPI capsule bus (`promptcapsule-demo`) — **not** in the PyPI wheel  
**Last updated:** 2026-09-23 (America/Toronto, EDT)  
**Security verification:** `security_tests/FIX_VERIFICATION_0_1_5.md`

---

## 1. Product vision

**One-liner:** Lossless, integrity-checked *prompt capsules* so agents and tools can hand off short or long prompts without dragging full text through every message.

**What it is**
- Hybrid packager: short text → portable inline capsule (`cap_i_…`); long text → vault reference (`cap_v_…`) + shared backend.
- Fail-closed integrity by default (`strict=True`).
- Pluggable vaults: InMemory, SQLite, GitHub Gist, S3.

**What it is not (and must stay honest about)**
- Not LLM token compression / summarization.
- Not encryption, authN, or authZ.
- Not a multi-tenant agent mesh by itself.
- Not a CLI yet (README TODO; wheel has **no** `console_scripts`).

**North-star outcome:** Developers building multi-agent systems treat a capsule string as the default *handoff payload* — small, verifiable, reconstructible — with a clear trust model.

---

## 2. Target users & jobs-to-be-done

| Persona | Job | Success looks like |
|---------|-----|-------------------|
| **Agent framework builder** | Pass long briefs between agents without stuffing every RPC | Capsule in message; decompress once at receiver; IntegrityError on tamper |
| **App / RAG engineer** | Version and share system prompts across services | Capsules in git/config; vault for long prompts; CI checks integrity |
| **Security-conscious platform team** | Allow handoffs without silent integrity failure | Fail-closed defaults; optional HMAC; documented threat model |
| **Student / hacker (MMAI, demos)** | Show A2A handoff in a classroom/demo | `pip install` + 10-line demo; optional local bus |
| **Ops / infra** | Run a shared capsule bus safely | Auth, quotas, audit log, size limits |

---

## 3. Current product snapshot (0.1.5)

| Area | Status |
|------|--------|
| Inline zlib+Base85 capsules | Shipped |
| Vault capsules (SQLite / memory / Gist / S3) | Shipped |
| Fail-closed `decompress(strict=True)` | Shipped (0.1.2+) |
| Checksum prefix validation (8 hex) | Shipped |
| Bounded decompress / prompt size (10 MiB) | Shipped |
| Unguessable vault keys | Shipped |
| Key↔checksum binding on retrieve | Shipped |
| Vault bind failure → empty text (even `strict=False`) | Shipped (0.1.4+) |
| S3 prefix / traversal guard | Shipped |
| Gist owner check + optional ID allowlist | Shipped (0.1.4+) |
| Base85 round-trip (partial trailing-junk reject) | Shipped (0.1.4+); **residual** `_EXTRA`-style malleability |
| HMAC helper (`IntegrityChecker`) | Shipped but **not wired into capsule format** |
| Official HTTP capsule bus | **Out of package** (demo only; no auth) |
| Encryption / ACLs / multi-tenant | Not started |
| CLI (`console_scripts`) | **Not started** — docs list as TODO; no entry point in 0.1.5 wheel |

**Open security backlog after 0.1.5 verification:** F09 (8-hex ≠ MAC), F13 residual (canonical b85 suffix + zlib trailing ignore), demo bus F03–F05, A4 `strict=False` warnings.

---

## 3b. Completed in 0.1.4 / 0.1.5

Evidence: `FIX_VERIFICATION_0_1_5.md` (PoCs in `verify_fixes_0_1_5.py`).

| Item | Finding / epic | Release | Notes |
|------|----------------|---------|-------|
| Fail-closed decompress | F01 | 0.1.2+ (reconfirmed 0.1.5) | `strict=True` → `IntegrityError` |
| Empty/malformed checksum prefix reject | F02 | 0.1.2+ | Exactly 8 lowercase hex |
| zlib / prompt size cap (10 MiB) | F06 | 0.1.2+ | 11 MiB bomb refused |
| Unguessable vault keys | F08 | 0.1.2+ | `secrets.token_urlsafe` |
| S3 prefix + `..` guard | F10 | 0.1.2+ | Before `get_object` |
| HMAC helper NameError fix | F12 | 0.1.2+ | Module-level `hmac` |
| Vault key-swap → empty text | F07 | **0.1.4** | Was PARTIAL in 0.1.3; now FIXED even if `strict=False` |
| Gist owner check + allowlist | F11 / **A3** | **0.1.4** | Was OPEN in 0.1.3 |
| Base85 round-trip (partial) | F13 / **A2** | **0.1.4** | Non-canonical junk refused; **PARTIAL** residual remains |
| Docs clarity (limits / fixed vs remaining) | — | **0.1.5** | Banner still says v0.1.4 (doc nit) |

**Doc nits (not product features):** PyPI README banner still **v0.1.4** on the **0.1.5** wheel; CLI section is an unchecked roadmap checkbox (not falsely claimed as shipped), but there is still no `console_scripts` entry point.

---

## 4. Prioritization rules

| Priority | Meaning | Rule of thumb |
|----------|---------|----------------|
| **P0** | Must for next minor | Trust/correctness, broken docs, regression risk |
| **P1** | Next release train | Core A2A value, security hardening users will notice |
| **P2** | Differentiation | New features that expand adoption |
| **P3** | Explore | Experiments; park unless pull demand |

**Icebox** = interesting but not committed.

Effort: **S** ≤1 day · **M** 2–5 days · **L** 1–2 weeks · **XL** multi-sprint.

---

## 5. Roadmap themes (suggested)

| Release | Theme | Outcome |
|---------|-------|---------|
| **0.1.4** ✅ | Trust polish | F07 empty-on-swap; F11 Gist gates; F13 partial; shipped |
| **0.1.5** ✅ | Docs clarity | Limits / fixed vs remaining; banner nit remains |
| **0.1.6** | Trust residuals | Close F13 residual; fix README banner; optional A4 warning |
| **0.2.0** | Signed capsules | Optional HMAC/MAC in format (F09/A1); migrate path; threat model |
| **0.3.0** | Capsule Bus (optional extra) | Auth’d HTTP bus as `promptcapsule[bus]` or separate package |
| **0.4.0** | Ecosystem | **CLI** (console_scripts), LangChain/CrewAI/AutoGen helpers |
| **1.0.0** | Stable contract | SemVer API freeze, security policy, SLA-style docs |

---

## 6. Epic backlog

### Epic A — Trust & integrity (library)

| ID | Item | Pri | Effort | Status | Notes / acceptance |
|----|------|-----|--------|--------|--------------------|
| A1 | Wire **HMAC-SHA256** (or full SHA-256) into capsule format as opt-in `signed=True` / env secret | P0 | M | **OPEN** | Fixes F09; default stays compatible; document migration |
| A2 | Reject **trailing junk** after Base85 / zlib (strict parse) | P0 | S | **PARTIAL** (0.1.4) | Round-trip helps; still need reject zlib unused tail / harden `_EXTRA` |
| A3 | **Gist allowlist** + owner check | P0 | S | **DONE** (0.1.4) | Closes F11 — verified 0.1.5 |
| A4 | Deprecate / warn loudly on `strict=False` in docs + runtime warning | P1 | S | **DONE** (0.1.6) | Runtime DeprecationWarning added; docstring updated |
| A5 | Constant-time compare for checksums where applicable | P1 | S | **OPEN** | Defense in depth (HMAC path already uses `compare_digest`) |
| A6 | Published **threat model** (TRUST.md): what capsule guarantees / does not | P0 | S | **DONE** (0.1.6) | 450-line comprehensive threat model published |
| A7 | Capsule **canonicalization** (normalize encoding, NFC, newline policy) | P2 | M | **OPEN** | Reproducible capsules across platforms |
| A8 | Optional **AEAD encryption** at rest in vault (key from env) | P2 | L | **OPEN** | New feature; still not transport auth |
| A9 | Vault key-swap empty text even if `strict=False` | P0 | S | **DONE** (0.1.4) | Closes F07 — verified 0.1.5 |

### Epic B — Capsule Bus (productize the demo)

| ID | Item | Pri | Effort | Status | Notes / acceptance |
|----|------|-----|--------|--------|--------------------|
| B1 | **API keys / bearer tokens** per agent on create/open | P0 | M | **OPEN** | Closes F03 for demo→product |
| B2 | Remove or ACL **list** endpoint; metadata-only without capsule string | P0 | S | **OPEN** | Closes F04 |
| B3 | **Body size + response size** limits; per-agent quota | P0 | S | **OPEN** | Closes F05 / DoS |
| B4 | Bind to localhost by default; document reverse-proxy TLS | P1 | S | **OPEN** | Safe defaults |
| B5 | Audit log: who created/opened what (hash of capsule, not plaintext) | P1 | M | **OPEN** | Ops requirement |
| B6 | TTL / expiry on vault rows + bus index | P1 | M | **OPEN** | Hygiene for shared buses |
| B7 | Publish as optional `promptcapsule-bus` or extra `[bus]` | P1 | M | **OPEN** | Clear packaging boundary |
| B8 | OpenAPI + typed client SDK (Python) | P2 | M | **OPEN** | Agent frameworks love clients |
| B9 | mTLS / JWT federation for multi-host agents | P3 | L | **OPEN** | Enterprise path |
| B10 | Webhook “capsule ready” notify | P3 | M | **OPEN** | Async agent wakes |

### Epic C — Developer experience

| ID | Item | Pri | Effort | Status | Notes / acceptance |
|----|------|-----|--------|--------|--------------------|
| C1 | First-class **CLI**: `promptcapsule pack\|unpack\|inspect\|verify` | P1 | M | **OPEN** | **Docs-ahead-of-code:** 0.1.5 wheel has **no** `console_scripts`; README TODO unchecked |
| C2 | Richer `CapsuleResult`: `agent_id`, `created_at`, `content_type`, `labels` | P1 | M | **OPEN** | Metadata without second DB |
| C3 | **Inspect** mode: decode headers without full decompress (where safe) | P1 | S | **OPEN** | Debugging |
| C4 | Typed exceptions hierarchy (`FormatError`, `IntegrityError`, `VaultError`, `SizeLimitError`) | P1 | S | **OPEN** | Better caller UX |
| C5 | Upgrade demo README to current API (`strict`, `IntegrityError`) | P0 | S | **OPEN** | Keep demo docs in sync with 0.1.5 |
| C6 | Cookiecutter / `promptcapsule init` scaffold for A2A handoff | P2 | M | **OPEN** | Classroom / hackathon |
| C7 | Interactive TUI or Streamlit “capsule playground” | P3 | M | **OPEN** | Marketing + teaching |
| C8 | VS Code / Cursor snippet pack | P3 | S | **OPEN** | Adoption |
| C9 | Fix PyPI README banner version (still says v0.1.4 on 0.1.5) | P0 | S | **OPEN** | Doc nit from 0.1.5 verification |

### Epic D — New features (differentiation)

| ID | Item | Pri | Effort | Status | Notes / acceptance |
|----|------|-----|--------|--------|--------------------|
| D1 | **Capsule chains / manifests**: one capsule points to N child capsules | P1 | L | **OPEN** | Multi-doc handoff |
| D2 | **Streaming / chunked vault** for >10 MiB with progressive verify | P2 | L | **OPEN** | Raise size ceiling safely |
| D3 | **Content-addressed** vault keys (hash of payload) + dedupe | P2 | M | **OPEN** | Storage savings |
| D4 | **Redaction profiles**: pack with PII scrub hook before vault write | P2 | M | **OPEN** | Enterprise / compliance |
| D5 | **Diff capsules**: pack delta vs base capsule | P2 | L | **OPEN** | Bandwidth on revise loops |
| D6 | **Multi-format payloads** with `content_type` | P1 | M | **OPEN** | Agents share more than prompts |
| D7 | **Policy tags** in capsule header: `ttl`, `max_opens`, `audience` | P2 | M | **OPEN** | Soft capability tokens |
| D8 | **Offline mirror**: export vault subset as portable archive | P2 | M | **OPEN** | Air-gapped demos |
| D9 | **Observation hooks** (OpenTelemetry) | P2 | M | **OPEN** | Production ops |
| D10 | **Capsule registry** UI | P3 | L | **OPEN** | Paired with bus |
| D11 | Native **Redis / Postgres / Cloudflare R2** backends | P2 | M each | **OPEN** | Meet agents where they run |
| D12 | **gRPC / NATS** transport adapters | P3 | L | **OPEN** | Mesh-friendly |
| D13 | **Prompt lint + capsule**: secrets scan before pack | P2 | M | **OPEN** | Stop leaking keys into vaults |
| D14 | **Human-readable aliases** on bus | P2 | M | **OPEN** | Operator ergonomics |
| D15 | **Agent SDK recipe** for CrewAI / LangGraph / AutoGen | P1 | M | **OPEN** | Distribution channel |

### Epic E — Ecosystem & distribution

| ID | Item | Pri | Effort | Status | Notes / acceptance |
|----|------|-----|--------|--------|--------------------|
| E1 | LangChain `Runnable` / tool wrapper | P1 | M | **OPEN** | Reach |
| E2 | LlamaIndex / Haystack adapters | P2 | M | **OPEN** | Reach |
| E3 | MCP tool server: `pack_prompt` / `unpack_prompt` | P1 | M | **OPEN** | Fits Cursor / MCP world |
| E4 | GitHub Action: verify capsules in PRs | P2 | S | **OPEN** | CI integrity |
| E5 | PyPI / docs site with tutorials (MkDocs) | P1 | M | **OPEN** | Convert curiosity → usage |
| E6 | Benchmark suite: size ratio, latency, concurrent vault | P1 | M | **OPEN** | Honest claims |
| E7 | Security.txt + coordinated disclosure policy | P1 | S | **OPEN** | Trust |
| E8 | SLSA / signed releases | P3 | M | **OPEN** | Supply chain |

### Epic F — Quality, compliance, governance

| ID | Item | Pri | Effort | Status | Notes / acceptance |
|----|------|-----|--------|--------|--------------------|
| F1 | Expand security regression suite (keep verify/adversarial scripts in CI) | P0 | S | **DONE** (0.1.6) | GitHub Actions CI with security tests across Python 3.9-3.12 |
| F2 | Property-based tests (Hypothesis) for parse/round-trip | P1 | M | **OPEN** | Robustness |
| F3 | mypy strict + typed public API | P1 | S | **OPEN** | Library hygiene |
| F4 | Performance budget tests (p95 decompress) | P2 | S | **OPEN** | Catch accidental O(n²) |
| F5 | Accessibility / clarity of error messages | P2 | S | **OPEN** | DX |
| F6 | Changelog discipline + `towncrier` | P1 | S | **OPEN** | Release quality |
| F7 | Dual license review only if needed — keep MIT | Icebox | — | — | Unless commercial fork |

---

## 7. Suggested sprint slices

### Sprint 1 — “Trustworthy 0.1.4” — **DONE** (shipped as 0.1.4 / 0.1.5)

| Planned | Outcome |
|---------|---------|
| A2 trailing junk reject | **PARTIAL** — Base85 round-trip shipped; F13 residual remains |
| A3 Gist allowlist | **DONE** |
| A9 / F07 vault key-swap hardening | **DONE** |
| A6 TRUST.md | **Still open** (carry to next sprint) |
| C5 update demo API docs | **Still open** (carry) |
| F1 CI security regressions | **Still open** (carry) |
| B1–B3 demo bus harden | **Still open** (demo unchanged; no auth) |

**Exit (achieved):** Re-ran fix verification on 0.1.5 — F07/F11 closed; F13 partial; F01/F02/F06/F08/F10/F12 remain fixed.

### Sprint 2 — “Trust residuals + honesty 0.1.6” (proposed next)

- Finish **A2**: reject zlib unused tail / harden trailing malleability (close F13 residual)  
- **C9**: bump README banner to match package version  
- **A6**: TRUST.md threat model  
- **A4**: runtime/`DeprecationWarning` or loud docs on `strict=False`  
- **C5**: demo README → 0.1.5 API  
- **F1**: CI gate with `verify_fixes_0_1_5.py`  
- Optional: minimal **B1–B3** local demo bus harden (even if unpublished)

**Exit:** F13 closed or documented as accepted risk; docs version-accurate; CI blocks integrity regressions.

### Sprint 3 — “Signed capsules 0.2.0”

- **A1** optional HMAC in capsule format (closes F09 direction)  
- **C1** CLI pack/unpack/verify via real `console_scripts`  
- **C4** exception hierarchy  
- **E6** size/latency benchmarks published  

**Exit:** Documented `PROMPT_CAPSULE_HMAC_KEY` path; `promptcapsule` on PATH after install.

### Sprint 4 — “Bus + ecosystem”

- **B7** publish bus package/extra  
- **B1–B3**, **B5**, **B6** auth / limits / audit / TTL  
- **D6** multi-format payloads  
- **E3** MCP tool server  
- **D15** / **E1** one framework recipe  

**Exit:** External agent can pack via MCP and open via authenticated bus.

---

## 8. New feature pitches (one-pagers)

### Pitch 1 — Signed Capsules
**Problem:** 8-hex prefix is integrity theater against a motivated peer.  
**Solution:** Optional HMAC over canonical payload; bus can require `sig=` capsules.  
**Why now:** Security review already named F09; README admits gap.  
**Metric:** % of decompress calls with signature verified in telemetry (opt-in).

### Pitch 2 — Capsule Manifests (multi-asset handoff)
**Problem:** Agents pass “research brief + table + tool log” as one blob or many ad-hoc messages.  
**Solution:** `cap_m_…` manifest listing child capsules + roles.  
**Why now:** Natural extension of A2A story without LLM compression fiction.  
**Metric:** Demo shows 3-file handoff with one parent capsule string.

### Pitch 3 — Capsule Bus as product
**Problem:** Library alone leaves every team reinventing HTTP + auth.  
**Solution:** First-party bus with API keys, quotas, TTL, audit.  
**Why now:** Demo already exists; findings F03–F05 are the product backlog.  
**Metric:** Time-to-first-authenticated-handoff &lt; 15 minutes.

### Pitch 4 — MCP Capsule Tools
**Problem:** Agents in Cursor/Claude need pack/unpack without custom code.  
**Solution:** MCP server exposing pack/unpack/inspect.  
**Why now:** Distribution where builders already live.  
**Metric:** Weekly MCP sessions / PyPI downloads correlation.

### Pitch 5 — Secrets-aware pack
**Problem:** Vaults become secret graves.  
**Solution:** Pre-pack scanner blocks high-entropy tokens unless `allow_secrets=True`.  
**Why now:** Trust + enterprise storytelling.  
**Metric:** Blocked packs in CI examples.

### Pitch 6 — Real CLI (close docs gap)
**Problem:** Users expect `promptcapsule` on PATH; wheel has no entry point.  
**Solution:** `pack|unpack|inspect|verify` with `console_scripts`.  
**Why now:** Sprint 1 trust work landed; DX is the next adoption lever.  
**Metric:** Time-to-first-capsule without writing Python &lt; 2 minutes.

---

## 9. Explicit non-goals (next 6 months)

1. Competing with LLM *semantic* prompt compressors (LLMLingua, etc.).  
2. Becoming a general object store or vector DB.  
3. Guaranteeing confidentiality without user-managed keys.  
4. Hosting a multi-tenant SaaS vault (unless separately funded).  
5. Replacing agent memory systems (Mem0, Zep, …) — capsules are *transport*, not memory.

---

## 10. Success metrics

| Metric | Baseline (guess) | 90-day target |
|--------|------------------|---------------|
| PyPI downloads / month | early | 5× from 0.1.3 week-1 |
| GitHub stars / issues with repro | — | Healthy issue hygiene &lt;7d first response |
| Security findings reopen rate | 0.1.0 high | Zero P0 reopen after 0.1.6 (F13 residual closed) |
| Time to A2A demo | ~30 min with demo | &lt;10 min with CLI + docs |
| % decompress using `strict=True` | default | Keep default; warn on False |

---

## 11. Decision log (PO)

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-09-22 | Library ≠ bus in wheel | Clear trust boundary; README out-of-scope note |
| 2026-09-22 | Fail-closed default | Agent handoffs must not silently accept tamper |
| 2026-09-23 | Backlog prioritizes trust → signed format → bus → ecosystem | Match evidence from security review + A2A positioning |
| 2026-09-23 | Mark A3/A9/F07/F11 done after 0.1.5 PoC verification; keep F09/F13 residual/CLI/bus open | Evidence-backed only (`FIX_VERIFICATION_0_1_5.md`) |
| 2026-09-23 | Next sprint = trust residuals + doc honesty (not jump straight to HMAC) | Close F13 gap and version banner before 0.2.0 signed capsules |
| Proposed | Keep MIT; optional paid “bus cloud” later only if demand | Stay open-core friendly without bait-and-switch on core |

---

## 12. How to use this backlog

1. Pick Sprint 2 items unless strategy changes.  
2. File GitHub issues with IDs (`A2`, `B1`, …) and link this doc.  
3. Do not ship features that contradict non-goals without updating §9.  
4. Re-score priorities after each security review or user interview.

---

*Product owner backlog for PromptCapsule — living document.*
