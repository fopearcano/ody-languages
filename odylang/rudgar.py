"""Rudgar — the tongue of old ground (docs/05 §02).

Mars: the conservative sister.  Rudgar (*rud-gar "red ground" — the world
and its tongue share a name) never lost *w or *h, the two sounds every
other daughter killed; Martian ears are the closest living ears to Old
Pelagic, which is why Assembly cantors and Wolori lectors are
disproportionately Mars-born.

Five changes (docs/05 §02, R-1..R-5):

* R-1 keeps *w and *h everywhere — encoded as a documented no-op so the
  rule table stays complete (the codex numbers it; identity never leaves
  a trace in a Derivation).
* R-2 backs *k, *g to kh, gh word-initially and between vowels; the glide
  *w counts as a vowel on the left (Suwkhel), a consonant blocks it
  (Rudgar, Akdol, Hekmor keep their plain stops).
* R-3 drops all final short vowels (*kap-a → khap).  A monosyllable never
  loses its only vowel (no attested form tests this edge; the guard keeps
  the engine total).
* R-4 monophthongizes *au → ā even word-finally (*dun-hau → Dunhā,
  *hau- → hā-), unlike Sūchel's SC-5 which spares the word edge.
* R-5 "dry leveling": with Old Pelagic initial stress, an unstressed
  medial (non-initial, non-final syllable) *e, *o levels to a.  The codex
  cites *pelag-ar → Pelaghar for it, whose medial vowel is already *a —
  the rule fires on no attested name (Soworn is two syllables), but it is
  implemented faithfully and locked by a synthetic test.

One documented exception: Galgar (*gal-gar) keeps its initial g where R-2
predicts gh — encoded as an :data:`~odylang.soundchange.Adjustment`
(dissimilation: gh…g avoided in the near-reduplicate; the codex prints
Galgar).  One spelling repair: Mars writes the /ks/ cluster out as ``ks``
(Neksdol), where Sūchel and Beltsel keep the ``x`` letter (nexath,
Nexbel).

The cognate line (docs/05 §02): the fleets' Sōrn is Mars's Soworn — the
glide kept; "the tombstone is still alive on Mars."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .phonology import SHORT_VOWELS, is_vowel, syllabify
from .soundchange import (Adjustment, Change, Derivation, Deriver, next_real,
                          prev_real, real_indices)

# ---------------------------------------------------------------------------
# the five changes (docs/05 §02)


def _r1(segs):
    """R-1 *w, *h retained everywhere (*wer-stan → Werstan) — the rule that
    makes Rudgar the conservative sister is a no-op by construction."""
    return list(segs)


def _r2(segs):
    """R-2 *k, *g → kh, gh initially and between vowels (khel, ghel,
    Khades, Pelaghar); the glide w counts as vocalic on the left
    (Suwkhel), any other consonant blocks (Rudgar, Akdol, Hekmor)."""
    out = list(segs)
    for i, s in enumerate(out):
        if s not in ("k", "g"):
            continue
        n = next_real(out, i)
        if n is None or not is_vowel(out[n]):
            continue
        p = prev_real(out, i)
        if p is None or is_vowel(out[p]) or out[p] == "w":
            out[i] = "kh" if s == "k" else "gh"
    return out


def _r3(segs):
    """R-3 all final short vowels lost (*kap-a → khap)."""
    out = list(segs)
    idx = real_indices(out)
    if not idx or out[idx[-1]] not in SHORT_VOWELS:
        return out
    vowels = [i for i in idx if is_vowel(out[i])]
    if len(vowels) < 2:      # a monosyllable keeps its only vowel
        return out
    del out[idx[-1]]
    return out


def _r4(segs):
    """R-4 *au → ā, including word-finally (*dun-hau → Dunhā, *hau- → hā-)."""
    return ["ā" if s == "au" else s for s in segs]


def _r5(segs):
    """R-5 dry leveling: unstressed medial (non-initial, non-final
    syllable) *e, *o → a under Old Pelagic initial stress."""
    out = list(segs)
    idx = real_indices(out)
    sylls = syllabify(out)
    if len(sylls) < 3:
        return out
    for syl in sylls[1:-1]:
        nucleus_at = idx[syl.seg_indices[len(syl.onset)]]
        if out[nucleus_at] in ("e", "o"):
            out[nucleus_at] = "a"
    return out


def _rep_ks(segs):
    """Spelling repair: Mars writes /ks/ as ks, not x (Neksdol, docs/05
    §02 place table; contrast Sūchel nexath, Beltsel Nexbel)."""
    out: List[str] = []
    for s in segs:
        if s == "x":
            out.extend(["k", "s"])
        else:
            out.append(s)
    return out


RUDGAR = Deriver(
    name="Rudgar",
    changes=[
        Change("R-1", "*w, *h retained everywhere", _r1),
        Change("R-2", "k,g -> kh,gh initially & between vowels (w counts as vocalic)", _r2),
        Change("R-3", "all final short vowels lost", _r3),
        Change("R-4", "au -> ā, even word-finally", _r4),
        Change("R-5", "dry leveling: unstressed medial e,o -> a", _r5),
    ],
    repairs=[Change("REP", "/ks/ spelled ks on Mars (Neksdol)", _rep_ks)],
)


# ---------------------------------------------------------------------------
# the twenty place names (docs/05 §02)


@dataclass
class Place:
    name: str                       # as the codex prints it
    proto: str
    gloss: str                      # the quoted gloss
    what: str                       # what it is (abridged from the table)
    cited: Tuple[str, ...] = ()     # changes expected to fire (locked by tests)
    adjustments: Tuple[Adjustment, ...] = ()

    def derive(self) -> Derivation:
        return RUDGAR.derive(self.proto, self.adjustments)


_GALGAR_NOTE = ("initial *g resists R-2 by dissimilation — gh…g avoided in "
                "the near-reduplicate *gal-gar; the codex prints Galgar")

PLACES: List[Place] = [
    Place("Rudgar", "*rud-gar", "Red Ground",
          "the world itself, and by extension its tongue"),
    Place("Khades", "*kad-es", "Beacon-stead",
          "capital; anchor-node of the planetary beacon net", cited=("R-2",)),
    Place("Hekmor", "*hek-mor", "High-rock",
          "the great shield volcano and its slope cities"),
    Place("Akdol", "*ak-dol", "Ice-pit", "the polar water mines"),
    Place("Weldol", "*wel-dol", "Nothing-pit",
          "the continental canyon; locals say it swallows echoes"),
    Place("Limbel", "*lim-bel", "Gate-hearth",
          "the elevator-foot city, oldest offworld port"),
    Place("Turstan", "*tur-stan", "Tower-station",
          "the tether counterweight settlement"),
    Place("Ghelren", "*gel-ren", "Seam-path",
          "the old pilgrim road to the first crossing shrine", cited=("R-2",)),
    Place("Khelsom", "*kel-som", "Speech-gathering",
          "the university town; seat of the cantor schools", cited=("R-2",)),
    Place("Rudmor", "*rud-mor", "Red-rock", "the southern highlands"),
    Place("Pelaghar", "*pelag-ar", "the Deephold",
          "fortress-archive over the old aquifer", cited=("R-2",)),
    Place("Dunhā", "*dun-hau", "Upper-mound",
          "the high observatory ring (R-4)", cited=("R-4",)),
    Place("Akstan", "*ak-stan", "Ice-station", "the mid-latitude glacier depot"),
    Place("Morbel", "*mor-bel", "Rock-hearth", "mining town in the cratered plain"),
    Place("Khadren", "*kad-ren", "Pulse-path",
          "the beacon highway girdling the equator", cited=("R-2",)),
    Place("Galgar", "*gal-gar", "Still-ground",
          "the dead flats; proverbial for boredom", cited=("R-2",),
          adjustments=((_GALGAR_NOTE,
                        lambda f: f.replace("ghal", "gal", 1)),)),
    Place("Neksdol", "*nex-dol", "Gap-pit",
          "the unexplained sink no survey closes"),
    Place("Durbel", "*dur-bel", "Endure-hearth",
          "the oldest surviving dome, kept lit as a vow"),
    Place("Suwren", "*suw-ren", "Crossing-path",
          "the first FTL launch field, now a memorial"),
    Place("Werstan", "*wer-stan", "Truth-station",
          "the old tribunal; one of the three sister-cities"),
]


@dataclass
class Cognate:
    form: str
    proto: str
    cited: Tuple[str, ...] = ()
    note: str = ""

    def derive(self) -> Derivation:
        return RUDGAR.derive(self.proto)


# the cognate line of docs/05 §02 (plus the rule-table examples)
COGNATES: List[Cognate] = [
    Cognate("Soworn", "*sow-orn",
            note="the fleets' Sōrn with the glide kept — the tombstone is "
                 "still alive on Mars"),
    Cognate("Suwkhel", "*suw-kel", cited=("R-2",),
            note="the fleets' Sūchel; k backs after the kept glide"),
    Cognate("khel", "*kel", cited=("R-2",), note="speech"),
    Cognate("ghel", "*gel", cited=("R-2",), note="the seam"),
    Cognate("khap", "*kap-a", cited=("R-2", "R-3"), note="tolerance (R-3 example)"),
    Cognate("hā", "*hau", cited=("R-4",), note="upper (R-4 example *hau- → hā-)"),
]


def derive(proto: str) -> Derivation:
    """Run a proto-form through R-1..R-5 (no adjustments)."""
    return RUDGAR.derive(proto)
