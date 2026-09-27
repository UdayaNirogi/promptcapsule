"""Tests for CLI functionality."""

import os
import subprocess
import sys

import pytest

from promptcapsule import __version__

CLI_MODULE = [sys.executable, "-m", "promptcapsule.cli"]


def run_cli(*args, hmac_key=None):
    """Run CLI command and return result."""
    env = {k: v for k, v in os.environ.items() if k != "PROMPT_CAPSULE_HMAC_KEY"}
    if hmac_key is not None:
        env["PROMPT_CAPSULE_HMAC_KEY"] = hmac_key
    result = subprocess.run(
        CLI_MODULE + list(args),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return result


def test_cli_version():
    """--version reports the installed package version."""
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout.strip() == f"promptcapsule {__version__}"


def test_cli_help():
    """Test --help flag."""
    result = run_cli("--help")
    assert result.returncode == 0
    assert "PromptCapsule CLI" in result.stdout
    assert "pack" in result.stdout
    assert "unpack" in result.stdout


@pytest.mark.parametrize("text", ["line one\nline two\n", "crlf\r\nkept\r\n", "caf\u00e9 \u2713"])
def test_pipe_roundtrip_is_byte_exact(text):
    """stdin -> pack -> unpack -> stdout must not add newlines or translate line endings."""
    env = {k: v for k, v in os.environ.items() if k != "PROMPT_CAPSULE_HMAC_KEY"}
    packed = subprocess.run(
        CLI_MODULE + ["pack", "--file", "-"],
        input=text.encode("utf-8"),
        capture_output=True,
        check=True,
        env=env,
    )
    unpacked = subprocess.run(
        CLI_MODULE + ["unpack", "--file", "-"],
        input=packed.stdout,
        capture_output=True,
        check=True,
        env=env,
    )
    assert unpacked.stdout == text.encode("utf-8")


def test_pack_unpack_roundtrip(tmp_path):
    """Test pack and unpack commands."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_text = "You are a helpful assistant"
    test_file.write_text(test_text)

    # Pack
    pack_result = run_cli("pack", "--file", str(test_file))
    assert pack_result.returncode == 0
    capsule = pack_result.stdout.strip()
    assert capsule.startswith("cap_i_")

    # Unpack
    unpack_result = run_cli("unpack", "--capsule", capsule)
    assert unpack_result.returncode == 0
    assert test_text in unpack_result.stdout


def test_pack_from_stdin():
    """Test packing from stdin."""
    text = "Test prompt from stdin"
    result = subprocess.run(
        CLI_MODULE + ["pack", "--file", "-"],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.startswith("cap_i_")


def test_pack_with_text_arg():
    """Test packing with --text argument."""
    result = run_cli("pack", "--text", "Direct text input")
    assert result.returncode == 0
    assert result.stdout.startswith("cap_i_")


def test_inspect_command():
    """Test inspect command."""
    # First create a capsule
    pack_result = run_cli("pack", "--text", "Test")
    capsule = pack_result.stdout.strip()

    # Inspect it
    inspect_result = run_cli("inspect", "--capsule", capsule)
    assert inspect_result.returncode == 0
    assert "Mode: inline" in inspect_result.stdout
    assert "Checksum prefix:" in inspect_result.stdout


def test_inspect_json_output():
    """Test inspect command with JSON output."""
    pack_result = run_cli("pack", "--text", "Test")
    capsule = pack_result.stdout.strip()

    inspect_result = run_cli("inspect", "--capsule", capsule, "--json")
    assert inspect_result.returncode == 0

    import json

    data = json.loads(inspect_result.stdout)
    assert data["mode"] == "inline"
    assert "checksum_prefix" in data


def test_verify_command():
    """Test verify command."""
    pack_result = run_cli("pack", "--text", "Test prompt")
    capsule = pack_result.stdout.strip()

    verify_result = run_cli("verify", "--capsule", capsule)
    assert verify_result.returncode == 0
    assert "PASSED" in verify_result.stdout


def test_verify_tampered_capsule():
    """Test verify command with tampered capsule."""
    pack_result = run_cli("pack", "--text", "Test")
    capsule = pack_result.stdout.strip()

    # Tamper with capsule
    tampered = capsule[:-5] + "XXXXX"

    verify_result = run_cli("verify", "--capsule", tampered)
    assert verify_result.returncode == 1
    # Error messages go to stderr
    assert "FAILED" in verify_result.stdout or "Error" in verify_result.stderr


def test_pack_output_file(tmp_path):
    """Test packing to output file."""
    output_file = tmp_path / "capsule.txt"

    result = run_cli("pack", "--text", "Test", "--output", str(output_file))
    assert result.returncode == 0
    assert output_file.exists()

    capsule = output_file.read_text().strip()
    assert capsule.startswith("cap_i_")


def test_unpack_output_file(tmp_path):
    """Test unpacking to output file."""
    pack_result = run_cli("pack", "--text", "Test prompt")
    capsule = pack_result.stdout.strip()

    output_file = tmp_path / "unpacked.txt"
    result = run_cli("unpack", "--capsule", capsule, "--output", str(output_file))
    assert result.returncode == 0
    assert output_file.exists()
    assert output_file.read_text().strip() == "Test prompt"


def test_pack_with_vault(tmp_path):
    """Test packing with vault backend."""
    vault_file = tmp_path / "test_vault.db"
    long_text = "X" * 1000  # Long enough to trigger vault mode

    result = run_cli("pack", "--text", long_text, "--vault", str(vault_file))
    assert result.returncode == 0
    capsule = result.stdout.strip()
    assert capsule.startswith("cap_v_")

    # Unpack
    unpack_result = run_cli("unpack", "--capsule", capsule, "--vault", str(vault_file))
    assert unpack_result.returncode == 0
    assert long_text in unpack_result.stdout


def test_verbose_flag():
    """Test --verbose flag."""
    result = run_cli("pack", "--text", "Test", "--verbose")
    assert result.returncode == 0
    assert "Mode:" in result.stderr
    assert "Input size:" in result.stderr


def test_no_strict_warning():
    """Test --no-strict flag shows warning."""
    # Create a tampered capsule
    pack_result = run_cli("pack", "--text", "Test")
    capsule = pack_result.stdout.strip()
    parts = capsule.split("_")
    tampered = f"cap_i_deadbeef_{parts[-1]}"

    # Try with --no-strict
    result = run_cli("unpack", "--capsule", tampered, "--no-strict")
    # Should not raise error, but should warn
    assert "Warning" in result.stderr or result.returncode == 0


def test_missing_arguments():
    """Test error handling for missing arguments."""
    result = run_cli("pack")
    assert result.returncode == 1
    assert "Error" in result.stderr

    result = run_cli("unpack")
    assert result.returncode == 1
    assert "Error" in result.stderr


class TestCLISigning:
    def test_sign_with_env_key_roundtrip(self):
        capsule = run_cli("pack", "--text", "hello", "--sign", hmac_key="s3cret").stdout.strip()
        assert "_sig_" in capsule

        result = run_cli("unpack", "--capsule", capsule, "--require-signature", hmac_key="s3cret")
        assert result.returncode == 0
        assert result.stdout.strip() == "hello"

    def test_sign_with_key_file_roundtrip(self, tmp_path):
        key_file = tmp_path / "hmac.key"
        key_file.write_text("file-secret\n")

        capsule = run_cli("pack", "--text", "hello", "--key-file", str(key_file)).stdout.strip()
        assert "_sig_" in capsule

        result = run_cli("verify", "--capsule", capsule, "--key-file", str(key_file))
        assert result.returncode == 0
        assert "Signature verification PASSED" in result.stdout

    def test_stripped_signature_rejected(self):
        capsule = run_cli("pack", "--text", "hello", "--sign", hmac_key="s3cret").stdout.strip()
        stripped = capsule.rsplit("_sig_", 1)[0]

        unpack = run_cli("unpack", "--capsule", stripped, "--require-signature", hmac_key="s3cret")
        assert unpack.returncode == 1
        assert "hello" not in unpack.stdout
        assert "unsigned" in unpack.stderr

        verify = run_cli("verify", "--capsule", stripped, "--require-signature", hmac_key="s3cret")
        assert verify.returncode == 1
        assert "Signature verification FAILED" in verify.stdout

    def test_wrong_key_rejected(self):
        capsule = run_cli("pack", "--text", "hello", "--sign", hmac_key="right").stdout.strip()
        result = run_cli("unpack", "--capsule", capsule, "--require-signature", hmac_key="wrong")
        assert result.returncode == 1
        assert "hello" not in result.stdout

    def test_sign_without_key_fails(self):
        result = run_cli("pack", "--text", "hello", "--sign")
        assert result.returncode == 1
        assert "PROMPT_CAPSULE_HMAC_KEY" in result.stderr

    def test_empty_key_file_fails(self, tmp_path):
        key_file = tmp_path / "empty.key"
        key_file.write_text("\n")
        result = run_cli("pack", "--text", "hello", "--key-file", str(key_file))
        assert result.returncode == 1
        assert "empty" in result.stderr

    def test_inspect_reports_signed(self):
        capsule = run_cli("pack", "--text", "hello", "--sign", hmac_key="k").stdout.strip()
        assert "Signed: yes" in run_cli("inspect", "--capsule", capsule).stdout
        plain = run_cli("pack", "--text", "hello").stdout.strip()
        assert "Signed: no" in run_cli("inspect", "--capsule", plain).stdout

    def test_verify_without_key_says_authenticity_not_checked(self):
        capsule = run_cli("pack", "--text", "hello", "--sign", hmac_key="k").stdout.strip()
        stripped = capsule.rsplit("_sig_", 1)[0]
        result = run_cli("verify", "--capsule", stripped)
        assert result.returncode == 0
        assert "Integrity verification PASSED" in result.stdout
        assert "Not signed" in result.stdout
        assert "Signature verification PASSED" not in result.stdout

    def test_signed_capsule_without_key_error_mentions_verification(self):
        capsule = run_cli("pack", "--text", "hello", "--sign", hmac_key="k").stdout.strip()
        result = run_cli("unpack", "--capsule", capsule)
        assert result.returncode == 1
        assert "verify" in result.stderr
        assert "Signing requested" not in result.stderr


class TestCLIMissingVault:
    @pytest.mark.parametrize("command", ["unpack", "verify"])
    def test_missing_vault_is_not_created(self, tmp_path, command):
        vault_db = tmp_path / "prompts.db"
        capsule = run_cli("pack", "--text", "x" * 600, "--vault", str(vault_db)).stdout.strip()
        missing = tmp_path / "does-not-exist.db"

        result = run_cli(command, "--capsule", capsule, "--vault", str(missing))
        assert result.returncode == 1
        assert "Vault database not found" in result.stderr
        assert not missing.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
