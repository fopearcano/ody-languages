"""Sūchel morphosyntax — the generative grammar of the Crossing-Speech.

Implements docs/01 §04 (nouns; the verb template STEM-(ASPECT)-MOOD=ANCHOR),
docs/01 §05 (the four systems: veridical moods, temporal anchors, depth
directionals, the gap particle *ne*), and the three small systems the
phrasebook's intro makes explicit (docs/02): the beatless imperative, the
vocative particle *ō*, the final question particle *vu*, and the accusative
clitic *-(e)n*.

Everything returns core :class:`~odylang.word.Word` objects, so stress, IPA
and the docs/04 rhythm notation fall out of the four-rule algorithm for
free.  The only stress datum ever passed in is the documented lexical
exception (the dative hail *ish-ol* [iˈʃol], docs/02 §01 / docs/04 line 01),
via ``stress_override``.

Documented wrinkles encoded here, each with its source:

* **Separator spelling is lexical, not phonological.**  The codices write
  ``enmai``/``ishmai`` (docs/01 §04, docs/02 §02) and ``Sōrnmai``/``Turmai``
  (docs/02 §12, §25) solid, but ``nav-mai`` (docs/01 §04), ``nexath-mai``
  (docs/02 §28) and ``ish-mai`` (docs/01 §07 text 03) hyphenated — so the
  constructors take ``mai_sep``.  The gloss follows the spelling: solid
  joins with '.' (``2SG.ENT``, docs/02 §02), hyphenated with '-'
  (``2SG-ENT``, docs/01 §07 text 03); both are attested and both are
  reproduced.
* **The accusative is written solid** (``ishen``, ``enen`` — docs/02 §04,
  §25 and the intro's "en → enen; ish → ishen") and glossed with '.'
  (``2SG.ACC``); the other cases attach with '-'.  Allomorphy of *-(e)n*:
  ``-en`` after a consonant, ``-n`` after a vowel.
* **The entangled first person is inherently crew-plural**: *enmai* is
  glossed ``1PL.ENT`` in every attestation although its stem is *en*
  '1SG' — "crew-we, the entangled we" (docs/01 §04).
* **System 03 (docs/01 §05): motion verbs demand a depth satellite** —
  *nuv* 'down-tower' or *hau* 'surfaceward' (and the death-formula's *zu*
  'adrift', docs/02 §29, patterns with them).  :func:`verb` and
  :func:`imperative` enforce this for the attested motion stems (*jed*,
  *ran*); the documented bare uses — the casual leave-taking *en jed-a=mi*
  (docs/02 §07) and the intro's citation forms *jed-u! / vo jed-u!*
  (docs/02) — must say so explicitly with ``bare_motion_ok=True``.
* **Mood F is periphrastic**: *vo* + plain T (docs/01 §05, "F | vo + -a"),
  so :func:`verb` refuses ``mood='F'`` and :func:`false_verb` returns the
  particle-plus-verb pair instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .suchel import LEXICON
from .word import (ANCHOR, CASE, IMP, MAI, MOOD, PART, PFV, PLURAL,
                   STEM, STEM2, Morph, Word)

# ---------------------------------------------------------------------------
# paradigm tables (docs/01 §04–05, docs/02 intro)

#: veridical moods (docs/01 §05 System 01): key -> (suffix, gloss).
MOODS: Dict[str, Tuple[str, str]] = {
    "T": ("a", "T"),        # classically true; settled
    "T-": ("im", "T⁻"),     # true-as-approached (IR)
    "T+": ("ur", "T⁺"),     # held-from-above, unaccredited (UV)
    "Ts": ("eshe", "T•"),   # seam-true; self-dual
}
_MOOD_KEY = {**{k: k for k in MOODS}, "T⁻": "T-", "T⁺": "T+", "T•": "Ts"}

#: temporal anchor clitics (docs/01 §05 System 02): form -> gloss.
ANCHORS: Dict[str, str] = {"ka": "BEAC", "mi": "PROP", "zu": "DARK"}

#: case clitics (docs/01 §04): name -> (form, gloss, separator).
#: ACC form is allomorphic -(e)n and computed in :func:`_case_morph`.
CASES: Dict[str, Tuple[Optional[str], str, str]] = {
    "ACC": (None, "ACC", ""),
    "GEN": ("en", "GEN", "-"),
    "DAT": ("ol", "DAT", "-"),
    "LOC": ("eth", "LOC", "-"),
}

#: the grammatical particles (docs/01 §04–05, docs/02 intro).
PARTICLES: Dict[str, str] = {
    "vo": "NEG",   # negation, pre-verbal (docs/01 §04)
    "vu": "Q",     # final question particle (docs/02 intro)
    "ō": "VOC",    # vocative (docs/02 intro)
    "ne": "GAP",   # the gap in syntax (docs/01 §05 System 04)
    "nuv": "DOWN", # down-tower (docs/01 §05 System 03)
    "hau": "UP",   # surfaceward
}

#: attested motion stems requiring a depth satellite (docs/01 §05 System 03:
#: "Verbs of movement are ungrammatical without a depth satellite").
MOTION_STEMS = frozenset({"jed", "ran"})

#: licit satellites for a motion verb: the two depth directionals, plus
#: *zu* 'adrift' as in the death formula *an zu jed-t-a=mi* (docs/02 §29).
DIRECTIONALS: Dict[str, str] = {"nuv": "DOWN", "hau": "UP", "zu": "adrift"}

_PERSON = {1: ("en", "1SG"), 2: ("ish", "2SG"), 3: ("an", "3SG")}
_PERSON_PL = {1: "1PL", 2: "2PL", 3: "3PL"}

_VOWEL_FINAL = "aeiouāēīōū"


class MotionSatelliteError(ValueError):
    """A motion verb was built without its depth satellite (docs/01 System 03)."""


# ---------------------------------------------------------------------------
# word assembly


def _autogloss(morphs: Sequence[Morph]) -> str:
    """Word-level gloss with the codices' joiners.

    ``=`` before anchors, ``-`` at hyphenated seams, ``.`` at solid nominal
    seams (2SG.ACC, 1PL.ENT, crosser.PL, dark.time) — except the imperative,
    which the codex glosses with ``-`` even when written solid
    (*oshu* 'swallow-IMP', docs/02 §18).
    """
    out = ""
    for m in morphs:
        if not m.gloss:
            continue
        if out:
            if m.sep == "=":
                out += "="
            elif m.sep == "-" or m.cat == IMP:
                out += "-"
            else:
                out += "."
        out += m.gloss
    return out


def _word(morphs: Sequence[Morph], stress_override: Optional[int] = None) -> Word:
    # core Word syllabification is seam-aware (nuv+ran [ˈnuv.ran], never
    # *[ˈnu.vran], while vel+osh still resyllabifies to [ˈve.loʃ])
    return Word(list(morphs), gloss_join=_autogloss(morphs),
                stress_override=stress_override)


def _case_morph(case: str, base_form: str) -> Morph:
    form, gloss, sep = CASES[case]
    if form is None:  # ACC -(e)n: en -> enen, ish -> ishen (docs/02 intro)
        form = "n" if base_form[-1].lower() in _VOWEL_FINAL else "en"
    return Morph(form, gloss, CASE, sep)


# ---------------------------------------------------------------------------
# nominals


def noun(stem: str, *, gloss: str = "", second: Optional[str] = None,
         second_sep: str = "", plural: bool = False, entangled: bool = False,
         mai_sep: str = "-", case: Optional[str] = None,
         stress_override: Optional[int] = None) -> Word:
    """A Sūchel noun (docs/01 §04): number, case, entangled possession.

    ``second`` builds a compound (rule-1 stress: *zukad*, *jelvos*);
    ``entangled`` adds *-mai* (spelled per ``mai_sep``, see module notes);
    ``case`` is one of ACC/GEN/DAT/LOC.  ``stress_override`` exists only
    for documented lexical exceptions.
    """
    morphs = [Morph(stem, gloss, STEM)]
    if second is not None:
        morphs.append(Morph(second, "", STEM2, second_sep))
    if plural:
        morphs.append(Morph("i", "PL", PLURAL, ""))
    if entangled:
        morphs.append(Morph("mai", "ENT", MAI, mai_sep))
    if case is not None:
        morphs.append(_case_morph(case, "".join(m.form for m in morphs)))
    return _word(morphs, stress_override)


def compound(first: str, second: str, *, sep: str = "",
             gloss: Optional[str] = None,
             glosses: Optional[Tuple[str, str]] = None) -> Word:
    """A two-member compound (rule-1 stress on the first member, docs/04 §02).

    Either one unit ``gloss`` on the whole (*jelvos* 'seam.scar') or
    per-member ``glosses`` (*vo-tem* 'NEG-pattern', *eshe-ver*
    'seam.true-truth').
    """
    g1, g2 = ("", "")
    if glosses is not None:
        g1, g2 = glosses
    elif gloss is not None:
        g1 = gloss
    return _word([Morph(first, g1, STEM), Morph(second, g2, STEM2, sep)])


def pronoun(person: int, *, plural: bool = False, entangled: bool = False,
            case: Optional[str] = None, mai_sep: str = "",
            stress_override: Optional[int] = None) -> Word:
    """en 1SG / ish 2SG / an 3SG; plural *eni*; entangled *enmai*, *ishmai*.

    *enmai* glosses 1PL.ENT (crew-we, docs/01 §04) although its stem is
    *en*; *eni* glosses plain 1PL (docs/02 §16).  Entangled pronouns are
    written solid by default (``mai_sep=''``); docs/01 §07 text 03 spells
    *ish-mai*, built with ``mai_sep='-'``.  The pronoun-with-*-mai*-under-
    case stress shift (*ishmai-ol* [iʃˈmai.ol]) is automatic in the core.
    """
    form, gloss = _PERSON[person]
    if entangled and person == 1:
        gloss = _PERSON_PL[1]
    elif plural:
        gloss = _PERSON_PL[person]
    morphs = [Morph(form, gloss, STEM)]
    if plural and not entangled:
        morphs.append(Morph("i", "", PLURAL, ""))
    if entangled:
        morphs.append(Morph("mai", "ENT", MAI, mai_sep))
    if case is not None:
        morphs.append(_case_morph(case, "".join(m.form for m in morphs)))
    return _word(morphs, stress_override)


# ---------------------------------------------------------------------------
# particles and directionals


def particle(form: str, gloss: Optional[str] = None) -> Word:
    """A grammatical particle; gloss defaults from :data:`PARTICLES`."""
    if gloss is None:
        gloss = PARTICLES[form]
    return Word([Morph(form, gloss, PART)])


def directional(name: str) -> Word:
    """A depth satellite: *nuv* DOWN, *hau* UP (docs/01 §05 System 03) —
    plus *zu* 'adrift' of the death formula (docs/02 §29)."""
    return particle(name, DIRECTIONALS[name])


def bare_anchor(anchor: str) -> Word:
    """A stranded anchor clitic, as in *…, vo =ka* (docs/01 §05 System 02)."""
    return Word([Morph("=" + anchor, ANCHORS[anchor], ANCHOR)],
                gloss_join="=" + ANCHORS[anchor])


def vocative(word: Word) -> List[Word]:
    """*ō* + noun: *ō mān!*, *ō Sōrnmai* (docs/02 intro)."""
    return [particle("ō"), word]


# ---------------------------------------------------------------------------
# verbs


def _check_motion(stem: str, directional_name: Optional[str],
                  bare_motion_ok: bool) -> None:
    if stem in MOTION_STEMS and not bare_motion_ok:
        if directional_name not in DIRECTIONALS:
            raise MotionSatelliteError(
                f"motion verb {stem!r} needs a depth satellite "
                f"({'/'.join(DIRECTIONALS)}) — docs/01 System 03: adults "
                f"always know which way the tower lies.  Pass "
                f"directional=... (see motion_verb()) or, for the attested "
                f"bare idioms, bare_motion_ok=True.")


def verb(stem: str, mood: str, anchor: str, *, pfv: bool = False,
         gloss: str = "", directional: Optional[str] = None,
         bare_motion_ok: bool = False,
         stress_override: Optional[int] = None) -> Word:
    """A finite verb: STEM-(PFV *-t-*)-MOOD=ANCHOR (docs/01 §04).

    ``mood`` is T / T- / T+ / Ts (unicode aliases T⁻ T⁺ T• accepted);
    ``anchor`` is ka / mi / zu.  Both are obligatory — "you cannot speak
    without taking a position on the truth" (docs/01 §05).  ``directional``
    declares the depth satellite standing in the clause (built separately;
    see :func:`motion_verb`).
    """
    if mood == "F":
        raise ValueError("F (false) is periphrastic: particle vo + plain T "
                         "(docs/01 §05) — build it with false_verb()")
    key = _MOOD_KEY.get(mood)
    if key is None:
        raise ValueError(f"unknown mood {mood!r}; expected one of "
                         f"{sorted(_MOOD_KEY)}")
    _check_motion(stem, directional, bare_motion_ok)
    suffix, mood_gloss = MOODS[key]
    morphs = [Morph(stem, gloss, STEM)]
    if pfv:
        morphs.append(Morph("t", "PFV", PFV, "-"))
    morphs.append(Morph(suffix, mood_gloss, MOOD, "-"))
    morphs.append(Morph(anchor, ANCHORS[anchor], ANCHOR, "="))
    return _word(morphs, stress_override)


def motion_verb(stem: str, direction: str, mood: str, anchor: str, *,
                pfv: bool = False, gloss: str = "") -> Tuple[Word, Word]:
    """A motion verb with its obligatory satellite, as the pair of words
    that stand in the clause: (*nuv*, *ran-eshe=mi*) — docs/01 System 03."""
    return (directional(direction),
            verb(stem, mood, anchor, pfv=pfv, gloss=gloss,
                 directional=direction))


def false_verb(stem: str, anchor: str, *, pfv: bool = False, gloss: str = "",
               **kw) -> Tuple[Word, Word]:
    """Mood F: the particle *vo* + the plain-T verb (docs/01 §05:
    "F | vo + -a | false (negated plain)")."""
    return (particle("vo"), verb(stem, "T", anchor, pfv=pfv, gloss=gloss, **kw))


def imperative(stem: str, gloss: str = "", *, solid: bool = False,
               directional: Optional[str] = None,
               bare_motion_ok: bool = False) -> Word:
    """Bare stem + *-u*: no mood, no anchor — non-assertive (docs/02 intro).

    Beatless by the rule-4 corollary (docs/04 §02).  Normally hyphenated
    (*tan-u*); the denominal *oshu* is written solid (docs/02 §18),
    hence ``solid``.
    """
    _check_motion(stem, directional, bare_motion_ok)
    morphs = [Morph(stem, gloss, STEM),
              Morph("u", "IMP", IMP, "" if solid else "-")]
    return _word(morphs)


def prohibitive(stem: str, gloss: str = "", **kw) -> Tuple[Word, Word]:
    """*vo* + imperative: *vo jed-u!* "don't go!" (docs/02 intro)."""
    return (particle("vo"), imperative(stem, gloss, **kw))


# ---------------------------------------------------------------------------
# sentences


@dataclass
class Break:
    """A medial juncture carried as data.

    The codex is inconsistent about junctures: some commas get a raised dot
    in the IPA (docs/02 §05, §16) and some do not (§08, §12, §25, §33, §35);
    the gloss line sometimes mirrors the mark (§15 '·', catechism ','),
    sometimes not (§05).  So each break records its own three surfaces.
    """
    after: int        # index of the word this break follows
    text: str = ","   # mark in the romanized line ('', ',', '.')
    ipa: str = ""     # '·' where the codex IPA shows a raised dot
    gloss: str = ""   # ',' or '·' where the codex gloss shows a mark


@dataclass
class Sentence:
    """A line of Sūchel: Words plus punctuation and junctures as data."""
    words: List[Word]
    punct: str = "."
    breaks: List[Break] = field(default_factory=list)
    gap_final: bool = False   # docs/04 line 38: trailing '|' (the gap/rest)

    def _marks(self) -> Dict[int, Break]:
        return {b.after: b for b in self.breaks}

    def text(self) -> str:
        """The romanized line, exactly as the codex letters it."""
        marks = self._marks()
        parts = []
        for i, w in enumerate(self.words):
            t = w.display()
            b = marks.get(i)
            if b is not None and b.text:
                t += b.text
            parts.append(t)
        return " ".join(parts) + self.punct

    def gloss_line(self) -> str:
        """The Leipzig-style morpheme gloss line."""
        marks = self._marks()
        parts = []
        for i, w in enumerate(self.words):
            g = w.gloss()
            b = marks.get(i)
            if b is not None and b.gloss:
                g += b.gloss if b.gloss == "," else " " + b.gloss
            parts.append(g)
        return " ".join(parts)

    def ipa(self) -> str:
        """Word IPAs joined with spaces; ' · ' at breaks that carry one."""
        marks = self._marks()
        parts = []
        for i, w in enumerate(self.words):
            p = w.ipa()
            b = marks.get(i)
            if b is not None and b.ipa:
                p += " " + b.ipa
            parts.append(p)
        return " ".join(parts)

    def syl_line(self) -> List[str]:
        """The docs/04 rhythm array: per-word syl_beats(), '/' between
        words, '|' for the gap-mark."""
        out: List[str] = []
        for i, w in enumerate(self.words):
            if i:
                out.append("/")
            out.extend(w.syl_beats())
        if self.gap_final:
            out.append("|")
        return out


# ---------------------------------------------------------------------------
# lexicon backing


def lexicon_has(stem: str) -> bool:
    """True if a stem is backed by the codex lexicon (docs/01 §06, docs/02 §F),
    checking the affix ('-mai', '-eshe', '-u') and capitalization variants."""
    return any(k in LEXICON for k in (stem, stem.lower(), "-" + stem,
                                      "-" + stem.lower()))
