# Changelog

All notable changes to PromptCapsule. Versions follow [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-09-27

Theme: **as simple as a string.**

### Added
- `pack(text) -> str` and `unpack(capsule) -> str` at the top level of the package.
- Zero-setup storage: long prompts go to a local SQLite vault at `~/.promptcapsule/vault.db` (or `$PROMPT_CAPSULE_VAULT`), created on first use with owner-only permissions. `unpack` never creates a missing vault. The CLI uses the same default, so `--vault` is optional.
- `SPEC.md`: the capsule format, frozen as version 1. Every capsule produced since 0.1.0 decodes in every future release; `tests/test_format_v1.py` enforces this with fixed test vectors, including capsules from past releases.

### Fixed
- A capsule is signed only if it *ends* with `_sig_` plus 32 lowercase hex characters. Previously `_sig_` anywhere (for example inside a vault key) was treated as a signature and the capsule failed to open.

### Changed
- Removed an unreachable zlib code path whose recompression check would have tied decoding to the encoder's zlib settings. Decoding is now documented as purely structural.

## [0.2.1.1] - 2026-09-27

### Changed
- `CapsuleResult` has a new last field, `signed`. Code that reads fields by name is unaffected; code that unpacks the result positionally into six variables must add a seventh.

### Added
- `CapsuleResult.signed`: `True` only when an HMAC signature was present and verified with a key. `verified` still covers the checksum only, so a signature-stripped capsule opened without a key now visibly reports `signed=False`.
- `promptcapsule verify` prints `Not signed: authenticity was not checked` for capsules that were not signature-verified; `unpack --verbose` shows `Signed: yes/no`.

### Fixed
- `unpack` and `verify` no longer create an empty SQLite file when the `--vault` path does not exist; they fail with `Vault database not found`.
- Opening a signed capsule without a key now says the key is needed to verify it, instead of "Signing requested".

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
