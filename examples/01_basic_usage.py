"""Example 1: Pass the prompt, not the payload. As simple as a string."""

from promptcapsule import PromptCapsule, PromptCapsuleError, pack, unpack

prompt = "You are a helpful Python coding assistant. Help the user write clean, efficient code."

# pack() returns a plain string you can store, log or send to another agent
capsule = pack(prompt)
print(f"Prompt:  {prompt}")
print(f"Capsule: {capsule}")
print()

# unpack() returns the exact original text, or raises
assert unpack(capsule) == prompt
print("✓ Exact reconstruction verified")
print()

# Tampering is rejected instead of returning corrupted text
print("--- Testing integrity protection ---")
tampered = capsule[:-5] + "XXXXX"
try:
    unpack(tampered)
    print("⚠️  Should not reach here - integrity should fail!")
except PromptCapsuleError as e:
    print(f"✓ Tampered capsule rejected: {e}")
print()

# The PromptCapsule class exposes details about the capsule
result = PromptCapsule().decompress(capsule)
print(f"Mode: {result.mode}  Verified: {result.verified}  Signed: {result.signed}")
