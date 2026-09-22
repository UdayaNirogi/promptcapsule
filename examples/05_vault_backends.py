"""
Comprehensive examples of using each vault storage backend with PromptCapsule.

This file demonstrates:
1. InMemoryBackend - for testing and development
2. SQLiteBackend - for local persistent storage
3. GitHubGistBackend - for cloud-based storage via GitHub
4. S3Backend - for scalable cloud storage via AWS
"""

from promptcapsule.core import PromptCapsule
from promptcapsule.backends import (
    InMemoryBackend,
    SQLiteBackend,
    GitHubGistBackend,
    S3Backend,
)


# =============================================================================
# EXAMPLE 1: IN-MEMORY BACKEND (Testing & Development)
# =============================================================================
def example_inmemory_backend():
    """
    Use InMemoryBackend for:
    - Unit testing and integration testing
    - Development and prototyping
    - Ephemeral storage (data lost on restart)
    - No external dependencies or setup required
    
    ✅ Pros:
       - No setup required
       - Fast (all in RAM)
       - Perfect for testing
       - No external services needed
    
    ❌ Cons:
       - Data lost on application restart
       - Not suitable for production
       - Limited by available RAM
    """
    print("=" * 70)
    print("EXAMPLE 1: IN-MEMORY BACKEND")
    print("=" * 70)
    
    # Initialize
    backend = InMemoryBackend()
    capsule = PromptCapsule()
    
    # Long prompt example
    long_prompt = """
    You are an expert AI assistant with deep knowledge in multiple domains.
    Your task is to provide comprehensive, accurate, and helpful responses.
    Consider the user's context, preferences, and level of expertise.
    Always prioritize clarity, accuracy, and usefulness in your responses.
    """ * 10  # Make it long enough to trigger vault mode
    
    # Compress and store
    compressed = capsule.compress(long_prompt, vault_backend=backend)
    print(f"✅ Compressed prompt: {compressed[:50]}...")
    print(f"   Original size: {len(long_prompt)} bytes")
    print(f"   Capsule size: {len(compressed)} bytes")
    print(f"   Compression ratio: {len(compressed)/len(long_prompt)*100:.1f}%")
    
    # Decompress and retrieve
    result = capsule.decompress(compressed, vault_backend=backend)
    print(f"\n✅ Decompressed successfully!")
    print(f"   Verified: {result.verified}")
    print(f"   Mode: {result.mode}")
    print(f"   Text preview: {result.text[:60]}...")
    
    # Verify integrity
    assert result.text == long_prompt, "Integrity check failed!"
    print("✅ Integrity verification PASSED!")
    print()


# =============================================================================
# EXAMPLE 2: SQLITE BACKEND (Local Persistent Storage)
# =============================================================================
def example_sqlite_backend():
    """
    Use SQLiteBackend for:
    - Local application storage
    - Persistent caching of compressed prompts
    - Development environments
    - Single-machine deployments
    
    ✅ Pros:
       - Persistent storage on disk
       - No external services needed
       - Built into Python
       - Good for local development
       - Easy to backup and version control
    
    ❌ Cons:
       - Not suitable for distributed systems
       - SQLite has concurrency limitations
       - File-based (single machine)
       - Performance degrades with large datasets
    
    Security Considerations:
    - SQLite file should have restricted file permissions (600)
    - Keep database file in a secure location
    - Consider encrypting the database file
    - Use connection timeout for production
    """
    print("=" * 70)
    print("EXAMPLE 2: SQLITE BACKEND (Local Persistent Storage)")
    print("=" * 70)
    
    # Initialize with custom database path
    db_path = "/tmp/promptcapsule_demo.db"
    backend = SQLiteBackend(db_path=db_path)
    capsule = PromptCapsule()
    
    # Example 1: Store a system prompt
    system_prompt = """
    You are a customer support specialist for an e-commerce platform.
    Handle customer inquiries with empathy and professionalism.
    Always aim to resolve issues on the first contact.
    """ * 5
    
    compressed1 = capsule.compress(system_prompt, vault_backend=backend)
    print(f"✅ Stored system prompt: {compressed1}")
    
    # Example 2: Store a user instruction prompt
    instruction_prompt = """
    Analyze the given text for:
    1. Sentiment (positive, negative, neutral)
    2. Key entities (people, places, organizations)
    3. Main topics discussed
    4. Recommended actions
    """ * 5
    
    compressed2 = capsule.compress(instruction_prompt, vault_backend=backend)
    print(f"✅ Stored instruction prompt: {compressed2}")
    
    # Retrieve and verify
    result1 = capsule.decompress(compressed1, vault_backend=backend)
    result2 = capsule.decompress(compressed2, vault_backend=backend)
    
    print(f"\n✅ Retrieved {2} prompts from SQLite database")
    print(f"   Prompt 1 verified: {result1.verified}")
    print(f"   Prompt 2 verified: {result2.verified}")
    
    # Verify integrity
    assert result1.text == system_prompt, "Integrity check 1 failed!"
    assert result2.text == instruction_prompt, "Integrity check 2 failed!"
    print("✅ All integrity checks PASSED!")
    print(f"   Database location: {db_path}")
    print()


# =============================================================================
# EXAMPLE 3: GITHUB GIST BACKEND (Cloud-Based Storage)
# =============================================================================
def example_github_gist_backend():
    """
    Use GitHubGistBackend for:
    - Cloud-based persistent storage
    - Version control friendly approach
    - Accessible from multiple machines
    - Built-in GitHub privacy controls
    
    ✅ Pros:
       - Cloud-based (accessible anywhere)
       - GitHub provides version history
       - Private gists by default
       - Free tier available
       - Good for sharing with teams
    
    ❌ Cons:
       - Requires GitHub account and token
       - API rate limits (60 requests/hour for unauthenticated)
       - Network latency
       - GitHub terms of service compliance
       - Token security concerns
    
    Security Considerations:
    - CRITICAL: Never commit tokens to version control
    - Use GitHub environment secrets in CI/CD
    - Rotate tokens regularly
    - Use fine-grained personal access tokens with minimal scopes
    - Ensure gists are set to private
    - Audit GitHub token usage regularly
    
    Setup Instructions:
    1. Create GitHub Personal Access Token at:
       https://github.com/settings/tokens
    2. Grant 'gist' scope only
    3. Store token in environment variable: GITHUB_TOKEN
    """
    print("=" * 70)
    print("EXAMPLE 3: GITHUB GIST BACKEND (Cloud Storage)")
    print("=" * 70)
    
    # NOTE: This example requires a valid GitHub token
    # For demo purposes, we'll show the code structure
    
    print("ℹ️  SETUP REQUIRED:")
    print("   1. Create GitHub Personal Access Token")
    print("   2. Grant 'gist' scope only")
    print("   3. Set GITHUB_TOKEN environment variable")
    print()
    
    # Example code (requires valid token):
    """
    import os
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    backend = GitHubGistBackend(token=token)
    capsule = PromptCapsule()
    
    # Store a prompt
    prompt = "Your long prompt here..."
    compressed = capsule.compress(prompt, vault_backend=backend)
    print(f"Stored in GitHub Gist: {compressed}")
    
    # Retrieve the prompt
    result = capsule.decompress(compressed, vault_backend=backend)
    print(f"Retrieved from GitHub: {result.text}")
    """
    
    print("Example code structure:")
    print("  1. Initialize backend with GitHub token")
    print("  2. Compress prompts (creates private gists)")
    print("  3. Keys are GitHub gist IDs")
    print("  4. Decompress prompts (retrieves from gists)")
    print("  5. GitHub provides version history automatically")
    print()


# =============================================================================
# EXAMPLE 4: AWS S3 BACKEND (Scalable Cloud Storage)
# =============================================================================
def example_s3_backend():
    """
    Use S3Backend for:
    - Scalable cloud storage
    - High-volume production deployments
    - Geographic distribution
    - Enterprise storage requirements
    
    ✅ Pros:
       - Highly scalable
       - Enterprise-grade availability
       - Good for production systems
       - Supports versioning and lifecycle policies
       - Strong access control options
       - Geographic redundancy available
    
    ❌ Cons:
       - Requires AWS account and credentials
       - Costs scale with usage
       - Network latency
       - Requires AWS SDK (boto3)
       - More complex setup
    
    Security Considerations:
    - CRITICAL: Use IAM roles instead of access keys when possible
    - CRITICAL: Never hardcode AWS credentials
    - Use AWS Secrets Manager or environment variables
    - Enable S3 bucket encryption (SSE-S3 or SSE-KMS)
    - Enable versioning for audit trail
    - Use VPC endpoints to avoid internet traffic
    - Implement bucket policies to restrict access
    - Enable MFA delete protection
    - Use S3 Block Public Access
    - Enable CloudTrail for audit logging
    - Regular backup strategy (cross-region replication)
    
    Setup Instructions:
    1. Create AWS account
    2. Create S3 bucket with encryption enabled
    3. Create IAM user or role with S3 permissions
    4. Configure AWS credentials (use IAM roles in production!)
    5. Install boto3: pip install promptcapsule[vault]
    """
    print("=" * 70)
    print("EXAMPLE 4: AWS S3 BACKEND (Scalable Cloud Storage)")
    print("=" * 70)
    
    print("ℹ️  SETUP REQUIRED:")
    print("   1. Create AWS S3 bucket")
    print("   2. Enable S3 encryption (highly recommended)")
    print("   3. Configure AWS IAM credentials or roles")
    print("   4. Install boto3")
    print()
    
    # Example code (requires valid AWS credentials and bucket):
    """
    import os
    
    backend = S3Backend(
        bucket="my-promptcapsule-bucket",
        region="us-east-1",
        prefix="prompts/production/"
    )
    capsule = PromptCapsule()
    
    # Store a prompt
    prompt = "Your long prompt here..."
    compressed = capsule.compress(prompt, vault_backend=backend)
    print(f"Stored in S3: {compressed}")
    
    # Retrieve the prompt
    result = capsule.decompress(compressed, vault_backend=backend)
    print(f"Retrieved from S3: {result.text}")
    
    # S3 Storage Structure:
    # s3://my-promptcapsule-bucket/prompts/production/20260922_113000_abc12345.txt
    """
    
    print("Example code structure:")
    print("  1. Initialize backend with bucket name and region")
    print("  2. Compress prompts (uploads to S3)")
    print("  3. Keys are S3 object paths")
    print("  4. Decompress prompts (retrieves from S3)")
    print("  5. S3 handles scalability automatically")
    print()
    
    print("⚠️  SECURITY BEST PRACTICES:")
    print("  ✓ Enable S3 bucket encryption (SSE-S3 or SSE-KMS)")
    print("  ✓ Use IAM roles instead of access keys (in AWS)")
    print("  ✓ Never hardcode credentials")
    print("  ✓ Enable versioning for audit trails")
    print("  ✓ Use VPC endpoints to avoid internet traffic")
    print("  ✓ Enable CloudTrail logging")
    print("  ✓ Implement least-privilege IAM policies")
    print("  ✓ Enable MFA delete protection")
    print("  ✓ Use S3 Block Public Access")
    print()


# =============================================================================
# COMPARISON TABLE
# =============================================================================
def print_comparison_table():
    """Print a comparison table of all backends."""
    print("=" * 70)
    print("VAULT BACKEND COMPARISON")
    print("=" * 70)
    
    comparison = """
    ╔═══════════════════╦════════╦═════════╦═══════╦═════════════════╗
    ║ Feature           ║ Memory ║ SQLite  ║ Gist  ║ S3              ║
    ╠═══════════════════╬════════╬═════════╬═══════╬═════════════════╣
    ║ Persistence       ║   ❌   ║   ✅    ║  ✅   ║ ✅              ║
    ║ Cloud-based       ║   ❌   ║   ❌    ║  ✅   ║ ✅              ║
    ║ Scalability       ║   ⚠️   ║   ⚠️    ║  ⚠️   ║ ✅              ║
    ║ Setup Complexity  ║   ✅   ║   ✅    ║  ⚠️   ║ ⚠️              ║
    ║ Cost              ║   ✅   ║   ✅    ║  ✅   ║ 💰              ║
    ║ Security         ║   ✅   ║   ⚠️    ║  ⚠️   ║ ✅              ║
    ║ Latency          ║   ✅   ║   ✅    ║  ⚠️   ║ ⚠️              ║
    ║ Team Sharing     ║   ❌   ║   ❌    ║  ✅   ║ ✅              ║
    ║ Version History  ║   ❌   ║   ❌    ║  ✅   ║ ✅              ║
    ║ Best For         ║ Testing│ Local   │Cloud  │Production       ║
    ║                  ║        │ Dev     │Team   │Enterprise       ║
    ╚═══════════════════╩════════╩═════════╩═══════╩═════════════════╝
    
    Legend: ✅ Excellent | ⚠️ Good/Considerations | ❌ Not Available | 💰 Costs
    """
    print(comparison)
    print()


# =============================================================================
# SECURITY RECOMMENDATIONS
# =============================================================================
def print_security_recommendations():
    """Print security recommendations for all backends."""
    print("=" * 70)
    print("SECURITY RECOMMENDATIONS")
    print("=" * 70)
    
    recommendations = """
    🔒 GENERAL SECURITY PRACTICES
    ══════════════════════════════════════════════════════════════════
    1. Use PromptCapsule's SHA256 integrity verification
    2. Keep checksums separate from encrypted data
    3. Implement access control at the storage level
    4. Enable encryption at rest and in transit
    5. Use TLS/HTTPS for all network connections
    6. Audit all access to sensitive prompts
    7. Implement rate limiting for API calls
    8. Monitor for unauthorized access attempts
    
    📋 INMEMORY BACKEND
    ──────────────────────────────────────────────────────────────────
    ✓ Use only for testing and development
    ✓ Do NOT use for production
    ✓ Do NOT store sensitive data
    ✓ Acceptable for unit tests and CI/CD
    
    💾 SQLITE BACKEND
    ──────────────────────────────────────────────────────────────────
    ✓ Set database file permissions to 600 (owner read/write only)
    ✓ Keep database file in a secure location
    ✓ Consider encrypting the database file using:
      - SQLCipher for encryption at rest
      - PRAGMA encrypt_key for password protection
    ✓ Implement backup strategy
    ✓ Use connection timeout: "sqlite3://db.db?timeout=30"
    ✓ Enable foreign keys: PRAGMA foreign_keys = ON
    ✓ Use WAL mode for better concurrency
    ✓ NOT suitable for distributed systems
    ✓ Be aware of SQLite's locking on writes
    
    🌐 GITHUB GIST BACKEND
    ──────────────────────────────────────────────────────────────────
    🚨 CRITICAL: Never commit tokens to version control!
    ✓ Use environment variables for tokens: export GITHUB_TOKEN=xxx
    ✓ Use GitHub Organization secrets in CI/CD
    ✓ Create fine-grained personal access tokens with minimal scopes
    ✓ Grant ONLY 'gist' scope, no other permissions
    ✓ Rotate tokens every 90 days
    ✓ Use GitHub's audit log to track token usage
    ✓ Revoke old tokens immediately
    ✓ Ensure gists are PRIVATE (not public)
    ✓ GitHub rate limits: 60 req/hr (unauthenticated)
    ✓ Implement exponential backoff for API calls
    ✓ Monitor gist activity via GitHub API
    ✓ Consider GitHub Advanced Security for audit logging
    ⚠️  Gists are accessible to anyone with the URL (even if private)
    ⚠️  Use GitHub's private gists as defense-in-depth, not sole security
    
    ☁️  AWS S3 BACKEND
    ──────────────────────────────────────────────────────────────────
    🚨 CRITICAL: Never hardcode AWS credentials!
    ✓ Use IAM roles instead of access keys (in AWS)
    ✓ Use AWS Secrets Manager or environment variables
    ✓ Enable S3 bucket encryption:
      - SSE-S3: Server-side encryption with S3-managed keys
      - SSE-KMS: Server-side encryption with KMS-managed keys (recommended)
    ✓ Enable bucket versioning for audit trail
    ✓ Implement S3 bucket policies for least-privilege access
    ✓ Enable CloudTrail logging for all S3 API calls
    ✓ Use VPC endpoints to avoid routing through internet
    ✓ Enable MFA delete protection for critical buckets
    ✓ Use S3 Block Public Access (all four options ON)
    ✓ Implement bucket lifecycle policies:
      - Archive old prompts to Glacier
      - Delete after retention period
    ✓ Enable object locking for immutable storage
    ✓ Use AWS KMS keys with strong key policies
    ✓ Implement cross-region replication for disaster recovery
    ✓ Regular backup and restore testing
    ✓ Monitor S3 access patterns with CloudWatch
    ✓ Use presigned URLs with short expiration (< 15 min)
    ⚠️  S3 bucket names are globally unique and publicly visible
    ⚠️  Verify IAM policies don't accidentally grant public access
    """
    print(recommendations)
    print()


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  PROMPTCAPSULE VAULT BACKEND EXAMPLES & SECURITY GUIDE".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")
    
    # Run examples
    example_inmemory_backend()
    example_sqlite_backend()
    example_github_gist_backend()
    example_s3_backend()
    
    # Print comparisons and recommendations
    print_comparison_table()
    print_security_recommendations()
    
    print("=" * 70)
    print("For more information, visit:")
    print("  GitHub: https://github.com/UdayaNirogi/promptcapsule")
    print("  PyPI: https://pypi.org/project/promptcapsule/")
    print("=" * 70)
