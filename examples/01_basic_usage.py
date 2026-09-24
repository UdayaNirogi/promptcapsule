"""Example 1: Basic usage of PromptCapsule (v0.1.5)."""

from promptcapsule import PromptCapsule, IntegrityError

# Create a PromptCapsule instance
pc = PromptCapsule()

# Compress a short prompt
prompt = "You are a helpful Python coding assistant. Help the user write clean, efficient code."
capsule = pc.compress(prompt)

print(f"Original prompt: {prompt}")
print(f"Capsule: {capsule}")
print(f"Capsule size: {len(capsule)} characters")
print()

# Decompress the capsule (strict=True by default in 0.1.5)
# This will raise IntegrityError if the capsule is tampered with
try:
    result = pc.decompress(capsule)  # strict=True is the default (fail-closed)
    print(f"Decompressed: {result.text}")
    print(f"Verified: {result.verified}")
    print(f"Mode: {result.mode}")
    print(f"Original size: {result.original_size} bytes")
    print(f"Capsule size: {result.capsule_size} bytes")
    print()
except IntegrityError as e:
    print(f"❌ Integrity check failed: {e}")
    # In agent-to-agent handoff, this means: reject the capsule
    raise

# Verify exact reconstruction
assert result.text == prompt, "Text mismatch!"
print("✓ Exact reconstruction verified!")
print()

# Demonstrate integrity protection
print("--- Testing integrity protection ---")
# Simulate tampering
tampered = capsule[:-5] + "XXXXX"
print(f"Tampered capsule: {tampered}")

try:
    bad_result = pc.decompress(tampered)
    print("⚠️  Should not reach here - integrity should fail!")
except IntegrityError as e:
    print(f"✓ Integrity check correctly rejected tampered capsule: {e}")
