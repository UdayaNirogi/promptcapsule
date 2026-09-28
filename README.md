# PromptCapsule

> **Pass the prompt, not the payload.**

Lossless prompt capsules with fail-closed integrity for agent-to-agent handoff.

**As simple as a string.** `pack(text)` turns a prompt into a capsule string you can store, log, or hand to another agent. `unpack(capsule)` gives back the exact original, or raises if the capsule was damaged on the way. The built-in checksum catches accidental corruption; signing (below) also catches deliberate changes.

```bash
pip install promptcapsule            # core: zero dependencies
pip install "promptcapsule[vault]"   # adds S3 and GitHub Gist backends
```

Python 3.8–3.13 · MIT · 200+ tests on Linux, macOS and Windows · [Frozen format spec](https://github.com/UdayaNirogi/promptcapsule/blob/main/SPEC.md) · [Architecture](https://github.com/UdayaNirogi/promptcapsule/blob/main/docs/ARCHITECTURE.md) · [Changelog](https://github.com/UdayaNirogi/promptcapsule/blob/main/CHANGELOG.md)

## Quick start

```python
from promptcapsule import pack, unpack

capsule = pack("You are a helpful Python coding assistant.")
# 'cap_i_45b72418_c-o81FI7k^N>xZy$Vkm8NGr`z2&gQ{$j?(q&QHnAOIJuNF3v12Nz5zJ0{}*34}|'

prompt = unpack(capsule)   # the exact original, or an exception
```

Nothing to configure. Prompts over 500 bytes are stored in a local SQLite vault, `~/.promptcapsule/vault.db`, created on first use (owner-only permissions on macOS and Linux):

```python
long_prompt = "You are a senior software architect reviewing a pull request. " * 40
capsule = pack(long_prompt)   # 'cap_v_66152d9b_sql_JME_tuuntLjuEVRztHpH4A' (key part is random)
unpack(capsule)               # works wherever that vault is available
```

A vault capsule is a checksummed reference to the stored text: the agent that unpacks it needs the same vault. To share one, point both sides at it with `PROMPT_CAPSULE_VAULT=/shared/team.db`, or pass `vault=` (a path or any backend below) to `pack` and `unpack`.

## What's in a capsule

| Mode | When | Format | What travels |
|------|------|--------|--------------|
| Inline | ≤ 500 bytes (UTF-8) | `cap_i_<checksum8>_<zlib+base85>` | The whole prompt, self-contained |
| Vault | > 500 bytes | `cap_v_<checksum8>_<key>` | A random key; the prompt stays in the vault |

Capsules are a packaging format, not a way to make prompts smaller: an inline capsule is usually a little longer than the prompt it carries, and the model always sees the full, unchanged text.

**The format is frozen.** [SPEC.md](https://github.com/UdayaNirogi/promptcapsule/blob/main/SPEC.md) defines it byte for byte, and every capsule produced since 0.1.0 will decode in every future release. CI enforces this with fixed test vectors.

## Signed capsules (authenticity)

The 8-hex (32-bit) checksum catches accidental corruption, but anyone can compute it, so it doesn't stop deliberate tampering. To detect deliberate changes, and to check that a capsule was made by someone holding a shared secret key, sign it with HMAC-SHA256:

```python
from promptcapsule import SignatureError

capsule = pack("Summarise the Q3 report", sign="shared-secret")

try:
    text = unpack(capsule, verify_signature="shared-secret")
except SignatureError:
    ...  # wrong key, tampered, or unsigned capsule: do not use
```

- **Receivers must pass the key.** When `verify_signature` is a key (or `True`), unsigned capsules — including ones with the `_sig_…` suffix stripped — are rejected before anything is decompressed or fetched from a vault. Without a key, unsigned capsules are accepted.
- `sign=True` / `verify_signature=True` read the key from `PROMPT_CAPSULE_HMAC_KEY`. Empty keys are rejected.
- The signature is a 128-bit truncated HMAC-SHA256 over the prompt text, compared in constant time.
- A valid signature proves only that the signer holds the shared key. It does not identify which key holder signed, and it does not prove when: a signed capsule can be replayed.

For metadata, use the class API: `PromptCapsule().decompress(capsule, ...)` returns a result with `.text`, `.verified` (checksum only) and `.signed` (`True` only when a signature was checked against the key).

## When to use it

- **Handing an exact prompt between agents, processes or services** through a channel that carries a single string: a queue message, a tool argument, a log line, a database column.
- **You need to catch prompts corrupted or truncated on the way**, and, with signing, prompts deliberately changed by someone without the shared key.
- **Referring to long prompts** from tickets, configs or commits without pasting them in.

## When not to use it

- **To cut tokens or cost.** PromptCapsule never shortens or rewrites what the model reads; use a prompt-optimization tool for that.
- **To keep prompts secret.** Capsules and vaults are not encrypted.
- **When the receiver can't reach your vault.** Long-prompt capsules need a vault both sides can read; otherwise send the text itself.
- **For identity, access control or replay protection.** Add those in your application.
- **For general file archiving.** Use gzip or zstd.

## Command line

```bash
echo "You are a helpful assistant" | promptcapsule pack --file -
promptcapsule pack --file long_prompt.txt        # long prompts use the default vault
promptcapsule unpack --file capsule.txt --vault team.db
promptcapsule verify --file capsule.txt           # check without printing the prompt
promptcapsule inspect --file capsule.txt --json   # mode, checksum, signed?

export PROMPT_CAPSULE_HMAC_KEY=...                 # or use --key-file PATH
promptcapsule pack --file prompt.txt --sign
promptcapsule unpack --file capsule.txt --require-signature
```

Keys are never accepted as command-line arguments, so they don't appear in process listings. Typing `export PROMPT_CAPSULE_HMAC_KEY=...` in an interactive shell records the key in shell history; prefer `--key-file` or a secrets manager.

## Backends

| Backend | Import | Notes |
|---------|--------|-------|
| In-memory | `InMemoryBackend()` | Tests and prototypes |
| SQLite | `SQLiteBackend("prompts.db")` | Local file, no dependencies; the default vault |
| GitHub Gist | `GitHubGistBackend(token=...)` | Secret (unlisted) gists: readable by anyone with the gist ID, which is in the capsule. By default, retrieval requires the gist to belong to the token's user |
| AWS S3 | `S3Backend(bucket=..., region=...)` | Keys confined to the configured prefix |

All live in `promptcapsule.backends`. Both agents must reach the same backend. Vault keys are random (`secrets.token_urlsafe`), and the capsule checksum is bound to the stored content, so swapping keys between capsules fails verification. The binding is 32 bits and isn't keyed, so it doesn't stop someone who can write to the vault; use signing for that.

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
| `VaultError` | Vault not found or unreachable, or backend failure |

`IntegrityError`, `FormatError` and `SizeLimitError` also subclass `ValueError`.

## Security model

**Provides:** exact reconstruction; detection of accidental corruption (unsigned capsules carry a 32-bit SHA-256 prefix); detection of deliberate tampering and authenticity only with HMAC signing verified with the key; zip-bomb protection (decoding is size-capped).

**Does not provide:**

- **Tamper resistance for unsigned capsules.** Anyone can recompute the checksum. Sign capsules and verify with the key.
- **Encryption.** Anyone holding an inline capsule, or with access to the vault, can read the prompt.
- **Identity or access control.** Protect your vault with its own ACLs (IAM, file permissions). GitHub secret gists have no access control: anyone with the ID can read them.
- **Replay protection.** Add your own nonce or expiry if you need it.

See [TRUST.md](https://github.com/UdayaNirogi/promptcapsule/blob/main/TRUST.md) for the full threat model.

## Development

```bash
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](https://github.com/UdayaNirogi/promptcapsule/blob/main/CONTRIBUTING.md). Report security issues privately via [GitHub Security Advisories](https://github.com/UdayaNirogi/promptcapsule/security/advisories/new) or data.pycap@gmail.com.

## License

MIT — see [LICENSE](https://github.com/UdayaNirogi/promptcapsule/blob/main/LICENSE).
