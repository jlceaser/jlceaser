"""Builds the translation panel, after Makine Çeviri's trade: four English lines turn into Turkish one after another.
Every English word drops a ribbon to the Turkish word or suffix that carries its meaning. The ribbons cross because
Turkish puts the verb last and folds small words into suffixes; the Turkish arrives in that scrambled order, and an
interlinear gloss splits each word into its morphemes. The third line is live: this year's contributions.

Run: GH_TOKEN=<token> python assets/make_translate.py [out_dir]  -> writes translate.svg (default out_dir: next to this file).
"""
import html
import sys
from pathlib import Path

from common import _static, DIM, FG, FLAME, HAIR, HERE, MONO, NAME, PEACH, RULE, SUN, W, card, write
from contrib import facts, fetch

H = 360
P = 7.0  # seconds per segment
T = 4 * P
LEAD = .5  # the cycle opens with the last segment fading out; playback starts right after, so it opens on an empty stage
FADE = .5  # each segment's exit
IN, DRAW = "cubic-bezier(.16,1,.3,1)", "cubic-bezier(.65,0,.35,1)"

EN_SIZE, TR_SIZE, MONO_SIZE = 24, 40, 12
EN_Y, EN_MARK, TR_MARK, TR_Y = 108, 119, 201, 242  # baselines and the bracket lines the ribbons hang between
SEG_Y, GLOSS_Y, RULE_Y, NOTE_Y = 272, 290, 312, 338
MONO_ADV = .6 * MONO_SIZE  # JetBrains Mono is 600 units wide in every weight


class Face:
    """Advance widths with pair kerning, read from the same static instance the panel embeds."""

    def __init__(self, font, weight):
        f = _static(font, weight)
        self.cmap, self.hmtx, self.upem = f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm
        gpos = f["GPOS"].table
        kern = sorted({i for fr in gpos.FeatureList.FeatureRecord if fr.FeatureTag == "kern" for i in fr.Feature.LookupListIndex})
        self.lookups = []
        for i in kern:
            lk = gpos.LookupList.Lookup[i]
            subs = [s.ExtSubTable if lk.LookupType == 9 else s for s in lk.SubTable]
            self.lookups.append([(s, {g: n for n, g in enumerate(s.Coverage.glyphs)}) for s in subs])

    def _pair(self, a, b):
        total = 0
        for subs in self.lookups:
            for s, cov in subs:
                if a not in cov:
                    continue
                if s.Format == 1:
                    rec = next((r for r in s.PairSet[cov[a]].PairValueRecord if r.SecondGlyph == b), None)
                    if rec is None:
                        continue
                    total += getattr(rec.Value1, "XAdvance", 0) or 0
                else:
                    v = s.Class1Record[s.ClassDef1.classDefs.get(a, 0)].Class2Record[s.ClassDef2.classDefs.get(b, 0)].Value1
                    total += getattr(v, "XAdvance", 0) or 0
                break
        return total

    def pens(self, text, size):
        """Pen position before each character and after the last, in px."""
        glyphs = [self.cmap[ord(c)] for c in text]
        x, out = 0, [0.0]
        for i, g in enumerate(glyphs):
            x += self.hmtx[g][0] + (self._pair(g, glyphs[i + 1]) if i + 1 < len(glyphs) else 0)
            out.append(x * size / self.upem)
        return out

    def width(self, text, size):
        return self.pens(text, size)[-1]


EN_FACE, TR_FACE, CAPS_FACE = Face("sans", 500), Face("sans", 600), Face("sans", 500)


def segments(total):
    en_n, tr_n = f"{total:,}", f"{total:,}".replace(",", ".")  # Turkish groups thousands with a dot
    # tr words split into morphemes with "|"; links: (English word, Turkish word, first morpheme, last morpheme).
    return [
        dict(en=["Welcome", "to", "my", "world."], tr=["Dünya|m|a", "hoş", "gel|di|n."],
             gloss=["world·my·to", "pleasant", "come·PST·2SG"],
             links=[(0, 1, 0, 0), (0, 2, 0, 2), (1, 0, 2, 2), (2, 0, 1, 1), (3, 0, 0, 0)],
             note=[("Three English words fold into one: ", 0), ("dünyama", 1), (" is “to my world”.", 0)]),
        dict(en=["We", "translate", "games", "into", "Turkish."], tr=["Oyun|lar|ı", "Türkçe|ye", "çevir|iyor|uz."],
             gloss=["game·PL·ACC", "Turkish·DAT", "translate·PROG·1PL"],
             links=[(0, 2, 2, 2), (1, 2, 0, 0), (2, 0, 0, 1), (3, 1, 1, 1), (4, 1, 0, 0)],
             note=[("The verb comes last and carries its subject: ", 0), ("-uz", 1), (" is the “we”.", 0)]),
        dict(en=[en_n, "contributions", "in", "the", "last", "year."], tr=["Son", "bir", "yıl|da", tr_n, "katkı."],
             gloss=["last", "one", "year·LOC", tr_n, "contribution"],
             links=[(0, 3, 0, 0), (1, 4, 0, 0), (2, 2, 1, 1), (4, 0, 0, 0), (5, 2, 0, 0)],
             note=[("After a number the noun stays singular: ", 0), (f"{tr_n} katkı", 1), (", never ", 0), ("katkılar", 1), (".", 0)]),
        dict(en=["Goodbye,", "World!"], tr=["Elveda,", "Dünya!"], gloss=["farewell", "world"],
             links=[(0, 0, 0, 0), (1, 1, 0, 0)],
             note=[("Hoşça kal", 1), (" is goodbye for now. ", 0), ("Elveda", 1), (" is goodbye for good.", 0)]),
    ]


def split_punct(word):
    core = word.rstrip(".,!")
    return core, word[len(core):]


def tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


class Frames:
    """Keyframes on the shared cycle. Segment k plays from LEAD + k·P; it leaves in the last FADE of its slot, except
    the last one, which stays to the end of the cycle (the reduced-motion still) and leaves at the start of the next."""

    def __init__(self):
        self.rules, self.n = [], 0

    def add(self, stops):
        name = f"k{self.n}"
        self.n += 1
        body = []
        for t, props, ease in stops:
            body.append(f"{100 * t / T:.3f}% {{ {props};{f' animation-timing-function: {ease};' if ease else ''} }}")
        self.rules.append(f"@keyframes {name} {{ {' '.join(body)} }}")
        return name

    def show(self, k, t_in, dur, hidden, shown, gone=None, ease=IN):
        """Hidden until t_in (seconds into segment k), shown after dur, gone when the segment leaves."""
        gone = gone or hidden
        s = LEAD + k * P
        if k < 3:
            return self.add([(0, hidden, None), (s + t_in, hidden, ease), (s + t_in + dur, shown, None),
                             (s + P - FADE, shown, "ease-in"), (s + P, gone, None), (T, gone, None)])
        return self.add([(0, shown, "ease-in"), (FADE, gone, None), (FADE + .01, hidden, None), (s + t_in, hidden, ease),
                         (s + t_in + dur, shown, None), (T, shown, None)])


def esc(s):
    return html.escape(s, quote=False)


def segment(k, seg, fr):
    out = []
    a = lambda name: f'class="a" style="animation-name:{name}"'

    # English line, centred, one word per text so the ribbons can start under each word.
    space = EN_FACE.width(" ", EN_SIZE)
    widths = [EN_FACE.width(w, EN_SIZE) for w in seg["en"]]
    x = W / 2 - (sum(widths) + space * (len(widths) - 1)) / 2
    en = []
    linked = {l[0] for l in seg["links"]}
    for i, (w, wd) in enumerate(zip(seg["en"], widths)):
        core, _ = split_punct(w)
        cw = EN_FACE.width(core, EN_SIZE)
        en.append((x, cw))
        name = fr.show(k, .1 + .07 * i, .7, "opacity: 0; transform: translateY(8px)", "opacity: 1; transform: translateY(0px)",
                       "opacity: 0; transform: translateY(0px)")
        out.append(f'<text x="{x:.1f}" y="{EN_Y}" class="en a{"" if i in linked else " loose"}" '
                   f'style="animation-name:{name}">{esc(w)}</text>')
        x += wd + space

    # Turkish line: each word placed by hand, its morphemes as tspans (stem peach, suffixes sun).
    space = TR_FACE.width(" ", TR_SIZE)
    words = []
    for w in seg["tr"]:
        parts = w.split("|")
        core, punct = split_punct(parts[-1])
        parts[-1] = core
        text = "".join(parts) + punct
        pens = TR_FACE.pens(text, TR_SIZE)
        spans, c = [], 0
        for m in parts:
            spans.append((pens[c], pens[c + len(m)]))
            c += len(m)
        words.append(dict(parts=parts, punct=punct, width=pens[-1], spans=spans))
    x = W / 2 - (sum(w["width"] for w in words) + space * (len(words) - 1)) / 2
    for w in words:
        w["x"] = x
        x += w["width"] + space

    # Ribbons in English order, so the Turkish assembles out of order: that is the reordering, made visible.
    arrive = {}
    for j, (ei, wi, m0, m1) in enumerate(sorted(seg["links"])):
        ex, ew = en[ei]
        w = words[wi]
        tx0, tx1 = w["x"] + w["spans"][m0][0], w["x"] + w["spans"][m1][1]
        x0, x1 = ex + ew / 2, (tx0 + tx1) / 2
        dy = TR_MARK - EN_MARK
        d = f"M{x0:.1f} {EN_MARK}C{x0:.1f} {EN_MARK + .62 * dy:.1f} {x1:.1f} {TR_MARK - .62 * dy:.1f} {x1:.1f} {TR_MARK}"
        start = .95 + .13 * j
        for m in range(m0, m1 + 1):
            arrive[(wi, m)] = min(arrive.get((wi, m), 99), start + 1.1)
        draw = fr.show(k, start, 1.1, "stroke-dashoffset: 1.1", "stroke-dashoffset: 0", "stroke-dashoffset: -1.1", DRAW)
        out.append(f'<path d="{d}" pathLength="1" class="halo a" style="animation-name:{draw}"/>'
                   f'<path d="{d}" pathLength="1" class="ribbon a" style="animation-name:{draw}"/>')
        # brackets: under the English word, over the Turkish span the ribbon lands on
        mark = lambda t: fr.show(k, t, .5, "opacity: 0; transform: scaleX(.2)", "opacity: 1; transform: scaleX(1)",
                                 "opacity: 0; transform: scaleX(1)")
        out.append(f'<line x1="{ex + 1:.1f}" y1="{EN_MARK}" x2="{ex + ew - 1:.1f}" y2="{EN_MARK}" class="mark-en a" '
                   f'style="animation-name:{mark(start - .05)}"/>')
        out.append(f'<line x1="{tx0 + 4:.1f}" y1="{TR_MARK}" x2="{tx1 - 4:.1f}" y2="{TR_MARK}" class="mark-tr a" '
                   f'style="animation-name:{mark(start + .95)}"/>')

    # Each Turkish word stays one text run, so the browser sets it whole; its morphemes ink in as their ribbons land,
    # and the word settles down from the ribbons with the first of them.
    settled = max(arrive.values())
    for wi, w in enumerate(words):
        times = [arrive.get((wi, m), settled) - .3 for m in range(len(w["parts"]))]
        tspans = []
        for m, part in enumerate(w["parts"]):
            ink = fr.show(k, times[m], .6, "fill-opacity: 0", "fill-opacity: 1")
            tspans.append(f'<tspan class="{"stem" if m == 0 else "sfx"} a" style="animation-name:{ink}">{esc(part)}</tspan>')
        if w["punct"]:
            ink = fr.show(k, settled - .3, .6, "fill-opacity: 0", "fill-opacity: 1")
            tspans.append(f'<tspan class="punct a" style="animation-name:{ink}">{esc(w["punct"])}</tspan>')
        drop = fr.show(k, min(times), .8, "transform: translateY(-9px)", "transform: translateY(0px)", "transform: translateY(0px)")
        out.append(f'<text x="{w["x"]:.1f}" y="{TR_Y}" class="tr a" style="animation-name:{drop}">{"".join(tspans)}</text>')

    # Interlinear gloss: morphemes, then what each one means; grammar in small capitals.
    for wi, (w, gloss) in enumerate(zip(words, seg["gloss"])):
        name = fr.show(k, settled + .15 + .06 * wi, .7, "opacity: 0; transform: translateY(5px)",
                       "opacity: 1; transform: translateY(0px)", "opacity: 0; transform: translateY(0px)")
        seg_runs = "<tspan class='dot'>·</tspan>".join(
            f'<tspan class="{"g-stem" if m == 0 else "g-sfx"}">{esc(tr_lower(p))}</tspan>' for m, p in enumerate(w["parts"]))
        gl_runs = "<tspan class='dot'>·</tspan>".join(
            f'<tspan class="{"label" if g.isupper() or g[:1].isdigit() and g[-1].isalpha() else "lex"}">{esc(g)}</tspan>'
            for g in gloss.split("·"))
        out.append(f'<g {a(name)}><text x="{w["x"] + 1:.1f}" y="{SEG_Y}" class="mono gl">{seg_runs}</text>'
                   f'<text x="{w["x"] + 1:.1f}" y="{GLOSS_Y}" class="mono gl">{gl_runs}</text></g>')

    note_x = 40 + CAPS_FACE.width("NOTE", 11.5) + 4 * .18 * 11.5 + 14
    name = fr.show(k, settled + .45, .8, "opacity: 0; transform: translateX(-6px)", "opacity: 1; transform: translateX(0px)",
                   "opacity: 0; transform: translateX(0px)")
    runs = "".join(f'<tspan class="{"tr-word" if tr else ""}">{esc(t)}</tspan>' for t, tr in seg["note"])
    out.append(f'<text x="{note_x:.1f}" y="{NOTE_Y}" class="note a" style="animation-name:{name}">{runs}</text>')
    return "\n  ".join(out)


def chrome(fr):
    """Top row (eyebrow, segment bars, counter) and the bottom rule with its label."""
    out = ['<text x="40" y="52" class="eyebrow">01 — MAKİNE ÇEVİRİ</text>',
           f'<text x="{W - 40}" y="52" class="mono count dim" text-anchor="end">/ 04</text>']
    num_x = W - 40 - MONO_ADV * 5
    bar_w, gap = 22, 5
    bars_x = W - 40 - MONO_ADV * 7 - 16 - (4 * bar_w + 3 * gap)
    for k in range(4):
        s = LEAD + k * P
        name = fr.show(k, 0, .35, "opacity: 0", "opacity: 1") if k < 3 else fr.add(
            [(0, "opacity: 1", "ease-in"), (.3, "opacity: 0", None), (s, "opacity: 0", "ease-out"), (s + .35, "opacity: 1", None),
             (T, "opacity: 1", None)])
        out.append(f'<text x="{num_x:.1f}" y="52" class="mono count a" text-anchor="end" style="animation-name:{name}">0{k + 1}</text>')
        bx = bars_x + k * (bar_w + gap)
        fill = fr.add([(0, "transform: scaleX(1)", "ease-in-out"), (FADE, "transform: scaleX(0)", None), (s, "transform: scaleX(0)", None),
                       (s + P - FADE if k < 3 else T, "transform: scaleX(1)", None), (T, "transform: scaleX(1)", None)])
        out.append(f'<rect x="{bx:.1f}" y="47" width="{bar_w}" height="2" rx="1" fill="{RULE}"/>'
                   f'<rect x="{bx:.1f}" y="47" width="{bar_w}" height="2" rx="1" class="bar a" style="animation-name:{fill}"/>')
    out.append(f'<line x1="40" y1="{RULE_Y}" x2="{W - 40}" y2="{RULE_Y}" stroke="{HAIR}"/>')
    out.append(f'<text x="40" y="{NOTE_Y}" class="caps dim">Note</text>')
    out.append(f'<text x="{W - 40}" y="{NOTE_Y}" class="mono count dim" text-anchor="end">EN → TR</text>')
    return "\n  ".join(out)


def svg(total):
    fr = Frames()
    segs = segments(total)
    body = "  " + chrome(fr) + "\n  " + "\n  ".join(segment(k, s, fr) for k, s in enumerate(segs))
    defs = f"""<linearGradient id="ink" gradientUnits="userSpaceOnUse" x1="0" y1="{EN_MARK}" x2="0" y2="{TR_MARK}">
    <stop offset="0" stop-color="{FLAME}"/><stop offset=".55" stop-color="{SUN}"/><stop offset="1" stop-color="{PEACH}"/></linearGradient>
  <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{SUN}"/><stop offset="1" stop-color="{PEACH}"/></linearGradient>"""
    css = f"""  .a {{ animation-duration: {T:g}s; animation-delay: -{LEAD:g}s; animation-iteration-count: infinite;
    animation-fill-mode: both; animation-timing-function: linear; }}
  .eyebrow {{ font-size: 11.5px; font-weight: 500; letter-spacing: .2em; fill: {FG}; fill-opacity: .82; }}
  .count {{ font-size: {MONO_SIZE}px; fill: {FG}; }}
  .bar {{ fill: url(#bar); transform-box: fill-box; transform-origin: left; }}
  .en {{ font-size: {EN_SIZE}px; font-weight: 500; fill: {FG}; fill-opacity: .7; }}
  .en.loose {{ fill-opacity: .36; }}
  .tr {{ font-size: {TR_SIZE}px; font-weight: 600; }}
  .stem {{ fill: {NAME}; }} .sfx {{ fill: {SUN}; }} .punct {{ fill: {NAME}; }}
  .ribbon {{ fill: none; stroke: url(#ink); stroke-width: 1.5; stroke-linecap: round; stroke-dasharray: 1 1.2; }}
  .halo {{ fill: none; stroke: url(#ink); stroke-width: 6; stroke-linecap: round; stroke-dasharray: 1 1.2; stroke-opacity: .1; }}
  .mark-en, .mark-tr {{ stroke-width: 1.5; stroke-linecap: round; transform-box: fill-box; transform-origin: center; }}
  .mark-en {{ stroke: {FG}; stroke-opacity: .24; }} .mark-tr {{ stroke: {PEACH}; stroke-opacity: .55; }}
  .gl {{ font-size: {MONO_SIZE}px; }}
  .g-stem {{ fill: {NAME}; fill-opacity: .85; }} .g-sfx {{ fill: {SUN}; }} .dot {{ fill: {FG}; fill-opacity: .3; }}
  .lex {{ fill: {FG}; fill-opacity: .6; }} .label {{ fill: {FG}; fill-opacity: .6; font-size: 10.5px; letter-spacing: .06em; }}
  .note {{ font-size: 13px; font-weight: 500; font-style: italic; fill: {FG}; fill-opacity: .7; }}
  .tr-word {{ fill: {NAME}; fill-opacity: 1; }}
  {chr(10).join("  " + r for r in fr.rules)}"""
    tr_n = f"{total:,}".replace(",", ".")
    label = ("Makine Çeviri, English to Turkish, one line at a time, with each English word linked to the Turkish word or "
             "suffix that carries it. 'Welcome to my world.' becomes 'Dünyama hoş geldin.' (dünya-m-a: world, my, to). "
             "'We translate games into Turkish.' becomes 'Oyunları Türkçeye çeviriyoruz.', the verb last with 'we' as its "
             f"suffix. '{total:,} contributions in the last year.' becomes 'Son bir yılda {tr_n} katkı.', singular after a "
             "number. 'Goodbye, World!' becomes 'Elveda, Dünya!'")
    return card(H, body, label=label, defs=defs, css=css,
                faces=[("sans", 500), ("sans", 600), ("sans-italic", 500), ("mono", 400)])


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    write("translate.svg", svg(facts(fetch())["total"]), out)
