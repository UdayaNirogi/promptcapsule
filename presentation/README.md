# C-Batch Presentation Pack

## Deliverables

| File | Description |
|------|-------------|
| **PromptCapsule_CBatch.pptx** | 8-slide deck with infographics |
| `ppt_architecture.png` | Hybrid architecture infographic |
| `ppt_quantify.png` | Quantified metrics infographic |
| `promptcapsule_infographic.png` | Product overview infographic |
| `build_pptx.py` | Regenerates the PPTX |

Companion docs (in `../docs/`):

- [ABSTRACT.md](../docs/ABSTRACT.md) — abstract + quantified table  
- [TECHNICAL_DESIGN.md](../docs/TECHNICAL_DESIGN.md) — full technical design  

## Slide outline (8)

1. Title  
2. Problem  
3. What exactly is this (quantified)  
4. Product infographic  
5. Technical architecture infographic  
6. Quantified results + benchmark table  
7. Backends & security  
8. Takeaways & links  

## Regenerate PPT

```bash
cd presentation
python3 build_pptx.py
```
