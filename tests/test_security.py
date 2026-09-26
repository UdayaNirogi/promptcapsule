"""Security regression tests mapped to fix-verification IDs (0.1.2–0.1.4).

Coverage matrix
---------------
F01 fail-open          → TestFailClosed.test_tampered_checksum_raises_by_default
F02 empty/short prefix → TestFailClosed.test_empty_checksum_prefix_rejected
                         TestFailClosed.test_short_and_invalid_prefix_rejected
F06 zlib bound         → TestSizeLimits.test_zlib_max_length_blocks_bomb
F07 key-swap           → TestVaultHardening.test_vault_key_swap_*
F08 unguessable keys   → TestVaultHardening.test_vault_keys_are_unguessable
F10 S3 prefix guard    → TestS3Guards.test_s3_prefix_and_traversal_refused
F11 Gist owner/list    → TestGistAllowlist.test_gist_owner_and_allowlist_guards
F12 HMAC NameError     → TestHmacFix.test_verify_signature_no_nameerror
F13 trailing junk      → TestCapsuleMalleability.test_trailing_*

Not asserted as "fixed" (by design / out of scope):
F03–F05 demo bus, F09 8-hex is not a MAC (documented limitation).
"""

import zlib

import pytest

from promptcapsule import FormatError, IntegrityError, PromptCapsule
from promptcapsule.backends import InMemoryBackend, S3Backend, SQLiteBackend
from promptcapsule.integrity import IntegrityChecker


class TestFailClosed:
    def test_tampered_checksum_raises_by_default(self):
        """F01: strict=True raises IntegrityError on bad checksum."""
        pc = PromptCapsule()
        capsule = pc.compress("hello integrity")
        parts = capsule.split("_")
        wrong = f"cap_i_deadbeef_{parts[-1]}"
        with pytest.raises(IntegrityError):
            pc.decompress(wrong)

    def test_strict_false_returns_unverified(self):
        """F01 legacy path: strict=False may return text with verified=False (inline)."""
        pc = PromptCapsule()
        capsule = pc.compress("hello integrity")
        parts = capsule.split("_")
        wrong = f"cap_i_deadbeef_{parts[-1]}"
        result = pc.decompress(wrong, strict=False)
        assert result.verified is False
        assert result.text == "hello integrity"

    def test_empty_checksum_prefix_rejected(self):
        """F02: empty prefix must not verify."""
        pc = PromptCapsule()
        capsule = pc.compress("abc")
        payload = capsule.split("_", 3)[-1]
        empty_prefix = f"cap_i__{payload}"
        with pytest.raises(IntegrityError):
            pc.decompress(empty_prefix)

    def test_short_and_invalid_prefix_rejected(self):
        """F02: short / uppercase / non-hex prefixes rejected."""
        pc = PromptCapsule()
        capsule = pc.compress("abc")
        payload = capsule.split("_", 3)[-1]
        for bad_prefix in ("ab", "ABCD1234", "ghijklmn", "1234567"):
            with pytest.raises(IntegrityError):
                pc.decompress(f"cap_i_{bad_prefix}_{payload}")


class TestSizeLimits:
    def test_compress_rejects_oversized_prompt(self):
        """F06 companion: MAX_PROMPT_SIZE on compress."""
        pc = PromptCapsule()
        huge = "x" * (pc.MAX_PROMPT_SIZE + 1)
        with pytest.raises(ValueError, match="maximum size"):
            pc.compress(huge, vault_backend=InMemoryBackend())

    def test_zlib_max_length_blocks_bomb(self):
        """F06: expansion above MAX_DECOMPRESSED_SIZE is refused."""
        pc = PromptCapsule()
        bomb = zlib.compress(b"A" * (pc.MAX_DECOMPRESSED_SIZE + 1024), level=9)
        import base64
        import hashlib

        checksum = hashlib.sha256(b"unused").hexdigest()[:8]
        encoded = base64.b85encode(bomb).decode("ascii")
        capsule = f"cap_i_{checksum}_{encoded}"
        with pytest.raises(ValueError):
            pc.decompress(capsule, strict=False)

    def test_under_cap_bomb_still_allowed_by_policy(self):
        """F06 policy note: payloads under the 10 MiB cap still decompress."""
        pc = PromptCapsule()
        data = "hello " * 50
        capsule = pc.compress(data)
        result = pc.decompress(capsule)
        assert result.verified is True
        assert result.text == data


class TestVaultHardening:
    def test_vault_keys_are_unguessable(self):
        """F08: keys are not sequential mem_00000001."""
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
        with pytest.raises(KeyError):
            backend.retrieve("mem_00000001")

    def test_vault_key_swap_fails_closed(self):
        """F07: key swap raises under strict=True."""
        backend = InMemoryBackend()
        pc = PromptCapsule()
        a = "A" * 600
        b = "B" * 600
        cap_a = pc.compress(a, vault_backend=backend)
        cap_b = pc.compress(b, vault_backend=backend)
        prefix_a = cap_a.split("_")[2]
        key_b = cap_b.split("_", 3)[-1]
        swapped = f"cap_v_{prefix_a}_{key_b}"
        with pytest.raises(IntegrityError):
            pc.decompress(swapped, vault_backend=backend)

    def test_vault_key_swap_strict_false_redacts_plaintext(self):
        """F07 (0.1.4): strict=False must not return the other agent's text."""
        backend = InMemoryBackend()
        pc = PromptCapsule()
        a = "A" * 600
        b = "B" * 600
        cap_a = pc.compress(a, vault_backend=backend)
        cap_b = pc.compress(b, vault_backend=backend)
        prefix_a = cap_a.split("_")[2]
        key_b = cap_b.split("_", 3)[-1]
        swapped = f"cap_v_{prefix_a}_{key_b}"
        result = pc.decompress(swapped, vault_backend=backend, strict=False)
        assert result.verified is False
        assert result.text == ""
        assert result.text != b

    def test_sqlite_checksum_binding(self, tmp_path):
        """Happy-path vault bind with stored checksum."""
        db = str(tmp_path / "vault.db")
        backend = SQLiteBackend(db)
        pc = PromptCapsule()
        text = "S" * 600
        capsule = pc.compress(text, vault_backend=backend)
        result = pc.decompress(capsule, vault_backend=backend)
        assert result.verified is True
        assert result.text == text


class TestCapsuleMalleability:
    def test_trailing_extra_rejected(self):
        """F13: trailing _EXTRA must not decompress."""
        pc = PromptCapsule()
        capsule = pc.compress("hello")
        with pytest.raises(ValueError, match="Base85|trailing|junk|canonical"):
            pc.decompress(capsule + "_EXTRA", strict=False)

    def test_trailing_deadbeef_rejected(self):
        """F13: other trailing junk rejected."""
        pc = PromptCapsule()
        capsule = pc.compress("hello")
        with pytest.raises(ValueError):
            pc.decompress(capsule + "_deadbeef", strict=False)
    
    def test_zlib_trailing_bytes_rejected(self):
        """F13 residual: zlib stream with trailing bytes should be rejected."""
        import base64
        
        pc = PromptCapsule()
        text = "test payload"
        
        # Create valid compressed data
        compressed = zlib.compress(text.encode("utf-8"), level=9)
        
        # Add trailing garbage bytes
        malicious = compressed + b"\xde\xad\xbe\xef"
        
        # Encode as Base85
        encoded = base64.b85encode(malicious).decode("ascii")
        checksum = pc._compute_checksum(text)
        
        # Create malicious capsule
        evil_capsule = f"cap_i_{checksum[:8]}_{encoded}"
        
        # Should be rejected even with strict=False
        with pytest.raises(FormatError):  # trailing bytes
            pc.decompress(evil_capsule, strict=False)
    
    def test_concatenated_zlib_streams_rejected(self):
        """F13 residual: multiple zlib streams concatenated should fail."""
        import base64
        
        pc = PromptCapsule()
        text1 = "first"
        text2 = "second"
        
        # Create two valid zlib streams
        stream1 = zlib.compress(text1.encode("utf-8"), level=9)
        stream2 = zlib.compress(text2.encode("utf-8"), level=9)
        
        # Concatenate them (malicious attempt)
        concatenated = stream1 + stream2
        
        encoded = base64.b85encode(concatenated).decode("ascii")
        checksum = pc._compute_checksum(text1)
        
        evil_capsule = f"cap_i_{checksum[:8]}_{encoded}"
        
        with pytest.raises(FormatError):  # trailing data
            pc.decompress(evil_capsule, strict=False)
    
    def test_incomplete_zlib_stream_rejected(self):
        """F13 residual: truncated zlib stream should fail."""
        import base64
        
        pc = PromptCapsule()
        text = "test data for truncation"
        
        # Create valid compressed data and truncate it
        compressed = zlib.compress(text.encode("utf-8"), level=9)
        truncated = compressed[:-5]  # Remove last 5 bytes
        
        encoded = base64.b85encode(truncated).decode("ascii")
        checksum = pc._compute_checksum(text)
        
        evil_capsule = f"cap_i_{checksum[:8]}_{encoded}"
        
        with pytest.raises(FormatError):  # incomplete stream
            pc.decompress(evil_capsule, strict=False)
    
    def test_valid_capsules_still_work(self):
        """Ensure F13 hardening doesn't break legitimate capsules."""
        pc = PromptCapsule()
        
        # Test various sizes and content types
        test_cases = [
            "short",
            "medium " * 10,
            "long " * 100,
            "unicode: 你好世界 🎉",
            "special\nchars\ttab\r\n",
        ]
        
        for text in test_cases:
            capsule = pc.compress(text)
            result = pc.decompress(capsule)
            assert result.text == text
            assert result.verified


class TestS3Guards:
    def test_s3_prefix_and_traversal_refused(self):
        """F10: keys outside prefix or with .. are refused before get_object."""

        class FakeS3:
            def get_object(self, **kwargs):
                raise AssertionError("get_object must not be called for bad keys")

            def put_object(self, **kwargs):
                return {}

        backend = object.__new__(S3Backend)
        backend.s3_client = FakeS3()
        backend.bucket = "bucket"
        backend.prefix = "promptcapsule/"

        with pytest.raises(KeyError, match="prefix|refused"):
            backend.retrieve_with_checksum("other/prefix/file.txt")
        with pytest.raises(KeyError, match="traversal|refused"):
            backend.retrieve_with_checksum("promptcapsule/../secrets.txt")


class TestGistAllowlist:
    def test_gist_owner_and_allowlist_guards(self):
        """F11: refuse foreign / non-allowlisted gist ids (mocked)."""
        from promptcapsule.backends import GitHubGistBackend

        class FakeOwner:
            def __init__(self, login):
                self.login = login

        class FakeFile:
            def __init__(self, content):
                self.content = content

        class FakeGist:
            def __init__(self, gid, owner_login, text="secret", checksum="abc"):
                self.id = gid
                self.owner = FakeOwner(owner_login)
                self.files = {
                    "prompt.txt": FakeFile(text),
                    "checksum.txt": FakeFile(checksum),
                }

        class FakeUser:
            login = "alice"

            def create_gist(self, **kwargs):
                return FakeGist("gist_owned", "alice")

        class FakeGithub:
            def __init__(self, token):
                self._gists = {
                    "gist_owned": FakeGist("gist_owned", "alice"),
                    "gist_other": FakeGist("gist_other", "bob", text="other"),
                }

            def get_user(self):
                return FakeUser()

            def get_gist(self, key):
                return self._gists[key]

        real_init = GitHubGistBackend.__init__

        def fake_init(self, token, *, require_owner=True, allowed_gist_ids=None):
            self.github = FakeGithub(token)
            self.user = self.github.get_user()
            self._login = self.user.login
            self.require_owner = require_owner
            self.allowed_gist_ids = (
                set(allowed_gist_ids) if allowed_gist_ids is not None else None
            )
            self._checksum_cache = {}

        GitHubGistBackend.__init__ = fake_init
        try:
            backend = GitHubGistBackend("token")
            with pytest.raises(KeyError, match="not owned|refused"):
                backend.retrieve_with_checksum("gist_other")
            text, _ = backend.retrieve_with_checksum("gist_owned")
            assert text == "secret"

            backend2 = GitHubGistBackend(
                "token", allowed_gist_ids={"only_this"}
            )
            with pytest.raises(KeyError, match="allowlist"):
                backend2.retrieve_with_checksum("gist_owned")
        finally:
            GitHubGistBackend.__init__ = real_init


class TestHmacFix:
    def test_verify_signature_no_nameerror(self):
        """F12: verify_signature works (no NameError)."""
        sig = IntegrityChecker.create_signature("data", "secret")
        assert IntegrityChecker.verify_signature("data", sig, "secret") is True
        assert IntegrityChecker.verify_signature("data", sig, "wrong") is False

    def test_empty_prefix_never_verifies(self):
        """F02 companion at IntegrityChecker layer."""
        assert IntegrityChecker.verify_checksum_prefix("x", "") is False
        assert IntegrityChecker.verify_checksum_prefix("x", "abc") is False
