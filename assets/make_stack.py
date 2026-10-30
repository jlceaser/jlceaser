"""Builds the toolbox as a one-row custom keyboard: dusk keycaps with peach legends and one ember accent key, tapped one
after another. Each tap sinks the key, lights its legend and the LED under it, blooms a warm underglow onto the plate
and types the tool's line into the readout below.

Logos come from simple-icons (CC0), fetched at build time and inlined.
Run: python assets/make_stack.py [out_dir]  -> writes stack.svg (default out_dir: next to this file).
"""
import re
import sys
import urllib.request

from common import DIM, FG, HERE, INK, NAME, SUN, W, card, text_width, write

H = 268
SIMPLE_ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@16.36.0/icons/{}.svg"

# (slug, name, note). The first key is the ember accent, set apart like an Esc key.
KEYS = [
    ("cplusplus", "C++23", "the core of the Makine launcher"),
    ("qt", "Qt 6 · QML", "every screen of the launcher"),
    ("cmake", "CMake", "builds everything native"),
    ("rust", "Rust", "the Makine Discord bot"),
    ("typescript", "TypeScript", "the websites and their Workers"),
    ("cloudflare", "Cloudflare", "Workers · R2 · D1, the edge it all runs on"),
    ("unity", "Unity · C#", "CEDRA prototypes and a Unity MCP server"),
    ("raylib", "raylib", "One Line's engine, native C++ on Android"),
    ("kotlin", "Kotlin", "the Android side"),
    ("python", "Python", "tooling, build scripts, data"),
    ("blender", "Blender", "models and renders"),
]
WORDS = {"raylib"}  # keys whose logo is a word too small to read on a cap
IDLE = "the toolbox behind CEDRA, Makine Çeviri and Finetion"
SCALE = {"cmake": .94, "unity": .96, "kotlin": .84, "typescript": .88, "cplusplus": 1.02, "cloudflare": 1.18, "blender": 1.08}  # optical sizes

U, GAP, ESC_GAP = 78, 10, 32  # key pitch, gap between keys, the gap after the accent key
KEY_H = 72  # footprint height: top face plus the front wall
CASE_X, CASE_Y, CASE_W, CASE_H = 40, 78, W - 80, 120
KEY_Y = CASE_Y + 15
LED_Y = KEY_Y + KEY_H + 16
READ_Y, READ_SIZE = 234, 14

STEP, START = 2.4, .6  # seconds per key, delay before the first tap
T = STEP * len(KEYS)
EASE_OUT = "cubic-bezier(.16,1,.3,1)"


def icon(slug):
    with urllib.request.urlopen(SIMPLE_ICONS.format(slug)) as r:
        return re.search(r' d="([^"]+)"', r.read().decode()).group(1)


def pct(s):
    return f"{100 * s / T:.3f}%"


def key_x(i):
    return CASE_X + (CASE_W - (len(KEYS) * U - GAP + ESC_GAP)) / 2 + i * U + (ESC_GAP if i else 0)


def keycap(i, slug, path):
    accent = i == 0
    x = key_x(i)
    w = U - GAP
    s = 28 / 24 * SCALE.get(slug, 1)
    face_cx, face_cy = w / 2, 3 + 29
    skirt, face, rim = ("url(#skirt-a)", "url(#face-a)", "url(#rim-a)") if accent else ("url(#skirt)", "url(#face)", "url(#rim)")
    delay = f"animation-delay:{START + i * STEP:.2f}s"
    cls = "legend-a" if accent else "legend"
    if path is None:  # no logo worth shrinking to a keycap: a text legend, as custom sets do for modifiers
        legend = f'<text x="{face_cx}" y="{face_cy + 4.5}" text-anchor="middle" class="{cls} word" style="{delay}">{slug}</text>'
    else:
        legend = (f'<g transform="translate({face_cx - 12 * s:.2f} {face_cy - 12 * s:.2f}) scale({s:.3f})">'
                  f'<path class="{cls}" style="{delay}" d="{path}"/></g>')
    return f"""  <g transform="translate({x:.1f} {KEY_Y})">
    <ellipse class="glow" style="{delay}" cx="{w / 2}" cy="{KEY_H / 2 + 4}" rx="{w * .86:.1f}" ry="{KEY_H * .78:.1f}" fill="url(#bloom)"/>
    <rect class="shadow-soft" style="{delay}" x="2" y="8" width="{w - 4}" height="{KEY_H - 2}" rx="10" fill="#000" filter="url(#soft)"/>
    <rect class="shadow-tight" style="{delay}" x="1" y="3" width="{w - 2}" height="{KEY_H - 1}" rx="10" fill="#000" filter="url(#tight)"/>
    <g class="tap" style="{delay}">
      <rect width="{w}" height="{KEY_H}" rx="10" fill="{skirt}"/>
      <rect width="{w}" height="{KEY_H}" rx="10" fill="url(#walls)"/>
      <rect x=".5" y=".5" width="{w - 1}" height="{KEY_H - 1}" rx="9.5" fill="none" stroke="{'rgba(255,214,186,.22)' if accent else 'rgba(237,233,228,.07)'}"/>
      <rect x="5" y="3" width="{w - 10}" height="61" rx="9" fill="#000" fill-opacity="{'.22' if accent else '.38'}" filter="url(#lip)"/>
      <rect x="6" y="3" width="{w - 12}" height="58" rx="8" fill="{face}"/>
      <rect x="6" y="3" width="{w - 12}" height="58" rx="8" fill="url(#dish)"/>
      <rect x="6" y="3" width="{w - 12}" height="58" rx="8" fill="url(#sheen)"/>
      <rect x="6.5" y="3.5" width="{w - 13}" height="57" rx="7.5" fill="none" stroke="{rim}"/>
      {legend}
    </g>
    <circle class="led" cx="{w / 2}" cy="{LED_Y - KEY_Y}" r="1.6"/>
    <circle class="led-on" style="{delay}" cx="{w / 2}" cy="{LED_Y - KEY_Y}" r="1.6"/>
    <circle class="led-on" style="{delay}" cx="{w / 2}" cy="{LED_Y - KEY_Y}" r="5" fill="url(#bloom)"/>
  </g>"""


def readout(i, name, note):
    """One line of the readout, typed out on its key's tap: a cover the colour of the card slides off it in steps."""
    x = CASE_X
    head = f"› {name}  "
    line = head + note
    n = len(line)
    tw = text_width(line, READ_SIZE, "mono", 400)
    adv = tw / n
    typing = min(.9, .02 * n)
    t0 = .05
    frames = (f"@keyframes l{i} {{ 0% {{ opacity: 0; }} {pct(.04)} {{ opacity: 1; }} {pct(STEP - .3)} {{ opacity: 1; }} "
              f"{pct(STEP - .06)} {{ opacity: 0; }} 100% {{ opacity: 0; }} }}\n"
              f"  @keyframes c{i} {{ 0% {{ transform: translateX(0px); }} {pct(t0)} {{ transform: translateX(0px); "
              f"animation-timing-function: steps({n}, end); }} {pct(t0 + typing)} {{ transform: translateX({tw:.1f}px); }} "
              f"100% {{ transform: translateX({tw:.1f}px); }} }}")
    count = f"{i + 1:02d} / {len(KEYS):02d}"
    delay = f"animation-delay:{START + i * STEP:.2f}s"
    return f"""  <g class="line" style="animation-name:l{i};{delay}">
    <text x="{x}" y="{READ_Y}" class="mono read" xml:space="preserve" textLength="{tw:.1f}" lengthAdjust="spacing"><tspan class="hot">›</tspan> <tspan class="hot name">{name}</tspan>  <tspan class="note">{note}</tspan></text>
    <g class="type" style="animation-name:c{i};{delay}">
      <rect x="{x - 1}" y="{READ_Y - 15}" width="{tw + 14:.1f}" height="21" fill="{INK}"/>
      <rect class="caret" x="{x + 1}" y="{READ_Y - 12}" width="{adv * .9:.1f}" height="15" rx="1"/>
    </g>
    <text x="{W - 40}" y="{READ_Y}" text-anchor="end" class="mono read dim">{count}</text>
  </g>""", frames


def svg():
    paths = {slug: None if slug in WORDS else icon(slug) for slug, _, _ in KEYS}
    keys = "\n".join(keycap(i, slug, paths[slug]) for i, (slug, _, _) in enumerate(KEYS))
    lines, frames = zip(*(readout(i, name, note) for i, (_, name, note) in enumerate(KEYS)))

    tap, hold, up = pct(.07), pct(.2), pct(.38)
    defs = f"""<linearGradient id="case" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#22272a"/><stop offset="1" stop-color="#14181a"/></linearGradient>
  <linearGradient id="case-edge" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{FG}" stop-opacity=".14"/><stop offset=".25" stop-color="{FG}" stop-opacity=".04"/>
    <stop offset="1" stop-color="#000" stop-opacity=".4"/></linearGradient>
  <linearGradient id="plate" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0c0e0f"/><stop offset="1" stop-color="#121516"/></linearGradient>
  <linearGradient id="skirt" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3b3d46"/><stop offset=".72" stop-color="#2a2c33"/><stop offset="1" stop-color="#1a1c20"/></linearGradient>
  <linearGradient id="skirt-a" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#e8712f"/><stop offset=".78" stop-color="#b9481a"/><stop offset="1" stop-color="#8e3511"/></linearGradient>
  <linearGradient id="walls" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#000" stop-opacity=".28"/><stop offset=".12" stop-color="#000" stop-opacity="0"/>
    <stop offset=".88" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".32"/></linearGradient>
  <linearGradient id="face" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#383a43"/><stop offset="1" stop-color="#454751"/></linearGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{NAME}" stop-opacity=".07"/><stop offset=".45" stop-color="{NAME}" stop-opacity="0"/></linearGradient>
  <filter id="lip" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="1.2"/></filter>
  <linearGradient id="face-a" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#f27a37"/><stop offset="1" stop-color="#ff9150"/></linearGradient>
  <radialGradient id="dish" cx=".5" cy=".42" r=".62">
    <stop offset="0" stop-color="#000" stop-opacity=".16"/><stop offset=".7" stop-color="#000" stop-opacity=".04"/>
    <stop offset="1" stop-color="#fff" stop-opacity=".03"/></radialGradient>
  <linearGradient id="rim" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{FG}" stop-opacity=".16"/><stop offset=".5" stop-color="{FG}" stop-opacity=".03"/>
    <stop offset="1" stop-color="{FG}" stop-opacity=".1"/></linearGradient>
  <linearGradient id="rim-a" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffd2b0" stop-opacity=".55"/><stop offset=".5" stop-color="#ffd2b0" stop-opacity=".08"/>
    <stop offset="1" stop-color="#ffd2b0" stop-opacity=".3"/></linearGradient>
  <radialGradient id="bloom">
    <stop offset="0" stop-color="{SUN}" stop-opacity=".75"/><stop offset=".45" stop-color="{SUN}" stop-opacity=".28"/>
    <stop offset="1" stop-color="{SUN}" stop-opacity="0"/></radialGradient>
  <filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4.5"/></filter>
  <filter id="tight" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.6"/></filter>
  <filter id="inset" x="0" y="0" width="100%" height="100%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="3"/><feOffset dy="2"/>
    <feComposite in2="SourceAlpha" operator="arithmetic" k2="-1" k3="1"/>
    <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .8 0"/></filter>"""
    css = f"""  .eyebrow {{ font-size: 11.5px; font-weight: 500; letter-spacing: .2em; fill: {FG}; fill-opacity: .82; }}
  .read {{ font-size: {READ_SIZE}px; white-space: pre; }}
  .word {{ font-size: 14px; font-weight: 600; letter-spacing: -.01em; }}
  .hot {{ fill: {SUN}; }} .name {{ font-weight: 500; }} .note {{ fill: {FG}; fill-opacity: .74; }}
  .tap, .shadow-soft, .shadow-tight, .glow, .legend, .legend-a, .led-on, .line, .type {{
    animation-duration: {T:.2f}s; animation-iteration-count: infinite; animation-fill-mode: both; }}
  .tap {{ animation-name: tap; }}
  .shadow-soft {{ opacity: .75; animation-name: soft; }}
  .shadow-tight {{ opacity: 0; animation-name: tight; }}
  .glow {{ opacity: 0; animation-name: glow; }}
  .legend {{ fill: {NAME}; fill-opacity: .92; animation-name: lit; }}
  .legend-a {{ fill: {INK}; fill-opacity: .88; animation-name: lit-a; }}
  .led {{ fill: {FG}; fill-opacity: .1; }}
  .led-on {{ fill: {SUN}; opacity: 0; animation-name: led; }}
  .line {{ opacity: 0; }}
  .type {{ animation-timing-function: linear; }}
  .caret {{ fill: {SUN}; animation: blink 1s steps(1, end) infinite; }}
  .idle {{ animation: hide 1s infinite; }}
  @keyframes tap {{ 0% {{ transform: translateY(0px); animation-timing-function: cubic-bezier(.3,0,.6,1); }}
    {tap} {{ transform: translateY(4px); }} {hold} {{ transform: translateY(4px); animation-timing-function: {EASE_OUT}; }}
    {up} {{ transform: translateY(0px); }} 100% {{ transform: translateY(0px); }} }}
  @keyframes soft {{ 0% {{ opacity: .75; }} {tap} {{ opacity: .15; }} {hold} {{ opacity: .15; }} {up} {{ opacity: .75; }} 100% {{ opacity: .75; }} }}
  @keyframes tight {{ 0% {{ opacity: 0; }} {tap} {{ opacity: .9; }} {hold} {{ opacity: .9; }} {up} {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
  @keyframes glow {{ 0% {{ opacity: 0; }} {pct(.09)} {{ opacity: 1; animation-timing-function: ease-out; }}
    {pct(STEP * .92)} {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
  @keyframes led {{ 0% {{ opacity: 0; }} {pct(.07)} {{ opacity: 1; animation-timing-function: ease-in; }}
    {pct(STEP * .95)} {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
  @keyframes lit {{ 0% {{ fill: {NAME}; }} {pct(.07)} {{ fill: {SUN}; animation-timing-function: ease-in; }}
    {pct(STEP * .9)} {{ fill: {NAME}; }} 100% {{ fill: {NAME}; }} }}
  @keyframes lit-a {{ 0% {{ fill: {INK}; }} {pct(.07)} {{ fill: #fff3e8; animation-timing-function: ease-in; }}
    {pct(STEP * .9)} {{ fill: {INK}; }} 100% {{ fill: {INK}; }} }}
  @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
  @keyframes hide {{ 0%, 100% {{ opacity: 0; }} }}
  {chr(10).join("  " + f for f in frames)}"""
    tools = ", ".join(f"{name} ({note})" for _, name, note in KEYS)
    body = f"""  <text x="40" y="52" class="eyebrow">03 — STACK</text>
  <text x="{W - 40}" y="52" text-anchor="end" class="eyebrow">DAILY DRIVERS</text>
  <rect x="{CASE_X}" y="{CASE_Y}" width="{CASE_W}" height="{CASE_H}" rx="16" fill="url(#case)"/>
  <rect x="{CASE_X + .5}" y="{CASE_Y + .5}" width="{CASE_W - 1}" height="{CASE_H - 1}" rx="15.5" fill="none" stroke="url(#case-edge)"/>
  <rect x="{CASE_X + 8}" y="{CASE_Y + 7}" width="{CASE_W - 16}" height="{KEY_H + 18}" rx="10" fill="url(#plate)"/>
  <rect x="{CASE_X + 8}" y="{CASE_Y + 7}" width="{CASE_W - 16}" height="{KEY_H + 18}" rx="10" fill="#000" filter="url(#inset)"/>
{keys}
  <text x="{CASE_X}" y="{READ_Y}" class="mono read idle" xml:space="preserve"><tspan class="hot">›</tspan> <tspan class="note">{IDLE}</tspan></text>
{chr(10).join(lines)}"""
    return card(H, body, label=f"Stack, as keys on a custom keyboard pressed one after another: {tools}.",
                defs=defs, css=css, faces=[("sans", 500), ("sans", 600), ("mono", 400), ("mono", 500)])


if __name__ == "__main__":
    write("stack.svg", svg(), sys.argv[1] if len(sys.argv) > 1 else HERE)
