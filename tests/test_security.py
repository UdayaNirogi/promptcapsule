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

    def test_vault_key_swap_strict_false_redacts_plaintext(self):
        """F07 residual: even strict=False must not return the other agent's text."""
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
        """F13: trailing _EXTRA must not decompress as verified."""
        pc = PromptCapsule()
        capsule = pc.compress("hello")
        with pytest.raises(ValueError, match="Base85|trailing|junk|canonical"):
            pc.decompress(capsule + "_EXTRA", strict=False)

    def test_trailing_deadbeef_rejected(self):
        pc = PromptCapsule()
        capsule = pc.compress("hello")
        with pytest.raises(ValueError):
            pc.decompress(capsule + "_deadbeef", strict=False)


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

        import promptcapsule.backends as backends_mod  # noqa: F401

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
            # Foreign owner refused
            with pytest.raises(KeyError, match="not owned|refused"):
                backend.retrieve_with_checksum("gist_other")
            # Own gist OK
            text, _ = backend.retrieve_with_checksum("gist_owned")
            assert text == "secret"

            # Allowlist refuses even own gist if not listed
            backend2 = GitHubGistBackend(
                "token", allowed_gist_ids={"only_this"}
            )
            with pytest.raises(KeyError, match="allowlist"):
                backend2.retrieve_with_checksum("gist_owned")
        finally:
            GitHubGistBackend.__init__ = real_init


class TestHmacFix:
    def test_verify_signature_no_nameerror(self):
        sig = IntegrityChecker.create_signature("data", "secret")
        assert IntegrityChecker.verify_signature("data", sig, "secret") is True
        assert IntegrityChecker.verify_signature("data", sig, "wrong") is False

    def test_empty_prefix_never_verifies(self):
        assert IntegrityChecker.verify_checksum_prefix("x", "") is False
        assert IntegrityChecker.verify_checksum_prefix("x", "abc") is False
