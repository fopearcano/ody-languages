"""Beltsel — the eroded sister (docs/05 §04).

Belgar (*bel-gar, "Hearth-ground"): the administrative capital, whose
prestige tongue Beltsel (*bel-kel, "hearth-speech") was sanded down by
centuries of court, commerce, and bureaucracy — unstressed vowels
deleted, clusters crushed, every long vowel shortened.  "The capital
cannot hold its breath": to a Belgar clerk the fleets' ū is a spelling
error, and Sūchel files as Suvtsel.

**Stress**: the capital shifted word stress to the PENULT before its
reductions — this is what Plagar and Dzels jointly imply.  *pelag-ar
stressed pe-LA-gar loses its first syllable's vowel (Plagar), and
dzeles stressed DZE-les loses its second (Dzels); under the family's
inherited initial stress B-2 could never have touched *pe-.  B-2 below
therefore protects the penult and deletes elsewhere.

Six changes (docs/05 §04, B-1..B-6):

* B-1 affrication: *k, *g → ts, dz before front vowels (tsel, dzel,
  Beltsel itself = *bel-kel).
* B-2 syncope: unstressed (non-penult) short vowels delete where the
  result stays pronounceable — a legal complex onset (Plagar's pl-) or a
  falling-sonority coda (Dzels's -ls).  *plagr is blocked (rising -gr),
  and every CVC-CVC compound of the table survives intact.  The codex's
  "non-final" is read as "not the word-final segment": the deleted vowel
  of Dzels sits in the final syllable but before its coda.
* B-3 cluster crush: three-consonant clusters simplify, the middle
  consonant drops — where the syllable contact cannot fall in sonority.
  *kad-stan → Kadtan (d.st rises), but the codex's own table keeps
  Morstan and Verstan (r.st falls), so a sonorant coda protects the
  cluster; this reading reproduces all three attestations.  ``x`` = /ks/
  is ONE segment, so Nexbel is untouched.
* B-4 fortition: *w → v everywhere, no lengthening (Verstan, Suvtsel,
  Sovorn).
* B-5 h-loss: *h → ∅, no lengthening (*hek- → ek-).
* B-6 breath-loss: ALL long vowels shorten (nāvren → Navren) — the rule
  the other sisters mock.  (No documented Beltsel form contains a
  diphthong; B-6 as implemented shortens only the macron vowels.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .phonology import (FRONT_VOWELS, SHORT_OF, SHORT_VOWELS, is_vowel,
                        syllabify)
from .soundchange import (Change, Derivation, Deriver, next_real,
                          real_indices)

# ---------------------------------------------------------------------------
# sonority (for B-2 pronounceability and B-3 syllable contact)

_SONORITY = {}
for _s in ("p", "b", "t", "d", "k", "g", "x", "ts", "dz", "ch", "j"):
    _SONORITY[_s] = 1        # stops & affricates (x = /ks/ is one segment)
for _s in ("f", "s", "z", "v", "sh", "th", "kh", "gh", "h"):
    _SONORITY[_s] = 2        # fricatives
for _s in ("m", "n"):
    _SONORITY[_s] = 3        # nasals
for _s in ("r", "l"):
    _SONORITY[_s] = 4        # liquids
for _s in ("w", "y"):
    _SONORITY[_s] = 5        # glides


def _son(seg: str) -> int:
    return _SONORITY.get(seg, 3)


def _pronounceable(plain: List[str]) -> bool:
    """B-2's filter: every consonant run of the boundary-free stream must
    be syllabifiable — word-initially a legal complex onset (obstruent +
    r/l), word-finally at most two consonants falling in sonority,
    medially at most two consonants."""
    if not any(is_vowel(s) for s in plain):
        return False
    n = len(plain)
    i = 0
    while i < n:
        if is_vowel(plain[i]):
            i += 1
            continue
        j = i
        while j < n and not is_vowel(plain[j]):
            j += 1
        run = plain[i:j]
        if i == 0:      # word-initial: (C) or legal complex onset
            ok = len(run) == 1 or (len(run) == 2 and _son(run[0]) <= 2
                                   and run[1] in ("r", "l"))
        elif j == n:    # word-final: (C) or falling-sonority CC coda
            ok = len(run) == 1 or (len(run) == 2
                                   and _son(run[0]) > _son(run[1]))
        else:           # medial: coda + onset at most
            ok = len(run) <= 2
        if not ok:
            return False
        i = j
    return True


# ---------------------------------------------------------------------------
# the six changes (docs/05 §04)


def _b1(segs):
    """B-1 *k, *g → ts, dz before front vowels (*kel → tsel, *gel → dzel)."""
    out = list(segs)
    for i, s in enumerate(out):
        if s in ("k", "g"):
            n = next_real(out, i)
            if n is not None and out[n] in FRONT_VOWELS:
                out[i] = "ts" if s == "k" else "dz"
    return out


def _b2(segs):
    """B-2 unstressed non-final short vowels lost (*pelag-ar → Plagar,
    dzeles → Dzels) — the penult carries the capital's stress and is
    immune; a deletion applies only where the word stays pronounceable."""
    out = list(segs)
    while True:
        idx = real_indices(out)
        plain = [out[i] for i in idx]
        sylls = syllabify(out)
        if len(sylls) < 2:
            return out
        penult = len(sylls) - 2
        deleted = False
        for k, syl in enumerate(sylls):
            if k == penult:
                continue                        # the stressed syllable
            nuc = syl.seg_indices[len(syl.onset)]
            if plain[nuc] not in SHORT_VOWELS:
                continue                        # long vowels are immune
            if nuc == len(plain) - 1:
                continue                        # word-final segment kept
            if _pronounceable(plain[:nuc] + plain[nuc + 1:]):
                del out[idx[nuc]]
                deleted = True
                break
        if not deleted:
            return out


def _b3(segs):
    """B-3 three-consonant clusters simplify, middle drops (*kad-stan →
    Kadtan) — unless the first consonant closes its syllable with falling
    sonority (Morstan, Verstan keep -rst-).  x = /ks/ is one segment
    (Nexbel untouched)."""
    out = list(segs)
    while True:
        idx = real_indices(out)
        plain = [out[i] for i in idx]
        n = len(plain)
        fired = False
        i = 0
        while i < n:
            if is_vowel(plain[i]):
                i += 1
                continue
            j = i
            while j < n and not is_vowel(plain[j]):
                j += 1
            if j - i >= 3 and _son(plain[i]) <= _son(plain[i + 1]):
                del out[idx[i + 1]]             # the middle drops
                fired = True
                break
            i = j
        if not fired:
            return out


def _b4(segs):
    """B-4 *w → v everywhere, no lengthening (*wer-stan → Verstan)."""
    return ["v" if s == "w" else s for s in segs]


def _b5(segs):
    """B-5 *h → ∅, no lengthening (*hek- → ek-)."""
    return [s for s in segs if s != "h"]


def _b6(segs):
    """B-6 all long vowels shorten (nāvren → Navren) — the capital
    cannot hold its breath."""
    return [SHORT_OF.get(s, s) for s in segs]


BELTSEL = Deriver(
    name="Beltsel",
    changes=[
        Change("B-1", "k,g -> ts,dz before front vowels", _b1),
        Change("B-2", "unstressed non-penult short vowels lost where pronounceable", _b2),
        Change("B-3", "three-consonant clusters simplify (middle drops)", _b3),
        Change("B-4", "w -> v everywhere, no lengthening", _b4),
        Change("B-5", "h -> ∅, no lengthening", _b5),
        Change("B-6", "all long vowels shorten", _b6),
    ],
)


# ---------------------------------------------------------------------------
# the twenty place names (docs/05 §04)


@dataclass
class Place:
    name: str
    proto: str
    gloss: str
    what: str
    cited: Tuple[str, ...] = ()

    def derive(self) -> Derivation:
        return BELTSEL.derive(self.proto)


PLACES: List[Place] = [
    Place("Belgar", "*bel-gar", "Hearth-ground",
          "the capital world; nine rings of city around one sea"),
    Place("Plagar", "*pelag-ar", "the Deep Quarter",
          "oldest district, sunk two syllables and ten meters",
          cited=("B-2",)),
    Place("Dzelren", "*gel-ren", "Seam-way",
          "the crossing terminal; a cathedral of departures", cited=("B-1",)),
    Place("Tselsom", "*kel-som", "Speech-gathering",
          "the great forum where the Assembly convenes", cited=("B-1",)),
    Place("Kadtan", "*kad-stan", "Beacon-stand",
          'the network throne; whoever holds it holds "when"',
          cited=("B-3",)),
    Place("Verstan", "*wer-stan", "Truth-station",
          "the high court; sister-city of Werstan and Ērstan",
          cited=("B-4",)),
    Place("Turdol", "*tur-dol", "Tower-pit",
          "the inverted undercity beneath the spires"),
    Place("Limgar", "*lim-gar", "Gate-ground",
          "the port ring; every fleet's first sight of the capital"),
    Place("Navren", "*nāw-ren", "Ship-road",
          "the orbital lanes, dense as a printed page", cited=("B-4", "B-6")),
    Place("Dundol", "*dun-dol", "Mound-pit",
          "the amphitheater bowl; riots and operas"),
    Place("Morstan", "*mor-stan", "Rock-station", "the shipbreaking yards"),
    Place("Akbel", "*ak-bel", "Ice-hearth",
          "the cold vaults; the capital's seed and gene banks"),
    Place("Somgar", "*som-gar", "Gathering-ground", "parliament plain"),
    Place("Dzels", "*gel-es", "Seam-shrine",
          "eroded to four letters; the name is the sermon",
          cited=("B-1", "B-2")),
    Place("Porgar", "*por-gar", "Harbor-ground",
          "the freeport where fleet law outranks capital law"),
    Place("Vosbel", "*wos-bel", "Wound-hearth",
          "the memorial city for the unreturned", cited=("B-4",)),
    Place("Ranren", "*ran-ren", "Run-road",
          "the speed straits; venue of the Corse Furiose"),
    Place("Temtur", "*tem-tur", "Weave-tower",
          "the archive spire; every crossing ever logged"),
    Place("Idgar", "*id-gar", "Open-ground",
          "the first landing field, kept unbuilt by law"),
    Place("Nexbel", "*nex-bel", "Gap-hearth",
          "the mourners' quarter, where the ne-liturgies are sung"),
]


@dataclass
class Cognate:
    form: str
    proto: str
    cited: Tuple[str, ...] = ()
    note: str = ""

    def derive(self) -> Derivation:
        return BELTSEL.derive(self.proto)


# the cognate line of docs/05 §04 (plus the rule-table examples)
COGNATES: List[Cognate] = [
    Cognate("Suvtsel", "*suw-kel", cited=("B-1", "B-4"),
            note="the crossing-speech in a capital mouth — 'the length you "
                 "hold is, to them, a spelling error'"),
    Cognate("Sovorn", "*sow-orn", cited=("B-4",), note="the drive"),
    Cognate("tsel", "*kel", cited=("B-1",), note="speech"),
    Cognate("dzel", "*gel", cited=("B-1",), note="the seam"),
    Cognate("ek", "*hek", cited=("B-5",), note="B-5 example *hek- → ek-"),
]


def derive(proto: str) -> Derivation:
    """Run a proto-form through B-1..B-6 (no adjustments)."""
    return BELTSEL.derive(proto)
