"""Builds the link buttons under the panels: one small pill per destination, each its own SVG so each can be a link.
Company marks are the logos from the personal site, turned into single-colour masks; Discord and X come from
simple-icons (CC0).

Run: python assets/make_links.py  -> writes links/*.svg next to this file.
"""
import base64
import io
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

from common import DIM, FG, HAIR, HERE, INK, SANS, SUN, font_face, text_width, write

H, ICON, PAD, SIZE = 38, 17, 14, 13
LOGOS = Path(r"C:/Workspace/Finetion/SezerUzun/assets/img")  # only read when the cached masks are missing
SIMPLE_ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@16.36.0/icons/{}.svg"

LINKS = [  # (file, label, icon)
    ("makine", "Makine Çeviri", "mask:makine"),
    ("cedra", "CEDRA Interactive", "cross"),
    ("finetion", "Finetion", "mask:finetion"),
    ("site", "Ceaser's World", "sun"),
    ("discord", "Discord", "si:discord"),
    ("x", "@jlceaser", "si:x"),
]


def mask(name):
    """A white-on-black luminance mask of a site logo, cached next to this file as links/<name>-mask.png."""
    cached = HERE / "links" / f"{name}-mask.png"
    if not cached.exists():
        im = Image.open(LOGOS / f"logo-{'makine-ceviri' if name == 'makine' else name}.png").convert("RGBA")
        if name == "finetion":  # black f and orange dot on a white tile: keep the ink, drop the tile
            grey = ImageOps.invert(im.convert("L"))
        else:  # white mark on transparency
            grey = im.getchannel("A")
        grey = grey.resize((72, 72), Image.LANCZOS)
        cached.parent.mkdir(exist_ok=True)
        grey.save(cached, optimize=True)
    return base64.b64encode(cached.read_bytes()).decode()


def icon(kind, x, y):
    """The icon drawn in an ICON-sized box at (x, y), plus any defs it needs."""
    s = ICON
    if kind == "cross":  # the CEDRA plus
        t = s * .34
        return "", (f'<path fill="{SUN}" d="M{x + (s - t) / 2:.2f} {y:.2f}h{t:.2f}v{(s - t) / 2:.2f}h{(s - t) / 2:.2f}v{t:.2f}'
                    f'h-{(s - t) / 2:.2f}v{(s - t) / 2:.2f}h-{t:.2f}v-{(s - t) / 2:.2f}h-{(s - t) / 2:.2f}v-{t:.2f}'
                    f'h{(s - t) / 2:.2f}z"/>')
    if kind == "sun":  # the site's sunset: a half sun on a horizon
        cx, cy = x + s / 2, y + s * .66
        return "", (f'<path fill="{SUN}" d="M{cx - 6.2:.2f} {cy:.2f}a6.2 6.2 0 0 1 12.4 0z"/>'
                    f'<path stroke="{SUN}" stroke-width="1.5" stroke-linecap="round" d="M{x:.2f} {cy + 2.6:.2f}h{s:.2f}"/>')
    if kind.startswith("mask:"):
        name = kind[5:]
        defs = (f'<mask id="m" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{s}" height="{s}">'
                f'<image href="data:image/png;base64,{mask(name)}" x="{x}" y="{y}" width="{s}" height="{s}"/></mask>')
        return defs, f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{SUN}" mask="url(#m)"/>'
    with urllib.request.urlopen(SIMPLE_ICONS.format(kind[3:])) as r:
        d = re.search(r' d="([^"]+)"', r.read().decode()).group(1)
    k = .86 if kind == "si:x" else 1  # the X mark fills its box edge to edge; bring it in line with the rest
    return "", f'<path fill="{SUN}" transform="translate({x + s * (1 - k) / 2:.2f} {y + s * (1 - k) / 2:.2f}) scale({s * k / 24:.4f})" d="{d}"/>'


def button(label, kind):
    tw = text_width(label, SIZE, weight=500)
    w = round(PAD + ICON + 9 + tw + 11 + 8 + PAD)
    defs, glyph = icon(kind, PAD, (H - ICON) / 2)
    ax = w - PAD - 8  # the arrow's box
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" height="{H}" role="img" aria-label="{label}">
<defs>{defs}</defs>
<style>
{font_face("sans", 500, label)}
  text {{ font: 500 {SIZE}px {SANS}; fill: {FG}; }}
</style>
<rect x=".5" y=".5" width="{w - 1}" height="{H - 1}" rx="{H / 2 - .5}" fill="{INK}" stroke="{HAIR}"/>
<rect x="1.5" y="1.5" width="{w - 3}" height="{H - 3}" rx="{H / 2 - 1.5}" fill="none" stroke="#fff" stroke-opacity=".04"/>
{glyph}
<text x="{PAD + ICON + 9}" y="{H / 2 + SIZE * .36:.2f}">{label.replace("&", "&amp;")}</text>
<path d="M{ax} {H / 2 + 4}l8 -8M{ax + 2.5} {H / 2 - 4}h5.5v5.5" stroke="{DIM}" stroke-width="1.4" fill="none"
  stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


if __name__ == "__main__":
    for name, label, kind in LINKS:
        write(f"{name}.svg", button(label, kind), HERE / "links")
