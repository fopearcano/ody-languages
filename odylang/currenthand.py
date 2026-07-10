"""The Current Hand — Navcher redesign 07-E, from the Claude Design handoff.

    "One unbroken line per word — but the line is alive now. It leans into
    its own momentum, sways on an invisible current, presses on the fall
    and feathers on the rise."

A faithful Python port of the handoff's pen engine (`Navcher Page
Studies.dc.html`, the design open at handoff time, marked AFTER ALPHA.2):
letters are variable-width ribbons interpolated with Catmull-Rom splines
and joined into one connected thread per word.  The featural system of the
stencil hand survives, re-expressed as things a single pressured line can
do without stopping:

* **place of articulation** — the knot's height: labial low (E=104),
  alveolar mid (78), velar high (44); affricates release the knot into a
  tremor (knotT);
* **voicing** — a drop released as the letter leaves (signal color);
* **frication** — the tremor, at elevation; nasals are open swells;
  *r* whips up, *l* glides under;
* **h** — the ink runs dry, the thread resumes shifted (the threshold
  letter is still mostly absence);
* **vowels** — ripples that never leave the carrier far; **length** is a
  breath-arc suspended above;
* **sigils** — upright, unswayed, machine-precise; the five moods are one
  family on one base shape (the eye); **T• is the filled eye**; **=zu is
  the one straight, uniform stroke — refuses to bend, refuses to breathe**;
  the gap is a split vertical in subdued ink.

Beyond single lines, the design defines five page *registers* (docs of the
handoff, reproduced by :func:`studies`): 2a the record (ruled, stilled),
2b the daily scrawl (jittered, one strike + rewrite), 2c the watch log
(stamped entries, compression betrays speed), 2d the vigil trace (one
unbroken boustrophedon line), 2e the liturgy disc (sentences rung at
R = phrase/2π).  All randomness is a seeded mulberry32 — the same seed
reproduces the prototype's output exactly (cross-validated against the
design's own JS in tests/test_currenthand.py).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable, Dict, List, Optional, Sequence, Tuple


def _tofixed(v: float, nd: int) -> str:
    """JavaScript Number.prototype.toFixed, exactly: quantize the exact
    binary double with ties away from zero (Python's %-formatting uses
    banker's rounding, which drifts from the prototype at .5 ties)."""
    q = Decimal(1).scaleb(-nd)
    d = Decimal(v).quantize(q, rounding=ROUND_HALF_UP)
    return f"{d:.{nd}f}"

# ---------------------------------------------------------------------------
# palettes (from the handoff's Current Hand study)

PALETTES = {
    "bone-paper": {"bg": "#EDE8DC", "ink": "#24282E", "acc": "#33707C",
                   "acc2": "#A65B3F", "sub": "#8A8478"},
    "light-trace": {"bg": "#0A0D11", "ink": "#E8E3D6", "acc": "#7FB4C0",
                    "acc2": "#D9A38A", "sub": "#8B93A0"},
}

SLANT = 0.10
LINEH = 152
MAXU = 1500

# ---------------------------------------------------------------------------
# the pen engine


def _cr1(a: float, b: float, c: float, d: float, t: float) -> float:
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2
                  + (-a + 3 * b - 3 * c + d) * t3)


def _lin(a: float, b: float, c: float, d: float, t: float) -> float:
    """Straight interpolation between the two middle control points — the
    faceted counterpart of :func:`_cr1`.  Used by the Logos (carved) hand."""
    return b + (c - b) * t


def _logos_carve(strokes, ndir: int = 8):
    """Snap every segment of every stroke to one of ``ndir`` compass
    directions (default 8: horizontal, vertical, and the diagonals),
    preserving segment length.  This turns the flowing pen skeleton into the
    rectilinear, rune-like cuts of the **Logos hand** — a monumental carved
    inscription, the sacred ancestor the Current Hand rounded into cursive.
    Mutates and returns the stroke list.
    """
    step = 2 * math.pi / ndir
    for st in strokes:
        pts = st.pts
        if len(pts) < 2:
            continue
        out = [list(pts[0])]
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1][0], pts[i - 1][1]
            x1, y1, w = pts[i]
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length < 1e-6:
                out.append([out[-1][0], out[-1][1], w])
                continue
            ang = round(math.atan2(dy, dx) / step) * step
            out.append([out[-1][0] + length * math.cos(ang),
                        out[-1][1] + length * math.sin(ang), w])
        st.pts = out
    return strokes


def ribbon(pts: Sequence[Sequence[float]], f: float,
           squared: bool = False) -> str:
    """A variable-width ribbon through [x, y, width] control points, offset
    both ways along the normal and closed as one filled path.

    ``squared=False`` (default) smooths the centreline with Catmull-Rom — the
    flowing **Current Hand**.  ``squared=True`` runs a straight (linear)
    centreline instead: the same skeleton rendered as faceted, angular cuts —
    the **Logos hand**, the old sacred carving.  The two are ancestor and
    descendant: identical control points, curve vs. facet.
    """
    n = len(pts)
    if n < 2:
        return ""
    def g(i):
        return pts[0 if i < 0 else (n - 1 if i > n - 1 else i)]
    S: List[List[float]] = []
    interp = _lin if squared else _cr1
    SEG = 1 if squared else 8
    for i in range(n - 1):
        p0, p1, p2, p3 = g(i - 1), g(i), g(i + 1), g(i + 2)
        top = SEG if i == n - 2 else SEG - 1
        for t in range(top + 1):
            u = t / SEG
            S.append([interp(p0[0], p1[0], p2[0], p3[0], u),
                      interp(p0[1], p1[1], p2[1], p3[1], u),
                      max(0.3, interp(p0[2], p1[2], p2[2], p3[2], u)) * f])
    L: List[str] = []
    R: List[str] = []
    for i in range(len(S)):
        a = S[i - 1 if i > 0 else 0]
        b = S[i + 1 if i < len(S) - 1 else len(S) - 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        hw = S[i][2] / 2
        L.append(_tofixed(S[i][0] + nx * hw, 1) + "," + _tofixed(S[i][1] + ny * hw, 1))
        R.append(_tofixed(S[i][0] - nx * hw, 1) + "," + _tofixed(S[i][1] - ny * hw, 1))
    R.reverse()
    return "M" + " L".join(L) + " L" + " L".join(R) + " Z"


# ---------------------------------------------------------------------------
# letterforms — pen data verbatim from the handoff


def _knot(E):
    return [[0, 88, 4.2], [18, 87, 5], [36, 82, 5.5], [48, E + 24, 7.5],
            [56, E + 6, 10.5], [54, E - 14, 8], [42, E - 22, 6],
            [32, E - 12, 4.5], [32, E + 6, 7], [46, E + 18, 12],
            [64, E + 26, 9.5], [80, 86, 5.5], [100, 88, 4.2]]


def _knot_t(E):
    return [[0, 88, 4.2], [16, 87, 5], [32, 82, 5.5], [44, E + 24, 7.5],
            [52, E + 6, 10.5], [50, E - 14, 8], [38, E - 22, 6],
            [28, E - 12, 4.5], [28, E + 6, 7], [42, E + 18, 12],
            [58, E + 26, 8], [70, 102, 6], [78, 108, 4.5], [86, 90, 4.8],
            [100, 88, 4.2]]


_LENSPEN = [[12, 99, 2.5], [20, 84, 5], [33, 82, 5.5], [44, 92, 5],
            [48, 99, 4.5], [42, 110, 5], [30, 116, 5.5], [18, 112, 5],
            [13, 101, 2.5]]


@dataclass
class Pen:
    w: float
    pen: Tuple[list, ...] = ()
    drop_at: Optional[float] = None
    vowel: bool = False
    sigil: bool = False
    pen_acc: Tuple[list, ...] = ()
    pen_acc2: Tuple[list, ...] = ()
    pen_sub: Tuple[list, ...] = ()


HAND: Dict[str, Pen] = {
    "p": Pen(100, (_knot(104),)),
    "b": Pen(100, (_knot(104),), drop_at=86),
    "t": Pen(98, (_knot(78),)),
    "d": Pen(98, (_knot(78),), drop_at=84),
    "k": Pen(106, (_knot(44),)),
    "g": Pen(106, (_knot(44),), drop_at=92),
    "ch": Pen(110, (_knot_t(60),)),
    "j": Pen(110, (_knot_t(60),), drop_at=96),
    "v": Pen(88, ([[0, 88, 4.2], [14, 88, 5], [26, 94, 6.5], [36, 110, 9.5],
                   [43, 121, 11], [50, 110, 8], [58, 96, 5.5], [68, 86, 4.8],
                   [80, 84, 4.6], [100, 88, 4.2]],), drop_at=74),
    "s": Pen(96, ([[0, 88, 4.2], [16, 88, 5], [28, 80, 6], [36, 62, 9],
                   [44, 56, 7], [52, 72, 10], [58, 94, 11], [64, 110, 8],
                   [72, 112, 5.5], [80, 96, 5], [86, 87, 4.8],
                   [100, 88, 4.2]],)),
    "z": Pen(96, ([[0, 88, 4.2], [16, 88, 5], [28, 96, 6], [36, 114, 9],
                   [44, 120, 7], [52, 104, 10], [58, 82, 11], [64, 66, 8],
                   [72, 64, 5.5], [80, 80, 5], [86, 89, 4.8],
                   [100, 88, 4.2]],), drop_at=82),
    "sh": Pen(102, ([[0, 88, 4.2], [14, 88, 5], [24, 78, 5.5], [32, 52, 8],
                     [38, 32, 9], [46, 28, 6.5], [52, 44, 9.5], [58, 64, 11],
                     [66, 74, 7], [74, 60, 5], [82, 72, 4.8], [92, 84, 4.6],
                     [100, 88, 4.2]],)),
    "m": Pen(98, ([[0, 88, 4.2], [16, 87, 5], [30, 92, 7], [36, 106, 10.5],
                   [46, 113, 12.5], [58, 112, 10.5], [66, 102, 8],
                   [72, 92, 6], [84, 87, 5], [100, 88, 4.2]],)),
    "n": Pen(84, ([[0, 88, 4.2], [14, 88, 5], [24, 80, 6], [32, 64, 9.5],
                   [42, 56, 11], [52, 60, 9], [58, 72, 6.5], [62, 86, 5.5],
                   [68, 98, 6.5], [76, 102, 6], [86, 94, 5],
                   [100, 88, 4.2]],)),
    "r": Pen(86, ([[0, 88, 4.2], [18, 88, 5], [34, 86, 5.5], [44, 78, 6.5],
                   [50, 56, 7.5], [53, 36, 3.5], [55, 50, 3], [58, 72, 6],
                   [64, 84, 7.5], [76, 88, 5], [100, 88, 4.2]],)),
    "l": Pen(94, ([[0, 88, 4.2], [16, 89, 5], [28, 94, 6.5], [40, 104, 9.5],
                   [54, 112, 11.5], [68, 112, 8.5], [80, 104, 5.5],
                   [88, 94, 4.6], [100, 88, 4.2]],)),
    "h": Pen(96, ([[0, 88, 4.2], [14, 88, 5], [26, 86, 5.5], [36, 80, 4.5],
                   [44, 72, 2.2], [48, 66, 0.6]],
                  [[56, 104, 0.6], [62, 100, 2.2], [70, 94, 4.5],
                   [80, 90, 5], [100, 88, 4.2]])),
    "a": Pen(58, ([[0, 88, 4.2], [10, 87, 5], [18, 80, 6], [26, 70, 7.5],
                   [33, 70, 6.5], [40, 78, 5.5], [48, 86, 4.8],
                   [60, 88, 4.2]],), vowel=True),
    "e": Pen(52, ([[0, 88, 4.2], [10, 86, 5], [20, 80, 6.5], [32, 79, 6],
                   [44, 83, 5], [60, 88, 4.2]],), vowel=True),
    "i": Pen(46, ([[0, 88, 4.2], [12, 88, 5], [20, 86, 5.5], [26, 76, 4.5],
                   [29, 66, 1.6], [33, 76, 3], [38, 84, 4.8], [48, 88, 4.6],
                   [60, 88, 4.2]],), vowel=True),
    "o": Pen(56, ([[0, 88, 4.2], [8, 89, 5], [14, 94, 6], [22, 101, 7.5],
                   [31, 103, 7], [40, 99, 6], [46, 93, 5], [52, 89, 4.6],
                   [60, 88, 4.2]],), vowel=True),
    "u": Pen(56, ([[0, 88, 4.2], [8, 88, 5], [13, 92, 5.5], [18, 102, 7.5],
                   [26, 109, 8], [35, 107, 7], [42, 98, 5.5], [48, 91, 4.8],
                   [60, 88, 4.2]],), vowel=True),
    "mT": Pen(60, (_LENSPEN,), sigil=True),
    "mTm": Pen(60, (_LENSPEN, [[12, 99, 3.5], [5, 98, 3], [0, 104, 1.2]]),
               sigil=True),
    "mTp": Pen(60, (_LENSPEN, [[48, 99, 3.5], [55, 98, 3], [60, 104, 1.2]]),
               sigil=True),
    "mTs": Pen(60, sigil=True,
               pen_acc2=([[30, 80, 1.5], [30, 87, 24], [30, 99, 35],
                          [30, 111, 24], [30, 118, 1.5]],)),
    "mF": Pen(60, (_LENSPEN, [[8, 118, 1.2], [22, 106, 4.8], [38, 93, 4.8],
                              [52, 80, 1.2]]), sigil=True),
    "aka": Pen(60, ([[4, 106, 1.5], [11, 90, 4.5], [18, 85, 5], [25, 98, 5.5],
                     [31, 114, 5], [38, 116, 4.5], [44, 102, 3],
                     [46, 94, 1.5]],), sigil=True),
    "ami": Pen(60, ([[46, 84, 1.2], [38, 92, 4.6], [26, 104, 5],
                     [14, 116, 1.5]],), sigil=True),
    "azu": Pen(60, sigil=True,
               pen_acc=([[50, 76, 4.6], [10, 124, 4.6]],)),
    "gap": Pen(70, sigil=True,
               pen_sub=([[35, 4, 0.8], [35, 15, 3.6]],
                        [[35, 125, 3.6], [35, 136, 0.8]])),
    "q": Pen(60, ([[10, 116, 1.2], [16, 103, 4.2], [24, 88, 1.5]],
                  [[31, 118, 1.2], [37, 105, 4.2], [45, 90, 1.5]]),
             sigil=True),
}

ARCPEN = [[14, 54, 0.7], [22, 47, 4.2], [34, 46, 4.2], [44, 52, 0.7]]
LEADIN = [[-15, 73, 0.5], [-8, 80, 2.8], [0, 88, 4.2]]
LEADOUT = [[0, 88, 4.2], [9, 85, 2.8], [18, 78, 1.2], [23, 70, 0.5]]


def _droppen(cx):
    return [[cx, 100, 0.8], [cx + 1.5, 106, 5.5], [cx + 0.8, 113, 8],
            [cx - 1, 117, 3.2]]


def _sx_of(g: Pen) -> float:
    return 1 if g.sigil else (g.w / 60 if g.vowel else g.w / 100)


def _w_of(k: str) -> float:
    return HAND[k[:-1] if k.endswith(":") else k].w


def _is_sig(k: str) -> bool:
    g = HAND.get(k)
    return bool(g and g.sigil)


# ---------------------------------------------------------------------------
# the thread builder


@dataclass
class Stroke:
    pts: List[List[float]]
    color: str = "ink"
    rigid: bool = False
    s0: float = 0.0
    op: Optional[float] = None
    ink: Optional[str] = None  # per-stroke color override (the blue hail)


@dataclass
class Thread:
    strokes: List[Stroke]
    total: float


def build(keys: Sequence[str], sway: Optional[float] = None,
          sway_phase: float = 0.0, word_fall: bool = False,
          fall_rate: Optional[float] = None, space_carrier: bool = False,
          no_tails: bool = False) -> Thread:
    """Thread a token stream into connected pen strokes.

    Tokens: letter keys ('v', 'sh'), long vowels ('u:'), sigil keys
    ('mT', 'aka', 'gap', 'q'), and ' ' word spaces.
    """
    sway_a = 0.4 if sway is None else sway
    ph = sway_phase

    def sway_f(x):
        return sway_a * (3.4 * math.sin((x + ph) / 56)
                         + 1.7 * math.sin((x + ph) / 19 + 2.1))

    strokes: List[Stroke] = []
    s = 0.0
    in_run = False
    word_start = 0.0

    def push_pen(pen, sx, off, sig, color="ink", s0=0.0):
        pts = []
        for x, y, w in pen:
            S = x * sx + (0 if sig else (88 - y) * SLANT) + off
            Y = y + (0 if sig else sway_f(S))
            if word_fall and not sig:
                Y += (0.14 if fall_rate is None else fall_rate) * max(0, S - word_start)
            pts.append([S, Y, w])
        strokes.append(Stroke(pts, color, bool(sig), s0))

    for k in keys:
        if k == " ":
            if space_carrier:
                push_pen([[0, 88, 4.2], [31, 87.2, 4.2], [62, 88, 4.2]], 1, s, False)
                s += 62
                continue
            if in_run and not no_tails:
                push_pen(LEADOUT, 1, s, False)
            in_run = False
            s += 62
            continue
        if _is_sig(k):
            if in_run and not no_tails:
                push_pen(LEADOUT, 1, s, False)
                in_run = False
            s += 18
            g = HAND[k]
            s0 = s + 30
            for p in g.pen:
                push_pen(p, 1, s, True, "ink", s0)
            for p in g.pen_acc:
                push_pen(p, 1, s, True, "acc2", s0)
            for p in g.pen_acc2:
                push_pen(p, 1, s, True, "acc2", s0)
            for p in g.pen_sub:
                push_pen(p, 1, s, True, "sub", s0)
            s += _w_of(k) + 18
            continue
        if not in_run:
            word_start = s
            if not no_tails:
                push_pen(LEADIN, 1, s, False)
            in_run = True
        long = k.endswith(":")
        g = HAND[k[:-1] if long else k]
        sx = _sx_of(g)
        for p in g.pen:
            push_pen(p, sx, s, False)
        if long:
            push_pen(ARCPEN, sx, s, False)
        if g.drop_at is not None:
            push_pen(_droppen(g.drop_at), 1, s, False, "acc")
        s += _w_of(k)
    if in_run and not no_tails:
        push_pen(LEADOUT, 1, s, False)
    return Thread(strokes, s)


def _map_strokes(th: Thread, fn, rigid_fn=None) -> List[Stroke]:
    out = []
    for st in th.strokes:
        pts = []
        for S, y, w in st.pts:
            p = rigid_fn(S, y, st.s0) if (st.rigid and rigid_fn) else fn(S, y)
            pts.append([p[0], p[1], w])
        out.append(Stroke(pts, st.color, st.rigid, st.s0, st.op, st.ink))
    return out


def _linear(s, y):
    return [s, y]


# ---------------------------------------------------------------------------
# seeded randomness — mulberry32, bit-exact with the prototype

_M = 0xFFFFFFFF


def _imul(x: int, y: int) -> int:
    return ((x & _M) * (y & _M)) & _M


def mul32(a: int) -> Callable[[], float]:
    state = a & _M

    def r() -> float:
        nonlocal state
        state = (state + 0x6D2B79F5) & _M
        a2 = state
        t = _imul(a2 ^ (a2 >> 15), (1 | a2) & _M)
        t = ((t + _imul(t ^ (t >> 7), (61 | t) & _M)) & _M) ^ t
        return ((t ^ (t >> 14)) & _M) / 4294967296

    return r


# ---------------------------------------------------------------------------
# the specimen: frequency-faithful, seeded (codex §5 letter distribution)

ONS = [("n", 70), ("l", 60), ("v", 58), ("r", 55), ("m", 52), ("t", 46),
       ("d", 30), ("k", 30), ("sh", 26), ("s", 20), ("j", 16), ("z", 10),
       ("p", 5), ("g", 4), ("ch", 3)]
VOWT = [("e", 140), ("a", 110), ("u", 74), ("i", 58), ("o", 53)]
CODA = [("n", 30), ("l", 26), ("r", 18), ("d", 13), ("s", 9), ("k", 8),
        ("m", 8)]

W = {
    "hail1": ["v", "e", "r"], "hail2": ["i", "sh", "o", "l"],
    "enmai": ["e", "n", "m", "a", "i"], "zukad": ["z", "u", "k", "a", "d"],
    "jel": ["j", "e", "l"], "suchel": ["s", "u:", "ch", "e", "l"],
    "hau": ["h", "a", "u"], "holt": ["h", "o:", "l", "t"], "ve": ["v", "e"],
}

PARAS = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]


def _make_sents(rand):
    def wpick(tbl):
        tot = sum(p[1] for p in tbl)
        r = rand() * tot
        for p in tbl:
            r -= p[1]
            if r < 0:
                return p[0]
        return tbl[0][0]

    def gen_word():
        r = rand()
        nsyl = 1 if r < 0.2 else (2 if r < 0.75 else 3)
        keys = []
        for i in range(nsyl):
            if i == 0 and rand() < 0.12:
                keys.append("h")
            elif not (i == 0 and rand() < 0.15):
                keys.append(wpick(ONS))
            keys.append(wpick(VOWT) + (":" if rand() < 0.15 else ""))
            if rand() < (0.45 if i == nsyl - 1 else 0.2):
                keys.append(wpick(CODA))
        return keys

    def gen(n):
        return [gen_word() for _ in range(n)]

    def ins(arr, at, w):
        arr.insert(at, w)
        return arr

    return [
        {"words": [W["hail1"], W["hail2"]]},
        {"words": ins(gen(4), 1, W["enmai"]), "mood": "mT", "anchor": "aka"},
        {"words": ins(gen(4), 2, W["zukad"]), "mood": "mTm", "anchor": "ami"},
        {"words": ins(gen(3), 2, W["jel"]), "mood": "mT"},
        {"words": ins(gen(3), 1, W["suchel"]), "mood": "mTp",
         "anchor": "aka", "q": True},
        {"words": gen(4), "mood": "mF", "anchor": "aka"},
        {"words": ins(gen(3), 2, W["hau"]), "mood": "mT", "anchor": "ami"},
        {"words": [W["holt"]], "mood": "mTs", "anchor": "azu"},
        {"words": [W["ve"]], "mood": "mT", "anchor": "ami"},
    ]


def _realize(S, hand):
    words = [list(w) for w in S["words"]]
    if S.get("mood") == "mF":
        words.insert(0, ["v", "o"])
    if hand == "careful":
        suf = {"mT": ["a"], "mTm": ["i", "m"], "mTp": ["u", "r"],
               "mTs": ["e", "sh", "e"], "mF": ["a"]}.get(S.get("mood"), [])
        anc = {"aka": ["k", "a"], "ami": ["m", "i"],
               "azu": ["z", "u"]}.get(S.get("anchor"), [])
        if suf or anc:
            words[-1] = words[-1] + suf + anc
    else:
        tail = []
        if S.get("mood"):
            tail.append(S["mood"])
        if S.get("anchor"):
            tail.append(S["anchor"])
        if tail:
            words.append(tail)
    if S.get("q"):
        words.append(["q"])
    return words


def _word_units(keys):
    u = sum(_w_of(k) + (36 if _is_sig(k) else 0) for k in keys)
    return u + (46 if any(not _is_sig(k) for k in keys) else 0)


def _flow(sents, hand, max_u, sent_idx=None):
    stream = []
    for pi, para in enumerate(PARAS):
        for si in para:
            if sent_idx and si not in sent_idx:
                continue
            for w in _realize(sents[si], hand):
                stream.append(w)
        if pi < len(PARAS) - 1:
            stream.append(["gap"])
    lines: List[List[str]] = []
    cur: List[str] = []
    u = 0.0
    for w in stream:
        wu = _word_units(w)
        if u > 0 and u + 62 + wu > max_u:
            lines.append(cur)
            cur = []
            u = 0
        if cur:
            cur.append(" ")
            u += 62
        cur.extend(w)
        u += wu
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# figure assembly

PAPER = {"ink": "#24282E", "acc": "#33707C", "acc2": "#A65B3F",
         "sub": "#8A8478"}


@dataclass
class Fig:
    vb: str
    elems: List[dict]      # {d, fill, opacity?}
    width: float
    height: float


def _fig(strokes: List[Stroke], ink_w: float, px: float = 560,
         squared: bool = False) -> Fig:
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    elems = []
    for st in strokes:
        for X, Y, w in st.pts:
            x0 = min(x0, X - w)
            y0 = min(y0, Y - w)
            x1 = max(x1, X + w)
            y1 = max(y1, Y + w)
        col = st.ink or PAPER.get(st.color, PAPER["ink"])
        e = {"d": ribbon(st.pts, ink_w, squared), "fill": col}
        if st.op is not None:
            e["opacity"] = st.op
        elems.append(e)
    pad = 20
    bw = (x1 - x0) + 2 * pad
    bh = (y1 - y0) + 2 * pad
    py = px * bh / bw
    vb = " ".join(_tofixed(v, 0) for v in (x0 - pad, y0 - pad, bw, bh))
    return Fig(vb, elems, px, py)


def _shift(strokes: List[Stroke], dy: float) -> None:
    for st in strokes:
        for p in st.pts:
            p[1] += dy


# ---------------------------------------------------------------------------
# the five page studies (2a–2e)


def _fig_record(sents, ink_w):
    """2a — the record page: ruled carriers, stilled current."""
    all_s: List[Stroke] = []
    for i, line_keys in enumerate(_flow(sents, "careful", MAXU)):
        all_s.append(Stroke([[-30, 88 + i * LINEH, 1.3],
                             [MAXU / 2, 88 + i * LINEH, 1.3],
                             [MAXU + 30, 88 + i * LINEH, 1.3]],
                            "sub", op=0.32))
        m = _map_strokes(build(line_keys, sway=0), _linear)
        _shift(m, i * LINEH)
        all_s.extend(m)
    return _fig(all_s, ink_w, 580)


def _fig_scrawl(sents, ink_w, seed):
    """2b — the daily scrawl: per-word jitter, crowding, strike + rewrite."""
    rnd = mul32(seed * 331 + 7)

    def R2(a, b):
        return a + (b - a) * rnd()

    all_s: List[Stroke] = []
    stream = []
    for pi, para in enumerate(PARAS):
        for si in para:
            for w in _realize(sents[si], "bridge"):
                stream.append(w)
        if pi < len(PARAS) - 1:
            stream.append(["gap"])
    state = {"x": 0.0, "lineY": 0.0}
    strike_at = 7 + math.floor(rnd() * 5)

    def place(w, kw, ink_k, strike):
        sig_w = all(_is_sig(k) for k in w)
        wu0 = _word_units(w) * kw
        if state["x"] > 0 and state["x"] + 50 + wu0 > MAXU:
            if state["x"] + 50 + wu0 < MAXU * 1.06 and not sig_w:
                kw *= 0.9
            else:
                state["lineY"] += LINEH * R2(0.88, 1.15)
                state["x"] = R2(0, 46)
        if state["x"] > 0:
            state["x"] += R2(38, 78)
        if sig_w:
            th = build(w)
        else:
            th = build(w, word_fall=True, fall_rate=R2(0.04, 0.22),
                       sway=R2(0.5, 1.5), sway_phase=R2(0, 500))
        dy = 0 if sig_w else R2(-9, 9)
        x0 = state["x"]
        line_y = state["lineY"]
        m = _map_strokes(
            th,
            lambda s, y: [x0 + s * kw, line_y + dy + 88 + (y - 88) * kw],
            lambda S, y, s0: [x0 + s0 * kw + (S - s0), line_y + dy + y])
        for st in m:
            for p in st.pts:
                p[2] *= kw * ink_k
            all_s.append(st)
        wu_f = _word_units(w) * kw
        if strike:
            all_s.append(Stroke([[x0 - 12, line_y + dy + 83, 2.4],
                                 [x0 + wu_f / 2, line_y + dy + 93, 3.2],
                                 [x0 + wu_f + 14, line_y + dy + 80, 1.8]],
                                "ink"))
        state["x"] += wu_f

    wi = 0
    for w in stream:
        sig_w = all(_is_sig(k) for k in w)
        do_strike = (not sig_w) and wi == strike_at
        place(w, 1 if sig_w else R2(0.85, 1.15),
              1 if sig_w else R2(0.8, 1.1), do_strike)
        if do_strike:
            place(w, R2(0.9, 1.1), R2(0.85, 1.05), False)
        if not sig_w:
            wi += 1
    return _fig(all_s, ink_w, 580)


def _fig_watch(sents, ink_w, seed):
    """2c — the watch log: stamped entries, compression betrays speed."""
    all_s: List[Stroke] = []
    rnd = mul32(seed * 97 + 3)
    for ln, si in enumerate(range(9)):
        S = sents[si]
        m_s = _map_strokes(build([S.get("anchor") or "ami"]), _linear)
        _shift(m_s, ln * LINEH)
        all_s.extend(m_s)
        words = _realize({"words": S["words"], "mood": S.get("mood"),
                          "q": S.get("q")}, "bridge")
        keys: List[str] = []
        for i, w in enumerate(words):
            if i:
                keys.append(" ")
            keys.extend(w)
        k = 0.55 if si == 0 else 0.68 + rnd() * 0.14
        m = _map_strokes(build(keys),
                         lambda s, y, k=k: [150 + s * k, y],
                         lambda S2, y, s0, k=k: [150 + s0 * k + (S2 - s0), y])
        if si == 0:
            for st in m:
                if st.color == "ink":
                    st.ink = "#39597A"
        _shift(m, ln * LINEH)
        all_s.extend(m)
    return _fig(all_s, ink_w, 580)


def _fig_vigil(sents, ink_w):
    """2d — the vigil trace: one unbroken folded (boustrophedon) line."""
    keys: List[str] = []
    for line in _flow(sents, "bridge", 1e9):
        keys.extend(line)
    L, gap_h = MAXU, LINEH
    strokes: List[Stroke] = []
    state = {"line": 0, "sl": 0.0, "dir": 1, "gs": 0.0, "curW": 0.0}

    def sway_f(x):
        return 0.4 * (3.4 * math.sin(x / 56) + 1.7 * math.sin(x / 19 + 2.1))

    def put(pen, sx, sig, color="ink"):
        pts = []
        for x, y, w in pen:
            S = x * sx + (0 if sig else (88 - y) * SLANT)
            if sig:
                X = (state["sl"] if state["dir"] > 0
                     else L - state["sl"] - state["curW"]) + S
            else:
                X = state["sl"] + S if state["dir"] > 0 else L - state["sl"] - S
            pts.append([X, state["line"] * gap_h + y
                        + (0 if sig else sway_f(state["gs"] + S)), w])
        strokes.append(Stroke(pts, color))

    def turn():
        R = gap_h / 2
        cy = state["line"] * gap_h + 88 + R
        mx = L if state["dir"] > 0 else 0
        sgn = 1 if state["dir"] > 0 else -1
        pts = []
        for a in range(-90, 91, 18):
            r = a * math.pi / 180
            pts.append([mx + sgn * R * math.cos(r), cy + R * math.sin(r),
                        3.2 if a == 0 else 4.2])
        strokes.append(Stroke(pts, "ink"))
        state["line"] += 1
        state["dir"] = -state["dir"]
        state["sl"] = 0
        state["gs"] += math.pi * R

    for k in keys:
        if k == " ":
            if state["sl"] + 50 > L:
                turn()
                continue
            put([[0, 88, 4.2], [25, 87.4, 4.2], [50, 88, 4.2]], 1, False)
            state["sl"] += 50
            state["gs"] += 50
            continue
        g = HAND[k[:-1] if k.endswith(":") else k]
        state["curW"] = _w_of(k)
        w = state["curW"] + (24 if g.sigil else 0)
        if state["sl"] + w > L:
            rem = L - state["sl"]
            put([[0, 88, 4.2], [rem / 2, 87.5, 4.2], [rem, 88, 4.2]], 1, False)
            state["gs"] += rem
            state["sl"] = L
            turn()
        if g.sigil:
            state["sl"] += 12
        sx = _sx_of(g)
        for p in g.pen:
            put(p, sx, g.sigil)
        for p in g.pen_acc:
            put(p, sx, g.sigil, "acc2")
        for p in g.pen_acc2:
            put(p, sx, g.sigil, "acc2")
        for p in g.pen_sub:
            put(p, sx, g.sigil, "sub")
        if k.endswith(":"):
            put(ARCPEN, sx, False)
        if g.drop_at is not None:
            put(_droppen(g.drop_at), 1, False, "acc")
        state["sl"] += state["curW"] + (12 if g.sigil else 0)
        state["gs"] += state["curW"]
    return _fig(strokes, ink_w, 580)


def _fig_disc(sents, ink_w):
    """2e — the liturgy disc: sentences rung at resonant radii R = phrase/2π."""
    def ring_sent(S):
        keys: List[str] = []
        for i, w in enumerate(_realize(S, "careful")):
            if i:
                keys.append(" ")
            keys.extend(w)
        return build(keys, space_carrier=True, no_tails=True, sway=0)

    rings = sorted((ring_sent(S) for S in
                    [{"words": [W["jel"]]}, sents[3], sents[8], sents[0],
                     sents[7], sents[1], sents[4]]),
                   key=lambda th: th.total)
    disc: List[Stroke] = []
    prev_r = 0.0
    for th in rings:
        R = max(prev_r + 95, th.total / (2 * math.pi))
        prev_r = R
        need = 2 * math.pi * R
        pad_u = need - th.total
        half = pad_u / 2
        for st in th.strokes:
            st.s0 += half
            for p in st.pts:
                p[0] += half
        if pad_u > 8:
            th.strokes.append(Stroke([[0, 88, 4.2], [half / 2, 87.6, 4.2],
                                      [half, 88, 4.2]], "ink"))
            th.strokes.append(Stroke([[need - half, 88, 4.2],
                                      [need - half / 2, 87.6, 4.2],
                                      [need, 88, 4.2]], "ink"))

        def fn(s, y, R=R, need=need):
            a = -math.pi / 2 + (s / need) * 2 * math.pi
            r = R + (88 - y)
            return [r * math.cos(a), r * math.sin(a)]

        def rigid_fn(S, y, s0, R=R, need=need):
            a0 = -math.pi / 2 + (s0 / need) * 2 * math.pi
            ds = S - s0
            rad = 88 - y
            return [(R + rad) * math.cos(a0) - ds * math.sin(a0),
                    (R + rad) * math.sin(a0) + ds * math.cos(a0)]

        disc.extend(_map_strokes(th, fn, rigid_fn))
    return _fig(disc, ink_w, 540)


PAGE_META = {
    "record": ("2a", "The record page", "LOG OF RECORD · CAREFUL HAND · RULED",
               "sway 0 · ruled carriers · suffixes spelled"),
    "scrawl": ("2b", "The daily scrawl", "DAY LEAF · QUICK HAND",
               "per-word size · ink · sway · fall all jittered · one strike + rewrite"),
    "watch": ("2c", "The watch log", "BRIDGE WATCH · BRIDGE HAND · ENTRIES",
              "clock stamped first · clause-mood last · λ betrays speed"),
    "vigil": ("2d", "The vigil trace", "VIGIL · BRIDGE HAND · DO NOT LIFT",
              "one stroke · folds mirrored · continuity is the record"),
    "disc": ("2e", "The liturgy disc", "LITURGY · CAREFUL HAND · RUNG, NOT CUT",
             "R = phrase/2π · silence held at the seam · uncut"),
}


def studies(seed: int = 11, ink_weight: float = 0.6) -> Dict[str, Fig]:
    """All five page studies for one seed (2a record, 2b scrawl, 2c watch,
    2d vigil, 2e disc) — deterministic, prototype-identical."""
    sents = _make_sents(mul32(seed * 7919 + 13))
    return {
        "record": _fig_record(sents, ink_weight),
        "scrawl": _fig_scrawl(sents, ink_weight, seed),
        "watch": _fig_watch(sents, ink_weight, seed),
        "vigil": _fig_vigil(sents, ink_weight),
        "disc": _fig_disc(sents, ink_weight),
    }


# ---------------------------------------------------------------------------
# SVG output


def fig_svg(fig: Fig, palette: str = "bone-paper", head: str = "",
            colophon: str = "") -> str:
    pal = PALETTES[palette]
    parts = []
    x, y, w, h = (float(v) for v in fig.vb.split())
    head_h = 34 if head else 0
    foot_h = 30 if colophon else 0
    total_h = fig.height + head_h + foot_h + 24
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{fig.width + 48:.0f}" height="{total_h:.0f}" '
        f'viewBox="0 0 {fig.width + 48:.0f} {total_h:.0f}">')
    parts.append(f'<rect width="100%" height="100%" fill="{pal["bg"]}"/>')
    mono = "font-family='ui-monospace,Menlo,Consolas,monospace' font-size='10' letter-spacing='2'"
    if head:
        parts.append(f"<text x='24' y='22' {mono} fill='{pal['sub']}'>{head}</text>")
        parts.append(f"<line x1='24' y1='30' x2='{fig.width + 24:.0f}' y2='30' "
                     f"stroke='{pal['sub']}' stroke-opacity='0.4'/>")
    parts.append(f'<svg x="24" y="{head_h + 12}" width="{fig.width:.0f}" '
                 f'height="{fig.height:.0f}" viewBox="{fig.vb}" '
                 f'preserveAspectRatio="xMidYMid meet">')
    for e in fig.elems:
        op = f' opacity="{e["opacity"]}"' if "opacity" in e else ""
        parts.append(f'<path d="{e["d"]}" fill="{e["fill"]}"{op}/>')
    parts.append("</svg>")
    if colophon:
        yc = head_h + fig.height + 30
        parts.append(f"<line x1='24' y1='{yc - 12:.0f}' x2='{fig.width + 24:.0f}' "
                     f"y2='{yc - 12:.0f}' stroke='{pal['sub']}' stroke-opacity='0.4'/>")
        parts.append(f"<text x='24' y='{yc:.0f}' {mono} fill='{pal['sub']}'>{colophon}</text>")
    parts.append("</svg>")
    return "\n".join(parts)


def page_svg(register: str, seed: int = 11, ink_weight: float = 0.6) -> str:
    """One page study as a standalone SVG (bone paper, headed and signed)."""
    fig = studies(seed, ink_weight)[register]
    pid, _title, head, colophon = PAGE_META[register]
    return fig_svg(fig, "bone-paper", f"{pid.upper()} · {head}",
                   f"{colophon} · seed {seed}")


# navcher-token adapter: the tokens produced by odylang.cli._sentence_tokens
_TOKEN_MAP = {"@T": "mT", "@T-": "mTm", "@T+": "mTp", "@Ts": "mTs",
              "@F": "mF", "=ka": "aka", "=mi": "ami", "=zu": "azu",
              "|": "gap", "?": "q"}


def keys_from_tokens(tokens: Sequence[str]) -> List[str]:
    return [_TOKEN_MAP.get(t, t) for t in tokens]


def line_svg(tokens: Sequence[str], palette: str = "light-trace",
             ink_weight: float = 0.85, sway: Optional[float] = None,
             px: float = 560, squared: bool = False) -> str:
    """Render one token line in the Current Hand (flowing) or, with
    ``squared=True``, in the Logos hand (faceted carving)."""
    # the Logos hand is a carved sacred script: it does not ride the living
    # current (written level, sway 0), and every segment is snapped to a
    # compass-cut facet
    th = build(keys_from_tokens(tokens), sway=0 if squared else sway)
    mapped = _map_strokes(th, _linear)
    if squared:
        _logos_carve(mapped)
    fig = _fig(mapped, ink_weight, px, squared)
    pal = PALETTES[palette]
    colors = {"#24282E": pal["ink"], "#33707C": pal["acc"],
              "#A65B3F": pal["acc2"], "#8A8478": pal["sub"]}
    elems = []
    for e in fig.elems:
        elems.append({**e, "fill": colors.get(e["fill"], e["fill"])})
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{fig.width:.0f}" '
             f'height="{fig.height:.0f}" viewBox="{fig.vb}">']
    x, y, w, h = (float(v) for v in fig.vb.split())
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                 f'fill="{pal["bg"]}"/>')
    for e in elems:
        op = f' opacity="{e["opacity"]}"' if "opacity" in e else ""
        parts.append(f'<path d="{e["d"]}" fill="{e["fill"]}"{op}/>')
    parts.append("</svg>")
    return "\n".join(parts)


def logos_line_svg(tokens: Sequence[str], palette: str = "light-trace",
                   ink_weight: float = 0.92, px: float = 560) -> str:
    """Render one token line in the **Logos hand** — the old sacred carving:
    the Current Hand's letterforms cut into straight facets, written level."""
    return line_svg(tokens, palette=palette, ink_weight=ink_weight, px=px,
                    squared=True)
