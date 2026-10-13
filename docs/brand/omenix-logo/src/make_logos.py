"""Generate the Omenix logo candidates as SVG files.

Colours come from exepex/omenix-dashboard design/system/tokens.css (scheme v2, 2026-10-08):
accent #5a5ee6 -> #7a7df0 (the sidebar active gradient), sidebar navy #2f3349, dark sidebar #1f2233.
Every mark is drawn on a 64 x 64 grid; the wordmark is Inter SemiBold converted to outlines so the SVG
needs no font. Usage: python make_logos.py <out-dir>
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ACCENT_A = "#5a5ee6"
ACCENT_B = "#7a7df0"
NAVY = "#2f3349"
WHITE = "#ffffff"
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
GRID = 64
STROKE = 7.5


def grad(gid: str = "g") -> str:
    """One gradient across the whole 64-unit mark box (user space), so stroked paths share it; an
    object-bounding-box gradient would give each path its own, and a gradient cannot be a `color` value."""
    return (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{GRID}" x2="{GRID}" y2="0">'
        f'<stop offset="0" stop-color="{ACCENT_A}"/><stop offset="1" stop-color="{ACCENT_B}"/></linearGradient>'
    )


def painted(inner: str, paint: str) -> str:
    """Apply a paint (a colour or url(#g)) to the mark's currentColor strokes and fills."""
    return inner.replace("currentColor", paint)


def num(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def pt(angle_deg: float, r: float, c: float = GRID / 2) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return (round(c + r * math.cos(a), 2), round(c + r * math.sin(a), 2))


def arc(start: float, end: float, r: float) -> str:
    """Clockwise arc (SVG y-down) from start to end angle, degrees, on the centred circle."""
    x0, y0 = pt(start, r)
    x1, y1 = pt(end, r)
    sweep = (end - start) % 360
    large = 1 if sweep > 180 else 0
    return f"M{x0} {y0} A{r} {r} 0 {large} 1 {x1} {y1}"


# ---- the three marks: each returns SVG inner markup using stroke/fill "currentColor" ------------------------
R = 20.5


def mark_signal() -> str:
    """A: the O as a trading range; the price line rises through it and breaks out at the top right."""
    body = arc(352, 284, R)
    line = "M21 45 L33 31 L39 36 L57 11"
    return (
        f'<path d="{body}" fill="none" stroke="currentColor" stroke-width="{STROKE}" stroke-linecap="round"/>'
        f'<path d="{line}" fill="none" stroke="currentColor" stroke-width="{STROKE}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )


def mark_omen() -> str:
    """B: the omen: an upper eyelid over an open ring iris, watching what is coming."""
    lid = "M7 40 A29 29 0 0 1 57 40"
    return (
        f'<path d="{lid}" fill="none" stroke="currentColor" stroke-width="{STROKE}" stroke-linecap="round"/>'
        f'<circle cx="32" cy="40" r="9.5" fill="none" stroke="currentColor" stroke-width="{STROKE}"/>'
    )


def mark_monogram() -> str:
    """C: O and M in one shape: the full ring with the M standing inside it."""
    m = "M20 43 L20 23 L32 36 L44 23 L44 43"
    return (
        f'<circle cx="32" cy="32" r="{R}" fill="none" stroke="currentColor" stroke-width="{STROKE - 1}"/>'
        f'<path d="{m}" fill="none" stroke="currentColor" stroke-width="{STROKE - 1.5}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
    )


MARKS = {"signal": mark_signal, "omen": mark_omen, "monogram": mark_monogram}


# ---- wordmark ---------------------------------------------------------------------------------------------
def wordmark_path(
    text: str = "Omenix", tracking_em: float = -0.015
) -> tuple[str, float, float, float]:
    """Return (path d, advance width, cap height, units per em) for the text in font units, y up."""
    font = TTFont(FONT)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    cap = font["OS/2"].sCapHeight
    x = 0.0
    parts = []
    for ch in text:
        name = cmap[ord(ch)]
        pen = SVGPathPen(glyph_set)
        glyph = glyph_set[name]
        glyph.draw(pen)
        d = pen.getCommands()
        parts.append(f'<path transform="translate({x:.1f} 0)" d="{d}"/>')
        x += glyph.width + tracking_em * upm
    return "".join(parts), x, cap, upm


# ---- svg assembly -----------------------------------------------------------------------------------------
def svg(width: float, height: float, view: str, body: str, defs: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(width)}" height="{num(height)}" viewBox="{view}">'
        f"<defs>{defs}</defs>{body}</svg>\n"
    )


def mark_only(inner: str, color: str, defs: str = "") -> str:
    return svg(GRID, GRID, f"0 0 {GRID} {GRID}", painted(inner, color), defs)


def tile(
    inner: str, bg: str, fg: str, radius: float, pad_scale: float = 0.72, defs: str = ""
) -> str:
    """A square tile (app rail, favicon, avatar): background with the mark scaled to pad_scale of it."""
    s = pad_scale
    off = GRID * (1 - s) / 2
    return svg(
        GRID,
        GRID,
        f"0 0 {GRID} {GRID}",
        f'<rect width="{GRID}" height="{GRID}" rx="{radius}" fill="{bg}"/>'
        f'<g transform="translate({off:.2f} {off:.2f}) scale({s})">{painted(inner, fg)}</g>',
        defs,
    )


def lockup(inner: str, mark_color: str, text_color: str, defs: str = "") -> str:
    d, adv, cap, upm = wordmark_path()
    mark_h = 44.0  # the mark box in the lock-up
    cap_h = 30.0  # wordmark cap height, visually balanced against the ring
    scale = cap_h / cap
    gap = 12.0
    text_w = adv * scale
    width = mark_h + gap + text_w
    height = mark_h
    baseline = height / 2 + cap_h / 2
    return svg(
        round(width, 1),
        height,
        f"0 0 {num(round(width, 1))} {num(height)}",
        f'<g transform="scale({mark_h / GRID:.4f})">{painted(inner, mark_color)}</g>'
        f'<g transform="translate({mark_h + gap:.1f} {baseline:.1f}) scale({scale:.5f} -{scale:.5f})" '
        f'fill="{text_color}">{d}</g>',
        defs,
    )


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    g = "url(#g)"
    for name, fn in MARKS.items():
        inner = fn()
        d = out_dir / name
        d.mkdir(exist_ok=True)
        files = {
            "mark-gradient.svg": mark_only(inner, g, grad()),
            "mark-white.svg": mark_only(inner, WHITE),
            "mark-navy.svg": mark_only(inner, NAVY),
            # app rail tile: gradient square, 4 px radius at 36 px (11%), white mark
            "tile.svg": tile(inner, g, WHITE, 7, defs=grad()),
            # social avatars (cropped to a circle by Facebook, Instagram, Google): mark inside the safe circle
            "avatar-gradient.svg": tile(inner, g, WHITE, 0, 0.6, grad()),
            "avatar-navy.svg": tile(inner, NAVY, WHITE, 0, 0.6),
            "avatar-white.svg": tile(inner, WHITE, g, 0, 0.6, grad()),
            # maskable app icon: everything inside the central 80 % circle
            "icon-maskable.svg": tile(inner, g, WHITE, 0, 0.56, grad()),
            "lockup-light.svg": lockup(inner, g, NAVY, grad()),
            "lockup-dark.svg": lockup(inner, WHITE, WHITE),
            "lockup-mono-navy.svg": lockup(inner, NAVY, NAVY),
            "lockup-mono-white.svg": lockup(inner, WHITE, WHITE),
        }
        for fname, content in files.items():
            (d / fname).write_text(content)
    print(f"wrote {len(MARKS)} marks to {out_dir}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
