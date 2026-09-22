# Abstract — PromptCapsule

**Version:** 0.1.4 · **PyPI:** `pip install promptcapsule`

**PromptCapsule** is an open-source Python library for **lossless prompt packaging**: it converts LLM prompt text into a portable *capsule* string that can be shared, versioned, and reconstructed with cryptographic integrity checks.

Unlike semantic “prompt compression” tools (e.g., LLMLingua) that shorten meaning for token savings—and may alter wording—PromptCapsule **never changes the prompt content**. It uses a **hybrid strategy** quantified by a fixed threshold:

| Mode | Trigger | Mechanism | Typical portable size | Integrity |
|------|---------|-----------|----------------------|-----------|
| **Inline** | Prompt ≤ **500 bytes** | zlib (level 9) + Base85 | Often ~90–140% of original* | SHA-256 prefix in capsule |
| **Vault** | Prompt **> 500 bytes** | Store full text in a backend; emit short key | Short ID (tens of chars); **~99% smaller** than multi‑KB prompts | SHA-256 verified on retrieve |

\*Short, non-repetitive text can expand slightly due to encoding overhead; vault mode is where the portable handle shrinks dramatically.

**Limits:** max prompt / capsule / zlib expansion = **10 MiB**. Default `decompress(strict=True)` raises `IntegrityError` on failure. Vault bind failures never return foreign plaintext. Base85 rejects trailing junk. Gist retrieve requires owner (optional allowlist).

**Quality:** **81** automated tests (core + security regressions). Historical “27+” refers to core unit tests — **not** capsule character length.

### Quantified example (measured locally)

| Prompt type | Original size | Capsule (portable ID) | Relative size | Mode |
|-------------|---------------|----------------------|---------------|------|
| Short system prompt | 251 chars | 248 chars | **98.8%** of original | Inline |
| Near-threshold prompt | 307 chars | 288 chars | **93.8%** of original | Inline |
| Long RAG-style context | 2,996 chars (~749 tokens†) | Short vault key (e.g. `cap_v_<hash8>_<backend_key>`) | **~1%** of original | Vault |
| Multi-shot transcript | 2,250 chars (~562 tokens†) | Short vault key | **~1%** of original | Vault |

†Token estimate ≈ characters ÷ 4 (rule of thumb; not a tokenizer). Vault key length varies by backend.

### Agent-to-agent potential

A capsule is a **message payload**. One agent packs a prompt and hands only the capsule to another agent; the receiver unpacks it and continues only if verification succeeds (`IntegrityError` otherwise).

- **Inline capsules** travel alone (no shared store) — short instructions ≤500 bytes.
- **Vault capsules** use a shared backend as shared memory — long context; small handle on the wire.
- **Not** encryption, **not** an agent framework, **not** a MAC (8-hex prefix). Use HMAC helpers if you need authenticity.

**Availability:** `pip install promptcapsule` · GitHub: [UdayaNirogi/promptcapsule](https://github.com/UdayaNirogi/promptcapsule) · PyPI: [promptcapsule](https://pypi.org/project/promptcapsule/0.1.4/)

**Keywords:** prompt management, lossless compression, vault retrieval, SHA-256 integrity, agent-to-agent handoff, LLM tooling, open source.
