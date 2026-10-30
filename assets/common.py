"""Shared look for every panel: the sunset palette of jlceaser.github.io/SezerUzun, the card they all sit on, and the
fonts, embedded as subsets so a panel renders the same on every machine (an SVG shown through <img> cannot load fonts).
"""
import base64
import html
import io
import re
from functools import lru_cache
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).parent
W = 1000
RADIUS = 18

# The palette the site samples from its sunset photo.
COAL, FLAME, EMBER, SUN, PEACH = "#661E08", "#B04214", "#E16523", "#FC7B34", "#FFAF70"
HAZE, DUSK, INK, NAME, FG = "#765141", "#2E2F37", "#171C1E", "#FDB68F", "#EDE9E4"
DIM, RULE, HAIR = "rgba(237,233,228,.52)", "rgba(237,233,228,.2)", "rgba(237,233,228,.1)"

SANS, MONO = "'Ceaser Sans', Montserrat, 'Segoe UI', sans-serif", "'Ceaser Mono', 'JetBrains Mono', Consolas, monospace"
FONTS = {"sans": "Montserrat[wght].ttf", "sans-italic": "Montserrat-Italic[wght].ttf", "mono": "JetBrainsMono[wght].ttf"}
FAMILY = {"sans": "Ceaser Sans", "sans-italic": "Ceaser Sans", "mono": "Ceaser Mono"}


@lru_cache(None)
def _static(font, weight):
    return instancer.instantiateVariableFont(TTFont(HERE / "fonts" / FONTS[font]), {"wght": weight})


def text_width(text, size, font="sans", weight=500, tracking=0):
    """Advance width of a single line in px; tracking in em, as in CSS letter-spacing."""
    ft = _static(font, weight)
    cmap, hmtx, upm = ft.getBestCmap(), ft["hmtx"], ft["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c), ".notdef")][0] for c in text) * size / upm + len(text) * tracking * size


def font_face(font, weight, text):
    """@font-face for one weight of one font, cut down to the characters of text."""
    buf = io.BytesIO()
    _static(font, weight).save(buf)
    buf.seek(0)
    ft = TTFont(buf)
    opts = subset.Options()
    opts.flavor, opts.layout_features, opts.name_IDs, opts.notdef_outline = "woff2", ["kern", "liga", "case"], [], True
    sub = subset.Subsetter(opts)
    sub.populate(text=text + " ")
    sub.subset(ft)
    out = io.BytesIO()
    ft.flavor = "woff2"
    ft.save(out)
    data = base64.b64encode(out.getvalue()).decode()
    style = "italic" if font.endswith("italic") else "normal"
    return (f"@font-face {{ font-family: '{FAMILY[font]}'; font-weight: {weight}; font-style: {style}; "
            f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}")


def text_of(svg):
    """Every character drawn by the <text> elements of an SVG body."""
    runs = re.findall(r"<text\b[^>]*>(.*?)</text>", svg, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", "".join(runs)))


def fonts_css(body, faces):
    """faces: (font, weight) pairs the body uses; each is subset to the body's text."""
    chars = text_of(body)
    upper = chars.upper().replace("I", "Iİ")  # small caps lines are uppercased by CSS
    return "\n".join(font_face(f, w, chars + upper) for f, w in faces)


GRAIN = ('<filter id="grain" x="0" y="0" width="100%" height="100%">'
         '<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="7" stitchTiles="stitch"/>'
         '<feColorMatrix values="0 0 0 0 .93  0 0 0 0 .9  0 0 0 0 .86  0 0 0 .07 0"/></filter>')


def card(h, body, *, label, faces, defs="", css="", grain=True, background=INK, border=True):
    """The panel shell: a rounded ink card with a hairline edge and a film grain over everything."""
    style = f"""{fonts_css(body, faces)}
  text {{ font-family: {SANS}; fill: {FG}; }}
  .mono {{ font-family: {MONO}; }}
  .caps {{ text-transform: uppercase; letter-spacing: .18em; font-size: 11.5px; font-weight: 500; }}
  .dim {{ fill: {DIM}; }}
{css}
  @media (prefers-reduced-motion: reduce) {{ *, *::before {{ animation-duration: 1ms !important; animation-delay: 0s !important;
    animation-iteration-count: 1 !important; }} }}"""
    edge = (f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="{RADIUS - .5}" fill="none" stroke="{HAIR}"/>'
            if border else "")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{html.escape(label)}">
<title>{html.escape(label)}</title>
<defs>
  <clipPath id="card"><rect width="{W}" height="{h}" rx="{RADIUS}"/></clipPath>
  {GRAIN}
  {defs}
</defs>
<style>
{style}
</style>
<g clip-path="url(#card)">
  <rect width="{W}" height="{h}" fill="{background}"/>
{body}
  {f'<rect width="{W}" height="{h}" filter="url(#grain)"/>' if grain else ""}
</g>
{edge}
</svg>
"""


def write(name, svg, out=HERE):
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / name).write_text(svg, encoding="utf-8")
    print(f"{name}: {len(svg.encode()) / 1024:.0f} KB")
