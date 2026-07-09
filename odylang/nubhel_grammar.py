"""Nubhel morphosyntax — the grammar of depth (docs/06 §03).

Same inherited machine as Sūchel, rebuilt for the determinate regime.
The verb template is unchanged — STEM–(ASP)–MOOD=ANCHOR — but every
slot drifted:

* **Three moods, and a hole.**  Plain ``-ó`` (witnessed, settled),
  approach ``-im`` (nearing a limit — the divers' home mood), hearsay
  ``-ur`` (old T⁺ 'held-from-above' drifted to 'held on another's
  word').  *-eshe left NO reflex: Nubhel cannot conjugate the
  seam-truth — asking for it raises :class:`SeamTruthError`, and
  :func:`code_switch` builds the documented borrowing instead.
  The plain mood is ``-ó`` where Sūchel has ``-a`` because D-4 rounds
  only *stressed* a: the suffix already carried the stress when the
  daughters split — the reconstruction proof that 'the mood carries the
  beat' is inherited late-Old-Pelagic prosody (docs/06 §03).
* **The debt anchor.**  =ka (beacon) and =mi (proper) are shared;
  =zu has no Nubhel cognate — divers rarely leave coverage — and asking
  for it raises :class:`DarkAnchorError`.  In its place =nu (from
  *nub), the deep-time anchor: 'stated in dive-time, conversion owed'.
  Formal register appends the debt as a numeral — the offset signature
  (:func:`offset`, :func:`sign_deep`, :func:`signature`).
* **Five degrees of depth** where Sūchel has two; motion verbs are
  ungrammatical without one (:func:`clause` enforces it).  TEXT 01's
  homecoming formula is the codex's own attested bare ``yed`` — the
  following ``neks`` licenses it (you do not narrate the vector of time
  your listener did not live); pass ``allow_bare=True`` to build it.
* **neks — the gap as courtesy.**  In Sūchel, ne marks what physics
  forbids narrating; in Nubhel, neks marks any interval your listener
  did not share.  Pragmatics, not physics: a returning diver says it
  once and moves on.

The copula is attested ``ve`` (TEXT 01), against D-2's expected †be —
carried here as data with the codex's evidence (see
:data:`odylang.nubhel.LEXICON` entry 've').
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .word import ANCHOR, MAI, MOOD, PART, PFV, STEM, Morph, Word

# ---------------------------------------------------------------------------
# SYSTEM 01 — three moods, and a hole


class SeamTruthError(ValueError):
    """Raised on any attempt to conjugate T•: *-eshe left no reflex —
    'Nubhel cannot conjugate the seam-truth' (docs/06 §03)."""


class DarkAnchorError(ValueError):
    """Raised on =zu: 'no Nubhel cognate — divers rarely leave coverage'
    (docs/06 §03)."""


class MissingDirectionalError(ValueError):
    """Raised for a motion verb without a depth directional: 'motion
    verbs are ungrammatical without one' (docs/06 §03)."""


# key -> (suffix form, gloss).  ó is the rounded reflex of stressed *-a.
MOODS: Dict[str, Tuple[str, str]] = {
    "plain": ("ó", "PLAIN"),
    "appr": ("im", "APPR"),
    "hearsay": ("ur", "HEARSAY"),
}

_MOOD_ALIASES = {
    "T": "plain", "ó": "plain", "-ó": "plain", "PLAIN": "plain",
    "T-": "appr", "T⁻": "appr", "im": "appr", "-im": "appr", "APPR": "appr",
    "T+": "hearsay", "T⁺": "hearsay", "ur": "hearsay", "-ur": "hearsay",
    "HEARSAY": "hearsay",
}

# every spelling of the seam-truth the rival language could ask for
_SEAM_TRUTH_KEYS = {"Ts", "T•", "T*", "eshe", "-eshe", "seam", "seam-true"}


def mood_morph(mood: str) -> Morph:
    if mood in _SEAM_TRUTH_KEYS:
        raise SeamTruthError(
            "*-eshe left no reflex: Nubhel cannot conjugate the seam-truth "
            "(docs/06 §03) — a diver narrating a crossing must borrow "
            "Sūchel; use code_switch()")
    key = _MOOD_ALIASES.get(mood, mood)
    if key not in MOODS:
        raise ValueError(f"unknown Nubhel mood {mood!r}; Nubhel kept three: "
                         f"{sorted(MOODS)}")
    form, gloss = MOODS[key]
    return Morph(form, gloss, MOOD, "-")


# ---------------------------------------------------------------------------
# SYSTEM 02 — the debt anchor & the signature

ANCHORS: Dict[str, Tuple[str, str]] = {
    "ka": ("ka", "BEAC"),   # beacon time — shared inheritance
    "mi": ("mi", "PROP"),   # proper time — shared inheritance
    "nu": ("nu", "DEEP"),   # deep time (from *nub): conversion owed
}


def anchor_morph(anchor: str) -> Morph:
    key = anchor.lstrip("=")
    if key == "zu":
        raise DarkAnchorError(
            "=zu has no Nubhel cognate — divers rarely leave coverage "
            "(docs/06 §03); the debt anchor is =nu")
    if key not in ANCHORS:
        raise ValueError(f"unknown Nubhel anchor {anchor!r}; the three are "
                         f"{sorted(ANCHORS)}")
    form, gloss = ANCHORS[key]
    return Morph(form, gloss, ANCHOR, "=")


# the counting row (docs/06 §04 'the counting test' + §03 mek-dok) —
# only the codex-attested numerals; the divers' formal signatures write
# larger debts in digits ('Mora, +212').
UNITS: Dict[int, str] = {1: "so", 4: "mek", 7: "ep", 10: "dok"}
_UNIT_GLOSS: Dict[str, str] = {"so": "one", "mek": "four", "ep": "seven",
                               "dok": "ten"}


def offset(n: int) -> str:
    """The offset numeral of the formal =nu register: '+so', '+mek-dok'.

    Decades compose unit + dok (mek-dok 'four-ten' = forty, docs/06
    §03).  Values the codex's counting row cannot spell raise — the
    attested fallback is the digit signature (:func:`signature`)."""
    if n in UNITS:
        return "+" + UNITS[n]
    if n % 10 == 0 and (n // 10) in UNITS and n > 10:
        return f"+{UNITS[n // 10]}-dok"
    raise ValueError(
        f"offset {n} is not spellable from the attested counting row "
        f"(docs/06 §04); formal signatures write digits: signature(name, n)")


def offset_gloss(n: int) -> str:
    """Interlinear gloss of the offset: +mek-dok = '+four-ten' (docs/06)."""
    form = offset(n)
    parts = form.lstrip("+").split("-")
    return "+" + "-".join(_UNIT_GLOSS[p] for p in parts)


def signature(name: str, n: int) -> str:
    """The offset signature: divers sign letters with their accrued
    cycles — 'Mora, +212': a life's dilation worn as a name-suffix."""
    return f"{name}, +{n}"


SIGNATURE_EXAMPLE = signature("Mora", 212)   # the codex's own (docs/06 §03)


def debt(n: int, cycles: bool = False) -> List[Word]:
    """The appended debt of a formal =nu clause: '+mek-dok' or
    '+so kodur' (with the unit word, docs/06 TEXT 03)."""
    words = [Word([Morph(offset(n), offset_gloss(n), PART)])]
    if cycles:
        words.append(Word.plain("kodur", "cycle"))
    return words


def sign_deep(clause_words: Sequence[Word], n: int,
              cycles: bool = False) -> List[Word]:
    """Formal register: a =nu clause appends the debt as a numeral —
    the offset signature.  Refuses a clause that is not deep-anchored."""
    verb = clause_words[-1]
    anchors = [m.form for m in verb.morphs if m.cat == ANCHOR]
    if anchors != ["nu"]:
        raise DarkAnchorError(
            "the offset signature belongs to the deep anchor: only a =nu "
            "clause declares a conversion owed (docs/06 §03)")
    return list(clause_words) + debt(n, cycles)


# ---------------------------------------------------------------------------
# SYSTEM 03 — five degrees of depth

# form -> (proto, meaning, gloss).  docs/06 §03: 'Where Sūchel has two
# directionals, Nubhel grades five.'
DIRECTIONALS: Dict[str, Tuple[str, str, str]] = {
    "len": ("*len-", "level; along, at this depth", "LEVEL"),
    "nub": ("*nub-", "down; a working descent", "DOWN"),
    "dolnub": ("*dol-nub", "pitward; a deep, committed dive", "PITWARD"),
    "ū": ("*hau", "up; surfaceward", "UP"),
    "ūtel": ("*hau-tel", "breach-up; an overshooting ascent", "BREACH-UP"),
}

# verbs of movement that demand a directional.  ōl 'to surface' is
# exempt: it incorporates its direction (*haw-ol- contains *hau 'up').
MOTION_VERBS = {"yed", "ron"}


def directional_word(form: str, gloss: Optional[str] = None) -> Word:
    if form not in DIRECTIONALS:
        raise ValueError(f"unknown depth directional {form!r}; the five are "
                         f"{sorted(DIRECTIONALS)}")
    return Word.particle(form, gloss if gloss is not None
                         else DIRECTIONALS[form][2])


# ---------------------------------------------------------------------------
# SYSTEM 04 — neks, the gap as courtesy

NEKS_PRAGMATICS = (
    "In Sūchel, ne marks what physics forbids narrating; in Nubhel, neks "
    "(*nex-, cluster kept) marks any interval your listener did not share "
    "— a returning diver summarizing years of away-time says it once and "
    "moves on. You do not narrate time your listener did not live. "
    "(docs/06 §03)")


def neks() -> Word:
    return Word.particle("neks", "GAP")


# ---------------------------------------------------------------------------
# pronouns & the verb/clause builders

PRONOUNS: Dict[str, str] = {
    "en": "1SG",
    "on": "3SG",        # *an- → D-4 (docs/06 §05)
    "enmai": "1PL.ENT",
}

COPULA = "ve"   # attested TEXT 01, against D-2's †be — see module docstring

TEMPLATE = "STEM – (ASPECT) – MOOD = ANCHOR"   # unchanged from Sūchel


def pronoun(form: str) -> Word:
    if form == "enmai":
        return Word([Morph("en", "1PL.ENT", STEM), Morph("mai", "", MAI)])
    return Word([Morph(form, PRONOUNS[form], STEM)])


def verb(stem: str, gloss: str, mood: str = "plain", anchor: str = "mi",
         pfv: bool = False) -> Word:
    """A finite Nubhel verb: STEM–(t)–MOOD=ANCHOR.

    >>> verb('yed', 'go', pfv=True).display()
    'yed-t-ó=mi'
    """
    morphs = [Morph(stem, gloss, STEM)]
    if pfv:
        morphs.append(Morph("t", "PFV", PFV, "-"))
    morphs.append(mood_morph(mood))
    morphs.append(anchor_morph(anchor))
    return Word(morphs)


def clause(subject: str, stem: str, gloss: str, mood: str = "plain",
           anchor: str = "mi", pfv: bool = False,
           directional: Optional[str] = None,
           allow_bare: bool = False) -> List[Word]:
    """SOV clause with the depth requirement enforced: a motion verb
    without a directional is ungrammatical (docs/06 §03) — unless
    ``allow_bare`` invokes TEXT 01's neks-licensed homecoming formula."""
    if stem in MOTION_VERBS and directional is None and not allow_bare:
        raise MissingDirectionalError(
            f"{stem!r} is a motion verb: ungrammatical without a depth "
            f"directional ({sorted(DIRECTIONALS)}) — fleet drill answers "
            f"run len? nub? dolnub? (docs/06 §03)")
    words = [pronoun(subject) if subject in PRONOUNS
             else Word.plain(subject, subject)]
    if directional is not None:
        words.append(directional_word(directional))
    words.append(verb(stem, gloss, mood, anchor, pfv))
    return words


# ---------------------------------------------------------------------------
# the code-switch rule


@dataclass
class CodeSwitch:
    """A Sūchel T• clause embedded mid-narration (docs/06 §03): 'a diver
    narrating a crossing must borrow Sūchel for the T• clause —
    mid-sentence, the rival's language appears exactly where the seam
    does. Enforced humility; on the page, a visible register shift.'"""

    words: List[Word]
    language: str = "Sūchel"
    note: str = ("letter the middle balloon in the Sūchel style: the "
                 "language shift is the seam (docs/06 TEXT 03)")

    def display(self) -> str:
        return " ".join(w.display() for w in self.words)

    def gloss(self) -> str:
        return "[SŪCHEL] " + " ".join(w.gloss() for w in self.words)


def code_switch(subject: str = "an", subject_gloss: str = "3SG",
                stem: str = "sū", stem_gloss: str = "cross",
                pfv: bool = True) -> CodeSwitch:
    """Build the borrowed Sūchel clause with core Word morphs directly —
    the rival's mood (-eshe), the rival's anchor (=zu), in the rival's
    color.  Default is the showpiece: an sū-t-eshe=zu."""
    morphs = [Morph(stem, stem_gloss, STEM)]
    if pfv:
        morphs.append(Morph("t", "PFV", PFV, "-"))
    morphs.append(Morph("eshe", "T•", MOOD, "-"))
    morphs.append(Morph("zu", "DARK", ANCHOR, "="))
    return CodeSwitch([Word([Morph(subject, subject_gloss, STEM)]),
                       Word(morphs)])


# ---------------------------------------------------------------------------
# the §03 example sentences, locked verbatim and rebuilt from the machinery


@dataclass(frozen=True)
class Example:
    display: str
    gloss: str
    translation: str
    note: str = ""


EXAMPLES: Tuple[Example, ...] = (
    Example("on nub yed-ó=mi.",
            "3SG DOWN go-PLAIN=PROP",
            '"She went down."',
            "Witnessed, own-clock. The everyday music of the fleet."),
    Example("en ōl-t-ó=nu, +mek-dok.",
            "1SG surface-PFV-PLAIN=DEEP, +four-ten",
            '"I surfaced — in dive-time; forty owed."',
            "Divers sign letters this way: Mora, +212 — a life's dilation "
            "worn as a name-suffix."),
    Example("en yed-t-ó=mi. neks. en len ve-ó=ka.",
            "1SG go-PFV-PLAIN=PROP · GAP · 1SG level be-PLAIN=BEAC",
            '"I left. — . I am here, level, in shared time."',
            "The homecoming formula: the away-years folded into one held "
            "mark, out of kindness."),
)
