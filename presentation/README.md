# C-Batch Presentation Pack

**Package version documented:** 0.1.4

## Deliverables

| File | Description |
|------|-------------|
| **PromptCapsule_CBatch.pptx** | 8-slide deck with infographics (v0.1.4) |
| `ppt_architecture.png` | Hybrid architecture infographic |
| `ppt_quantify.png` | Metrics infographic |
| `promptcapsule_infographic.png` | Product overview infographic |
| `build_pptx.py` | Regenerates the PPTX |

Companion docs:

- `../docs/ABSTRACT.md`
- `../docs/TECHNICAL_DESIGN.md`
- `../README.md` — PyPI long description (limits + security)

## Slide outline (8)

1. Title (v0.1.4)
2. Problem
3. What it is (limits + test count)
4. Product infographic
5. Technical architecture
6. Limits & security hardening
7. Agent-to-agent handoff
8. Takeaways & links

## Regenerate PPT

```bash
cd presentation
python3 build_pptx.py
```
