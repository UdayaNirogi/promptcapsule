"""Example 1: Basic usage of PromptCapsule."""

from promptcapsule import PromptCapsule

# Create a PromptCapsule instance
pc = PromptCapsule()

# Compress a short prompt
prompt = "You are a helpful Python coding assistant. Help the user write clean, efficient code."
capsule = pc.compress(prompt)

print(f"Original prompt: {prompt}")
print(f"Capsule: {capsule}")
print(f"Capsule size: {len(capsule)} characters")
print()

# Decompress the capsule
result = pc.decompress(capsule)

print(f"Decompressed: {result.text}")
print(f"Verified: {result.verified}")
print(f"Mode: {result.mode}")
print(f"Original size: {result.original_size} bytes")
print(f"Capsule size: {result.capsule_size} bytes")
print()

# Verify exact reconstruction
assert result.text == prompt, "Text mismatch!"
print("✓ Exact reconstruction verified!")
