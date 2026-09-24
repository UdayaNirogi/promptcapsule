"""Command-line interface for PromptCapsule."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from promptcapsule import IntegrityError, PromptCapsule
from promptcapsule.backends import InMemoryBackend, SQLiteBackend


def pack_command(args):
    """Pack a prompt into a capsule."""
    pc = PromptCapsule()
    
    # Read input
    if args.file:
        if args.file == '-':
            text = sys.stdin.read()
        else:
            text = Path(args.file).read_text(encoding='utf-8')
    elif args.text:
        text = args.text
    else:
        print("Error: Either --file or --text required", file=sys.stderr)
        return 1
    
    # Setup vault backend if needed
    vault_backend = None
    if args.vault:
        vault_backend = SQLiteBackend(args.vault)
    
    # Compress
    try:
        capsule = pc.compress(text, vault_backend=vault_backend)
        
        if args.output:
            Path(args.output).write_text(capsule, encoding='utf-8')
            print(f"✓ Capsule saved to {args.output}")
        else:
            print(capsule)
        
        if args.verbose:
            mode = "vault" if capsule.startswith("cap_v_") else "inline"
            print(f"Mode: {mode}", file=sys.stderr)
            print(f"Input size: {len(text)} bytes", file=sys.stderr)
            print(f"Capsule size: {len(capsule)} characters", file=sys.stderr)
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def unpack_command(args):
    """Unpack a capsule to retrieve the original prompt."""
    pc = PromptCapsule()
    
    # Read capsule
    if args.file:
        if args.file == '-':
            capsule = sys.stdin.read().strip()
        else:
            capsule = Path(args.file).read_text(encoding='utf-8').strip()
    elif args.capsule:
        capsule = args.capsule
    else:
        print("Error: Either --file or --capsule required", file=sys.stderr)
        return 1
    
    # Setup vault backend if needed
    vault_backend = None
    if args.vault:
        vault_backend = SQLiteBackend(args.vault)
    
    # Decompress
    try:
        result = pc.decompress(
            capsule,
            vault_backend=vault_backend,
            strict=not args.no_strict
        )
        
        if args.output:
            Path(args.output).write_text(result.text, encoding='utf-8')
            print(f"✓ Text saved to {args.output}")
        else:
            print(result.text)
        
        if args.verbose:
            print(f"\nMode: {result.mode}", file=sys.stderr)
            print(f"Verified: {result.verified}", file=sys.stderr)
            print(f"Original size: {result.original_size} bytes", file=sys.stderr)
        
        if not result.verified:
            print("\n⚠️  Warning: Integrity verification failed!", file=sys.stderr)
            if not args.no_strict:
                return 1
        
        return 0
    
    except IntegrityError as e:
        print(f"❌ Integrity Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def inspect_command(args):
    """Inspect a capsule without decompressing (show metadata)."""
    pc = PromptCapsule()
    
    # Read capsule
    if args.file:
        if args.file == '-':
            capsule = sys.stdin.read().strip()
        else:
            capsule = Path(args.file).read_text(encoding='utf-8').strip()
    elif args.capsule:
        capsule = args.capsule
    else:
        print("Error: Either --file or --capsule required", file=sys.stderr)
        return 1
    
    # Parse capsule metadata without full decompression
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
            "capsule_length": len(capsule),
        }
        
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print(f"Capsule: {info['capsule']}")
            print(f"Mode: {info['mode']}")
            print(f"Checksum prefix: {info['checksum_prefix']}")
            print(f"Length: {info['capsule_length']} characters")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def verify_command(args):
    """Verify capsule integrity without printing contents."""
    pc = PromptCapsule()
    
    # Read capsule
    if args.file:
        if args.file == '-':
            capsule = sys.stdin.read().strip()
        else:
            capsule = Path(args.file).read_text(encoding='utf-8').strip()
    elif args.capsule:
        capsule = args.capsule
    else:
        print("Error: Either --file or --capsule required", file=sys.stderr)
        return 1
    
    # Setup vault backend if needed
    vault_backend = None
    if args.vault:
        vault_backend = SQLiteBackend(args.vault)
    
    # Verify
    try:
        result = pc.decompress(capsule, vault_backend=vault_backend, strict=True)
        
        if result.verified:
            print("✓ Integrity verification PASSED")
            if args.verbose:
                print(f"Mode: {result.mode}")
                print(f"Checksum: {result.checksum[:16]}...")
                print(f"Size: {result.original_size} bytes")
            return 0
        else:
            print("❌ Integrity verification FAILED")
            return 1
    
    except IntegrityError as e:
        print(f"❌ Integrity verification FAILED: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='promptcapsule',
        description='PromptCapsule CLI - Lossless prompt packaging and retrieval',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pack a prompt from file
  promptcapsule pack --file prompt.txt
  
  # Pack from stdin
  echo "You are a helpful assistant" | promptcapsule pack --file -
  
  # Pack with vault storage
  promptcapsule pack --file long_prompt.txt --vault prompts.db
  
  # Unpack a capsule
  promptcapsule unpack --capsule "cap_i_a8f3b2_..."
  
  # Unpack from file
  promptcapsule unpack --file capsule.txt --vault prompts.db
  
  # Verify integrity
  promptcapsule verify --capsule "cap_i_a8f3b2_..."
  
  # Inspect capsule metadata
  promptcapsule inspect --capsule "cap_i_a8f3b2_..." --json
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='promptcapsule 0.1.5'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # pack command
    pack_parser = subparsers.add_parser('pack', help='Pack a prompt into a capsule')
    pack_parser.add_argument('--file', '-f', help='Input file (use - for stdin)')
    pack_parser.add_argument('--text', '-t', help='Input text directly')
    pack_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    pack_parser.add_argument('--vault', '-v', help='Vault database path (for long prompts)')
    pack_parser.add_argument('--verbose', action='store_true', help='Show detailed info')
    
    # unpack command
    unpack_parser = subparsers.add_parser('unpack', help='Unpack a capsule to retrieve prompt')
    unpack_parser.add_argument('--file', '-f', help='Capsule file (use - for stdin)')
    unpack_parser.add_argument('--capsule', '-c', help='Capsule string directly')
    unpack_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    unpack_parser.add_argument('--vault', '-v', help='Vault database path (for vault capsules)')
    unpack_parser.add_argument('--no-strict', action='store_true', help='Allow unverified capsules (not recommended)')
    unpack_parser.add_argument('--verbose', action='store_true', help='Show detailed info')
    
    # inspect command
    inspect_parser = subparsers.add_parser('inspect', help='Inspect capsule metadata')
    inspect_parser.add_argument('--file', '-f', help='Capsule file (use - for stdin)')
    inspect_parser.add_argument('--capsule', '-c', help='Capsule string directly')
    inspect_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # verify command
    verify_parser = subparsers.add_parser('verify', help='Verify capsule integrity')
    verify_parser.add_argument('--file', '-f', help='Capsule file (use - for stdin)')
    verify_parser.add_argument('--capsule', '-c', help='Capsule string directly')
    verify_parser.add_argument('--vault', '-v', help='Vault database path (for vault capsules)')
    verify_parser.add_argument('--verbose', action='store_true', help='Show detailed info')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == 'pack':
        return pack_command(args)
    elif args.command == 'unpack':
        return unpack_command(args)
    elif args.command == 'inspect':
        return inspect_command(args)
    elif args.command == 'verify':
        return verify_command(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
