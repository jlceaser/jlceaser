"""Builds the One Line panel: the last 12 months of contributions as a board from One Line, CEDRA Interactive's puzzle
game, where a single line has to visit every cell once. The line snakes through the year week by week, down one
column and up the next, so it passes the days nearly in order; each day lights as the head goes over it, the busy ones
in ember. It plays once and stays, the head resting on today, then the year's numbers come up underneath.

Run: GH_TOKEN=<token> python assets/make_oneline.py [out_dir]  -> writes oneline.svg (default out_dir: next to this file).
"""
import calendar
import math
import sys
from pathlib import Path

from common import DIM, EMBER, FG, FLAME, HAIR, HAZE, INK, NAME, PEACH, SUN, W, card, write
from contrib import facts, fetch

H = 344
GX, GY = 41, 76  # top-left of the board
PITCH, CELL, TILE_R = 17.4, 13.2, 3.4
TURN_R = 5.2  # corner radius of the line where it turns at the top and bottom of a column
LINE_W = 3.6
START, DRAW = .7, 8.4  # when the line sets off and how long it takes to cross the year
EASE = "cubic-bezier(.16,1,.3,1)"
LEVELS = ["", "#9A3A13", "#CC5119", "#F37A30", "#FFB07A"]  # tile colour for contribution levels 1-4
SAMPLES = 48


def progress(u):
    """Share of the line drawn at share u of the time: sets off briskly, slows as it reaches today."""
    return .62 * u + .38 * math.sin(u * math.pi / 2)


def time_at(f):
    """Inverse of progress() as SMIL will play it: linear between the sampled points."""
    us = [i / SAMPLES for i in range(SAMPLES + 1)]
    ps = [progress(u) for u in us]
    for i in range(SAMPLES):
        if ps[i + 1] >= f:
            return us[i] + (us[i + 1] - us[i]) * (f - ps[i]) / ((ps[i + 1] - ps[i]) or 1)
    return 1


def centre(col, row):
    return GX + col * PITCH + CELL / 2, GY + row * PITCH + CELL / 2


def route(weeks):
    """Every day in snake order, columns alternating direction so the last week runs down and ends on today."""
    cells = []
    for col, week in enumerate(weeks):
        days = sorted(week, key=lambda d: d["weekday"])
        if (len(weeks) - 1 - col) % 2:
            days.reverse()
        cells += [(col, d["weekday"], d) for d in days]
    return cells


def line(cells):
    """The path through every cell centre with rounded turns, and how far along it each cell is visited."""
    pts = [centre(c, r) for c, r, _ in cells]
    d, dist, run, cut = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"], [0.0], 0.0, 0.0
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        step = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / step, (y1 - y0) / step
        nxt = pts[i + 1] if i + 1 < len(pts) else None
        if nxt:
            n = math.hypot(nxt[0] - x1, nxt[1] - y1)
            vx, vy = (nxt[0] - x1) / n, (nxt[1] - y1) / n
        if nxt and abs(ux * vx + uy * vy) < .99:  # a turn: round the corner
            sweep = 1 if ux * vy - uy * vx > 0 else 0
            ax, ay, bx, by = x1 - ux * TURN_R, y1 - uy * TURN_R, x1 + vx * TURN_R, y1 + vy * TURN_R
            d.append(f"L{ax:.1f} {ay:.1f}A{TURN_R} {TURN_R} 0 0 {sweep} {bx:.1f} {by:.1f}")
            arc = math.pi * TURN_R / 2
            dist.append(run + step - cut - TURN_R + arc / 2)  # the arc's midpoint is where the head passes the cell
            run += step - cut - TURN_R + arc
            cut = TURN_R  # the next straight starts where the arc ends
        else:
            d.append(f"L{x1:.1f} {y1:.1f}")
            run += step - cut
            cut = 0.0
            dist.append(run)
    return "".join(d), dist, run


def months(weeks):
    """Month initials under the column holding each month's first day."""
    out, last = [], -9
    for col, week in enumerate(weeks):
        first = next((d for d in week if d["date"].endswith("-01")), None)
        if first and col - last > 2 and col < len(weeks) - 1:
            x = GX + col * PITCH
            out.append(f'<text x="{x:.1f}" y="{GY + 7 * PITCH + 13}" class="mono month">'
                       f'{calendar.month_abbr[int(first["date"][5:7])]}</text>')
            last = col
    return "".join(out)


def stats(f):
    # A live streak earns its slot; between streaks the busiest single day takes it instead of a bare zero.
    peak = (str(f["streak"]), "Day streak") if f["streak"] else (
        str(f["top_n"]), f"Peak day · {calendar.month_abbr[int(f['top_day'][5:7])]} {int(f['top_day'][8:])}")
    items = [(f"{f['total']:,}", "Contributions", "lead"), (str(f["active"]), "Active days", ""),
             (*peak, ""), (str(f["best"]), "Best streak", ""),
             (f["month"][:3], f"Busiest · {f['month_n']}", "")]
    out, y, col = [], H - 80, (W - 80) / len(items)
    for i, (value, label, cls) in enumerate(items):
        x = 40 + i * col
        delay = START + DRAW + .15 + i * .09
        sep = f'<line x1="{x - 24:.1f}" y1="{y - 27}" x2="{x - 24:.1f}" y2="{y + 19}" class="sep"/>' if i else ""
        out.append(f'<g class="rise" style="animation-delay:{delay:.2f}s">{sep}'
                   f'<text x="{x:.1f}" y="{y}" class="stat {cls}">{value}</text>'
                   f'<text x="{x:.1f}" y="{y + 19}" class="caps dim">{label}</text></g>')
    return "".join(out)


def svg(weeks):
    f = facts(weeks)
    cells = route(weeks)
    path, dist, length = line(cells)
    today = cells[-1]
    tx, ty = centre(today[0], today[1])
    sx, sy = centre(cells[0][0], cells[0][1])

    us = [i / SAMPLES for i in range(SAMPLES + 1)]
    key_times = ";".join(f"{u:.4f}" for u in us)
    key_points = ";".join(f"{progress(u):.4f}" for u in us)
    offsets = ";".join(f"{length * (1 - progress(u)):.1f}" for u in us)

    board, seen, hot, sparks = [], [], [], []
    for (col, row, day), at in zip(cells, dist):
        x, y = GX + col * PITCH, GY + row * PITCH
        t = START + DRAW * time_at(at / length)
        board.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="{TILE_R}" class="in" '
                     f'style="animation-delay:{col * .012:.3f}s"/>')
        (hot if day["level"] else seen).append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="{TILE_R}" '
            f'class="{f"hot l{day["level"]}" if day["level"] else "seen"}" style="animation-delay:{t:.3f}s"/>')
        if day["level"] >= 2:
            cx, cy = x + CELL / 2, y + CELL / 2
            sparks.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{CELL / 2:.1f}" class="burst" style="animation-delay:{t:.3f}s"/>')

    end = START + DRAW
    first, last = weeks[0][0]["date"], weeks[-1][-1]["date"]
    span = f"{calendar.month_abbr[int(first[5:7])]} {first[:4]} — {calendar.month_abbr[int(last[5:7])]} {last[:4]}"
    defs = f"""<linearGradient id="year" gradientUnits="userSpaceOnUse" x1="{GX}" y1="0" x2="{GX + len(weeks) * PITCH}" y2="0">
    <stop offset="0" stop-color="{FLAME}"/><stop offset=".38" stop-color="{EMBER}"/><stop offset=".72" stop-color="{SUN}"/>
    <stop offset="1" stop-color="{PEACH}"/></linearGradient>
  <radialGradient id="head-glow"><stop offset="0" stop-color="{PEACH}" stop-opacity=".75"/>
    <stop offset="1" stop-color="{SUN}" stop-opacity="0"/></radialGradient>
  <path id="route" d="{path}"/>"""
    css = f"""  .eyebrow {{ font-size: 11.5px; font-weight: 500; letter-spacing: .2em; fill: {FG}; fill-opacity: .82; }}
  .month {{ font-size: 10.5px; fill: {DIM}; }}
  .in {{ fill: {FG}; fill-opacity: .055; animation: in .6s ease-out both; }}
  .seen {{ fill: {HAZE}; fill-opacity: .36; animation: seen .35s ease-out both; }}
  .hot {{ stroke: {INK}; stroke-width: 1.6; paint-order: stroke; transform-box: fill-box; transform-origin: center;
    animation: pop .55s {EASE} both; }}
  .l1 {{ fill: {LEVELS[1]}; }} .l2 {{ fill: {LEVELS[2]}; }} .l3 {{ fill: {LEVELS[3]}; }} .l4 {{ fill: {LEVELS[4]}; }}
  .burst {{ fill: none; stroke: {PEACH}; stroke-width: 1.2; opacity: 0; transform-box: fill-box; transform-origin: center;
    animation: burst .7s ease-out both; }}
  .trail {{ fill: none; stroke: url(#year); stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: {length:.1f} {length + 10:.1f}; }}
  .core {{ stroke-width: {LINE_W}; opacity: .9; }}
  .halo {{ stroke-width: 10; opacity: .08; }}
  .static {{ display: none; }}
  .stat {{ font-size: 28px; font-weight: 600; letter-spacing: -.02em; fill: {FG}; }}
  .lead {{ fill: {NAME}; }}
  .sep {{ stroke: {HAIR}; }}
  .caption {{ font-size: 12.5px; font-weight: 500; fill: {DIM}; }}
  .rise {{ animation: rise .9s {EASE} both; }}
  .fade {{ animation: fade .8s ease-out both; }}
  .mover {{ animation: gone .25s ease-out {end:.2f}s both; }}
  .rest {{ animation: fade .3s ease-out {end - .05:.2f}s both; }}
  .pulse {{ transform-box: fill-box; transform-origin: center; animation: pulse 2.6s ease-out {end:.2f}s infinite both; }}
  @keyframes in {{ from {{ fill-opacity: 0; }} to {{ fill-opacity: .055; }} }}
  @keyframes seen {{ from {{ fill-opacity: 0; }} to {{ fill-opacity: .36; }} }}
  @keyframes pop {{ 0% {{ opacity: 0; transform: scale(.35); }} 55% {{ opacity: 1; transform: scale(1.22); }}
    100% {{ opacity: 1; transform: scale(1); }} }}
  @keyframes burst {{ 0% {{ opacity: 0; transform: scale(.8); }} 10% {{ opacity: .9; }} 100% {{ opacity: 0; transform: scale(2.4); }} }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0px); }} }}
  @keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @keyframes gone {{ from {{ opacity: 1; }} to {{ opacity: 0; }} }}
  @keyframes pulse {{ 0% {{ opacity: .9; transform: scale(.5); }} 70%, 100% {{ opacity: 0; transform: scale(1.9); }} }}
  @media (prefers-reduced-motion: reduce) {{ .static {{ display: inline; }} .drawn, .mover {{ display: none; }} }}"""
    anim = f'dur="{DRAW}s" begin="{START}s" fill="freeze" calcMode="linear" keyTimes="{key_times}"'
    body = f"""  <g class="fade" style="animation-delay:.05s">
    <text x="40" y="52" class="eyebrow">02 — ONE LINE</text>
    <text x="{W - 40}" y="52" text-anchor="end" class="eyebrow">{span.upper()} · UPDATED DAILY</text>
  </g>
  <g>{"".join(board)}</g>
  <g>{"".join(seen)}</g>
  <g class="fade" style="animation-delay:.3s">{months(weeks)}</g>
  <g class="drawn">
    <use href="#route" class="trail halo" stroke-dashoffset="{length:.1f}"><animate attributeName="stroke-dashoffset" values="{offsets}" {anim}/></use>
    <use href="#route" class="trail core" stroke-dashoffset="{length:.1f}"><animate attributeName="stroke-dashoffset" values="{offsets}" {anim}/></use>
  </g>
  <g class="static"><use href="#route" class="trail halo"/><use href="#route" class="trail core"/></g>
  <g>{"".join(hot)}</g>
  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="2.6" fill="#fff" class="fade" style="animation-delay:.4s"/>
  <g>{"".join(sparks)}</g>
  <g class="mover"><g opacity="0"><set attributeName="opacity" to="1" begin="{START}s" fill="freeze"/>
    <animateMotion {anim} keyPoints="{key_points}"><mpath href="#route"/></animateMotion>
    <circle r="9" fill="url(#head-glow)"/><circle r="3.4" fill="#fff"/></g></g>
  <g class="rest" transform="translate({tx:.1f} {ty:.1f})">
    <circle r="7" fill="none" stroke="{PEACH}" stroke-width="1.4" class="pulse"/>
    <circle r="9" fill="url(#head-glow)"/><circle r="3.4" fill="#fff"/>
  </g>
  <line x1="40" y1="{H - 120}" x2="{W - 40}" y2="{H - 120}" stroke="{HAIR}" class="fade" style="animation-delay:{end:.2f}s"/>
  {stats(f)}
  <g class="fade" style="animation-delay:{end + .6:.2f}s">
    <text x="40" y="{H - 26}" class="caption">One line through the year, every day visited once.</text>
    <text x="{W - 40}" y="{H - 26}" text-anchor="end" class="caption">After One Line, CEDRA Interactive’s puzzle game</text>
  </g>"""
    label = (f"One Line: a single line visits every day of the last 12 months once, lighting the days with contributions. "
             f"{f['total']} contributions on {f['active']} active days; current streak {f['streak']} days, best {f['best']}; "
             f"busiest month {f['month']} with {f['month_n']}.")
    return card(H, body, label=label, defs=defs, css=css, faces=[("sans", 500), ("sans", 600), ("mono", 400)])


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    write("oneline.svg", svg(fetch()), out)
