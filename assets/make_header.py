"""Builds the header: the sunset from the personal site, the name rising out of it, embers drifting up off the horizon
and the three trades on the dark ground below, each rule with a spark running along it.

Run: python assets/make_header.py  -> writes header.svg next to this file.
"""
import base64
import random

from common import DIM, EMBER, FG, HAIR, INK, MONO, NAME, PEACH, RULE, SUN, HERE, W, card, write

H = 460
HORIZON = 332  # where the sky meets the ground in the cropped photo
EASE = "cubic-bezier(.16,1,.3,1)"  # the site's easing

ROWS = [("Video games", "Game Director · Creative Director"),
        ("Software", "Full-stack · native C++ and Qt"),
        ("Localization", "Founder, Makine Çeviri")]
TABLE_X, VALUE_X, TABLE_R, ROW_Y, ROW_H = 476, 640, 960, 342, 32


def embers(n=38, seed=11):
    """Sparks lifting off the horizon and fading as they climb."""
    rng = random.Random(seed)
    out, frames = [], []
    for i in range(n):
        x, y = rng.uniform(20, W - 20), rng.uniform(HORIZON - 30, H - 10)
        r, rise, drift = rng.uniform(.7, 1.9), rng.uniform(140, 300), rng.uniform(-40, 40)
        dur, delay = rng.uniform(7, 15), rng.uniform(0, 15)
        color = rng.choice([SUN, PEACH, EMBER])
        frames.append(f"@keyframes e{i} {{ 0% {{ transform: translate(0px, 0px); opacity: 0; }} 12% {{ opacity: .95; }} "
                      f"70% {{ opacity: .6; }} 100% {{ transform: translate({drift:.0f}px, -{rise:.0f}px); opacity: 0; }} }}")
        out.append(f'<g transform="translate({x:.0f} {y:.0f})"><g class="ember" style="animation-name:e{i};'
                   f'animation-duration:{dur:.1f}s;animation-delay:-{delay:.1f}s">'
                   f'<circle r="{r * 3.2:.1f}" fill="url(#spark)"/><circle r="{r:.1f}" fill="{color}"/></g></g>')
    return "\n  ".join(out), "\n  ".join(frames)


def table():
    out = []
    for i, (label, value) in enumerate(ROWS):
        y = ROW_Y + i * ROW_H
        delay = 1.1 + i * .12
        out.append(f'<line class="rule" x1="{TABLE_X}" y1="{y}" x2="{TABLE_R}" y2="{y}" style="animation-delay:{delay:.2f}s"/>'
                   f'<line class="spark-line" x1="{TABLE_X}" y1="{y}" x2="{TABLE_R}" y2="{y}" '
                   f'style="animation-duration:{9 + i * 2.6:.1f}s;animation-delay:-{i * 3.1:.1f}s"/>'
                   f'<g class="fade" style="animation-delay:{delay + .2:.2f}s">'
                   f'<text x="{TABLE_X}" y="{y + 21}" class="caps dim">{label}</text>'
                   f'<text x="{VALUE_X}" y="{y + 21}" class="value">{value}</text></g>')
    y = ROW_Y + len(ROWS) * ROW_H
    out.append(f'<line class="rule" x1="{TABLE_X}" y1="{y}" x2="{TABLE_R}" y2="{y}" style="animation-delay:1.46s"/>')
    return "\n  ".join(out)


def svg():
    sparks, ember_frames = embers()
    photo = base64.b64encode((HERE / "sunset.jpg").read_bytes()).decode()
    defs = f"""<linearGradient id="left" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{INK}" stop-opacity=".72"/><stop offset=".42" stop-color="{INK}" stop-opacity=".18"/>
    <stop offset=".7" stop-color="{INK}" stop-opacity="0"/></linearGradient>
  <linearGradient id="top" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{INK}" stop-opacity=".55"/><stop offset=".22" stop-color="{INK}" stop-opacity="0"/>
    <stop offset=".7" stop-color="{INK}" stop-opacity="0"/><stop offset="1" stop-color="{INK}" stop-opacity=".6"/></linearGradient>
  <radialGradient id="glow" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="{SUN}" stop-opacity=".55"/><stop offset="1" stop-color="{SUN}" stop-opacity="0"/></radialGradient>
  <radialGradient id="spark"><stop offset="0" stop-color="{SUN}" stop-opacity=".5"/><stop offset="1" stop-color="{SUN}" stop-opacity="0"/></radialGradient>
  <linearGradient id="spark-grad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{SUN}" stop-opacity="0"/><stop offset=".5" stop-color="{SUN}"/><stop offset="1" stop-color="{PEACH}" stop-opacity="0"/></linearGradient>
  <clipPath id="l1"><rect x="0" y="120" width="{W}" height="104"/></clipPath>
  <clipPath id="l2"><rect x="0" y="224" width="{W}" height="104"/></clipPath>"""
    css = f"""  .kb {{ transform-origin: 600px 300px; animation: kb 40s ease-in-out infinite alternate; }}
  .glow {{ transform-box: fill-box; transform-origin: center; animation: breathe 7s ease-in-out infinite alternate; }}
  .ember {{ animation-timing-function: linear; animation-iteration-count: infinite; opacity: 0; }}
  .name {{ font-weight: 600; font-size: 96px; letter-spacing: -.035em; fill: {NAME}; }}
  .up {{ animation: up 1.3s {EASE} both; }}
  .fade {{ animation: fade 1.2s {EASE} both; }}
  .eyebrow {{ font-size: 11.5px; font-weight: 500; letter-spacing: .2em; fill: {FG}; fill-opacity: .82; }}
  .mark {{ font-size: 13px; font-weight: 600; letter-spacing: .26em; fill: {FG}; }}
  .value {{ font-size: 15px; font-weight: 500; fill: {FG}; }}
  .rule {{ stroke: {RULE}; stroke-width: 1; transform-box: fill-box; transform-origin: left; animation: draw 1.4s {EASE} both; }}
  .spark-line {{ stroke: url(#spark-grad); stroke-width: 1.4; stroke-dasharray: 120 1400; stroke-dashoffset: 120;
    animation: run linear infinite; }}
  .live {{ fill: {SUN}; animation: live 2.4s ease-in-out infinite; }}
  .live-ring {{ fill: none; stroke: {SUN}; transform-box: fill-box; transform-origin: center; animation: ring 2.4s ease-out infinite; }}
  @keyframes kb {{ from {{ transform: scale(1); }} to {{ transform: scale(1.07) translate(-6px, 4px); }} }}
  @keyframes breathe {{ from {{ opacity: .55; transform: scale(.94); }} to {{ opacity: 1; transform: scale(1.06); }} }}
  {ember_frames}
  @keyframes up {{ from {{ transform: translateY(104px); }} to {{ transform: translateY(0); }} }}
  @keyframes fade {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  @keyframes draw {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
  @keyframes run {{ from {{ stroke-dashoffset: 120; }} to {{ stroke-dashoffset: -1400; }} }}
  @keyframes live {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .45; }} }}
  @keyframes ring {{ from {{ transform: scale(.6); opacity: .8; }} to {{ transform: scale(2.4); opacity: 0; }} }}"""
    body = f"""  <g class="kb"><image href="data:image/jpeg;base64,{photo}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/></g>
  <ellipse class="glow" cx="300" cy="{HORIZON - 6}" rx="300" ry="46" fill="url(#glow)"/>
  <rect width="{W}" height="{H}" fill="url(#left)"/>
  <rect width="{W}" height="{H}" fill="url(#top)"/>
  {sparks}
  <g class="fade" style="animation-delay:.1s">
    <text x="40" y="52" class="mark">CEASER</text>
    <circle class="live-ring" cx="{W - 197}" cy="47.5" r="4" stroke-width="1"/><circle class="live" cx="{W - 197}" cy="47.5" r="3"/>
    <text x="{W - 40}" y="52" text-anchor="end" class="eyebrow">TÜRKİYE · GMT+3</text>
  </g>
  <g class="fade" style="animation-delay:.35s">
    <text x="42" y="102" class="eyebrow">FOUNDER, CEDRA INTERACTIVE</text>
    <text x="42" y="121" class="eyebrow">CO-FOUNDER, MAKİNE ÇEVİRİ &amp; FINETION</text>
  </g>
  <g clip-path="url(#l1)"><text x="34" y="212" class="name up" style="animation-delay:.25s">SEZER</text></g>
  <g clip-path="url(#l2)"><text x="148" y="314" class="name up" style="animation-delay:.42s">UZUN</text></g>
  {table()}"""
    label = ("Sezer Uzun (Ceaser), silhouetted against a sunset. Founder of CEDRA Interactive, co-founder of Makine Çeviri "
             "and Finetion. Video games: Game Director and Creative Director. Software: full-stack, native C++ and Qt. "
             "Localization: founder of Makine Çeviri.")
    return card(H, body, label=label, defs=defs, css=css, faces=[("sans", 500), ("sans", 600)])


if __name__ == "__main__":
    write("header.svg", svg())
