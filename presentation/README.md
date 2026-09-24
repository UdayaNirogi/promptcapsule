# C-Batch Presentation Pack

**Package version documented:** 0.1.5

## Deliverables

| File | Description |
|------|-------------|
| **PromptCapsule_CBatch.pptx** | 8-slide deck with infographics (v0.1.5) |
| `ppt_architecture.png` | Hybrid architecture infographic |
| `ppt_quantify.png` | Metrics infographic (81 tests, 10 MiB, fail-closed) |
| `promptcapsule_infographic.png` | Product overview (also copied to `../assets/`) |
| `render_infographics.py` | Regenerates the three PNGs with exact metrics |
| `build_pptx.py` | Rebuilds the PPTX from text + PNGs |

Companion docs:

- `../docs/ABSTRACT.md`
- `../docs/TECHNICAL_DESIGN.md`
- `../README.md` — PyPI long description (limits + security)

## Slide outline (8)

1. Title (v0.1.5)
2. Problem
3. What it is (limits + 81 tests)
4. Product infographic
5. Technical architecture
6. Limits & security hardening
7. Agent-to-agent handoff
8. Takeaways & links

## Regenerate images + PPT

```bash
cd presentation
python3 render_infographics.py
python3 build_pptx.py
```
