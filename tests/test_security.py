"""Security regression tests for Report1 findings (P0/P1)."""

import zlib

import pytest

from promptcapsule import IntegrityError, PromptCapsule
from promptcapsule.backends import InMemoryBackend, SQLiteBackend
from promptcapsule.integrity import IntegrityChecker


class TestFailClosed:
    def test_tampered_checksum_raises_by_default(self):
        pc = PromptCapsule()
        capsule = pc.compress("hello integrity")
        # Flip checksum hex nibble (positions after cap_i_)
        bad = capsule[:6] + ("0" if capsule[6] != "0" else "1") + capsule[7:]
        with pytest.raises(IntegrityError):
            pc.decompress(bad)

    def test_strict_false_returns_unverified(self):
        pc = PromptCapsule()
        capsule = pc.compress("hello integrity")
        bad = capsule[:6] + ("0" if capsule[6] != "0" else "1") + capsule[7:]
        # May fail decode if we corrupted format; craft valid format with wrong prefix
        parts = capsule.split("_")
        # cap_i_<8hex>_<payload>
        wrong = f"cap_i_deadbeef_{parts[-1]}"
        result = pc.decompress(wrong, strict=False)
        assert result.verified is False
        assert result.text == "hello integrity"

    def test_empty_checksum_prefix_rejected(self):
        pc = PromptCapsule()
        capsule = pc.compress("abc")
        payload = capsule.split("_", 3)[-1]
        empty_prefix = f"cap_i__{payload}"
        with pytest.raises(IntegrityError):
            pc.decompress(empty_prefix)


class TestSizeLimits:
    def test_compress_rejects_oversized_prompt(self):
        pc = PromptCapsule()
        huge = "x" * (pc.MAX_PROMPT_SIZE + 1)
        with pytest.raises(ValueError, match="maximum size"):
            pc.compress(huge, vault_backend=InMemoryBackend())

    def test_zlib_max_length_blocks_bomb(self):
        pc = PromptCapsule()
        # Highly compressible payload larger than MAX when expanded would be caught
        # Build a hand-crafted inline capsule with a compressed blob that expands big
        # if max_length were missing — with max_length it must fail.
        bomb = zlib.compress(b"A" * (pc.MAX_DECOMPRESSED_SIZE + 1024), level=9)
        import base64
        import hashlib

        # Fake checksum for format only; decompress should fail on max_length first
        checksum = hashlib.sha256(b"unused").hexdigest()[:8]
        encoded = base64.b85encode(bomb).decode("ascii")
        capsule = f"cap_i_{checksum}_{encoded}"
        with pytest.raises(ValueError):
            pc.decompress(capsule, strict=False)


class TestVaultHardening:
    def test_vault_keys_are_unguessable(self):
        backend = InMemoryBackend()
        pc = PromptCapsule()
        long = "y" * 600
        c1 = pc.compress(long, vault_backend=backend)
        c2 = pc.compress(long + "z", vault_backend=backend)
        k1 = c1.split("_", 3)[-1]
        k2 = c2.split("_", 3)[-1]
        assert k1 != k2
        assert not k1.endswith("00000001")
        assert "mem_" in k1

    def test_vault_key_swap_fails_closed(self):
        backend = InMemoryBackend()
        pc = PromptCapsule()
        a = "A" * 600
        b = "B" * 600
        cap_a = pc.compress(a, vault_backend=backend)
        cap_b = pc.compress(b, vault_backend=backend)
        # Swap B's key into A's capsule (prefix from A, key from B)
        prefix_a = cap_a.split("_")[2]
        key_b = cap_b.split("_", 3)[-1]
        swapped = f"cap_v_{prefix_a}_{key_b}"
        with pytest.raises(IntegrityError):
            pc.decompress(swapped, vault_backend=backend)

    def test_sqlite_checksum_binding(self, tmp_path):
        db = str(tmp_path / "vault.db")
        backend = SQLiteBackend(db)
        pc = PromptCapsule()
        text = "S" * 600
        capsule = pc.compress(text, vault_backend=backend)
        result = pc.decompress(capsule, vault_backend=backend)
        assert result.verified is True
        assert result.text == text


class TestHmacFix:
    def test_verify_signature_no_nameerror(self):
        sig = IntegrityChecker.create_signature("data", "secret")
        assert IntegrityChecker.verify_signature("data", sig, "secret") is True
        assert IntegrityChecker.verify_signature("data", sig, "wrong") is False

    def test_empty_prefix_never_verifies(self):
        assert IntegrityChecker.verify_checksum_prefix("x", "") is False
        assert IntegrityChecker.verify_checksum_prefix("x", "abc") is False
