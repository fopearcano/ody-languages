"""Old Pelagic (*Pelgar*), the proto-language — the tongue before the seam.

Compiled from the etymology columns of all six codices (docs/01–06).
Old Pelagic is rigid SOV, fully inflected, phonologically conservative
(docs/01 §01).  Two chronological layers matter:

* **Classical (pre-seam / liturgical) Old Pelagic** — no veridical moods,
  no temporal anchors, no *ne* (docs/05 §05): the hypothesis-space
  language.  This is the register the Assembly froze and the layer this
  module's citation forms romanize.
* **Late Old Pelagic** (the post-seam koine both fleets descend from) —
  had developed the veridical-mood suffixes and the first anchors.  The
  evidence is phonological: Nubhel's plain mood is ``-ó`` where Sūchel has
  ``-a``, and D-4 rounds only *stressed* \\*a — so the suffix already
  carried the stress when the daughters split ("the mood carries the
  beat" is inherited prosody, docs/06 §03).

Citation forms keep \\*w and \\*h everywhere (the sounds every daughter
but Rudgar killed) — Werstan, Suwkel, gel.
"""

from __future__ import annotations

from .soundchange import parse_proto
from .phonology import romanize

# root -> gloss.  Sources: docs/01 lexicon & §03, docs/02 appendix,
# docs/05 place-name tables & Lorkel table, docs/06 lexicon.
ROOTS = {
    "*suw-": "to thread through, to cross (zero grade; o-grade *sow-)",
    "*sow-": "to thread through, to cross (o-grade of *suw-)",
    "*kel": "speech",
    "*gel-": "to stitch, to join; the seam",
    "*ged-": "to go, move",
    "*pelag-": "the open deep",
    "*id-": "open",
    "*ren-": "path",
    "*kad-": "pulse, beat; beacon",
    "*dzu-": "to drift; adrift",
    "*mei-": "self",
    "*nex-": "absence; gap",
    "*nub-": "under; the deep",
    "*hau": "upper air; up (also *haw- before suffixes)",
    "*kap-": "to hold in; tolerance, limit",
    "*tem-": "to weave; pattern",
    "*tur-": "to pile, stack; tower",
    "*mor-": "sea-rock; rock",
    "*mar-": "pearl; sea-stone",
    "*wel-": "nothing; no-thing",
    "*os-": "mouth",
    "*wer-": "truth",
    "*wur-": "to spin, whirl; madness",
    "*lor-": "rule, law; ratio",
    "*som-": "to gather",
    "*nāw-": "ship",
    "*mahin": "hand",
    "*ran-": "to run",
    "*tel-": "to stretch to, reach; (numeral) three",
    "*dur-": "to endure, survive",
    "*dol-": "pit, well",
    "*wos-": "wound",
    "*tan-": "to hold, keep",
    "*men-": "to wait, remain",
    "*ret-": "again",
    "*anh-": "breath",
    "*kru-": "blood",
    "*gal-": "still; becalmed",
    "*les-": "alignment; fair phase (with front-vowel extension *lesi-)",
    "*om-": "all, every",
    "*len-": "level; along",
    "*wo-": "not",
    "*we-": "to be",
    "*wu": "question particle",
    "*mag-i": "bound; entangled",
    "*en-": "I (1SG)",
    "*is-": "you (2SG; extended *isi-)",
    "*an-": "she/he/it (3SG)",
    # numerals (docs/01)
    "*sa": "one",
    "*wor": "two",
    "*mek": "four",
    "*pew": "five",
    "*sen": "six",
    "*hep": "seven",
    "*ok": "eight",
    "*nur": "nine",
    "*dak": "ten",
    # place-name elements (docs/05)
    "*rud-": "red",
    "*hek-": "high",
    "*ak-": "ice",
    "*dun-": "mound",
    "*lim-": "gate",
    "*stan": "station; stand",
    "*bel-": "hearth",
    "*por-": "harbor",
}

AFFIXES = {
    "*-orn": "instrumental ('instrument of')",
    "*-es": "place of",
    "*-el": "agent (also zero-grade *-il)",
    "*-il": "agent (zero grade of *-el)",
    "*-ath": "nominalizer (act or result)",
    "*-eth": "locative",
    "*-ol": "dative",
    "*-en": "genitive",
    "*-i": "plural",
    "*-ur": "duration suffix",
    "*-u": "hortative (the daughters' imperative)",
    "*ō": "vocative interjection",
}

# Late Old Pelagic verb machinery (docs/06 §03 'reconstruction proof';
# classical/liturgical OP predates all of it, docs/05 §05).
LATE_OP_VERB = {
    "*-a": "plain indicative — stressed: 'the truth-beat' both fleets inherit",
    "*-im": "approach ('true as neared from below')",
    "*-ur": "held-from-above (> Sūchel T⁺, > Nubhel hearsay)",
    "*-eshe": "seam-true (> Sūchel T•; left no reflex in Nubhel)",
    "*-t-": "perfective",
    "*=kad": "beacon anchor (> =ka)",
    "*=mei": "proper-time anchor (> =mi)",
}


def citation(proto: str) -> str:
    """Classical Old Pelagic citation form: the proto-form romanized as the
    liturgy (and Lorkel) pronounce it — *w and *h intact, no sound changes.

    >>> citation('*suw-kel')
    'suwkel'
    >>> citation('*wer-stan')
    'werstan'
    """
    return romanize(parse_proto(proto))


def gloss(proto: str) -> str:
    for table in (ROOTS, AFFIXES):
        if proto in table:
            return table[proto]
    return ""
