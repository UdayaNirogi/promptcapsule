# Abstract — PromptCapsule

**PromptCapsule** is an open-source Python library for **lossless prompt packaging**: it converts LLM prompt text into a portable *capsule* string that can be shared, versioned, and reconstructed with cryptographic integrity checks.

Unlike semantic “prompt compression” tools (e.g., LLMLingua) that shorten meaning for token savings—and may alter wording—PromptCapsule **never changes the prompt content**. It uses a **hybrid strategy** quantified by a fixed threshold:

| Mode | Trigger | Mechanism | Typical portable size | Integrity |
|------|---------|-----------|----------------------|-----------|
| **Inline** | Prompt ≤ **500 bytes** | zlib (level 9) + Base85 | Often ~90–140% of original* | SHA-256 prefix in capsule |
| **Vault** | Prompt **> 500 bytes** | Store full text in a backend; emit short key | Short ID (tens of chars); **~99% smaller** than multi‑KB prompts | SHA-256 verified on retrieve |

\*Short, non-repetitive text can expand slightly due to encoding overhead; vault mode is where the portable handle shrinks dramatically.

**Quality signal (do not confuse with capsule length):** the library ships with **27+ automated test cases** covering core, backends, integrity, and integration.

### Quantified example (measured locally on v0.1.0)

| Prompt type | Original size | Capsule (portable ID) | Relative size | Mode |
|-------------|---------------|----------------------|---------------|------|
| Short system prompt | 251 chars | 248 chars | **98.8%** of original | Inline |
| Near-threshold prompt | 307 chars | 288 chars | **93.8%** of original | Inline |
| Long RAG-style context | 2,996 chars (~749 tokens†) | Short vault key (e.g. `cap_v_<hash8>_<backend_key>`) | **~1%** of original | Vault |
| Multi-shot transcript | 2,250 chars (~562 tokens†) | Short vault key | **~1%** of original | Vault |

†Token estimate ≈ characters ÷ 4 (rule of thumb; not a tokenizer). Vault key length varies by backend (InMemory vs SQLite vs Gist vs S3), not a fixed “27 characters.”

### Agent-to-agent potential

A capsule is a **message payload**. One agent can pack a prompt and hand only the capsule to another agent; the receiver unpacks it and checks `verified` before acting.

- **Inline capsules** travel alone (no shared store) — suited to short instructions.
- **Vault capsules** use a shared backend (SQLite, GitHub Gist, S3) as shared memory — suited to long context, with a much smaller handle on the wire.
- This is a **use of the existing API**, not a separate agent protocol and not encryption. Vault-mode handoff requires both agents to reach the same backend.

### What this is — and is not

- **Is:** A packaging + retrieval layer for exact prompt text (shareable IDs, vault backends, checksums), including agent-to-agent handoff of that text.
- **Is not:** An LLM that compresses meaning; not a claim of “any prompt → 8 characters” without storage; not an agent framework.

**Availability:** `pip install promptcapsule` · GitHub: [UdayaNirogi/promptcapsule](https://github.com/UdayaNirogi/promptcapsule) · PyPI: [promptcapsule](https://pypi.org/project/promptcapsule/)

**Keywords:** prompt management, lossless compression, vault retrieval, SHA-256 integrity, agent-to-agent handoff, LLM tooling, open source.
