"""The three Nubhel texts of docs/06 §06 — the deep-speech breathing.

Each line stores the codex's careful-hand spelling, interlinear gloss
and translation verbatim, plus the same sentence rebuilt from
morpheme-structured :class:`~odylang.word.Word` objects (so stress, IPA
and morphology all replay).  TEXT 02's Sūchel line and TEXT 03's
borrowed T• clause are built with core Word morphs directly — the
register shift is data, not prose.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .word import ANCHOR, CASE, MAI, MOOD, STEM, Morph, Word
from . import nubhel_grammar as G

# ---------------------------------------------------------------------------
# structure


@dataclass(frozen=True)
class Line:
    language: str            # 'Nubhel' | 'Sūchel'
    display: str             # verbatim codex spelling, punctuation kept
    gloss: str               # verbatim interlinear gloss
    translation: str         # verbatim codex translation
    words: Tuple[Word, ...]  # the same line, morph by morph

    def words_display(self) -> str:
        return " ".join(w.display() for w in self.words)


@dataclass(frozen=True)
class Text:
    id: str
    title: str
    jp: str
    lines: Tuple[Line, ...]
    commentary: str


_PUNCT = str.maketrans("", "", ".,—·")


def strip_punct(display: str) -> str:
    """Reduce a codex line to its word stream (for locking words against
    the verbatim spelling): drop . , — · and collapse spaces."""
    return " ".join(display.translate(_PUNCT).split())


# ---------------------------------------------------------------------------
# shared word builders

def _en() -> Word:
    return G.pronoun("en")


def _on() -> Word:
    return G.pronoun("on")


# ---------------------------------------------------------------------------
# TEXT 01 — A DIVER'S HOMECOMING 帰還

TEXT_01 = Text(
    id="TEXT 01",
    title="A DIVER'S HOMECOMING",
    jp="帰還",
    lines=(
        Line("Nubhel",
             "en yed-t-ó=mi. neks.",
             "1SG go-PFV-PLAIN=PROP · GAP",
             "I left. — .",
             # the codex's own bare yed: the following neks licenses it
             tuple(G.clause("en", "yed", "go", pfv=True, anchor="mi",
                            allow_bare=True)) + (G.neks(),)),
        Line("Nubhel",
             "en len ve-ó=ka, +mek-dok kodur.",
             "1SG level be-PLAIN=BEAC · +four-ten cycle",
             "I am here, level, in shared time — forty cycles owed.",
             (_en(), G.directional_word("len", "level"),
              G.verb(G.COPULA, "be", anchor="ka"))
             + tuple(G.debt(40, cycles=True))),
    ),
    commentary=(
        "The whole determinate regime in two lines: the away-years folded "
        "into one neks out of courtesy, the return re-anchored to the "
        "beacon, and the dilation declared as a number. Where a crosser's "
        "homecoming ends in a question no arithmetic settles, a diver's "
        "ends in an invoice."),
)


# ---------------------------------------------------------------------------
# TEXT 02 — THE PARALLEL SENTENCE — HALF-UNDERSTANDING 対訳

def _suchel_parallel_words() -> Tuple[Word, ...]:
    """The Sūchel line, built with core Word morphs directly."""
    return (
        Word([Morph("en", "1PL.ENT", STEM), Morph("mai", "", MAI)]),
        Word([Morph("nav", "ship", STEM), Morph("mai", "ENT", MAI, "-")]),
        Word.particle("nuv", "DOWN"),
        Word([Morph("jed", "go", STEM), Morph("a", "T", MOOD, "-"),
              Morph("mi", "PROP", ANCHOR, "=")]),
    )


def _nubhel_parallel_words() -> Tuple[Word, ...]:
    return (
        G.pronoun("enmai"),
        Word([Morph("nā", "ship", STEM), Morph("mai", "ENT", MAI, "-")]),
        G.directional_word("nub"),
        G.verb("yed", "go", anchor="mi"),
    )


TEXT_02 = Text(
    id="TEXT 02",
    title="THE PARALLEL SENTENCE — HALF-UNDERSTANDING",
    jp="対訳",
    lines=(
        Line("Sūchel",
             "enmai nav-mai nuv jed-a=mi.",
             "SŪCHEL — 1PL.ENT ship-ENT DOWN go-T=PROP",
             '"We take our ship down, by our own clock."',
             _suchel_parallel_words()),
        Line("Nubhel",
             "enmai nā-mai nub yed-ó=mi.",
             "NUBHEL — 1PL.ENT ship-ENT DOWN go-PLAIN=PROP",
             "The same sentence, the sister's mouth.",
             _nubhel_parallel_words()),
    ),
    commentary=(
        "Roughly four words in five land across the gap — enmai, -mai, "
        "=mi and the shape of the verb are shared bones. What trips the "
        "ear is exactly the rivalry: nav/nā, nuv/nub, jed/yed, -a/-ó. "
        "Enough to trade, marry, and mishear a docking order at the worst "
        "possible moment."),
)

# what trips the ear (docs/06 §06): the rivalry, pair by pair
PARALLEL_CONTRASTS: Tuple[Tuple[str, str], ...] = (
    ("nav", "nā"), ("nuv", "nub"), ("jed", "yed"), ("-a", "-ó"))


# ---------------------------------------------------------------------------
# TEXT 03 — THE CODE-SWITCH — SHOWPIECE 切替

_SWITCH = G.code_switch()   # an sū-t-eshe=zu — the rival's mood, anchor, color

TEXT_03 = Text(
    id="TEXT 03",
    title="THE CODE-SWITCH — SHOWPIECE",
    jp="切替",
    lines=(
        Line("Nubhel",
             "on dolnub yed-t-ó=mi, yel-ol —",
             "3SG PITWARD go-PFV-PLAIN=PROP · seam-DAT",
             "She dove pitward, to the seam —",
             tuple(G.clause("on", "yed", "go", pfv=True, anchor="mi",
                            directional="dolnub"))
             + (Word([Morph("yel", "seam", STEM),
                      Morph("ol", "DAT", CASE, "-")]),)),
        Line("Sūchel",
             "an sū-t-eshe=zu.",
             "[SŪCHEL] 3SG cross-PFV-T•=DARK",
             "— she crossed: seam-true, in the dark.",
             tuple(_SWITCH.words)),
        Line("Nubhel",
             "on ōl-t-ó=nu, +so kodur.",
             "3SG surface-PFV-PLAIN=DEEP · +one cycle",
             "She surfaced, in dive-time — one cycle owed.",
             tuple(G.sign_deep(G.clause("on", "ōl", "surface", pfv=True,
                                        anchor="nu"),
                               1, cycles=True))),
    ),
    commentary=(
        "The grammatical hole made visible: Nubhel carries the narration "
        "to the seam's edge and must borrow Sūchel for the crossing itself "
        "— the rival's mood, the rival's anchor, in the rival's color — "
        "then takes the story back on the far side. Letter the middle "
        "balloon in the Sūchel style: the language shift is the seam."),
)


TEXTS: Tuple[Text, ...] = (TEXT_01, TEXT_02, TEXT_03)
