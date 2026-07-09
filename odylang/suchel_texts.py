"""The Sūchel texts: docs/01 §07 (log, catechism, ne-liturgy) + the §05 Κ5
showpieces (Absolute Verdict, Madman's Theorem, Tragic Truth).

Every sentence is built through :mod:`odylang.suchel_grammar` — the module
carries only translations and abridged codex commentary as data; the
romanization and Leipzig glosses are generated and locked by
tests/test_suchel_texts.py against docs/01.

Consistency notes (readings chosen where the codex wavers, per the more
attested variant):

* The Absolute Verdict's gloss line in docs/01 §05 spells the beacon
  anchor ``=BEACON`` once; every other gloss in docs/01 and all of docs/02
  write ``=BEAC`` (about a dozen attestations), so ``BEAC`` is used here.
* docs/01 §07 text 03 writes the entangled 2SG *ish-mai* (glossed
  ``2SG-ENT``) where docs/02 §02 writes *ishmai* (``2SG.ENT``); spelling
  and gloss are lexical data (``mai_sep``), and each text reproduces its
  own source exactly.
* The catechism's question line carries its comma into the gloss
  (``endure-T=BEAC, NEG``) — unlike most phrasebook commas — so the mark
  is per-break data (:class:`~odylang.suchel_grammar.Break`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .suchel_grammar import (Break, Sentence, Word, false_verb, noun,
                             particle, pronoun, verb)


@dataclass
class Passage:
    """One glossed line of a text."""
    sentence: Sentence
    translation: str


@dataclass
class Text:
    key: str
    title: str
    lines: List[Passage]
    commentary: str      # abridged from docs/01 §07


@dataclass
class Showpiece:
    """One of the three Κ5 conjugations (docs/01 §05)."""
    key: str
    title: str
    attribution: str
    sentence: Sentence
    translation: str
    commentary: str      # abridged from docs/01 §05


def _n(form: str, gloss: str) -> Word:
    return Word.plain(form, gloss)


def _gap() -> Passage:
    return Passage(Sentence([particle("ne")]), "—")


# ---------------------------------------------------------------------------
# docs/01 §07 — the three texts


PILOTS_LOG = Text(
    key="pilots_log",
    title="A pilot's log, after a crossing",
    lines=[
        Passage(Sentence([pronoun(1, entangled=True), _n("kad", "beacon"),
                          noun("tel", case="LOC", gloss="three"),
                          verb("sū", "Ts", "ka", pfv=True, gloss="cross")]),
                "We crossed at the third beacon."),
        _gap(),
        Passage(Sentence([pronoun(1, entangled=True),
                          verb("hōl", "Ts", "zu", pfv=True, gloss="surface")]),
                "We surfaced, in dark time."),
    ],
    commentary="Three sentences tell the whole voyage through grammar "
               "alone: the crossing seam-true, the departure =ka, the "
               "return =zu — and between them the mark for the interval "
               "that never became memory. A censor could reconstruct the "
               "flight plan from the morphology.",
)


CATECHISM = Text(
    key="catechism",
    title="Catechism, with one heretical answer",
    lines=[
        Passage(Sentence([_n("tem", "pattern"),
                          noun("kav", case="LOC", gloss="limit"),
                          verb("dur", "T", "ka", gloss="endure"),
                          particle("vo")],
                         punct="?", breaks=[Break(2, ",", gloss=",")]),
                "Does a pattern endure at the limit — no? "
                "(the catechist, expecting the doctrinal denial)"),
        Passage(Sentence([particle("vo"), verb("dur", "T", "ka", gloss="endure"),
                          noun("somath", case="GEN", gloss="assembly"),
                          noun("ver", case="LOC", gloss="truth")],
                         breaks=[Break(1, ",", gloss=",")]),
                "It does not endure — in the Assembly's truth. "
                "(the correct answer)"),
        Passage(Sentence([verb("dur", "Ts", "zu", gloss="endure")]),
                "It endures — seam-true, in the dark. "
                "(the pupil who will not pass)"),
    ],
    commentary="The pupil's heresy is two morphemes long: -eshe for -a, "
               "=zu for =ka. Doctrine and its undoing differ by a "
               "conjugation — the entire Κ5 controversy, miniaturized "
               "into a classroom.",
)


NE_LITURGY = Text(
    key="ne_liturgy",
    title="Ne-liturgy, for the unreturned",
    lines=[
        Passage(Sentence([noun("sīl", plural=True, gloss="crosser"),
                          verb("sū", "Ts", "mi", gloss="cross")]),
                "The crossers cross, by their own clocks."),
        _gap(),
        Passage(Sentence([_n("kad", "beacon"), _n("vel", "nothing"),
                          verb("ver", "T", "ka", gloss="speak.true")]),
                "The beacon vouches for nothing."),
        _gap(),
        Passage(Sentence([pronoun(1, entangled=True),
                          pronoun(2, entangled=True, mai_sep="-"),
                          verb("tel", "T-", "zu", gloss="reach")]),
                "We reach toward you — approaching-true, in the dark."),
    ],
    commentary="The mourning form for those lost past coverage; every "
               "second line is the gap-mark — grief structured as the "
               "thing it grieves. The last verb is T⁻, the mood of a "
               "limit neared from below, and the entangled -mai on 'you' "
               "declares the dead still possessed as kin.",
)


TEXTS: List[Text] = [PILOTS_LOG, CATECHISM, NE_LITURGY]


# ---------------------------------------------------------------------------
# docs/01 §05 — the Κ5 showpiece: one sentence, three moods


def _k5(verb_words) -> Sentence:
    return Sentence([_n("tem", "pattern"),
                     noun("kav", case="LOC", gloss="limit"), *verb_words])


ABSOLUTE_VERDICT = Showpiece(
    key="absolute_verdict",
    title="The Absolute Verdict",
    attribution="Pelagian Assembly · doctrine",
    sentence=_k5(false_verb("dur", "ka", gloss="endure")),
    translation="No pattern endures at the limit.",
    commentary="Plain T, beacon-anchored: settled truth in shared time. "
               "The audacity is grammatical: doctrine claims "
               "network-verifiable knowledge of the one event no beacon "
               "has ever witnessed.",
)

MADMANS_THEOREM = Showpiece(
    key="madmans_theorem",
    title="The Madman's Theorem",
    attribution="the mythical ship · heresy",
    sentence=_k5([verb("dur", "T+", "zu", gloss="endure")]),
    translation="A pattern endures at the limit",
    commentary="T⁺, dark-anchored: held-from-above, in time no one "
               "shares. The grammar itself brands the claim unaccredited "
               "— to even say the theorem is to conjugate yourself a "
               "crank.",
)

TRAGIC_TRUTH = Showpiece(
    key="tragic_truth",
    title="The Tragic Truth",
    attribution="what actually happens · unsayable-as-fact",
    sentence=_k5([verb("dur", "Ts", "zu", gloss="endure")]),
    translation="A pattern endures — seam-true — in dark time.",
    commentary="The only honest conjugation, and the trap closes: T• is "
               "self-dual, so the sentence and its negation have the same "
               "value. The epistemic trap is not in the debate — it is in "
               "the verb.",
)

K5: List[Showpiece] = [ABSOLUTE_VERDICT, MADMANS_THEOREM, TRAGIC_TRUTH]
