# PromptCapsule architecture

*Pass the prompt, not the payload.*

This document describes how the code in `promptcapsule/` works, as of 0.3.3.1. The byte-level format is specified in [SPEC.md](../SPEC.md) and the threat model in [TRUST.md](../TRUST.md); where this document and SPEC.md differ, SPEC.md is normative.

## 1. Purpose

PromptCapsule turns a prompt into a single string (a *capsule*) that one agent, process or service can hand to another, and turns it back into the exact original text or raises an exception. It does not shorten, rewrite or encrypt the prompt.

The core package uses only the Python standard library. The GitHub Gist and S3 backends import PyGithub and boto3 lazily, in their constructors; both come with the `promptcapsule[vault]` extra.

## 2. Modules

| Module | Role |
|--------|------|
| `simple.py` | The two-function API, `pack(text) -> str` and `unpack(capsule) -> str`, and the default SQLite vault (`default_vault_path()`, `resolve_vault()`). |
| `core.py` | `PromptCapsule` (encoding and decoding), `CapsuleResult` (decode result), and the `VaultBackend` base class. |
| `backends.py` | Vault backends: `InMemoryBackend`, `SQLiteBackend`, `GitHubGistBackend`, `S3Backend`. |
| `integrity.py` | `IntegrityChecker`: SHA-256 hashing and HMAC-SHA256 helpers. `core.py` uses it to create signatures; its other helpers are exported utilities, and the decode path does its own comparisons. |
| `exceptions.py` | The exception hierarchy (section 8). |
| `cli.py` | The `promptcapsule` command (`pack`, `unpack`, `inspect`, `verify`). |
| `__init__.py` | Public exports and `__version__`. |

## 3. Capsule types

The size of the text in UTF-8 bytes decides the type (`PromptCapsule.INLINE_THRESHOLD` is 500):

| Type | Chosen when | String | What it carries |
|------|-------------|--------|-----------------|
| Inline | text ≤ 500 bytes | `cap_i_<checksum8>_<payload>` | The whole prompt: `base64.b85encode(zlib.compress(utf8, level=9))` |
| Vault | text > 500 bytes | `cap_v_<checksum8>_<key>` | A key returned by the vault backend; the text stays in the vault |

- `checksum8` is the first 8 lowercase hex characters (32 bits) of the SHA-256 of the UTF-8 text.
- A signed capsule has `_sig_<32 hex>` appended: the first 32 hex characters (128 bits) of HMAC-SHA256 over the UTF-8 text. A capsule is signed if and only if it ends with that suffix (`_SIG_SUFFIX` in `core.py`).
- Inline capsules are about as long as the prompt, and often a little longer. Vault capsules are short because the text is elsewhere.

## 4. Pack data flow

`simple.pack(text, sign=None, vault=None)`:

1. Raises `TypeError` if `text` is not a `str`.
2. If the text is 500 bytes or less, or over 10 MiB, calls `PromptCapsule.compress` without a vault, so no vault file is created (an oversized text is then rejected by `compress`).
3. Otherwise resolves the vault with `resolve_vault(vault, create=True)` and calls `compress` with it.

`PromptCapsule.compress(text, vault_backend=None, sign=None)`:

1. Rejects non-strings (`TypeError`), empty text (`FormatError`) and text over 10 MiB (`SizeLimitError`).
2. Computes the full SHA-256 hex digest of the text.
3. Resolves the signing key *before* storing anything: a string is used as the key, `True` reads `PROMPT_CAPSULE_HMAC_KEY`, and an empty or missing key raises `SignatureError`.
4. Inline: zlib level 9, then Base85. Vault: `vault_backend.store(text, checksum)` returns a key; without a backend it raises `VaultError`.
5. Appends `_sig_<hmac128>` if a key was resolved.

## 5. Unpack data flow

`simple.unpack(capsule, verify_signature=None, vault=None)` resolves a vault only for `cap_v_` capsules, with `create=False` (a missing vault file raises `VaultError` and is never created), then calls `PromptCapsule.decompress(..., strict=True)` and returns `.text`.

`PromptCapsule.decompress(capsule, vault_backend=None, strict=True, verify_signature=None)`:

1. `strict=False` emits a `DeprecationWarning`.
2. Rejects non-strings (`TypeError`), strings not starting with `cap_` (`FormatError`) and capsules over 10 MiB (`SizeLimitError`).
3. **Signature presence.** If `verify_signature` is a key or `True` and the capsule has no `_sig_` suffix, raises `SignatureError` before decoding anything or contacting a vault.
4. If the capsule is signed, the suffix is removed. Unless `verify_signature` is `False`, a key is resolved: `None` means "use `PROMPT_CAPSULE_HMAC_KEY`", and a signed capsule with no key available raises `SignatureError`.
5. **Decode.** `i_` goes to `_decompress_inline`, `v_` to `_decompress_vault` (which requires a backend, else `VaultError`); any other type raises `FormatError`.
6. `capsule_size` is set to the length of the whole capsule string.
7. **Signature check.** If a key was resolved, HMAC-SHA256 over the decoded text is truncated to 32 hex characters and compared with `hmac.compare_digest`. A mismatch raises `SignatureError`; a match sets `signed=True`.
8. **Fail closed.** If `strict` and the checksum did not verify, raises `IntegrityError`.

**Inline decoding** (`_decompress_inline`): the checksum must be exactly 8 lowercase hex characters (else `IntegrityError`). The Base85 payload must re-encode to the identical string (else `FormatError`). zlib output is capped at 10 MiB (`SizeLimitError`), and the stream must be complete with no trailing bytes (`FormatError`). The text is then decoded as UTF-8, and it is verified if its SHA-256 starts with the capsule's 8-hex prefix. Any zlib stream is accepted, whatever level or implementation produced it.

**Vault decoding** (`_decompress_vault`): after the same prefix check and an empty-key check, calls `vault_backend.retrieve_with_checksum(key)`. The record is accepted only if the stored checksum is non-empty, equals the SHA-256 of the returned text, and starts with the capsule's prefix. If not, the result's text is `""` even when `strict=False`. Backend exceptions other than PromptCapsule's own (for example `KeyError` for a missing key) are wrapped in `VaultError`.

`CapsuleResult` fields: `text`, `verified` (checksum only), `mode` (`"inline"` or `"vault"`), `checksum` (full hex), `original_size` (UTF-8 bytes), `capsule_size` (characters in the capsule string), `signed` (`True` only if a signature was verified with a key).

## 6. Vault backends

A backend subclasses `core.VaultBackend` and implements `store(text, checksum) -> key`, `retrieve(key)` and `retrieve_with_checksum(key) -> (text, checksum)`. The base class's default `retrieve_with_checksum` recomputes the checksum from the retrieved text, so for a backend that does not override it, the vault binding reduces to the 8-hex prefix check.

| Backend | Storage | Keys | Notes from the code |
|---------|---------|------|---------------------|
| `InMemoryBackend` | A dict in the process | `mem_` + `secrets.token_urlsafe(16)` | Lost when the process exits. Stores the checksum. |
| `SQLiteBackend(db_path)` | A SQLite file, table `capsules(key, text, checksum, created_at)` | `sql_` + `secrets.token_urlsafe(16)` | Creates the table on the first `store`. Reading from a missing or empty file raises `KeyError` and creates nothing. Opens a connection per operation. |
| `GitHubGistBackend(token, require_owner=True, allowed_gist_ids=None)` | A gist with `prompt.txt` and `checksum.txt`, created with `public=False` | The gist ID | `public=False` makes a GitHub *secret* gist: unlisted, but readable by anyone who has its ID, and the ID is in the capsule. `require_owner` makes retrieval refuse gists not owned by the token's user; `allowed_gist_ids` restricts retrieval to listed IDs. The gist description contains the 8-hex prefix and a timestamp. |
| `S3Backend(bucket, region, prefix="promptcapsule/")` | An S3 object; the checksum is in object metadata | `<prefix><token_urlsafe(16)>_<checksum8>.txt` | Retrieval refuses keys outside the prefix or containing a `..` path segment. |

**Default vault** (`simple.py`): `$PROMPT_CAPSULE_VAULT`, or `~/.promptcapsule/vault.db`. When `pack` first needs it, the directory is created with mode `0700` and the file with mode `0600` (effective on POSIX systems). Backends are cached per resolved path for the life of the process.

## 7. Integrity: checksum versus signing

| | Checksum (every capsule) | HMAC signature (optional) |
|--|--------------------------|---------------------------|
| What | First 32 bits of SHA-256 of the text | First 128 bits of HMAC-SHA256 of the text, keyed with a shared secret |
| Keyed | No: anyone can compute it | Yes |
| Catches | Accidental corruption and truncation | Deliberate changes by anyone without the key, and removal of the signature when the receiver passes the key |
| Does not catch | Deliberate tampering: anyone can pack new text, and text matching a given 8-hex prefix takes about 2^32 attempts (relevant when an attacker can write to the vault) | Replay of a valid capsule, or which key holder signed |
| Comparison | `str.startswith` / `==` (the checksum is not secret) | `hmac.compare_digest` (constant time) |

The signature covers only the text. A change to the type, checksum, payload encoding or vault key that alters the decoded text fails verification; a change that leaves the text identical is not detected and has no effect.

## 8. Errors

All exceptions raised for capsule problems derive from `PromptCapsuleError`. Non-string input raises `TypeError`.

| Exception | Raised for (from the code) |
|-----------|----------------------------|
| `IntegrityError` (also `ValueError`) | Malformed or empty checksum prefix; checksum mismatch or failed vault binding in strict mode (for a signed capsule opened with a key, a failed binding surfaces as `SignatureError`, because the signature is checked first) |
| `SignatureError` (subclass of `IntegrityError`) | Key given but capsule unsigned; signed capsule with no key available; wrong signature; empty key; signing requested without a key |
| `FormatError` (also `ValueError`) | Empty text; missing `cap_` prefix; unknown type; wrong number of parts; empty vault key; invalid or non-canonical Base85; invalid, incomplete or trailing zlib data; invalid UTF-8 |
| `SizeLimitError` (also `ValueError`) | Text over 10 MiB on pack; capsule over 10 MiB; decoded output over 10 MiB |
| `VaultError` | Long prompt without a backend; vault capsule without a backend; missing default vault file on unpack; backend failures, including a missing key |

## 9. Command line

`promptcapsule` (entry point `promptcapsule.cli:main`) has four commands:

- `pack` and `unpack` wrap `simple.pack` and `PromptCapsule.decompress`, reading and writing files byte-exactly. `--vault` takes a SQLite path and defaults to the default vault.
- `verify` decodes without printing the text and reports integrity and signature status. For a signed capsule with no key available it checks integrity only and warns that the signature was not checked; `--require-signature` without a key fails.
- `inspect` parses the capsule string (type, checksum prefix, whether it ends with a signature, length) without decoding or verifying it.
- Keys come from `--key-file PATH` or `PROMPT_CAPSULE_HMAC_KEY`, never from a command-line argument.

## 10. Limits

| Limit | Value | Where |
|-------|-------|-------|
| Inline threshold | 500 bytes of UTF-8 (encoder policy) | `PromptCapsule.INLINE_THRESHOLD` |
| Text | 10 MiB of UTF-8 | `MAX_PROMPT_SIZE` |
| Capsule string | 10 MiB of UTF-8 | checked in `decompress` |
| Decoded zlib output | 10 MiB | `MAX_DECOMPRESSED_SIZE` |
| Checksum in capsule | 8 hex characters (32 bits) | `CHECKSUM_PREFIX_LEN` |
| Signature | 32 hex characters (128 bits) | `_add_signature` |

## 11. What the code does not do

- **No encryption.** Inline payloads are zlib + Base85 and anyone can decode them. Vault backends store the text as-is.
- **No access control or identity.** Who can read or write a vault depends on the vault (file permissions, IAM, the GitHub token). A signature proves only that the signer holds the shared key.
- **No replay protection or expiry.** Capsules and vault records have no TTL, and a signed capsule stays valid.
- **No tamper resistance for unsigned capsules.** See section 7.
