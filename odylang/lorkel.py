"""Lorkel — working Old Pelagic, the tongue of the Irrationals (docs/05 §05).

Old Pelagic survives twice over, and the difference between its two hands
is the whole politics of truth in this universe:

* **Custodian 01 — the Assembly**: liturgical Pelgar, frozen and
  performative — the grammatical claim that truth has not moved since
  before the seam.  Doxa's instrument; creed «tutto è connesso con tutto».
  Sacred precisely because it is blind to the new world: it cannot
  conjugate a crossing, so in it no crossing can contradict doctrine.
* **Custodian 02 — the Wolori**: Lorkel (*lor-kel, "ratio-speech"), the
  Ricercatori del Limite's living technical register, extended by coinage
  the way Neo-Latin coined *oxygenium*.  Same corpus, opposite use: the
  Assembly embalmed the ancestor; the Wolori keep it employed.
* **Custodian 00 — NOTATION**: the zero-tongue.  Above Lorkel sits the
  order's true liturgy, mathematics itself — no moods, no anchors, no
  native speakers; the only medium in which T• can be written without
  being sworn.

Why the moodless tongue is the scientific one (docs/05 §05): in Sūchel
every finite verb must swear a mood, so a conjecture is grammatical
perjury; Old Pelagic predates the seam — no veridical moods, no anchors,
no *ne* — the only tongue in which a proposition can be entertained
without being asserted.  Hence the mirrored joke: the Assembly keeps Old
Pelagic because it cannot describe the seam; the Wolori keep it for the
same reason.

Lorkel grows by :func:`coin` — compounding proto-roots with NO sound
changes applied (the ancestor's morphology, employed for post-seam
physics).  The eight standard Neo-Pelagic terms live in
:data:`NEO_PELAGIC`, each carrying the codex's Sūchel-reflex column: only
*gel-* → jel is an engine-derivable cognate; the rest are different
formations (kaplor~kav, pewlor~pevlor, gelwer~eshe-ver, turom~Turmai,
nexlor~ne, suwath~sūath) or have no reflex at all (wolor), so the
relationship is recorded as data, not derivation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .proto import citation

# ---------------------------------------------------------------------------
# coinage


def coin(*parts: str) -> str:
    """Neo-Pelagic coinage: compound proto-roots with no sound changes —
    the classical citation form of the joined parts.

    >>> coin('*kap-', '*lor-')
    'kaplor'
    >>> coin('*suw-', '*-ath')
    'suwath'
    """
    body = "-".join(p.strip().lstrip("*").strip("-")
                    for p in parts if p.strip("*- "))
    return citation("*" + body)


# ---------------------------------------------------------------------------
# the eight standard terms (docs/05 §05 table)

# reflex_kind:
#   'cognate'   — the Sūchel column is the same proto-form run through
#                 SC-1..7 (engine-checkable via odylang.suchel)
#   'formation' — the Sūchel column is a different formation; the reflex
#                 exists in suchel.LEXICON and the relationship is data
#   'none'      — the fleets never needed the noun


@dataclass
class NeoTerm:
    form: str                       # the Lorkel coinage
    formation: Tuple[str, ...]      # proto parts fed to coin()
    meaning: str                    # the codex's meaning column
    suchel_reflex: Optional[str]    # the codex's comparison column (form)
    reflex_kind: str                # 'cognate' | 'formation' | 'none'
    reflex_note: str = ""           # the codex's own aside, verbatim

    def coined(self) -> str:
        return coin(*self.formation)


_T: List[NeoTerm] = [
    NeoTerm("gel", ("*gel-",),
            "the seam 𝔍 (unshifted)", "jel", "cognate"),
    NeoTerm("kaplor", ("*kap-", "*lor-"),
            '"the holding-rule" — the curvature limit Κ as law',
            "kav", "formation",
            reflex_note="the fleets' kav is *kap-a, not a -lor compound"),
    NeoTerm("pewlor", ("*pew-", "*lor-"),
            '"five-rule" — the logic ΛL', "pevlor", "formation",
            reflex_note="pevlor (its regular reflex) — the fleets compound "
                        "the daughter forms pev + lor"),
    NeoTerm("gelwer", ("*gel-", "*wer-"),
            '"seam-truth" — the value T•', "eshe-ver", "formation",
            reflex_note="the fleets lexicalized the mood suffix instead"),
    NeoTerm("turom", ("*tur-", "*om-"),
            '"all-tower" — the OCT entire', "Turmai", "formation",
            reflex_note="(the fleets add kinship)"),
    NeoTerm("nexlor", ("*nex-", "*lor-"),
            '"gap-law" — the principle that the crossing interval admits '
            "no predicate", "ne", "formation",
            reflex_note="(the fleets keep only the particle)"),
    NeoTerm("suwath", ("*suw-", "*-ath"),
            '"a crossing" — the event, stated flat, unmooded',
            "sūath", "formation",
            reflex_note="the fleets build sūath on the irregular verb sū"),
    NeoTerm("wolor", ("*wo-", "*lor-"),
            '"the un-ratioed" — an incommensurable; a truth outside the '
            "five moods", None, "none",
            reflex_note="no reflex — the fleets never needed the noun"),
]

NEO_PELAGIC: Dict[str, NeoTerm] = {t.form: t for t in _T}


# ---------------------------------------------------------------------------
# the custodians (docs/05 §05)


@dataclass
class Custodian:
    number: str
    name: str
    register: str
    mode: str
    description: str


CUSTODIANS: Dict[str, Custodian] = {
    "assembly": Custodian(
        "01", "the Assembly", "Liturgical Pelgar",
        "frozen — performed, not lived",
        "the grammatical claim that truth has not moved since before the "
        "seam; Doxa's instrument, the tongue of the consensus, whose creed "
        "is «tutto è connesso con tutto» — sacred precisely because it is "
        "blind to the new world"),
    "wolori": Custodian(
        "02", "the Wolori", "Lorkel — working Old Pelagic",
        "living, coining, moodless by design",
        '*lor-kel, "ratio-speech": the Irrationals\' living technical '
        "register, extended by coinage the way Neo-Latin coined oxygenium; "
        "the Assembly embalmed the ancestor, the Wolori keep it employed"),
    "notation": Custodian(
        "00", "NOTATION", "the zero-tongue",
        "no moods, no anchors, no native speakers",
        "mathematics itself — the order's true liturgy; the only medium in "
        "which T• can be written without being sworn"),
}

# notation-names, exactly as the codex prints them: pronounced differently
# on every world, written identically on all of them
NOTATION_NAMES: Tuple[str, ...] = ("√2", "π", "φ", "√−1", "z")


# ---------------------------------------------------------------------------
# the Wolori themselves


# *wo-lor-i "the un-ratioed" — Doxa's sneer worn as a badge ("Irrationals"
# being merely its translation); like √2 in a Pythagorean hand, the order
# is named for what escapes ratio.
ENDONYM = {
    "form": "Wolori",
    "proto": "*wo-lor-i",
    "gloss": "the un-ratioed",
    "note": "Doxa's sneer worn as a badge; 'Irrationals' is merely its "
            "translation — Bone's uniform bears «√2» for exactly this reason",
}

# the scholars' tell (docs/05 §01 & §05): a Wolori lector says the
# unshifted proto-forms — the order is audible in a single syllable
SHIBBOLETH: Tuple[Tuple[str, str], ...] = (
    ("gel", "*gel-"),
    ("kel", "*kel"),
    ("Suwkel", "*suw-kel"),
)

# open proposal (docs/05 §05) — explicitly NOT yet canon
OPEN_PROPOSAL = {
    "canon": False,
    "proposal": "the Wolori motherhouse on old ground — Mars, at Pelaghar, "
                '"the Deephold"',
    "rationale": "it would make Rudgar their cradle vernacular, which fits "
                 "the phonology beautifully: the conservative sister that "
                 "kept *w and *h is the closest living tongue to the "
                 "ancestor, so Mars-born lectors read Old Pelagic with the "
                 "least accent",
    "status": "confirm or relocate as the story needs",
}
