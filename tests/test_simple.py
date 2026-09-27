"""Tests for the two-function API: pack(text) -> str, unpack(capsule) -> str."""

import os
import stat
import sys

import pytest

import promptcapsule
from promptcapsule import (
    InMemoryBackend,
    IntegrityError,
    SignatureError,
    VaultError,
    default_vault_path,
    pack,
    unpack,
)

SHORT = "You are a helpful Python coding assistant."
LONG = "You are a senior software architect reviewing a pull request. " * 40


def test_exported_at_top_level():
    assert promptcapsule.pack is pack
    assert promptcapsule.unpack is unpack


@pytest.mark.parametrize(
    "text", [SHORT, LONG, "caf\u00e9 \u2713\r\nline two\n", "x" * 500, "x" * 501]
)
def test_roundtrip_with_nothing_configured(text):
    capsule = pack(text)
    assert isinstance(capsule, str)
    assert unpack(capsule) == text


def test_short_prompt_is_inline_and_never_creates_vault(isolated_default_vault):
    capsule = pack(SHORT)
    assert capsule.startswith("cap_i_")
    assert unpack(capsule) == SHORT
    assert not isolated_default_vault.exists()


def test_long_prompt_goes_to_default_vault(isolated_default_vault):
    capsule = pack(LONG)
    assert capsule.startswith("cap_v_")
    assert len(capsule) == 41
    assert isolated_default_vault.is_file()
    assert default_vault_path() == isolated_default_vault


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
def test_default_vault_is_private_to_user(isolated_default_vault):
    pack(LONG)
    assert stat.S_IMODE(os.stat(isolated_default_vault).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(isolated_default_vault.parent).st_mode) & 0o077 == 0


def test_default_vault_location_without_env(monkeypatch, tmp_path):
    monkeypatch.delenv("PROMPT_CAPSULE_VAULT", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert default_vault_path() == tmp_path / ".promptcapsule" / "vault.db"


def test_unpack_never_creates_missing_vault(tmp_path):
    capsule = pack(LONG, vault=tmp_path / "a.db")
    missing = tmp_path / "missing.db"
    with pytest.raises(VaultError, match="not found"):
        unpack(capsule, vault=missing)
    assert not missing.exists()


def test_unpack_vault_capsule_when_default_vault_missing(isolated_default_vault, tmp_path):
    capsule = pack(LONG, vault=tmp_path / "elsewhere.db")
    with pytest.raises(VaultError, match="not found"):
        unpack(capsule)
    assert not isolated_default_vault.exists()


def test_explicit_path_and_backend(tmp_path):
    db = tmp_path / "team.db"
    assert unpack(pack(LONG, vault=db), vault=str(db)) == LONG

    backend = InMemoryBackend()
    capsule = pack(LONG, vault=backend)
    assert "_mem_" in capsule
    assert unpack(capsule, vault=backend) == LONG


def test_vault_capsules_survive_process_restart(tmp_path):
    db = tmp_path / "persist.db"
    capsule = pack(LONG, vault=db)
    promptcapsule.simple._opened.clear()
    assert unpack(capsule, vault=db) == LONG


def test_signed_roundtrip_and_stripping_rejected():
    capsule = pack(SHORT, sign="k")
    assert unpack(capsule, verify_signature="k") == SHORT
    with pytest.raises(SignatureError):
        unpack(capsule.rsplit("_sig_", 1)[0], verify_signature="k")
    with pytest.raises(SignatureError):
        unpack(capsule, verify_signature="wrong")


def test_unpack_is_fail_closed():
    capsule = pack(SHORT)
    tampered = capsule[:6] + ("0" if capsule[6] != "0" else "1") + capsule[7:]
    with pytest.raises(IntegrityError):
        unpack(tampered)


def test_invalid_input_never_creates_vault(isolated_default_vault):
    with pytest.raises(TypeError):
        pack(123)
    with pytest.raises(TypeError):
        unpack(123)
    with pytest.raises(promptcapsule.SizeLimitError):
        pack("x" * (10 * 1024 * 1024 + 1))
    assert not isolated_default_vault.exists()
