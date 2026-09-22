#!/usr/bin/env python3
"""Build PromptCapsule C-batch presentation (8 slides) with infographics."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "PromptCapsule_CBatch.pptx"

# Brand colors
NAVY = RGBColor(0x0B, 0x1F, 0x3A)
TEAL = RGBColor(0x0D, 0x94, 0x88)
LIGHT = RGBColor(0xF0, 0xF7, 0xF6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0x4A, 0x55, 0x68)
ACCENT = RGBColor(0x14, 0xB8, 0xA6)


def set_run(run, size=18, bold=False, color=NAVY, font="Calibri"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font


def add_textbox(slide, left, top, width, height, text, size=18, bold=False, color=NAVY, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run(run, size=size, bold=bold, color=color)
    return box


def add_rect(slide, left, top, width, height, fill, line=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
    return shape


def add_footer(slide, page, total=8):
    add_textbox(
        slide, Inches(0.4), Inches(7.05), Inches(8), Inches(0.3),
        f"PromptCapsule  ·  C-Batch  ·  {page}/{total}",
        size=11, color=GRAY,
    )


def blank_slide(prs):
    blank = prs.slide_layouts[6]  # blank
    return prs.slides.add_slide(blank)


def slide_title(prs):
    slide = blank_slide(prs)
    # background bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()

    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(5.9), Inches(13.333), Inches(0.12))
    accent.fill.solid()
    accent.fill.fore_color.rgb = TEAL
    accent.line.fill.background()

    add_textbox(slide, Inches(0.8), Inches(2.0), Inches(11), Inches(1),
                "PromptCapsule", size=48, bold=True, color=WHITE)
    add_textbox(slide, Inches(0.8), Inches(3.0), Inches(11), Inches(0.8),
                "Lossless Prompt Packaging & Retrieval  ·  v0.1.4", size=24, color=ACCENT)
    add_textbox(slide, Inches(0.8), Inches(3.9), Inches(11), Inches(0.6),
                "C-Batch  ·  Hybrid packaging  ·  Agent handoff  ·  Security-hardened",
                size=16, color=WHITE)
    add_textbox(slide, Inches(0.8), Inches(6.2), Inches(11), Inches(0.4),
                "pip install promptcapsule==0.1.4   ·   github.com/UdayaNirogi/promptcapsule",
                size=14, color=LIGHT)


def slide_problem(prs):
    slide = blank_slide(prs)
    add_textbox(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
                "1  ·  The Problem", size=28, bold=True, color=NAVY)
    add_textbox(slide, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
                "Teams need exact prompt reuse — not lossy “semantic compression.”",
                size=18, color=GRAY)

    cards = [
        ("Share exact prompts", "Same system prompt across apps,\nPRs, and environments"),
        ("Shrink the handle", "Multi-KB prompts → short,\nportable capsule string"),
        ("Prove integrity", "SHA-256 verification on\nevery reconstruct"),
    ]
    for i, (title, body) in enumerate(cards):
        left = Inches(0.5 + i * 4.1)
        add_rect(slide, left, Inches(1.8), Inches(3.8), Inches(2.4), LIGHT)
        add_textbox(slide, left + Inches(0.2), Inches(2.0), Inches(3.4), Inches(0.5),
                    title, size=18, bold=True, color=TEAL)
        add_textbox(slide, left + Inches(0.2), Inches(2.6), Inches(3.4), Inches(1.4),
                    body, size=15, color=NAVY)

    add_rect(slide, Inches(0.5), Inches(4.6), Inches(12.3), Inches(1.9), NAVY)
    add_textbox(slide, Inches(0.7), Inches(4.8), Inches(12), Inches(0.4),
                "Two things people confuse", size=16, bold=True, color=ACCENT)
    add_textbox(slide, Inches(0.7), Inches(5.3), Inches(12), Inches(1.0),
                "Type 1 — True compression: entropy-limited; good for small text; no storage.\n"
                "Type 2 — Key-based retrieval: short ID → full prompt from a vault; solves long prompts.\n"
                "PromptCapsule does BOTH, automatically, with checksums.",
                size=15, color=WHITE)
    add_footer(slide, 2)


def slide_what_it_is(prs):
    slide = blank_slide(prs)
    add_textbox(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.5),
                "2  ·  What Exactly Is This?", size=28, bold=True, color=NAVY)

    add_rect(slide, Inches(0.5), Inches(1.0), Inches(12.3), Inches(1.5), LIGHT)
    add_textbox(slide, Inches(0.7), Inches(1.15), Inches(12), Inches(1.2),
                "Abstract: PromptCapsule is a Python library that turns LLM prompt text into a portable "
                "capsule string and reconstructs the original byte-for-byte. Inline mode (≤500 bytes) "
                "uses zlib+Base85; vault mode stores long prompts and returns a short backend key "
                "(~99% smaller shareable handle). Every decompress returns verified SHA-256 integrity. "
                "Quality: 27+ automated test cases.",
                size=14, color=NAVY)

    metrics = [
        ("500 B", "Inline threshold"),
        ("10 MiB", "Max prompt / zlib expand"),
        ("SHA-256", "Fail-closed integrity"),
        ("81", "Automated tests"),
        ("4", "Pluggable backends"),
        ("0.1.4", "Current release"),
    ]
    for i, (num, label) in enumerate(metrics):
        col, row = i % 3, i // 3
        left = Inches(0.5 + col * 4.1)
        top = Inches(2.8 + row * 1.8)
        add_rect(slide, left, top, Inches(3.8), Inches(1.55), WHITE, TEAL)
        add_textbox(slide, left + Inches(0.15), top + Inches(0.25), Inches(3.5), Inches(0.6),
                    num, size=28, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
        add_textbox(slide, left + Inches(0.15), top + Inches(0.9), Inches(3.5), Inches(0.45),
                    label, size=14, color=NAVY, align=PP_ALIGN.CENTER)
    add_footer(slide, 3)


def slide_infographic_overview(prs):
    slide = blank_slide(prs)
    add_textbox(slide, Inches(0.4), Inches(0.15), Inches(12), Inches(0.4),
                "3  ·  Product Infographic", size=24, bold=True, color=NAVY)
    img = ROOT / "promptcapsule_infographic.png"
    # Fit 16:9 content under title
    slide.shapes.add_picture(str(img), Inches(0.35), Inches(0.6), width=Inches(12.6))
    add_footer(slide, 4)


def slide_architecture(prs):
    slide = blank_slide(prs)
    add_textbox(slide, Inches(0.4), Inches(0.15), Inches(12), Inches(0.4),
                "4  ·  Technical Design — Hybrid Architecture", size=24, bold=True, color=NAVY)
    img = ROOT / "ppt_architecture.png"
    slide.shapes.add_picture(str(img), Inches(0.3), Inches(0.55), width=Inches(12.7))
    add_footer(slide, 5)


def slide_quantify(prs):
    slide = blank_slide(prs)
    add_textbox(slide, Inches(0.4), Inches(0.15), Inches(12), Inches(0.4),
                "5  ·  Limits & Security (v0.1.4)", size=24, bold=True, color=NAVY)
    img = ROOT / "ppt_quantify.png"
    slide.shapes.add_picture(str(img), Inches(0.25), Inches(0.55), width=Inches(8.2))

    add_rect(slide, Inches(8.6), Inches(0.7), Inches(4.3), Inches(5.8), LIGHT)
    add_textbox(slide, Inches(8.8), Inches(0.9), Inches(4), Inches(0.4),
                "Hardening summary", size=16, bold=True, color=TEAL)
    rows = [
        "Limits:",
        "• Inline ≤ 500 bytes",
        "• Max size 10 MiB",
        "",
        "Fixed (library):",
        "• Fail-closed IntegrityError",
        "• Empty prefix rejected",
        "• zlib expansion capped",
        "• Unguessable vault keys",
        "• Vault leak redacted",
        "• Base85 junk rejected",
        "• S3 prefix + Gist owner",
        "",
        "Still not:",
        "• Encryption / auth / MAC",
        "• Demo HTTP bus (OOS)",
        "",
        "81 automated tests",
    ]
    add_textbox(slide, Inches(8.8), Inches(1.35), Inches(4), Inches(5.0),
                "\n".join(rows), size=12, color=NAVY)
    add_footer(slide, 6)


def slide_agent_to_agent(prs):
    """Potential use: agents exchange capsules instead of full prompts."""
    slide = blank_slide(prs)
    add_textbox(slide, Inches(0.5), Inches(0.25), Inches(12), Inches(0.45),
                "6  ·  Agent-to-Agent Communication", size=26, bold=True, color=NAVY)
    add_textbox(slide, Inches(0.5), Inches(0.75), Inches(12), Inches(0.4),
                "Potential: agents pass a capsule, then reconstruct the exact prompt with a checksum.",
                size=15, color=GRAY)

    steps = [
        ("1  Agent A", "Packs context\ncompress(prompt)"),
        ("2  Message", "Sends only the\ncapsule string"),
        ("3  Agent B", "Unpacks + checks\ndecompress → verified"),
    ]
    for i, (title, body) in enumerate(steps):
        left = Inches(0.5 + i * 4.2)
        add_rect(slide, left, Inches(1.3), Inches(3.9), Inches(1.7), NAVY if i == 1 else LIGHT)
        add_textbox(slide, left + Inches(0.2), Inches(1.45), Inches(3.5), Inches(0.4),
                    title, size=16, bold=True, color=ACCENT if i == 1 else TEAL)
        add_textbox(slide, left + Inches(0.2), Inches(1.95), Inches(3.5), Inches(0.85),
                    body, size=14, color=WHITE if i == 1 else NAVY)

    modes = [
        ("Inline capsule", "Self-contained. No shared store.\nBest for short instructions between agents."),
        ("Vault capsule", "Shared backend = shared memory.\nLong context stays in SQLite / Gist / S3."),
        ("Integrity gate", "strict=True → IntegrityError on fail.\nVault bind failure returns empty text."),
    ]
    for i, (title, body) in enumerate(modes):
        left = Inches(0.5 + i * 4.2)
        add_rect(slide, left, Inches(3.25), Inches(3.9), Inches(1.85), WHITE, TEAL)
        add_textbox(slide, left + Inches(0.2), Inches(3.4), Inches(3.5), Inches(0.4),
                    title, size=15, bold=True, color=TEAL)
        add_textbox(slide, left + Inches(0.2), Inches(3.9), Inches(3.5), Inches(1.0),
                    body, size=13, color=NAVY)

    add_textbox(slide, Inches(0.5), Inches(5.3), Inches(12.3), Inches(1.4),
                "v0.1.4: not encryption / not auth. Capsule = payload format. Gist require_owner=True by default.\n"
                "Both agents must share the same vault for vault-mode. Inline capsules travel alone.\n"
                "81 tests. Historical “27+” = core test count, not capsule length.",
                size=13, color=GRAY)
    add_footer(slide, 7)


def slide_backends_security(prs):
    slide = blank_slide(prs)
    add_textbox(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.5),
                "6  ·  Backends & Security Posture", size=28, bold=True, color=NAVY)

    backends = [
        ("InMemory", "Tests / demos", "Risk: Low"),
        ("SQLite", "Local persistent", "Risk: Med*"),
        ("GitHub Gist", "Team cloud share", "Risk: Med*"),
        ("AWS S3", "Production scale", "Risk: Low*"),
    ]
    for i, (name, use, risk) in enumerate(backends):
        left = Inches(0.5 + i * 3.15)
        add_rect(slide, left, Inches(1.1), Inches(3.0), Inches(2.2), LIGHT)
        add_textbox(slide, left + Inches(0.15), Inches(1.25), Inches(2.7), Inches(0.45),
                    name, size=16, bold=True, color=NAVY)
        add_textbox(slide, left + Inches(0.15), Inches(1.8), Inches(2.7), Inches(0.7),
                    use, size=13, color=GRAY)
        add_textbox(slide, left + Inches(0.15), Inches(2.6), Inches(2.7), Inches(0.4),
                    risk, size=13, bold=True, color=TEAL)

    add_textbox(slide, Inches(0.5), Inches(3.5), Inches(12), Inches(0.35),
                "*Risk depends on configuration (file perms, tokens, IAM). Integrity ≠ encryption.",
                size=12, color=GRAY)

    points = [
        "Core: stdlib only — zlib, Base85, SHA-256",
        "SQL backends use parameterized queries (injection-safe)",
        "Bandit scan: 0 HIGH severity findings in library core",
        "Never hardcode GitHub/AWS credentials; use env / IAM roles",
        "Capsules are portable IDs — protect vault contents separately",
    ]
    add_rect(slide, Inches(0.5), Inches(4.0), Inches(12.3), Inches(2.5), NAVY)
    add_textbox(slide, Inches(0.7), Inches(4.2), Inches(12), Inches(0.4),
                "Security highlights", size=16, bold=True, color=ACCENT)
    add_textbox(slide, Inches(0.7), Inches(4.7), Inches(12), Inches(1.6),
                "\n".join(f"•  {p}" for p in points), size=14, color=WHITE)
    add_footer(slide, 7)


def slide_close(prs):
    slide = blank_slide(prs)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()

    add_textbox(slide, Inches(0.8), Inches(1.2), Inches(11.5), Inches(0.6),
                "7  ·  Takeaways & Next Steps", size=28, bold=True, color=WHITE)
    takeaways = [
        "PromptCapsule v0.1.4 = lossless packaging + vault retrieval + fail-closed integrity",
        "Limits: ≤500B inline · 10 MiB max prompt/zlib · unguessable vault keys",
        "Agent handoff: decompress(strict=True); treat IntegrityError as reject",
        "Not encryption / not MAC — protect vault ACLs; 81 automated tests on PyPI",
    ]
    add_textbox(slide, Inches(0.8), Inches(2.1), Inches(11.5), Inches(2.2),
                "\n".join(f"→  {t}" for t in takeaways), size=16, color=LIGHT)

    add_textbox(slide, Inches(0.8), Inches(4.5), Inches(11.5), Inches(0.4),
                "Resources", size=16, bold=True, color=ACCENT)
    add_textbox(slide, Inches(0.8), Inches(5.0), Inches(11.5), Inches(1.2),
                "pip install promptcapsule==0.1.4\n"
                "https://github.com/UdayaNirogi/promptcapsule\n"
                "https://pypi.org/project/promptcapsule/0.1.4/\n"
                "Docs: ABSTRACT.md · TECHNICAL_DESIGN.md · README security section",
                size=14, color=WHITE)
    add_footer(slide, 8)


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide_title(prs)
    slide_problem(prs)
    slide_what_it_is(prs)
    slide_infographic_overview(prs)
    slide_architecture(prs)
    slide_quantify(prs)
    slide_agent_to_agent(prs)
    slide_close(prs)

    prs.save(OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB, {len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
