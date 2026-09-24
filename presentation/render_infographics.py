#!/usr/bin/env python3
"""Render PromptCapsule presentation/README infographics with exact metrics (v0.1.5)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT.parent / "assets"

NAVY = (11, 31, 58)
TEAL = (13, 148, 136)
ACCENT = (20, 184, 166)
LIGHT = (240, 247, 246)
WHITE = (255, 255, 255)
GRAY = (74, 85, 104)
SOFT = (226, 238, 236)
DARK_BAR = (11, 31, 58)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    idx = 1 if bold else 0
    try:
        return ImageFont.truetype(path, size=size, index=idx)
    except OSError:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=size)


def rounded_rect(draw, xy, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_center(draw, cx, cy, text, fnt, fill):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - w / 2, cy - h / 2), text, font=fnt, fill=fill)


def save(img: Image.Image, name: str):
    out = ROOT / name
    img.save(out, "PNG", optimize=True)
    ASSETS.mkdir(exist_ok=True)
    if name == "promptcapsule_infographic.png":
        img.save(ASSETS / name, "PNG", optimize=True)
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB)")


def render_product():
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # header
    d.rectangle((0, 0, W, 140), fill=NAVY)
    d.text((60, 36), "PromptCapsule", font=font(54, True), fill=WHITE)
    d.text(
        (60, 98),
        "Lossless Prompt Packaging & Retrieval Library  ·  v0.1.5",
        font=font(24),
        fill=ACCENT,
    )
    d.text((1580, 58), "Open Source", font=font(22, True), fill=WHITE)

    # two mode panels
    panels = [
        (
            60,
            "INLINE MODE  (≤500 bytes)",
            [
                "zlib + Base85 encoding",
                "Self-contained capsule string (cap_i_…)",
                "No vault / no shared store required",
                "Best for short system prompts & tool args",
            ],
        ),
        (
            990,
            "VAULT MODE  (>500 bytes)",
            [
                "Short opaque key (cap_v_…) into a vault",
                "Backends: InMemory · SQLite · Gist · S3",
                "Retrieve + SHA-256 verify on unpack",
                "Best for long context & multi-agent memory",
            ],
        ),
    ]
    for left, title, lines in panels:
        rounded_rect(d, (left, 180, left + 870, 560), 24, LIGHT, TEAL, 3)
        d.text((left + 36, 210), title, font=font(28, True), fill=NAVY)
        y = 280
        for line in lines:
            d.ellipse((left + 40, y + 8, left + 56, y + 24), fill=TEAL)
            d.text((left + 72, y), line, font=font(22), fill=GRAY)
            y += 55

    # benefits
    d.text((60, 600), "KEY BENEFITS", font=font(22, True), fill=TEAL)
    cards = [
        ("SHA-256", "Fail-closed verify"),
        ("10 MiB", "Max prompt / zlib"),
        ("4", "Pluggable backends"),
        ("81", "Automated tests"),
    ]
    for i, (num, label) in enumerate(cards):
        x = 60 + i * 465
        rounded_rect(d, (x, 650, x + 440, 860), 20, WHITE, TEAL, 3)
        text_center(d, x + 220, 720, num, font(44, True), TEAL)
        text_center(d, x + 220, 790, label, font(22), NAVY)

    # footer
    d.rectangle((0, 920, W, H), fill=DARK_BAR)
    d.text(
        (60, 970),
        "pip install promptcapsule==0.1.5    ·    github.com/UdayaNirogi/promptcapsule    ·    pypi.org/project/promptcapsule/0.1.5/",
        font=font(22),
        fill=WHITE,
    )
    save(img, "promptcapsule_infographic.png")


def render_architecture():
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    d.text((60, 40), "Hybrid Architecture", font=font(44, True), fill=NAVY)
    d.text((60, 100), "PromptCapsule v0.1.5  ·  auto-select by UTF-8 size", font=font(22), fill=GRAY)

    # decision diamond (drawn as rotated square approx via polygon)
    cx, cy = 960, 280
    diamond = [(cx, cy - 70), (cx + 160, cy), (cx, cy + 70), (cx - 160, cy)]
    d.polygon(diamond, fill=TEAL)
    text_center(d, cx, cy - 10, "Auto-select", font(20, True), WHITE)
    text_center(d, cx, cy + 18, "by size", font(18), WHITE)

    def lane(y, title, steps, result, fill):
        rounded_rect(d, (60, y, 1860, y + 230), 20, fill, TEAL, 2)
        d.text((90, y + 24), title, font=font(26, True), fill=NAVY)
        box_w = 260
        gap = 40
        start = 90
        for i, step in enumerate(steps):
            x = start + i * (box_w + gap)
            rounded_rect(d, (x, y + 80, x + box_w, y + 170), 14, WHITE, NAVY, 2)
            text_center(d, x + box_w / 2, y + 125, step, font(20, True), NAVY)
            if i < len(steps) - 1:
                ax = x + box_w + 8
                d.polygon([(ax, y + 115), (ax + 22, y + 125), (ax, y + 135)], fill=TEAL)
        # result chip
        rx = 1580
        rounded_rect(d, (rx, y + 90, rx + 250, y + 160), 14, NAVY)
        text_center(d, rx + 125, y + 125, result, font(16, True), WHITE)

    lane(
        380,
        "INLINE MODE  (≤500 bytes)",
        ["Prompt", "zlib", "Base85", "cap_i_…"],
        "self-contained",
        LIGHT,
    )
    lane(
        640,
        "VAULT MODE  (>500 bytes)",
        ["Prompt", "Vault store", "cap_v_…", "SHA-256"],
        "fail-closed",
        SOFT,
    )

    # backends + limits bar
    rounded_rect(d, (60, 900, 1860, 1040), 16, NAVY)
    d.text((90, 920), "VAULT BACKENDS", font=font(18, True), fill=ACCENT)
    backends = "InMemory    ·    SQLite    ·    GitHub Gist    ·    AWS S3"
    d.text((90, 955), backends, font=font(24), fill=WHITE)
    d.text(
        (90, 1000),
        "Limits: ≤500 B inline  ·  10 MiB max prompt/zlib  ·  unguessable vault keys  ·  81 automated tests",
        font=font(18),
        fill=ACCENT,
    )
    save(img, "ppt_architecture.png")


def render_quantify():
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    d.text((60, 40), "What PromptCapsule Quantifies", font=font(44, True), fill=NAVY)
    d.text((60, 100), "v0.1.5  ·  hard limits & measured packaging", font=font(22), fill=GRAY)

    cards = [
        ("≤500 bytes", "Inline threshold"),
        ("10 MiB", "Max prompt / zlib expand"),
        ("SHA-256", "Fail-closed integrity (8-hex)"),
        ("81 tests", "Automated suite (core + security)"),
    ]
    for i, (num, label) in enumerate(cards):
        x = 60 + i * 465
        rounded_rect(d, (x, 170, x + 440, 420), 22, LIGHT, TEAL, 3)
        text_center(d, x + 220, 250, num, font(40, True), TEAL)
        # wrap label
        words = label.split()
        line1 = " ".join(words[:3]) if len(words) > 3 else label
        line2 = " ".join(words[3:]) if len(words) > 3 else ""
        text_center(d, x + 220, 330, line1, font(20), NAVY)
        if line2:
            text_center(d, x + 220, 360, line2, font(20), NAVY)

    # comparison
    rounded_rect(d, (60, 480, 1860, 900), 24, WHITE, TEAL, 3)
    d.text((90, 510), "COMPARISON", font=font(22, True), fill=TEAL)

    # left
    d.text((120, 580), "Long prompt", font=font(28, True), fill=NAVY)
    d.text((120, 630), "~3000 chars", font=font(24), fill=GRAY)
    d.rounded_rectangle((120, 700, 820, 760), radius=12, fill=NAVY)
    d.text((120, 790), "Multi-KB  ·  bulky  ·  hard to share", font=font(20), fill=GRAY)

    # VS
    d.ellipse((900, 680, 1020, 800), fill=TEAL)
    text_center(d, 960, 740, "VS", font(28, True), WHITE)

    # right
    d.text((1120, 580), "Vault capsule key", font=font(28, True), fill=NAVY)
    d.text((1120, 630), "short opaque ID", font=font(24), fill=GRAY)
    d.rounded_rectangle((1120, 700, 1280, 760), radius=12, fill=TEAL)
    d.text((1120, 790), "~1% handle size  ·  compact  ·  easy to share", font=font(20), fill=GRAY)

    d.text(
        (90, 960),
        "Not encryption  ·  Not authentication  ·  Integrity only  ·  v0.1.5",
        font=font(22),
        fill=GRAY,
    )
    save(img, "ppt_quantify.png")


def main():
    render_product()
    render_architecture()
    render_quantify()


if __name__ == "__main__":
    main()
