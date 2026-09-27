"""Command-line interface for PromptCapsule."""

import argparse
import json
import os
import sys
from pathlib import Path

from promptcapsule import IntegrityError, PromptCapsule, SignatureError, __version__
from promptcapsule.core import _SIG_SUFFIX
from promptcapsule.simple import pack, resolve_vault

_NO_KEY_HINT = "pass --key-file PATH or set the PROMPT_CAPSULE_HMAC_KEY environment variable"


def _read_text(path):
    """Read text exactly: no newline translation, so round trips stay byte-identical."""
    if path == "-":
        return sys.stdin.buffer.read().decode("utf-8")
    return Path(path).read_bytes().decode("utf-8")


def _write_text(path, text):
    if path is None:
        sys.stdout.flush()
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.flush()
    else:
        Path(path).write_bytes(text.encode("utf-8"))


def _vault_for(capsule, path):
    """Vault needed to open this capsule; never creates a database file."""
    if not capsule.startswith("cap_v_"):
        return None
    return resolve_vault(path, create=False)


def _read_capsule(args):
    if args.file:
        return _read_text(args.file).strip()
    return args.capsule


def _signing_key(args, flag):
    """Resolve the HMAC key: --key-file wins, else True (PROMPT_CAPSULE_HMAC_KEY) if flag set."""
    if getattr(args, "key_file", None):
        key = Path(args.key_file).read_text(encoding="utf-8").strip()
        if not key:
            raise SignatureError(f"Key file is empty: {args.key_file}")
        return key
    return True if flag else None


def pack_command(args):
    """Pack a prompt into a capsule."""
    if args.file:
        text = _read_text(args.file)
    elif args.text:
        text = args.text
    else:
        print("Error: Either --file or --text required", file=sys.stderr)
        return 1

    try:
        sign = _signing_key(args, args.sign)
        capsule = pack(text, sign=sign, vault=args.vault)

        if args.output:
            Path(args.output).write_text(capsule, encoding="utf-8")
            print(f"[OK] Capsule saved to {args.output}")
        else:
            print(capsule)

        if args.verbose:
            mode = "vault" if capsule.startswith("cap_v_") else "inline"
            print(f"Mode: {mode}", file=sys.stderr)
            print(f"Signed: {'yes' if sign else 'no'}", file=sys.stderr)
            print(f"Input size: {len(text.encode('utf-8'))} bytes", file=sys.stderr)
            print(f"Capsule size: {len(capsule)} characters", file=sys.stderr)

        return 0

    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 1


def unpack_command(args):
    """Unpack a capsule to retrieve the original prompt."""
    pc = PromptCapsule()

    capsule = _read_capsule(args)
    if not capsule:
        print("Error: Either --file or --capsule required", file=sys.stderr)
        return 1

    try:
        vault_backend = _vault_for(capsule, args.vault)
        verify = _signing_key(args, args.require_signature)
        result = pc.decompress(
            capsule,
            vault_backend=vault_backend,
            strict=not args.no_strict,
            verify_signature=verify,
        )

        _write_text(args.output, result.text)
        if args.output:
            print(f"[OK] Text saved to {args.output}")

        if args.verbose:
            print(f"\nMode: {result.mode}", file=sys.stderr)
            print(f"Verified: {result.verified}", file=sys.stderr)
            print(f"Signed: {'yes' if result.signed else 'no'}", file=sys.stderr)
            print(f"Original size: {result.original_size} bytes", file=sys.stderr)

        if not result.verified:
            print("\n[WARN] Integrity verification failed!", file=sys.stderr)
            if not args.no_strict:
                return 1

        return 0

    except SignatureError as e:
        print(f"[ERROR] Signature Error: {e}", file=sys.stderr)
        return 1
    except IntegrityError as e:
        print(f"[ERROR] Integrity Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 1


def inspect_command(args):
    """Inspect a capsule without decompressing (show metadata)."""
    capsule = _read_capsule(args)
    if not capsule:
        print("Error: Either --file or --capsule required", file=sys.stderr)
        return 1

    try:
        if not capsule.startswith("cap_"):
            print("Error: Invalid capsule format", file=sys.stderr)
            return 1

        parts = capsule[4:].split("_", 2)
        if len(parts) < 2:
            print("Error: Invalid capsule structure", file=sys.stderr)
            return 1

        mode_char = parts[0]
        checksum_prefix = parts[1]

        mode = "inline" if mode_char == "i" else "vault" if mode_char == "v" else "unknown"

        info = {
            "capsule": capsule[:50] + "..." if len(capsule) > 50 else capsule,
            "mode": mode,
            "checksum_prefix": checksum_prefix,
            "signed": _SIG_SUFFIX.search(capsule) is not None,
            "capsule_length": len(capsule),
        }

        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print(f"Capsule: {info['capsule']}")
            print(f"Mode: {info['mode']}")
            print(f"Checksum prefix: {info['checksum_prefix']}")
            print(f"Signed: {'yes' if info['signed'] else 'no'}")
            print(f"Length: {info['capsule_length']} characters")

        return 0

    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 1


def verify_command(args):
    """Verify capsule integrity without printing contents."""
    pc = PromptCapsule()

    capsule = _read_capsule(args)
    if not capsule:
        print("Error: Either --file or --capsule required", file=sys.stderr)
        return 1

    try:
        vault_backend = _vault_for(capsule, args.vault)
        verify = _signing_key(args, args.require_signature)
        have_key = isinstance(verify, str) or bool(os.environ.get("PROMPT_CAPSULE_HMAC_KEY"))
        if verify is True and not have_key:
            print(f"[FAIL] Signature required but no key was given: {_NO_KEY_HINT}")
            return 1
        is_signed = _SIG_SUFFIX.search(capsule) is not None
        signature_unchecked = is_signed and not have_key
        result = pc.decompress(
            capsule,
            vault_backend=vault_backend,
            strict=True,
            verify_signature=False if signature_unchecked else verify,
        )

        if result.verified:
            print("[PASS] Integrity verification PASSED")
            if result.signed:
                print("[PASS] Signature verification PASSED")
            elif signature_unchecked:
                print(
                    f"[WARN] Signed, but no key was given, so the signature was NOT checked: {_NO_KEY_HINT}"
                )
            else:
                print("[INFO] Not signed: authenticity was not checked")
            if args.verbose:
                print(f"Mode: {result.mode}")
                print(f"Checksum: {result.checksum[:16]}...")
                print(f"Size: {result.original_size} bytes")
            return 0
        else:
            print("[FAIL] Integrity verification FAILED")
            return 1

    except SignatureError as e:
        print(f"[FAIL] Signature verification FAILED: {e}")
        return 1
    except IntegrityError as e:
        print(f"[FAIL] Integrity verification FAILED: {e}")
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _add_key_file(parser):
    parser.add_argument(
        "--key-file",
        metavar="PATH",
        help="Read the HMAC key from this file (implies signing / signature required)",
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="promptcapsule",
        description="PromptCapsule: pass the prompt, not the payload. Lossless prompt capsules with fail-closed integrity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pack a prompt from file
  promptcapsule pack --file prompt.txt

  # Pack from stdin
  echo "You are a helpful assistant" | promptcapsule pack --file -

  # Long prompts go to ~/.promptcapsule/vault.db ($PROMPT_CAPSULE_VAULT), or pick one
  promptcapsule pack --file long_prompt.txt --vault prompts.db

  # Sign with the key in PROMPT_CAPSULE_HMAC_KEY (or use --key-file PATH)
  promptcapsule pack --file prompt.txt --sign

  # Unpack, rejecting unsigned or tampered capsules
  promptcapsule unpack --file capsule.txt --require-signature

  # Verify integrity (and signature) without printing the prompt
  promptcapsule verify --file capsule.txt --key-file hmac.key

  # Inspect capsule metadata
  promptcapsule inspect --file capsule.txt --json

Keys are never taken as command-line arguments, so they do not appear in
process listings. Prefer --key-file over typing the key into an interactive shell.
        """,
    )

    parser.add_argument("--version", action="version", version=f"promptcapsule {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    pack_parser = subparsers.add_parser("pack", help="Pack a prompt into a capsule")
    pack_parser.add_argument("--file", "-f", help="Input file (use - for stdin)")
    pack_parser.add_argument("--text", "-t", help="Input text directly")
    pack_parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    pack_parser.add_argument(
        "--vault",
        "-v",
        help="SQLite vault path (default: ~/.promptcapsule/vault.db or $PROMPT_CAPSULE_VAULT)",
    )
    pack_parser.add_argument(
        "--sign",
        action="store_true",
        help="Sign the capsule with the key in PROMPT_CAPSULE_HMAC_KEY",
    )
    _add_key_file(pack_parser)
    pack_parser.add_argument("--verbose", action="store_true", help="Show detailed info")

    unpack_parser = subparsers.add_parser("unpack", help="Unpack a capsule to retrieve prompt")
    unpack_parser.add_argument("--file", "-f", help="Capsule file (use - for stdin)")
    unpack_parser.add_argument("--capsule", "-c", help="Capsule string directly")
    unpack_parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    unpack_parser.add_argument(
        "--vault",
        "-v",
        help="SQLite vault path (default: ~/.promptcapsule/vault.db or $PROMPT_CAPSULE_VAULT)",
    )
    unpack_parser.add_argument(
        "--require-signature",
        action="store_true",
        help="Reject unsigned capsules; verify with the key in PROMPT_CAPSULE_HMAC_KEY",
    )
    _add_key_file(unpack_parser)
    unpack_parser.add_argument(
        "--no-strict", action="store_true", help="Allow unverified capsules (not recommended)"
    )
    unpack_parser.add_argument("--verbose", action="store_true", help="Show detailed info")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect capsule metadata")
    inspect_parser.add_argument("--file", "-f", help="Capsule file (use - for stdin)")
    inspect_parser.add_argument("--capsule", "-c", help="Capsule string directly")
    inspect_parser.add_argument("--json", action="store_true", help="Output as JSON")

    verify_parser = subparsers.add_parser("verify", help="Verify capsule integrity")
    verify_parser.add_argument("--file", "-f", help="Capsule file (use - for stdin)")
    verify_parser.add_argument("--capsule", "-c", help="Capsule string directly")
    verify_parser.add_argument(
        "--vault",
        "-v",
        help="SQLite vault path (default: ~/.promptcapsule/vault.db or $PROMPT_CAPSULE_VAULT)",
    )
    verify_parser.add_argument(
        "--require-signature",
        action="store_true",
        help="Reject unsigned capsules; verify with the key in PROMPT_CAPSULE_HMAC_KEY",
    )
    _add_key_file(verify_parser)
    verify_parser.add_argument("--verbose", action="store_true", help="Show detailed info")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "pack":
        return pack_command(args)
    elif args.command == "unpack":
        return unpack_command(args)
    elif args.command == "inspect":
        return inspect_command(args)
    elif args.command == "verify":
        return verify_command(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
