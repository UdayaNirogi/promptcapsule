# Abstract — PromptCapsule

**Version:** 0.1.5 · **PyPI:** `pip install promptcapsule`

**PromptCapsule** is an open-source Python library for **lossless prompt packaging**: it converts LLM prompt text into a portable *capsule* string that can be shared, versioned, and reconstructed with integrity checks.

Unlike semantic “prompt compression” tools (e.g., LLMLingua) that shorten meaning for token savings—and may alter wording—PromptCapsule **never changes the prompt content**. It uses a **hybrid strategy**:

| Mode | Trigger | Mechanism | Typical portable size | Integrity |
|------|---------|-----------|----------------------|-----------|
| **Inline** | Prompt ≤ **500 bytes** | zlib (level 9) + Base85 | Often ~90–140% of original* | SHA-256 prefix in capsule |
| **Vault** | Prompt **> 500 bytes** | Store full text in a backend; emit short key | Short ID; **~99% smaller** than multi‑KB prompts | SHA-256 verified on retrieve |

\*Short, non-repetitive text can expand slightly due to encoding overhead.

**Hard limits:** max prompt / capsule / zlib expansion = **10 MiB**. Default `decompress(strict=True)` raises on failure.

**Quality:** **81 automated tests** (core + security).

### Limitations (important)

- Not encryption, not authentication, not a full MAC (8-hex SHA-256 prefix only).
- Long-prompt handoffs need a **shared vault** with proper ACLs.
- A demo HTTP “bus” is **not** part of this package.

### Agent-to-agent potential

Agents can pass a capsule instead of the full prompt; the receiver uses `decompress` and only continues if verification succeeds.

**Availability:** GitHub [UdayaNirogi/promptcapsule](https://github.com/UdayaNirogi/promptcapsule) · PyPI [promptcapsule](https://pypi.org/project/promptcapsule/)
