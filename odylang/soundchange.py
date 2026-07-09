"""Ordered sound-change engine (Peterson's method: naturalism is history).

A daughter language is a :class:`Deriver`: an ordered list of named
:class:`Change` functions over segment lists, plus optional phonotactic
repairs.  Every derivation returns a :class:`Derivation` with a full trace,
so any documented etymology in the codices can be replayed step by step::

    >>> from odylang.suchel import SUCHEL
    >>> SUCHEL.derive('*suw-kel').form
    'sūchel'
    >>> [step.change for step in SUCHEL.derive('*suw-kel').steps]
    ['SC-1', 'SC-3']

Proto-forms are written Peterson-style with a leading ``*`` and hyphens at
morpheme boundaries (``*suw-kel``); boundaries stay in the segment stream
(several sister-language rules are boundary-sensitive) and are stripped at
romanization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .phonology import BOUNDARIES, is_vowel, romanize, syllabify, tokenize

Segs = List[str]


def parse_proto(form: str) -> Segs:
    """``'*haw-ol-'`` -> ``['h','au','-','o','l']`` (``aw`` is the /au/ diphthong)."""
    body = form.strip().lstrip("*").strip("-")
    segs = tokenize(body)
    # normalise a+w to the diphthong au wherever it occurs (docs write both)
    out: Segs = []
    for s in segs:
        if s == "w" and out and out[-1] == "a":
            out[-1] = "au"
        else:
            out.append(s)
    return out


def next_real(segs: Segs, i: int) -> Optional[int]:
    """Index of the next non-boundary segment after i."""
    j = i + 1
    while j < len(segs):
        if segs[j] not in BOUNDARIES:
            return j
        j += 1
    return None


def prev_real(segs: Segs, i: int) -> Optional[int]:
    j = i - 1
    while j >= 0:
        if segs[j] not in BOUNDARIES:
            return j
        j -= 1
    return None


@dataclass
class Change:
    id: str
    summary: str
    fn: Callable[[Segs], Segs]


@dataclass
class Step:
    change: str
    before: str
    after: str


@dataclass
class Derivation:
    proto: str
    form: str
    steps: List[Step]
    adjustments: List[str] = field(default_factory=list)

    @property
    def fired(self) -> List[str]:
        return [s.change for s in self.steps]

    def trace(self) -> str:
        lines = [self.proto]
        for s in self.steps:
            lines.append(f"  {s.change}: {s.before} -> {s.after}")
        for a in self.adjustments:
            lines.append(f"  (adjustment) {a}")
        lines.append(f"  = {self.form}")
        return "\n".join(lines)


# adjustment: (form) -> form, applied after the numbered changes, each carrying
# the codex's own note — used only where the source document itself flags a
# special development.
Adjustment = Tuple[str, Callable[[str], str]]


@dataclass
class Deriver:
    name: str
    changes: List[Change]
    repairs: List[Change] = field(default_factory=list)  # unnumbered cleanup

    def derive(self, proto: str, adjustments: Sequence[Adjustment] = ()) -> Derivation:
        segs = parse_proto(proto)
        steps: List[Step] = []
        for ch in list(self.changes) + list(self.repairs):
            before = romanize(segs)
            segs = ch.fn(list(segs))
            after = romanize(segs)
            if after != before:
                steps.append(Step(ch.id, before, after))
        form = romanize(segs)
        notes = []
        for note, fn in adjustments:
            new = fn(form)
            if new != form:
                notes.append(f"{form} -> {new}: {note}")
                form = new
        return Derivation(proto, form, steps, notes)


# ---------------------------------------------------------------------------
# shared helpers used by several daughters


def initial_stress_syllables(segs: Segs):
    """Old Pelagic word stress fell on the first syllable (docs/01 §03:
    Pelgar/Idrenes lose their *second*-syllable vowel; docs/06 §03: D-4
    rounds the stressed vowel of monosyllabic roots).  Returns syllables of
    the boundary-free stream."""
    return syllabify(segs)


def real_indices(segs: Segs) -> List[int]:
    return [i for i, s in enumerate(segs) if s not in BOUNDARIES]
