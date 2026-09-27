# PromptCapsule

**Pass the prompt, not the payload.** Lossless prompt capsules for agent-to-agent handoff: inline when small, vault-backed when large, fail-closed integrity by default.

```bash
pip install promptcapsule            # core: zero dependencies
pip install "promptcapsule[vault]"   # adds S3 and GitHub Gist backends
```

Python 3.8–3.13 · MIT · 130+ tests on Linux, macOS and Windows · [Changelog](https://github.com/UdayaNirogi/promptcapsule/blob/main/CHANGELOG.md)

## What it does

A capsule is a short string one agent hands to another. The receiver gets the exact original prompt back, or an exception — never silently corrupted text.

| Mode | When | Format | What travels |
|------|------|--------|--------------|
| Inline | ≤ 500 bytes (UTF-8) | `cap_i_<checksum8>_<zlib+base85>` | The whole prompt, self-contained |
| Vault | > 500 bytes | `cap_v_<checksum8>_<key>` | A random key; the prompt stays in a shared backend |

Inline capsules are about packaging, not shrinking: very short prompts get *longer* (a 42-byte prompt becomes a 78-character capsule). The size win is vault mode, where a 2,480-byte prompt becomes a 41-character capsule.

## Quick start

```python
from promptcapsule import PromptCapsule, IntegrityError
from promptcapsule.backends import SQLiteBackend

pc = PromptCapsule()

capsule = pc.compress("You are a helpful Python coding assistant.")
# cap_i_45b72418_c-o81FI7k^N>xZy$Vkm8NGr`z2&gQ{$j?(q&QHnAOIJuNF3v12Nz5zJ0{}*34}|

vault = SQLiteBackend("prompts.db")
long_prompt = "You are a senior software architect reviewing a pull request. " * 40
long_capsule = pc.compress(long_prompt, vault_backend=vault)
# cap_v_66152d9b_sql_JME_tuuntLjuEVRztHpH4A  (the key part is random)

try:
    text = pc.decompress(long_capsule, vault_backend=vault).text
except IntegrityError:
    ...  # tampered or corrupted: do not use
```

`decompress` is strict by default: a checksum mismatch raises `IntegrityError`.

## Signed capsules (authenticity)

The 8-hex checksum detects corruption, but anyone can compute it. To know a capsule came from someone holding a shared secret, sign it with HMAC-SHA256:

```python
from promptcapsule import SignatureError

capsule = pc.compress("Summarise the Q3 report", sign="shared-secret")

try:
    text = pc.decompress(capsule, verify_signature="shared-secret").text
except SignatureError:
    ...  # wrong key, tampered, or unsigned capsule: do not use
```

- **Receivers must pass the key.** When `verify_signature` is a key (or `True`), unsigned capsules — including ones with the `_sig_…` suffix stripped — are rejected before anything is decompressed or fetched from a vault. With the default `verify_signature=None`, unsigned capsules are accepted.
- `result.verified` covers the checksum (integrity) only. `result.signed` is `True` only when a signature was checked against the key, so a stripped capsule opened without a key reports `verified=True, signed=False`.
- `sign=True` / `verify_signature=True` read the key from `PROMPT_CAPSULE_HMAC_KEY`. Empty keys are rejected.
- The signature is a 128-bit truncated HMAC-SHA256 over the prompt text, compared in constant time.
- Signing proves who created the prompt, not when: a valid capsule can be replayed.

## Command line

```bash
echo "You are a helpful assistant" | promptcapsule pack --file -
promptcapsule pack --file long_prompt.txt --vault prompts.db
promptcapsule unpack --file capsule.txt --vault prompts.db
promptcapsule verify --file capsule.txt           # check without printing the prompt
promptcapsule inspect --file capsule.txt --json   # mode, checksum, signed?

export PROMPT_CAPSULE_HMAC_KEY=...                 # or use --key-file PATH
promptcapsule pack --file prompt.txt --sign
promptcapsule unpack --file capsule.txt --require-signature
```

Keys are never accepted as command-line arguments, so they stay out of shell history and process listings.

## Backends

| Backend | Import | Notes |
|---------|--------|-------|
| In-memory | `InMemoryBackend()` | Tests and prototypes |
| SQLite | `SQLiteBackend("prompts.db")` | Local file, no dependencies |
| GitHub Gist | `GitHubGistBackend(token=...)` | Private gists; retrieval requires the gist to belong to the token's user |
| AWS S3 | `S3Backend(bucket=..., region=...)` | Keys confined to the configured prefix |

All live in `promptcapsule.backends`. Both agents must reach the same backend. Vault keys are random (`secrets.token_urlsafe`), and the capsule checksum is bound to the stored content, so swapping keys between capsules fails verification.

Custom backend: subclass `promptcapsule.core.VaultBackend` and implement `store(text, checksum) -> key`, `retrieve(key)`, and `retrieve_with_checksum(key) -> (text, checksum)`.

## Limits

| Limit | Value |
|-------|-------|
| Inline threshold | 500 bytes |
| Max prompt / capsule / decompressed size | 10 MiB each (blocks zip bombs) |
| Checksum in capsule | First 8 hex chars of SHA-256 |

Oversized input raises `SizeLimitError`.

## Errors

All exceptions derive from `PromptCapsuleError`:

| Exception | Raised when |
|-----------|-------------|
| `IntegrityError` | Checksum mismatch, bad checksum prefix, vault content mismatch |
| `SignatureError` | Wrong key, tampered or missing signature (subclass of `IntegrityError`) |
| `FormatError` | Malformed capsule, trailing or truncated zlib data |
| `SizeLimitError` | Input or output over 10 MiB |
| `VaultError` | Vault capsule without a backend, or backend failure |

`IntegrityError`, `FormatError` and `SizeLimitError` also subclass `ValueError`.

## Security model

**Provides:** exact reconstruction; tamper and corruption detection; optional authenticity with a shared secret; bounded decompression.

**Does not provide:**

- **Encryption.** Anyone holding an inline capsule, or with access to the vault, can read the prompt.
- **Identity or access control.** Protect your vault with its own ACLs (IAM, private gists, file permissions).
- **Replay protection.** Add your own nonce or expiry if you need it.

See [TRUST.md](https://github.com/UdayaNirogi/promptcapsule/blob/main/TRUST.md) for the full threat model.

## How it compares

| Tool | Approach | Trade-off |
|------|----------|-----------|
| LLMLingua | Lossy semantic compression | Smaller prompts, but not exact |
| LangChain Hub | Hosted prompt registry | Tied to the LangChain ecosystem |
| zlib directly | General compression | No integrity, no vault, no signing |
| **PromptCapsule** | Lossless capsule + pluggable vault | Needs a shared backend for long prompts |

## Development

```bash
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](https://github.com/UdayaNirogi/promptcapsule/blob/main/CONTRIBUTING.md). Report security issues privately via [GitHub Security Advisories](https://github.com/UdayaNirogi/promptcapsule/security/advisories/new) or data.pycap@gmail.com.

## License

MIT — see [LICENSE](https://github.com/UdayaNirogi/promptcapsule/blob/main/LICENSE).
