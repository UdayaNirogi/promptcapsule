"""Example 3: Version-controlling prompts in your project."""

import json
import os
from promptcapsule import PromptCapsule
from promptcapsule.backends import SQLiteBackend

# Create instances
pc = PromptCapsule()
vault = SQLiteBackend("prompts_vault.db")

# Simulate iterative prompt development
prompts_data = {
    "blog_writer": {
        "v1.0": "Write a blog post about the topic provided.",
        "v1.1": "Write a blog post about the topic provided. Make it engaging and informative.",
        "v1.2": "Write a well-structured blog post (1500+ words) about the topic. Include:\n- Introduction\n- Main sections\n- Conclusion\n- Call to action",
    },
    "code_reviewer": {
        "v1.0": "Review the code and provide feedback.",
        "v1.1": "Review the code and provide feedback on:\n1. Design patterns\n2. Performance\n3. Security\n4. Testing",
    },
}

# Compress all prompts and save their capsules to a JSON file
prompts_config = {}

print("Compressing and saving prompts...")
print("=" * 70)

for prompt_name, versions in prompts_data.items():
    prompts_config[prompt_name] = {}
    
    for version, text in versions.items():
        capsule = pc.compress(text, vault_backend=vault)
        prompts_config[prompt_name][version] = {
            "capsule": capsule,
            "size_bytes": len(text.encode('utf-8')),
        }
        print(f"{prompt_name} {version}:")
        print(f"  Capsule: {capsule}")
        print(f"  Original size: {len(text.encode('utf-8'))} bytes")
        print()

# Save to a config file (this would be committed to git)
config_file = "prompts.json"
with open(config_file, "w") as f:
    json.dump(prompts_config, f, indent=2)

print(f"Saved prompt configuration to {config_file}")
print()

# Load and use prompts later
print("=" * 70)
print("Loading and using prompts from config...")
print("=" * 70)

with open(config_file, "r") as f:
    loaded_config = json.load(f)

# Use the latest version of blog_writer
capsule = loaded_config["blog_writer"]["v1.2"]["capsule"]
result = pc.decompress(capsule, vault_backend=vault)

print(f"Using blog_writer v1.2:")
print(f"  Verified: {result.verified}")
print(f"  Original prompt:")
print(f"    {result.text}")
print()

# Use an older version of code_reviewer
capsule = loaded_config["code_reviewer"]["v1.0"]["capsule"]
result = pc.decompress(capsule, vault_backend=vault)

print(f"Using code_reviewer v1.0:")
print(f"  Verified: {result.verified}")
print(f"  Original prompt:")
print(f"    {result.text}")
print()

# Show how git diff would work
print("=" * 70)
print("In git, you'd see:")
print("=" * 70)
print("""
commitb98ad1b Author: Your Name <you@example.com>

    Update blog_writer prompt to v1.3

diff --git a/prompts.json b/prompts.json
index 1a2b3c4..5d6e7f8 100644
--- a/prompts.json
+++ b/prompts.json
@@ -5,7 +5,7 @@
       "v1.0": {"capsule": "cap_i_abc12345_...", "size_bytes": 45},
       "v1.1": {"capsule": "cap_i_def67890_...", "size_bytes": 78},
-      "v1.2": {"capsule": "cap_i_ghi01234_...", "size_bytes": 156}
+      "v1.2": {"capsule": "cap_i_ghi01234_...", "size_bytes": 156},
+      "v1.3": {"capsule": "cap_i_jkl56789_...", "size_bytes": 201}
     }
   }
}
""")

# Cleanup
os.remove(config_file)
os.remove("prompts_vault.db")
print("Cleaned up example files")
