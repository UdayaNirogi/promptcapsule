"""Capsule format v1 test vectors (SPEC.md).

These strings are frozen. If a change makes any of these tests fail, the change breaks
capsules that users already have: fix the change, never the vectors.
"""

import pytest

from promptcapsule import (
    FormatError,
    IntegrityError,
    PromptCapsule,
    SignatureError,
    unpack,
)
from promptcapsule.core import VaultBackend

SHORT = "You are a helpful Python coding assistant."
LONG = "You are a senior software architect reviewing a pull request. " * 40
LONG_SHA256 = "66152d9b27f5b8ddc75e782e5d1e17cdd33cb7506fa6d7458f7d874585e75c4b"
UNI = 'Caf\u00e9 \u2713 \u4f60\u597d \U0001f30d\r\nTabs\tand "quotes"\n'

# Produced byte-for-byte identically by every release from 0.1.0 to 0.2.1.
INLINE = "cap_i_45b72418_c-o81FI7k^N>xZy$Vkm8NGr`z2&gQ{$j?(q&QHnAOIJuNF3v12Nz5zJ0{}*34}|"
# Same text compressed at zlib level 1: decoders must not depend on the encoder's settings.
INLINE_LEVEL1 = "cap_i_45b72418_cma#dFI7k^N>xZy$Vkm8NGr`z2&gQ{$j?(q&QHnAOIJuNF3v12Nz5zJ0{}*34}|"
INLINE_UNICODE = "cap_i_3f95b5bb_c-nJLOgp?%;nAGQ3QzVfc)E12!iV`iy}Vo@iAlwriFqjsN`<BQC8@<qTmY&&5(E"
# Produced by releases 0.2.0 and 0.2.1 with key "shared-secret".
INLINE_SIGNED = INLINE + "_sig_bc353d30413dc6e2003560bac8c44566"
LONG_SIG = "_sig_9d34a07baf13a678e04637ba794847c2"


class DictVault(VaultBackend):
    """Vault whose records are part of the test vectors."""

    def __init__(self, records):
        self.records = records

    def store(self, text, checksum):
        raise AssertionError("vectors are decode-only")

    def retrieve(self, key):
        return self.records[key][0]

    def retrieve_with_checksum(self, key):
        return self.records[key]


VAULT_KEYS = [
    "sql_N4I8aKfn1gQepXT-2fFeFw",  # SQLiteBackend (0.1.2+)
    "sql_20240921_120000_0001",  # sequential keys from 0.1.0/0.1.1
    "mem_q3Zx-_Yb0T1vUo9rL2kWcA",  # InMemoryBackend
    "promptcapsule/aB3_x-9.txt",  # S3Backend keys contain '/' and '.'
    "k_sig_x",  # '_sig_' inside a key is not a signature
]
VAULT = DictVault({key: (LONG, LONG_SHA256) for key in VAULT_KEYS})


@pytest.mark.parametrize(
    "capsule, text, key",
    [
        (INLINE, SHORT, None),
        (INLINE_LEVEL1, SHORT, None),
        (INLINE_UNICODE, UNI, None),
        (INLINE_SIGNED, SHORT, "shared-secret"),
    ],
)
def test_inline_vectors_decode(capsule, text, key):
    assert unpack(capsule, verify_signature=key) == text


def test_encoder_output_is_stable():
    pc = PromptCapsule()
    assert pc.compress(SHORT) == INLINE
    assert pc.compress(UNI) == INLINE_UNICODE
    assert pc.compress(SHORT, sign="shared-secret") == INLINE_SIGNED


@pytest.mark.parametrize("key", VAULT_KEYS)
def test_vault_vectors_decode(key):
    capsule = f"cap_v_66152d9b_{key}"
    result = PromptCapsule().decompress(capsule, vault_backend=VAULT)
    assert result.text == LONG
    assert result.verified is True


def test_signed_vault_vector():
    capsule = f"cap_v_66152d9b_{VAULT_KEYS[0]}{LONG_SIG}"
    result = PromptCapsule().decompress(
        capsule, vault_backend=VAULT, verify_signature="shared-secret"
    )
    assert result.text == LONG
    assert result.signed is True


@pytest.mark.parametrize(
    "capsule, error",
    [
        ("cap_i_45B72418" + INLINE[14:], IntegrityError),  # checksum must be lowercase hex
        ("cap_i_45b7241" + INLINE[14:], IntegrityError),  # checksum must be 8 chars
        ("cap_i_00000000" + INLINE[14:], IntegrityError),  # checksum mismatch
        ("cap_x_45b72418" + INLINE[14:], FormatError),  # unknown type letter
        ("CAP_i_45b72418" + INLINE[14:], FormatError),  # prefix is case-sensitive
        (INLINE + "~", FormatError),  # trailing junk in payload
        (INLINE[:-3], FormatError),  # truncated payload
        ("cap_v_66152d9b_", FormatError),  # empty vault key
    ],
)
def test_invalid_vectors_rejected(capsule, error):
    with pytest.raises(error):
        PromptCapsule().decompress(capsule, vault_backend=VAULT)


@pytest.mark.parametrize(
    "suffix",
    [
        "_sig_bc353d30413dc6e2003560bac8c4456",  # 31 hex chars
        "_sig_BC353D30413DC6E2003560BAC8C44566",  # uppercase
        "_sig_bc353d30413dc6e2003560bac8c44566_",  # not at the end
    ],
)
def test_malformed_signature_suffix_is_not_a_signature(suffix):
    with pytest.raises(SignatureError, match="unsigned"):
        PromptCapsule().decompress(INLINE + suffix, verify_signature="shared-secret")
