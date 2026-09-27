# PromptCapsule Capsule Format, Version 1

**Status: frozen.** This document describes every capsule produced by promptcapsule 0.1.0 and later. It is normative: an implementation in any language that follows it can create and open capsules interchangeably with the Python package.

The key words MUST, MUST NOT, SHOULD and MAY are used as in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## 1. Compatibility promise

1. Every valid v1 capsule decodes to the same text in every future release of promptcapsule.
2. Future releases MAY change encoder *policy* (for example the inline size threshold or the zlib compression level), but MUST only produce capsules that are valid under this document.
3. An incompatible format, if ever needed, MUST use a new type letter. The letters `i` and `v` are never reused. v1 decoders reject unknown type letters with `FormatError`, so an old decoder can never silently misread a newer capsule.
4. Vault files written by the built-in SQLite backend (section 7) remain readable by future releases.
5. The test vectors in section 10 are enforced by [`tests/test_format_v1.py`](tests/test_format_v1.py) on every CI run. They MUST NOT be edited.

## 2. Syntax

```abnf
capsule   = "cap_" body [signature]
body      = inline / vault
inline    = "i_" checksum "_" payload
vault     = "v_" checksum "_" key
checksum  = 8LHEX
signature = "_sig_" 32LHEX
payload   = 1*B85CHAR
key       = 1*%x21-7E          ; visible ASCII, opaque to the decoder
LHEX      = %x30-39 / %x61-66  ; 0-9 a-f (lowercase only)
B85CHAR   = ALPHA / DIGIT / "!" / "#" / "$" / "%" / "&" / "(" / ")" / "*" / "+" / "-"
          / ";" / "<" / "=" / ">" / "?" / "@" / "^" / "_" / "`" / "{" / "|" / "}" / "~"
```

All matching is case-sensitive. A capsule contains no whitespace.

## 3. Parsing

A decoder MUST parse a capsule string `s` as follows:

1. `s` MUST start with `cap_`; otherwise `FormatError`.
2. **Signature.** `s` is signed if and only if it ends with `_sig_` followed by exactly 32 lowercase hex characters (regular expression `_sig_[0-9a-f]{32}\Z`). If so, remove that suffix and keep the 32 characters as the signature. The substring `_sig_` anywhere else, or a malformed suffix, does not make a capsule signed.
3. **Type.** The character after `cap_` is the type letter: `i` (inline) or `v` (vault), followed by `_`. Any other letter is a `FormatError`.
4. **Checksum.** The next characters up to the following `_` are the checksum. They MUST be exactly 8 lowercase hex characters; otherwise `IntegrityError`.
5. **Rest.** Everything after that `_` is the payload (inline) or key (vault), and MUST be non-empty. Keys may themselves contain `_`.

## 4. Text and checksum

- The text is a non-empty Unicode string, encoded as UTF-8. It is not normalized: line endings, Unicode normalization form and trailing whitespace are preserved exactly.
- The text MUST be at most 10 MiB (10,485,760 bytes) of UTF-8.
- `checksum` is the first 8 characters of the lowercase hex SHA-256 digest of the UTF-8 bytes.

A decoded capsule is **verified** only if the checksum of the decoded text matches. Decoders SHOULD fail closed (raise instead of returning unverified text).

The checksum is not keyed and is only 32 bits, so "verified" means "not accidentally corrupted". It does not resist deliberate tampering: anyone can pack different text into a new capsule, and text that matches a given checksum can be found in about 2^32 attempts, which matters when an attacker can write to the vault. Use signatures (section 8) to detect deliberate changes.

## 5. Inline capsules

```
payload = Base85( zlib( UTF-8(text) ) )
```

- **zlib:** a single zlib stream ([RFC 1950](https://www.rfc-editor.org/rfc/rfc1950), deflate with the 2-byte header and Adler-32 trailer). Any compression level, strategy or zlib implementation is valid. Decoders MUST reject a stream that is incomplete or followed by extra bytes, and MUST stop with `SizeLimitError` if the output exceeds 10 MiB.
- **Base85:** the [RFC 1924](https://www.rfc-editor.org/rfc/rfc1924) alphabet, in value order 0–84:

  ```
  0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~
  ```

  Each 4-byte group, read big-endian, becomes 5 characters. There is no padding: a final group of *n* bytes (1–3) is encoded as *n*+1 characters. This is exactly Python's `base64.b85encode(data)`. Decoders MUST reject payloads that do not re-encode to the identical string.

The reference encoder uses zlib level 9 and chooses inline for texts of 500 bytes or less. Both are policy, not format: decoders MUST accept inline capsules of any size within the limits.

## 6. Vault capsules

The key refers to a record in a vault that both sides can reach. The key is opaque to the decoder. A decoder:

1. Asks the vault for the record `(text, stored_checksum)` under `key`, where `stored_checksum` is the full 64-character SHA-256 hex digest saved with the text.
2. Accepts the record only if `SHA-256(text) == stored_checksum` **and** `stored_checksum` starts with the capsule's `checksum`. Otherwise the capsule is unverified and its text MUST NOT be returned, even in non-strict mode.

Key shapes produced by the built-in backends (informative): `sql_<22 url-safe chars>`, `mem_<22 url-safe chars>`, GitHub gist IDs (hex), and S3 object keys such as `promptcapsule/<token>_<checksum8>.txt`.

## 7. Built-in SQLite vault (stable storage layout)

The default vault used by `pack()` / `unpack()` is a SQLite file at `$PROMPT_CAPSULE_VAULT`, or `~/.promptcapsule/vault.db` when that is unset. Its table is:

```sql
CREATE TABLE IF NOT EXISTS capsules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    text TEXT NOT NULL,
    checksum TEXT NOT NULL,          -- full SHA-256 hex of text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

Future releases MAY add columns or tables but MUST keep reading rows in this layout.

## 8. Signatures

```
signature = first 32 characters of lowercase hex HMAC-SHA256(key = UTF-8(secret), message = UTF-8(text))
```

- The signature (128 bits) covers the text only, not the type, checksum, payload encoding or vault key. Any change to those that alters the decoded text therefore fails verification; a change that leaves the text identical (for example a different zlib encoding of it) is not detected and has no effect on what the receiver gets.
- Secrets MUST be non-empty. Verifiers MUST compare signatures in constant time.
- A verifier that is given a secret MUST reject unsigned capsules (including capsules whose signature suffix was removed) before decoding the payload or contacting a vault.
- A signature proves possession of the secret, not freshness: a signed capsule can be replayed.

## 9. Limits

| Item | Maximum |
|------|---------|
| Capsule string | 10 MiB of UTF-8 |
| Text (before compression) | 10 MiB of UTF-8 |
| Decompressed inline payload | 10 MiB |

## 10. Test vectors

`SHORT` is `You are a helpful Python coding assistant.` (42 bytes). `LONG` is `You are a senior software architect reviewing a pull request. ` repeated 40 times (2,480 bytes), whose SHA-256 is `66152d9b27f5b8ddc75e782e5d1e17cdd33cb7506fa6d7458f7d874585e75c4b`.

```
# SHORT, as produced by every release from 0.1.0 to 0.2.1
cap_i_45b72418_c-o81FI7k^N>xZy$Vkm8NGr`z2&gQ{$j?(q&QHnAOIJuNF3v12Nz5zJ0{}*34}|

# SHORT, zlib level 1 (decoders must not depend on encoder settings)
cap_i_45b72418_cma#dFI7k^N>xZy$Vkm8NGr`z2&gQ{$j?(q&QHnAOIJuNF3v12Nz5zJ0{}*34}|

# SHORT, signed with secret "shared-secret"
cap_i_45b72418_c-o81FI7k^N>xZy$Vkm8NGr`z2&gQ{$j?(q&QHnAOIJuNF3v12Nz5zJ0{}*34}|_sig_bc353d30413dc6e2003560bac8c44566

# LONG, vault record (LONG, 66152d9b27f5b8ddc75e782e5d1e17cdd33cb7506fa6d7458f7d874585e75c4b)
# stored under key sql_N4I8aKfn1gQepXT-2fFeFw
cap_v_66152d9b_sql_N4I8aKfn1gQepXT-2fFeFw

# LONG, same vault record, signed with secret "shared-secret"
cap_v_66152d9b_sql_N4I8aKfn1gQepXT-2fFeFw_sig_9d34a07baf13a678e04637ba794847c2
```

More vectors (Unicode, unusual vault keys, and invalid capsules that MUST be rejected) are in [`tests/test_format_v1.py`](tests/test_format_v1.py).
