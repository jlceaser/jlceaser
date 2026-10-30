"""Builds the closing panel: the seed poem, after dusk. A seed lies under the soil line; roots feel their way down, a
sprout climbs and opens two leaves, and the poem's lines arrive with the growth, each with its English underneath.
Then it stays; only the leaves sway, the afterglow breathes and a few motes drift.

Run: python assets/make_seed.py [out_dir]  -> writes seed.svg (default out_dir: next to this file).
"""
import math
import random
import sys
from pathlib import Path

from common import COAL, EMBER, FG, HAZE, HERE, INK, NAME, PEACH, RULE, SUN, W, card, write

H = 344
EASE = "cubic-bezier(.16,1,.3,1)"
HORIZON, SX, SY = 211, 768, 228  # the soil line and the seed under it

POEM = [  # (Turkish rows, English, seconds it arrives)
    (["Toprak altında bir tohum var."], "There is a seed beneath the soil.", .55),
    (["Tohum bilmiyor toprağın üstünde ne olduğunu."], "The seed doesn't know what lies above the soil.", 1.75),
    (["Sadece biliyor: <tspan class='up'>yukarı</tspan> doğru bir şey var",
      "ve <tspan class='down'>aşağı</tspan> doğru bir şey var."],
     "It only knows: there is something upward, and something downward.", 3.2),
]
TEXT_X, FIRST_Y, TR_LEAD, EN_GAP = 40, 110, 30, 22
STANZA = (38, 50)  # the second gap is the soil line: the last stanza is underground

ROOT_SPEED, ROOT_START = 50, 1.55  # px/s at which a root tip advances; when the first root sets off
STEM_START, STEM_TIME = 1.8, 1.5


def smooth(pts, lo=0, hi=None):
    """Catmull-Rom through pts[lo..hi] as cubic Béziers, with tangents taken from the whole run so pieces of one
    curve meet without a kink. Returns the path and its length."""
    hi = len(pts) - 1 if hi is None else hi
    d, ln = f"M{pts[lo][0]:.1f} {pts[lo][1]:.1f}", 0
    for i in range(lo, hi):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        prev = p1
        for k in range(1, 17):  # arc length by sampling the Bézier
            t = k / 16
            q = tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * e
                      for a, b, c, e in zip(p1, c1, c2, p2))
            ln, prev = ln + math.dist(prev, q), q
    return d, ln


def length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


class Roots:
    """A taproot with laterals and rootlets, each bending back towards the pull of gravity. Every root is drawn in
    three pieces of falling width, one after another, so it tapers as it grows."""

    def __init__(self, seed=4):
        self.rng, self.paths, self.deepest = random.Random(seed), [], 0

    def grow(self, start, angle, size, width, depth, t0):
        rng = self.rng
        n = max(4, round(size / 7))
        pull = (.2, .075, .05)[depth]
        pts, a = [start], angle
        for _ in range(n):
            a += rng.gauss(0, (3.5, 5, 6)[depth])
            a += (90 - a) * pull
            x, y = pts[-1]
            pts.append((x + size / n * math.cos(math.radians(a)), y + size / n * math.sin(math.radians(a))))
            self.deepest = max(self.deepest, pts[-1][1])
        # Three tapering pieces sharing their joints.
        cuts = [0, n // 3, 2 * n // 3, n]
        t = t0
        for k in range(3):
            if cuts[k + 1] == cuts[k]:
                continue
            d, ln = smooth(pts, cuts[k], cuts[k + 1])
            dur = ln / ROOT_SPEED * (1 + .35 * depth)
            self.paths.append((d, ln, width * (1, .72, .45)[k], t, dur, depth, k == 2))
            t += dur
        if depth == 2:
            return
        total = length(pts)
        # Branch points along the root, alternating sides, set off when the tip passes them.
        fracs = [.2, .3, .4, .5, .6, .7, .8, .88] if depth == 0 else [.42, .74]
        side = rng.choice((-1, 1))
        for f in fracs:
            i = max(1, min(n - 1, round(f * n)))
            here = pts[i]
            seg = math.degrees(math.atan2(pts[i + 1][1] - pts[i - 1][1], pts[i + 1][0] - pts[i - 1][0]))
            if depth == 0:  # laterals leave the taproot almost level, alternating sides
                branch = seg + side * rng.uniform(70, 88)
                sz = size * rng.uniform(.36, .74) * (1.12 - .8 * f)
            else:  # rootlets fork off a lateral on its lower side, at a shallow angle
                branch = min((seg + s * rng.uniform(28, 45) for s in (-1, 1)), key=lambda b: abs(b - 90))
                sz = rng.uniform(6, 12)
            self.grow(here, branch, sz, width * (.58 if depth == 0 else .7), depth + 1,
                      t0 + length(pts[:i + 1]) / total * (t - t0) + rng.uniform(.05, .2))
            side = -side

    def svg(self):
        out, frames = [], []
        for i, (d, ln, w, t, dur, depth, last) in enumerate(self.paths):
            ease = "cubic-bezier(.3,.6,.4,1)" if last else "linear"
            op = (.78, .6, .45)[depth]
            out.append(f'<path d="{d}" class="root" stroke-width="{w:.2f}" stroke-opacity="{op}" '
                       f'stroke-dasharray="{ln + 1:.1f}" style="stroke-dashoffset:{ln + 1:.1f};animation:grow {dur:.2f}s {ease} '
                       f'{t:.2f}s both"/>')
        return "\n    ".join(out)

    def end(self):
        return max(t + dur for *_, t, dur, _d, _l in self.paths)


def leaf(size, turn, delay):
    """A cotyledon: an outline, a breath of fill and a midrib, folded shut along the stem until it opens."""
    L, w = size, size * .36
    d = (f"M0 0C{w * .55:.1f} {-L * .12:.1f} {w * 1.08:.1f} {-L * .42:.1f} {w * .72:.1f} {-L * .74:.1f}"
         f"C{w * .45:.1f} {-L * .94:.1f} {w * .1:.1f} {-L * 1.0:.1f} 0 {-L:.1f}"
         f"C{-w * .2:.1f} {-L * .96:.1f} {-w * .62:.1f} {-L * .86:.1f} {-w * .8:.1f} {-L * .6:.1f}"
         f"C{-w * .98:.1f} {-L * .32:.1f} {-w * .5:.1f} {-L * .1:.1f} 0 0Z")
    rib = f"M0 -1.5C{w * .06:.1f} {-L * .35:.1f} {w * .05:.1f} {-L * .6:.1f} {-w * .02:.1f} {-L * .86:.1f}"
    veins = "".join(f'<path d="M{w * .03:.1f} {-L * f:.1f}q{s * w * .32:.1f} {-L * .07:.1f} {s * w * .55:.1f} {-L * .2:.1f}"/>'
                    for f, s in [(.3, 1), (.42, -1), (.55, 1), (.66, -1)])
    name = "open-l" if turn < 0 else "open-r"
    return (f'<g class="leaf" style="animation-name:{name};animation-delay:{delay:.2f}s">'
            f'<path d="{d}" class="blade"/><path d="{rib}" class="rib"/><g class="vein">{veins}</g></g>')


def sprout():
    """Stem from the seed up through the soil line, then two leaves opening at the top."""
    pts = [(0, -4), (1.0, -28), (1.7, -52), (1.3, -76), (0, -98)]
    (lower, l1), (upper, l2) = smooth(pts, 0, 2), smooth(pts, 2)
    t1 = STEM_TIME * l1 / (l1 + l2)
    top = pts[-1]
    leaves_at = STEM_START + STEM_TIME - .12
    return f"""<g class="sway">
      <path d="{lower}" class="stem" stroke-width="1.9" stroke-dasharray="{l1 + 1:.1f}"
        style="stroke-dashoffset:{l1 + 1:.1f};animation:grow {t1:.2f}s linear {STEM_START:.2f}s both"/>
      <path d="{upper}" class="stem" stroke-width="1.45" stroke-dasharray="{l2 + 1:.1f}"
        style="stroke-dashoffset:{l2 + 1:.1f};animation:grow {STEM_TIME - t1:.2f}s cubic-bezier(.3,.6,.4,1) {STEM_START + t1:.2f}s both"/>
      <g transform="translate({top[0]} {top[1]})">
        <g transform="rotate(-6)">{leaf(38, -1, leaves_at)}</g>
        <g transform="rotate(4)">{leaf(33, 1, leaves_at + .14)}</g>
        <circle r="1.3" class="bud" style="animation-delay:{leaves_at + .5:.2f}s"/>
      </g>
    </g>"""


def measure(top, bottom, at):
    """A plate's scale bar beside the plant: how far it reaches up, how far down, drawn once it has grown."""
    x, out = SX + 100, []
    for y0, y1, label, delay in [(HORIZON - 5, top, "YUKARI", at), (HORIZON + 5, bottom, "AŞAĞI", at + .2)]:
        mid = (y0 + y1) / 2
        out.append(f'<g class="bar" style="transform-origin:{x}px {y0}px;animation-delay:{delay:.2f}s">'
                   f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}"/><line x1="{x - 3.5}" y1="{y1}" x2="{x + 3.5}" y2="{y1}"/></g>'
                   f'<text x="{x + 10}" y="{mid + 3.5:.0f}" class="note fade" style="animation-delay:{delay + .35:.2f}s">{label}</text>')
    return "\n  ".join(out)


def poem():
    out, y = [], FIRST_Y
    for i, (rows, english, t) in enumerate(POEM):
        for k, row in enumerate(rows):
            out.append(f'<text x="{TEXT_X}" y="{y}" class="tr fade" style="animation-delay:{t + k * .22:.2f}s">{row}</text>')
            y += TR_LEAD
        y += EN_GAP - TR_LEAD
        out.append(f'<text x="{TEXT_X + 1}" y="{y}" class="en mono fade" style="animation-delay:{t + .2 + (len(rows) - 1) * .22:.2f}s">'
                   f'{english}</text>')
        y += STANZA[min(i, 1)]
    return "\n  ".join(out)


def motes(n=5, seed=3):
    rng = random.Random(seed)
    out, frames = [], []
    for i in range(n):
        x, y = SX + rng.uniform(-150, 160), HORIZON - rng.uniform(8, 60)
        dx, dy, dur = rng.uniform(-18, 18), -rng.uniform(26, 48), rng.uniform(9, 14)
        frames.append(f"@keyframes m{i} {{ 0% {{ transform: translate(0px, 0px); opacity: 0; }} 25% {{ opacity: .7; }} "
                      f"100% {{ transform: translate({dx:.0f}px, {dy:.0f}px); opacity: 0; }} }}")
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(.6, 1.1):.1f}" class="mote" '
                   f'style="animation:m{i} {dur:.1f}s ease-in-out {4.5 + rng.uniform(0, 5):.1f}s infinite"/>')
    return "\n  ".join(out), "\n  ".join(frames)


def svg():
    roots = Roots()
    roots.grow((0, 4), 90, 90, 1.6, 0, ROOT_START)
    grown = max(roots.end(), STEM_START + STEM_TIME + 1.2)
    specks, mote_frames = motes()
    rng = random.Random(9)
    grains = []
    while len(grains) < 22:  # loose soil around the seed, no two grains touching
        g = (SX + max(-110, min(110, rng.gauss(0, 48))), HORIZON + 5 + min(60, abs(rng.gauss(0, 24))))
        if all(math.dist(g, o) > 9 for o in grains):
            grains.append(g)
    soil = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(.4, .9):.1f}"/>' for x, y in grains)
    defs = f"""<linearGradient id="sky" x1="0" y1="0" x2="0" y2="{HORIZON}" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#1a1c22"/><stop offset=".72" stop-color="#1d1b1f"/><stop offset="1" stop-color="#2a1c18"/></linearGradient>
  <linearGradient id="ground" x1="0" y1="{HORIZON}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#141617"/><stop offset="1" stop-color="#0e1011"/></linearGradient>
  <radialGradient id="afterglow" cx="{SX + 30}" cy="{HORIZON}" r="330" gradientUnits="userSpaceOnUse"
    gradientTransform="translate({SX + 30} {HORIZON}) scale(1 .3) translate({-SX - 30} {-HORIZON})">
    <stop offset="0" stop-color="{SUN}" stop-opacity=".34"/><stop offset=".35" stop-color="{EMBER}" stop-opacity=".12"/>
    <stop offset="1" stop-color="{EMBER}" stop-opacity="0"/></radialGradient>
  <linearGradient id="soil-line" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="{FG}" stop-opacity="0"/><stop offset=".5" stop-color="{FG}" stop-opacity=".08"/>
    <stop offset=".7" stop-color="{PEACH}" stop-opacity=".55"/><stop offset=".86" stop-color="{FG}" stop-opacity=".16"/>
    <stop offset="1" stop-color="{FG}" stop-opacity="0"/></linearGradient>
  <radialGradient id="seed-fill" cx=".38" cy=".35" r=".75">
    <stop offset="0" stop-color="{HAZE}"/><stop offset="1" stop-color="{COAL}"/></radialGradient>
  <clipPath id="above"><rect width="{W}" height="{HORIZON}"/></clipPath>"""
    css = f"""  .eyebrow {{ font-size: 11.5px; font-weight: 500; letter-spacing: .2em; fill: {FG}; fill-opacity: .82; }}
  .tr {{ font-style: italic; font-weight: 400; font-size: 21px; letter-spacing: -.005em; fill: {FG}; fill-opacity: .94; }}
  .up, .down {{ fill: {NAME}; fill-opacity: 1; }}
  .en {{ font-size: 12.5px; letter-spacing: .01em; fill: {FG}; fill-opacity: .46; }}
  .fade {{ animation: fade 1.4s {EASE} both; }}
  .root {{ fill: none; stroke: {PEACH}; stroke-linecap: round; }}
  .stem {{ fill: none; stroke: {NAME}; stroke-linecap: round; }}
  .blade {{ fill: {NAME}; fill-opacity: .1; stroke: {NAME}; stroke-width: 1.1; stroke-linejoin: round; }}
  .rib {{ fill: none; stroke: {NAME}; stroke-width: .7; stroke-opacity: .8; stroke-linecap: round; }}
  .vein path {{ fill: none; stroke: {NAME}; stroke-width: .45; stroke-opacity: .5; stroke-linecap: round; }}
  .leaf {{ animation-duration: 1.5s; animation-timing-function: cubic-bezier(.2,.8,.25,1); animation-fill-mode: both; }}
  .bud {{ fill: {NAME}; animation: pop .8s {EASE} both; }}
  .sway {{ animation: sway 6s ease-in-out {grown:.1f}s infinite alternate; }}
  .seed {{ animation: seed 1.1s {EASE} .35s both; }}
  .soil-line {{ transform-origin: {SX}px {HORIZON}px; animation: spread 2.4s {EASE} .1s both; }}
  .glow {{ animation: glow-in 3s ease-out both; }}
  .breathe {{ animation: breathe 8s ease-in-out {3:.1f}s infinite alternate; }}
  .specks {{ fill: {PEACH}; fill-opacity: .16; animation: fade 2s ease-out 1.2s both; }}
  .mote {{ fill: {PEACH}; opacity: 0; }}
  .bar {{ stroke: {FG}; stroke-opacity: .26; stroke-width: .8; animation: bar 1.4s {EASE} both; }}
  .note {{ font-size: 10.5px; font-weight: 500; letter-spacing: .2em; fill: {NAME}; fill-opacity: .75; }}
  @keyframes bar {{ from {{ transform: scaleY(0); }} to {{ transform: scaleY(1); }} }}
  @keyframes grow {{ to {{ stroke-dashoffset: 0; }} }}
  @keyframes fade {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0px); }} }}
  @keyframes open-l {{ 0% {{ opacity: 0; transform: rotate(4deg) scale(.12, .3); }} 12% {{ opacity: 1; }}
    100% {{ opacity: 1; transform: rotate(-52deg) scale(1, 1); }} }}
  @keyframes open-r {{ 0% {{ opacity: 0; transform: rotate(-4deg) scale(.12, .3); }} 12% {{ opacity: 1; }}
    100% {{ opacity: 1; transform: rotate(48deg) scale(1, 1); }} }}
  @keyframes pop {{ from {{ opacity: 0; transform: scale(0); }} to {{ opacity: .9; transform: scale(1); }} }}
  @keyframes sway {{ from {{ transform: rotate(-1.4deg); }} to {{ transform: rotate(1.6deg); }} }}
  @keyframes seed {{ from {{ opacity: 0; transform: translateY(-4px) scale(.7); }} to {{ opacity: 1; transform: translateY(0px) scale(1); }} }}
  @keyframes spread {{ from {{ transform: scaleX(0); opacity: 0; }} to {{ transform: scaleX(1); opacity: 1; }} }}
  @keyframes glow-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @keyframes breathe {{ from {{ opacity: 1; }} to {{ opacity: .62; }} }}
  {mote_frames}"""
    body = f"""  <rect width="{W}" height="{HORIZON}" fill="url(#sky)"/>
  <rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" fill="url(#ground)"/>
  <g clip-path="url(#above)" class="glow"><g class="breathe"><rect width="{W}" height="{HORIZON}" fill="url(#afterglow)"/></g></g>
  <line x1="0" y1="{HORIZON}" x2="{W}" y2="{HORIZON}" stroke="url(#soil-line)" stroke-width="1" class="soil-line"/>
  <g class="specks">{soil}</g>
  {specks}
  <text x="40" y="52" class="eyebrow fade" style="animation-delay:.05s">04 — TOHUM</text>
  <text x="{W - 40}" y="52" text-anchor="end" class="eyebrow fade" style="animation-delay:.05s">GOODBYE, WORLD.</text>
  {poem()}
  {measure(SY - 128, SY + roots.deepest, grown - .6)}
  <g transform="translate({SX} {SY})">
    {roots.svg()}
    {sprout()}
    <g class="seed"><g transform="rotate(-24)">
      <ellipse rx="7.4" ry="4.6" fill="url(#seed-fill)" stroke="{EMBER}" stroke-width=".8" stroke-opacity=".85"/>
      <path d="M-5.2 .4Q0 -1.8 5.2 .2" fill="none" stroke="{PEACH}" stroke-width=".5" stroke-opacity=".55"/></g></g>
  </g>"""
    label = ("Toprak altında bir tohum var. Tohum bilmiyor toprağın üstünde ne olduğunu. Sadece biliyor: yukarı doğru bir "
             "şey var ve aşağı doğru bir şey var. — There is a seed beneath the soil. The seed doesn't know what lies above "
             "the soil. It only knows: there is something upward, and something downward. A seed under the soil line puts "
             "down roots and sends up a sprout that opens two leaves, in the last glow after sunset.")
    return card(H, body, label=label, defs=defs, css=css, faces=[("sans", 500), ("sans-italic", 400), ("mono", 400)])


if __name__ == "__main__":
    write("seed.svg", svg(), Path(sys.argv[1]) if len(sys.argv) > 1 else HERE)
