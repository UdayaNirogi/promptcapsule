# Abstract — PromptCapsule

**Pass the prompt, not the payload.**

**Version:** 0.3.0 · **PyPI:** `pip install promptcapsule` · **License:** MIT

PromptCapsule is an open-source Python library for **lossless prompt capsules**: it turns prompt text into a short, portable string that one agent, process or service can hand to another, and turns it back into the exact original text on the other side, or raises an error. It never returns silently corrupted text.

The API is as simple as a string:

```python
from promptcapsule import pack, unpack

capsule = pack(prompt)   # a plain str: store it, log it, send it
prompt = unpack(capsule) # the exact original, or an exception
```

| Mode | Used for | What the capsule holds | Integrity |
|------|----------|------------------------|-----------|
| **Inline** | Prompts up to 500 bytes | The whole prompt (zlib + Base85), self-contained | SHA-256 prefix checked on every unpack |
| **Vault** | Longer prompts | A random key; the text is stored in a vault both sides can reach | SHA-256 bound to the stored text |

Long prompts go to a local SQLite vault (`~/.promptcapsule/vault.db`) with no configuration; teams can point both sides at a shared vault, S3 or GitHub Gist instead. PromptCapsule never shortens or rewrites the prompt: the model always reads the full, unchanged text.

**Optional signing:** HMAC-SHA256 with a shared secret key. A receiver that passes the key rejects unsigned, stripped or tampered capsules. A valid signature proves only that the signer holds the key.

**Stability:** the capsule format is frozen in [SPEC.md](../SPEC.md). Every capsule produced since 0.1.0 decodes in every future release, enforced by fixed test vectors in CI (Python 3.8–3.13 on Linux, macOS and Windows).

### Limitations

- Not encryption: anyone with an inline capsule or vault access can read the prompt.
- Not identity, access control or replay protection.
- Long-prompt capsules only unpack where the same vault is available.

**Availability:** GitHub [UdayaNirogi/promptcapsule](https://github.com/UdayaNirogi/promptcapsule) · PyPI [promptcapsule](https://pypi.org/project/promptcapsule/)
