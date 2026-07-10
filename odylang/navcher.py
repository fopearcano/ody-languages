"""Navcher — the fleet script of Sūchel, rendered to SVG (docs/03).

From *nav* "ship" + *cher* "to carve, write".  Old Pelagic wrote the
flowing tide-script, boustrophedon; the fleets linearized it left-to-right
for terminals and stencils, demoting the old vowel diacritics to small
inline letters.  The working system (docs/03, SCRIPT CODEX REV 1.0):

* 17 consonant letters (16 living consonants plus *he*, the threshold
  letter — "a stem with a gap in it"), 5 small half-height vowels with the
  held-breath bar for length, 5 mood sigils, 3 anchor marks, the
  gap-stroke, and the question mark: 32 glyphs in all.
* Design rule 02 (stencil-safe): every stroke is straight; **the only
  curve in the entire system is the =zu anchor** — the open hook, "the one
  sign that refuses to close".  The seam-mood T• is the only filled glyph.
* Design rule 03 (two hands): the **careful hand** spells every suffix
  phonetically (liturgy, law, log-of-record); the **bridge hand**
  compresses mood and anchor into sigils (instrument panels, hull marks,
  haste).  Same letters, two registers.

:data:`GLYPHS` ports the doc's ``const G`` table byte-for-byte (polyline
stroke coordinates, the one arc path, the one fill, per-glyph widths), and
:data:`SAMPLES` its five sample token sequences exactly.  The renderer
reimplements ``drawGlyph``/``renderWord``/``sample`` — geometry box 100
units wide for consonants / 60 for vowels and operators (the gap-stroke is
70, "wide-set"), 140 units tall with baseline 120, stroke width 7
pre-scale, square linecaps, miter joins, line height ``150*scale + 18`` —
without a DOM and without external dependencies.

Spelling choices this module makes, each anchored to the sources:

* **Diphthongs are two small letters**: docs/03 sv-line40 letters *enmai*
  as e‑n‑m‑a‑i, so ``ai``/``au`` decompose to their vowel pair.
* **x → k,s**: the letter table has no *x*; docs/01 §02 defines ``x`` as
  /ks/ (*nexath* [ˈne.ksath]), so it is lettered as its cluster.
* **th → t,h** (UNATTESTED — a documented choice): no docs/03 sample ever
  letters a ``th`` word and the table has no *th* glyph, so the digraph is
  lettered as its two nearest letters, t + the threshold letter, parallel
  to the x → k,s decomposition.  Locked here so the choice is data.
* **The hyphenated cases are lettered spaced**: sv-hail letters *ish-ol*
  as i‑sh ␣ o‑l — "the codex letters the dative spaced" ("Word-space is a
  full consonant-width of silence").  Generalized to the three cases that
  attach with '-' in docs/01 §04 (-ol DAT, -eth LOC, -en GEN); the solid
  accusative -(e)n and every verb-internal seam letter solid, as attested
  by sv-compare (*ver-a=ka* careful = v‑e‑r‑a‑k‑a).
* **@F is carvable but never produced by :func:`tokens_bridge`**: mood F
  is periphrastic *vo* + plain T (docs/01 §05), so no core Word carries an
  F MOOD morph; the crossed-square sigil (chart caption "F · vo") remains
  available as an explicit ``'@F'`` token, exactly as the doc's
  ``renderWord`` supports it.
* The vowels section of docs/03 carries no family caption (the group
  headers exist only for consonants and operators), so the chart's vowel
  caption is assembled from that section's own heading ("THE VOWELS" /
  "Small letters and the held-breath bar").
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union
from xml.sax.saxutils import escape

from .phonology import tokenize
from .word import ANCHOR, CASE, MOOD, Word

# ---------------------------------------------------------------------------
# the glyph table — docs/03 'const G', ported verbatim
#
#   Box: width units — consonants 100, vowels/ops 60. Height 140, baseline 120.
#   Each glyph: {w, strokes:[[x,y,...]], paths:[d], fills:[d]}


@dataclass(frozen=True)
class Glyph:
    """One letterform: polyline strokes, arc paths, filled paths (docs/03)."""
    w: int
    strokes: Tuple[Tuple[int, ...], ...] = ()
    paths: Tuple[str, ...] = ()
    fills: Tuple[str, ...] = ()


GLYPHS: Dict[str, Glyph] = {
    # stops: head box (left/center/right), stem, voiced foot
    "p": Glyph(100, strokes=((70, 10, 70, 120), (70, 10, 30, 10, 30, 45, 70, 45))),
    "b": Glyph(100, strokes=((70, 10, 70, 120), (70, 10, 30, 10, 30, 45, 70, 45),
                             (70, 120, 45, 120))),
    "t": Glyph(100, strokes=((10, 10, 90, 10), (50, 10, 50, 120),
                             (35, 10, 35, 40, 65, 40, 65, 10))),
    "d": Glyph(100, strokes=((10, 10, 90, 10), (50, 10, 50, 120),
                             (35, 10, 35, 40, 65, 40, 65, 10), (50, 120, 75, 120))),
    "k": Glyph(100, strokes=((30, 10, 30, 120), (30, 10, 70, 10, 70, 45, 30, 45))),
    "g": Glyph(100, strokes=((30, 10, 30, 120), (30, 10, 70, 10, 70, 45, 30, 45),
                             (30, 120, 55, 120))),
    # affricates: T-frame + slash; j adds foot
    "ch": Glyph(100, strokes=((10, 10, 90, 10), (50, 10, 50, 120), (30, 22, 70, 60))),
    "j": Glyph(100, strokes=((10, 10, 90, 10), (50, 10, 50, 120), (30, 22, 70, 60),
                             (50, 120, 75, 120))),
    # fricatives
    "s": Glyph(100, strokes=((70, 10, 30, 45, 70, 80, 30, 115),)),
    "z": Glyph(100, strokes=((30, 10, 70, 45, 30, 80, 70, 115), (45, 120, 70, 120))),
    "sh": Glyph(100, strokes=((20, 10, 80, 10), (70, 22, 30, 55, 70, 88, 30, 120))),
    "v": Glyph(100, strokes=((70, 10, 30, 120), (30, 120, 55, 120))),
    # nasals
    "m": Glyph(100, strokes=((30, 10, 30, 120), (70, 10, 70, 120), (30, 10, 70, 10))),
    "n": Glyph(100, strokes=((30, 10, 30, 120), (30, 10, 70, 10), (70, 10, 70, 55))),
    # liquids
    "r": Glyph(100, strokes=((30, 10, 30, 120), (30, 60, 68, 44))),
    "l": Glyph(100, strokes=((30, 10, 30, 120), (30, 120, 78, 120))),
    # threshold letter
    "h": Glyph(100, strokes=((30, 10, 30, 52), (30, 74, 30, 120))),
    # vowels (small)
    "a": Glyph(60, strokes=((10, 120, 30, 76, 50, 120),)),
    "e": Glyph(60, strokes=((10, 96, 50, 96),)),
    "i": Glyph(60, strokes=((30, 78, 30, 120),)),
    "o": Glyph(60, strokes=((30, 76, 52, 98, 30, 120, 8, 98, 30, 76),)),
    "u": Glyph(60, strokes=((10, 76, 30, 120, 50, 76),)),
    # mood sigils
    "mT": Glyph(60, strokes=((12, 80, 48, 80, 48, 118, 12, 118, 12, 80),)),
    "mTm": Glyph(60, strokes=((12, 80, 48, 80, 48, 118, 12, 118, 12, 80),
                              (12, 99, 0, 99))),
    "mTp": Glyph(60, strokes=((12, 80, 48, 80, 48, 118, 12, 118, 12, 80),
                              (48, 99, 60, 99))),
    "mTs": Glyph(60, fills=("M14,82 L46,82 L46,116 L14,116 Z",)),
    "mF": Glyph(60, strokes=((12, 80, 48, 80, 48, 118, 12, 118, 12, 80),
                             (12, 80, 48, 118), (48, 80, 12, 118))),
    # anchors
    "aka": Glyph(60, strokes=((4, 112, 18, 84, 32, 112, 46, 84),)),
    "ami": Glyph(60, strokes=((46, 84, 14, 116),)),
    "azu": Glyph(60, paths=("M46,84 A22,22 0 1 0 46,114",)),
    # gap + question
    "gap": Glyph(70, strokes=((35, 4, 35, 136),)),
    "q": Glyph(60, strokes=((10, 116, 24, 92), (32, 116, 46, 92))),
}

#: the held-breath bar, drawn over a vowel (docs/03 'const LONGBAR').
LONGBAR: Tuple[int, int, int, int] = (8, 62, 52, 62)

#: the seventeen consonant letters, in the doc's chart order.
CONSONANTS: Tuple[str, ...] = ("p", "b", "t", "d", "k", "g", "ch", "j",
                               "s", "z", "sh", "v", "m", "n", "r", "l", "h")

#: the five small vowel letters.
VOWEL_LETTERS: Tuple[str, ...] = ("a", "e", "i", "o", "u")


# ---------------------------------------------------------------------------
# the token model — docs/03 renderWord:
#   token: "s","u:","ch","@Ts","=zu","|","?"," "

#: mood-sigil token -> glyph key (docs/03 renderWord's inline map).
MOOD_TOKEN_GLYPH: Dict[str, str] = {"@T": "mT", "@T-": "mTm", "@T+": "mTp",
                                    "@Ts": "mTs", "@F": "mF"}

#: anchor token -> glyph key (docs/03 renderWord's inline map).
ANCHOR_TOKEN_GLYPH: Dict[str, str] = {"=ka": "aka", "=mi": "ami", "=zu": "azu"}

#: veridical mood suffix (docs/01 §05) -> bridge-hand sigil token.
MOOD_SIGILS: Dict[str, str] = {"a": "@T", "im": "@T-", "ur": "@T+",
                               "eshe": "@Ts"}

#: temporal anchor clitic -> bridge-hand anchor token.
ANCHOR_SIGILS: Dict[str, str] = {"ka": "=ka", "mi": "=mi", "zu": "=zu"}

# letter-less segments and their letterings (see module docstring)
_DECOMPOSE: Dict[str, Tuple[str, str]] = {
    "ai": ("a", "i"),   # attested: enmai = e-n-m-a-i (docs/03 sv-line40)
    "au": ("a", "u"),
    "x": ("k", "s"),    # docs/01 §02: x = /ks/
    "th": ("t", "h"),   # unattested in docs/03 — documented choice
}
_LONG_TOKEN: Dict[str, str] = {"ā": "a:", "ē": "e:", "ī": "i:",
                               "ō": "o:", "ū": "u:"}
_LETTERS = frozenset(CONSONANTS) | frozenset(VOWEL_LETTERS)

#: case suffixes that attach with '-' (docs/01 §04) — lettered with a
#: word-space in Navcher ("the codex letters the dative spaced", sv-hail).
_HYPHEN_SPACED_CASES = frozenset({"ol", "eth", "en"})


def _spell(text: str) -> List[str]:
    """Letter one solid chunk of romanized Sūchel phonetically."""
    out: List[str] = []
    for seg in tokenize(text):
        if seg in ("-", "="):
            continue
        if seg in _LONG_TOKEN:
            out.append(_LONG_TOKEN[seg])
        elif seg in _DECOMPOSE:
            out.extend(_DECOMPOSE[seg])
        elif seg in _LETTERS:
            out.append(seg)
        else:
            raise ValueError(f"no Navcher letter for segment {seg!r} — the "
                             f"fleet script letters the Sūchel inventory "
                             f"(docs/03)")
    return out


def _word_tokens(word: Word, bridge: bool) -> List[str]:
    out: List[str] = []
    for m in word.morphs:
        form = m.form.lstrip("=")   # bare_anchor Words carry '=' in the form
        if bridge and m.cat == MOOD:
            try:
                out.append(MOOD_SIGILS[form])
            except KeyError:
                raise ValueError(f"no mood sigil for suffix {form!r}; the "
                                 f"five sigils cover -a -im -ur -eshe and "
                                 f"the periphrastic F (docs/03 §03)")
            continue
        if bridge and m.cat == ANCHOR:
            try:
                out.append(ANCHOR_SIGILS[form])
            except KeyError:
                raise ValueError(f"no anchor mark for clitic {form!r} "
                                 f"(docs/03 §03: =ka =mi =zu)")
            continue
        if m.cat == CASE and m.sep == "-" and out:
            out.append(" ")         # the spaced case boundary (sv-hail)
        out.extend(_spell(form))
    return out


def tokens_careful(text_or_word: Union[str, Word]) -> List[str]:
    """Careful-hand tokens: everything spelled phonetically (docs/03 rule 03).

    Words are lettered solid with a ``' '`` between words; the one seam
    that surfaces as a space is the hyphenated case suffix (sv-hail:
    *ish-ol* = i‑sh ␣ o‑l).  Accepts a romanized string (morpheme
    separators ``-``/``=`` allowed) or a core :class:`~odylang.word.Word`,
    whose CASE morphs carry the spacing decision as data.

    >>> tokens_careful('Sūchel')
    ['s', 'u:', 'ch', 'e', 'l']
    """
    if isinstance(text_or_word, Word):
        return _word_tokens(text_or_word, bridge=False)
    out: List[str] = []
    for wi, w in enumerate(text_or_word.split()):
        if wi:
            out.append(" ")
        pieces = re.split(r"([-=])", w)
        for pi in range(0, len(pieces), 2):
            chunk = pieces[pi]
            if not chunk:
                continue
            sep = pieces[pi - 1] if pi else ""
            if (sep == "-" and pi == len(pieces) - 1
                    and chunk.lower() in _HYPHEN_SPACED_CASES and out):
                out.append(" ")
            out.extend(_spell(chunk))
    return out


def tokens_bridge(word: Word) -> List[str]:
    """Bridge-hand tokens for a core Word (docs/03 rule 03, sv-compare).

    The stem (and a perfective *-t-*) is spelled; the MOOD morph becomes
    its sigil token and the ANCHOR morph its anchor mark: *ver-a=ka* →
    ``['v','e','r','@T','=ka']`` — "stem + T-sigil + beacon-pulse".
    """
    return _word_tokens(word, bridge=True)


# ---------------------------------------------------------------------------
# rendering — docs/03 drawGlyph / renderWord / sample, DOM-free

#: doc palette — gold letters, red for the special signs, blue for the
#: bridge hand, the label grey (docs/03 sample code), and the doc's own
#: :root dark ground (--bg: #08070a).
GOLD = "#f5d76e"
RED = "#e8362a"
BLUE = "#6fa8ff"
INK = "#8c8a82"
BACKGROUND = "#08070a"

_STROKE_WIDTH = 7        # pre-scale (docs/03 drawGlyph: const sw=7)
_WORD_SPACE = 100        # ' ' advances a full consonant width
_LINE_MODEL = 140        # glyph box height; baseline 120 (docs/03)


def _fmt(v: float) -> str:
    return f"{v:g}"


def glyph_svg(key: str, x: float, scale: float, color: str,
              long_mark: bool = False) -> Tuple[str, float]:
    """One glyph as an SVG ``<g>`` fragment; returns (fragment, new x).

    Mirrors docs/03 ``drawGlyph``: translate/scale group, stroke width 7
    inside the scaled group, square linecaps, miter joins on polylines,
    the held-breath bar over a long vowel.
    """
    g = GLYPHS[key]
    parts = [f'<g transform="translate({_fmt(x)},0) scale({_fmt(scale)})">']
    for pts in g.strokes:
        coords = " ".join(f"{pts[i]},{pts[i + 1]}"
                          for i in range(0, len(pts), 2))
        parts.append(f'<polyline points="{coords}" fill="none" '
                     f'stroke="{color}" stroke-width="{_STROKE_WIDTH}" '
                     f'stroke-linecap="square" stroke-linejoin="miter"/>')
    for d in g.paths:
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" '
                     f'stroke-width="{_STROKE_WIDTH}" '
                     f'stroke-linecap="square"/>')
    for d in g.fills:
        parts.append(f'<path d="{d}" fill="{color}"/>')
    if long_mark:
        parts.append(f'<polyline points="{LONGBAR[0]},{LONGBAR[1]} '
                     f'{LONGBAR[2]},{LONGBAR[3]}" fill="none" '
                     f'stroke="{color}" stroke-width="{_STROKE_WIDTH}" '
                     f'stroke-linecap="square"/>')
    parts.append("</g>")
    return "".join(parts), x + g.w * scale


def word_svg(tokens: Sequence[str], x0: float, scale: float,
             color: str) -> Tuple[str, float]:
    """A token stream as SVG fragments; returns (fragment, end x).

    Mirrors docs/03 ``renderWord``: ``' '`` word space (a full
    consonant-width of silence), ``'|'`` gap-stroke, ``'?'`` question,
    ``@``-sigils, ``=``-anchors, letters with ``':'`` for the long bar.
    """
    parts: List[str] = []
    x = x0
    for t in tokens:
        if t == " ":
            x += _WORD_SPACE * scale
            continue
        long_mark = False
        if t == "|":
            key = "gap"
        elif t == "?":
            key = "q"
        elif t.startswith("@"):
            key = MOOD_TOKEN_GLYPH[t]
        elif t.startswith("="):
            key = ANCHOR_TOKEN_GLYPH[t]
        else:
            long_mark = t.endswith(":")
            key = t[:-1] if long_mark else t
        frag, x = glyph_svg(key, x, scale, color, long_mark)
        parts.append(frag)
    return "".join(parts), x


@dataclass
class Line:
    """One rendered line: tokens, an optional right-hand label, a color."""
    tokens: List[str]
    label: str = ""
    color: Optional[str] = None


def render_svg(lines: Sequence[Union[Line, Sequence[str]]], scale: float = 0.5,
               color: str = GOLD,
               background: Optional[str] = BACKGROUND) -> str:
    """Render token lines to a standalone SVG string (docs/03 ``sample``).

    Same layout model as the doc: line height ``150*scale + 18`` over the
    140-unit glyph box, words started at x = 6, labels in Share Tech Mono
    12px at ``y = 100*scale``, canvas width from the widest line.  The
    dark panel ground is a plain rect (pass ``background=None`` for a
    transparent SVG).
    """
    lns = [ln if isinstance(ln, Line) else Line(list(ln)) for ln in lines]
    line_h = 150 * scale + 18
    max_w = 0.0
    body: List[str] = []
    for i, ln in enumerate(lns):
        frag, w = word_svg(ln.tokens, 6, scale, ln.color or color)
        if ln.label:
            frag += (f'<text x="{_fmt(w + 16)}" y="{_fmt(100 * scale)}" '
                     f'fill="{INK}" font-family="Share Tech Mono, monospace" '
                     f'font-size="12">{escape(ln.label)}</text>')
            max_w = max(max_w, w + 16 + len(ln.label) * 7.5)
        max_w = max(max_w, w + 10)
        body.append(f'<g transform="translate(0,{_fmt(i * line_h)})">'
                    f'{frag}</g>')
    width = math.ceil(max_w)
    height = math.ceil(len(lns) * line_h)
    bg = (f'<rect x="0" y="0" width="{width}" height="{height}" '
          f'fill="{background}"/>' if background else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}">{bg}{"".join(body)}</svg>')


# ---------------------------------------------------------------------------
# the glyph chart — docs/03 card() calls, with the doc's own captions


@dataclass(frozen=True)
class ChartEntry:
    """One chart card: glyph key, display name, the doc's caption."""
    key: str
    name: str
    sub: str
    special: bool = False    # the red cards (he, T•, =zu, the gap)
    long_mark: bool = False  # the ā demo card


def _C(*args, **kw) -> ChartEntry:
    return ChartEntry(*args, **kw)


#: the chart, grouped and captioned as docs/03 groups it.  The vowel
#: caption is assembled from that section's heading (no fam header there).
CHART: Tuple[Tuple[str, Tuple[ChartEntry, ...]], ...] = (
    ("STOPS — closed head · voiced adds the foot", (
        _C("p", "p", "labial · head-left"),
        _C("b", "b", "p + voice-foot"),
        _C("t", "t", "alveolar · head-center"),
        _C("d", "d", "t + voice-foot"),
        _C("k", "k", "velar · head-right"),
        _C("g", "g", "k + voice-foot"),
    )),
    ("AFFRICATES & FRICATIVES — the slash family", (
        _C("ch", "ch", "T-frame + slash"),
        _C("j", "j", "ch + voice-foot"),
        _C("s", "s", "the zigzag"),
        _C("z", "z", "s reversed + foot"),
        _C("sh", "sh", "zigzag + top bar"),
        _C("v", "v", "slash + foot"),
    )),
    ("NASALS · LIQUIDS · THE THRESHOLD LETTER", (
        _C("m", "m", "double stem"),
        _C("n", "n", "half-frame"),
        _C("r", "r", "stem + mid-tick"),
        _C("l", "l", "stem + long foot"),
        _C("h", "he", "the threshold letter — a stem with a gap", special=True),
    )),
    ("THE VOWELS — small letters and the held-breath bar", (
        _C("a", "a", "the wedge"),
        _C("e", "e", "the level"),
        _C("i", "i", "the tick"),
        _C("o", "o", "the diamond"),
        _C("u", "u", "the cup"),
        _C("a", "ā", "+ held-breath bar", long_mark=True),
    )),
    ("THE FIVE MOOD SIGILS", (
        _C("mT", "T · -a", "plain square · settled"),
        _C("mTm", "T⁻ · -im", "tick left · IR approach"),
        _C("mTp", "T⁺ · -ur", "tick right · UV approach"),
        _C("mTs", "T• · -eshe", "the seam-mark · filled", special=True),
        _C("mF", "F · vo", "crossed out"),
    )),
    ("THE THREE ANCHOR MARKS · THE GAP · THE QUESTION", (
        _C("aka", "=ka", "the beacon pulse"),
        _C("ami", "=mi", "the chest-stroke"),
        _C("azu", "=zu", "the open hook — the only curve", special=True),
        _C("gap", "ne", "the gap-stroke", special=True),
        _C("q", "vu", "the rising pair · question"),
    )),
)


def _wrap(text: str, limit: int = 26) -> List[str]:
    lines: List[str] = []
    cur = ""
    for w in text.split(" "):
        cand = (cur + " " + w).strip()
        if len(cand) > limit and cur:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def render_glyph_chart(background: Optional[str] = BACKGROUND) -> str:
    """The full alphabet/sigil chart as one standalone SVG.

    Groups and captions follow docs/03 exactly (cards at the doc's 0.5
    card scale, special glyphs in the doc's red, the rest in gold).
    """
    cols, cell_w, cell_h, margin = 6, 168, 128, 26
    width = margin * 2 + cols * cell_w
    scale = 0.5
    mono = "Share Tech Mono, monospace"
    sans = "Chakra Petch, Bahnschrift, Segoe UI, sans-serif"
    body: List[str] = []
    y = 44.0
    body.append(f'<text x="{margin}" y="{_fmt(y)}" fill="{GOLD}" '
                f'font-family="{sans}" font-size="21" font-weight="700" '
                f'letter-spacing="3">NAVCHER · THE FLEET SCRIPT OF SŪCHEL'
                f'</text>')
    y += 18
    strapline = escape("ship-carve — angular, featural, and with exactly "
                       "one curve in the whole system")
    body.append(f'<text x="{margin}" y="{_fmt(y)}" fill="{INK}" '
                f'font-family="{mono}" font-size="11" letter-spacing="2">'
                f'{strapline}</text>')
    y += 14
    for caption, entries in CHART:
        y += 30
        body.append(f'<text x="{margin}" y="{_fmt(y)}" fill="{RED}" '
                    f'font-family="{mono}" font-size="11" letter-spacing="2">'
                    f'{escape(caption.upper())}</text>')
        body.append(f'<line x1="{margin}" y1="{_fmt(y + 8)}" '
                    f'x2="{width - margin}" y2="{_fmt(y + 8)}" '
                    f'stroke="{RED}" stroke-opacity="0.25"/>')
        y += 18
        rows = math.ceil(len(entries) / cols)
        for i, e in enumerate(entries):
            col, row = i % cols, i // cols
            cx = margin + col * cell_w
            cy = y + row * cell_h
            color = RED if e.special else GOLD
            gw = GLYPHS[e.key].w * scale
            frag, _ = glyph_svg(e.key, cx + (cell_w - gw) / 2, scale, color,
                                e.long_mark)
            body.append(f'<g transform="translate(0,{_fmt(cy)})">{frag}</g>')
            mid = cx + cell_w / 2
            body.append(f'<text x="{_fmt(mid)}" y="{_fmt(cy + 88)}" '
                        f'fill="{color}" font-family="{sans}" font-size="15" '
                        f'font-weight="600" text-anchor="middle">'
                        f'{escape(e.name)}</text>')
            for k, sub_line in enumerate(_wrap(e.sub)):
                body.append(f'<text x="{_fmt(mid)}" y="{_fmt(cy + 103 + k * 11)}" '
                            f'fill="{INK}" font-family="{mono}" font-size="9" '
                            f'text-anchor="middle">{escape(sub_line)}</text>')
        y += rows * cell_h
    y += 26
    body.append(f'<text x="{_fmt(width / 2)}" y="{_fmt(y)}" fill="#5a5852" '
                f'font-family="{mono}" font-size="10" letter-spacing="2" '
                f'text-anchor="middle">17 CONSONANTS · 5 VOWELS · 5 MOOD '
                f'SIGILS · 3 ANCHORS · 1 GAP // REV 1.0</text>')
    height = math.ceil(y + 26)
    bg = (f'<rect x="0" y="0" width="{width}" height="{height}" '
          f'fill="{background}"/>' if background else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}">{bg}{"".join(body)}</svg>')


# ---------------------------------------------------------------------------
# the doc's sample renders — token sequences extracted exactly


@dataclass(frozen=True)
class Sample:
    """One docs/03 sample block: its token lines, scale, and captions."""
    key: str
    title: str
    latin: str
    lines: Tuple[Line, ...]
    scale: float


SAMPLES: Dict[str, Sample] = {s.key: s for s in (
    Sample("sv-names", "CANON NAMES", "Sūchel · Sōrn · jel · zukad", (
        Line(["s", "u:", "ch", "e", "l", " ", " "], label="Sūchel"),
        Line(["s", "o:", "r", "n", " ", " "], label="Sōrn"),
        Line(["j", "e", "l", " ", " "], label="jel — the seam"),
        Line(["z", "u", "k", "a", "d", " ", " "], label="zukad — dark time"),
    ), 0.36),
    Sample("sv-hail", "PHRASE 01 · THE HAIL", 'ver ish-ol. — "Truth to you."', (
        Line(["v", "e", "r", " ", "i", "sh", " ", "o", "l"],
             label="ver ish-ol."),
    ), 0.42),
    Sample("sv-compare", "CAREFUL HAND vs BRIDGE HAND",
           'ver-a=ka — "It holds."', (
        Line(["v", "e", "r", "a", "k", "a"],
             label="careful hand — fully spelled"),
        Line(["v", "e", "r", "@T", "=ka"],
             label="bridge hand — sigils", color="#6fa8ff"),
    ), 0.42),
    Sample("sv-line40", "SHOWPIECE · LITANY LINE 40 · BRIDGE HAND",
           "hōl-t-eshe=zu. enmai ve-a=mi.", (
        Line(["h", "o:", "l", "t", "@Ts", "=zu", " ", " ",
              "e", "n", "m", "a", "i", " ", "v", "e", "@T", "=mi"],
             color="#e8362a"),
    ), 0.46),
    Sample("sv-gap", "THE GAP-STROKE", "ne — line 38, as lettered", (
        Line([" ", "|", " "], color="#e8362a"),
    ), 0.5),
)}


def render_sample(key: str, background: Optional[str] = BACKGROUND) -> str:
    """Render one docs/03 sample block (``sv-names`` … ``sv-gap``) exactly."""
    s = SAMPLES[key]
    return render_svg(s.lines, scale=s.scale, background=background)
