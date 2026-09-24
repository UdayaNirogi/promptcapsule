"""Tests for CLI functionality."""

import subprocess
import sys
from pathlib import Path

import pytest

# Path to the CLI module
CLI_MODULE = ["python3", "-m", "promptcapsule.cli"]


def run_cli(*args):
    """Run CLI command and return result."""
    result = subprocess.run(
        CLI_MODULE + list(args),
        capture_output=True,
        text=True
    )
    return result


def test_cli_version():
    """Test --version flag."""
    result = run_cli("--version")
    assert result.returncode == 0
    assert "0.1.5" in result.stdout


def test_cli_help():
    """Test --help flag."""
    result = run_cli("--help")
    assert result.returncode == 0
    assert "PromptCapsule CLI" in result.stdout
    assert "pack" in result.stdout
    assert "unpack" in result.stdout


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
        text=True
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
