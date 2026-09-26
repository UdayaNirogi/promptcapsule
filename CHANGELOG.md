# Changelog

All notable changes to PromptCapsule. Versions follow [Semantic Versioning](https://semver.org/).

## [0.2.1] - 2026-09-26

Security fix. Everyone on 0.2.0 should upgrade.

### Security
- **Fixed signature-stripping bypass.** In 0.2.0, a receiver that passed a key still accepted a capsule whose `_sig_…` suffix had been removed, or any unsigned capsule. Passing `verify_signature="key"` (or `True`) now requires a valid signature: unsigned capsules raise `SignatureError` before anything is decompressed or fetched from a vault.
- **Empty keys are rejected.** `sign=""`, `verify_signature=""`, or an empty `PROMPT_CAPSULE_HMAC_KEY` raise `SignatureError` instead of silently producing or accepting unsigned capsules.

### CLI
- `promptcapsule --version` reports the installed version (it was hard-coded to 0.1.5).
- `pack --sign` / `--key-file PATH` create signed capsules; `unpack` and `verify` accept `--require-signature` / `--key-file`; `inspect` shows whether a capsule is signed. Keys are never taken as command-line arguments.
- `pack` / `unpack` are byte-exact through pipes and files: no added trailing newline and no line-ending translation on Windows.

### Project
- README rewritten and shortened; examples are real, generated capsules.
- CI covers Python 3.8–3.13; tagged versions publish GitHub Releases automatically.

## [0.2.0] - 2026-09-26

> **Do not use.** Signature verification in this release can be bypassed by stripping the signature. Upgrade to 0.2.1.

### Added
- **Optional HMAC-SHA256 signed capsules**: `compress(text, sign="key")` appends a signature; `decompress(capsule, verify_signature="key")` raises `SignatureError` if the key or content does not match. `sign=True` / `verify_signature=True` read the key from `PROMPT_CAPSULE_HMAC_KEY`. Signature checks are constant-time.
- **Typed exceptions**: `PromptCapsuleError` (base), `IntegrityError`, `SignatureError`, `FormatError`, `SizeLimitError`, `VaultError`. `IntegrityError`, `FormatError` and `SizeLimitError` still subclass `ValueError`.

### Fixed
- Inline capsules with trailing bytes, concatenated streams, or truncated zlib streams are rejected.
- Windows: CLI output is ASCII-only, and the SQLite backend closes connections explicitly.

## [0.1.6] - 2026-09-24

### Added
- Command-line interface with `pack`, `unpack`, `verify` and `inspect`.
- `TRUST.md` threat model.
- GitHub Actions CI on Ubuntu, macOS and Windows.
- `DeprecationWarning` when using `strict=False`.

## [0.1.5] - 2026-09-23

### Changed
- Documentation clarity: limitations (not encryption, not authentication, 8-hex checksum limits) and fixed vs open issues.

## [0.1.4]

### Security
- Base85 payloads must round-trip; trailing junk is rejected.
- On vault checksum-binding failure, returned text is empty even with `strict=False`.
- Gist backend: retrieval requires a gist owned by the token's user; optional ID allowlist.

## [0.1.3] / [0.1.2]

### Security
- Fail-closed by default: `decompress(strict=True)` raises `IntegrityError`.
- Checksum prefix must be exactly 8 lowercase hex characters.
- Compress input, capsule size and zlib expansion capped at 10 MiB.
- Vault keys generated with `secrets.token_urlsafe` instead of sequential counters.
- Vault checksum binding prevents key swaps from returning another agent's text.
- S3 keys confined to the configured prefix; `..` blocked.
