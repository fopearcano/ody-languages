"""Sel — the liquid sister (docs/05 §03).

Maren (*mar-en, "of the pearls"): the ocean moon whose tongue drowned its
glides.  Where Mars preserved, Maren dissolved — every *w and *h drowned
into vowel length, stops soften between vowels, old *k hisses to s before
front vowels.  Fleet slang calls Sel speakers "the vowel-farmers"; Sel
calls Sūchel "the tongue in a hurry."

Five changes (docs/05 §03, S-1..S-5) plus one phonotactic repair:

* S-1 assibilation: *k, *g → s, z before front vowels (sel, zel, Selsom,
  Sūsel — "the same lengthening as Sūchel, then S-1 instead of
  palatalization").
* S-2 glide drowning: *w → ∅ everywhere with compensatory lengthening —
  of the following vowel word-initially (*wer-stan → Ērstan), of the
  preceding vowel otherwise (*sow-mor → Sōmor).  The offglide of *au
  counts (*hau-bel → hā-bel at this step, → Ābel after S-4), and a short
  vowel left in hiatus after a long vowel is absorbed: *nāw-es → nā-es →
  Nās ("S-2 swallowed nearly the whole word"), *sow-orn → sō-orn → Sōrn.
* S-3 lenition: intervocalic *p, *t, *k → b, d, g (*kap-a → kaba).
* S-4 h-drowning: *h → ∅ with lengthening in all positions — word-initial
  h lengthens the following vowel (*hek-mar → Ēkmar), post-consonantal h
  lengthens the vowel before the consonant (*anh-es → Ānes).
* S-5 final lowering: word-final short *i, *u → e, o (*kad-u → kado);
  finals are otherwise KEPT — Sel, unlike every sister, drops nothing.
* repair: degemination at morpheme joins (*lim-mar → Limar, *kad-dun →
  Kadun).

The good omen (docs/05 §03): *sow-orn comes out Sōrn — identical to the
fleet form; on the drive's own name the two tongues agree by accident of
sound law.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .phonology import (BOUNDARIES, FRONT_VOWELS, LONG_VOWELS, SHORT_VOWELS,
                        is_vowel, lengthen)
from .soundchange import (Change, Derivation, Deriver, next_real, prev_real,
                          real_indices)

# ---------------------------------------------------------------------------
# the five changes (docs/05 §03)


def _s1(segs):
    """S-1 *k, *g → s, z before front vowels (*kel → sel, *gel → zel)."""
    out = list(segs)
    for i, s in enumerate(out):
        if s in ("k", "g"):
            n = next_real(out, i)
            if n is not None and out[n] in FRONT_VOWELS:
                out[i] = "s" if s == "k" else "z"
    return out


def _s2(segs):
    """S-2 *w → ∅ everywhere, with compensatory lengthening (*wer-stan →
    Ērstan word-initially, *sow-mor → Sōmor otherwise); the offglide of
    *au counts (au → ā); a short vowel in hiatus after a long vowel is
    absorbed (nā-es → Nās, sō-orn → Sōrn)."""
    out = list(segs)
    # (a) the diphthong's offglide drowns too
    for i, s in enumerate(out):
        if s == "au":
            out[i] = "ā"
    # (b) w -> ∅ with lengthening
    i = 0
    while i < len(out):
        if out[i] == "w":
            p, n = prev_real(out, i), next_real(out, i)
            if p is not None and is_vowel(out[p]):
                out[p] = lengthen(out[p])
            elif n is not None and is_vowel(out[n]):
                out[n] = lengthen(out[n])
            del out[i]
            continue
        i += 1
    # (c) absorb a short vowel left in hiatus after a long vowel
    i = 0
    while i < len(out):
        if out[i] in LONG_VOWELS:
            n = next_real(out, i)
            if n is not None and out[n] in SHORT_VOWELS:
                del out[n]
                continue
        i += 1
    return out


def _s3(segs):
    """S-3 intervocalic *p, *t, *k → b, d, g (*kap-a → kaba)."""
    voiced = {"p": "b", "t": "d", "k": "g"}
    out = list(segs)
    for i, s in enumerate(out):
        if s in voiced:
            p, n = prev_real(out, i), next_real(out, i)
            if (p is not None and is_vowel(out[p])
                    and n is not None and is_vowel(out[n])):
                out[i] = voiced[s]
    return out


def _s4(segs):
    """S-4 *h → ∅ with lengthening in all positions: word-initially the
    following vowel lengthens (*hek-mar → Ēkmar), after a consonant the
    vowel before it does (*anh-es → Ānes)."""
    out = list(segs)
    i = 0
    while i < len(out):
        if out[i] == "h":
            p = prev_real(out, i)
            if p is not None:
                if is_vowel(out[p]):
                    out[p] = lengthen(out[p])
                else:
                    pp = prev_real(out, p)
                    if pp is not None and is_vowel(out[pp]):
                        out[pp] = lengthen(out[pp])
            else:
                n = next_real(out, i)
                if n is not None and is_vowel(out[n]):
                    out[n] = lengthen(out[n])
            del out[i]
            continue
        i += 1
    return out


def _s5(segs):
    """S-5 final short *i, *u lowered to e, o (*kad-u → kado); finals
    otherwise kept."""
    out = list(segs)
    idx = real_indices(out)
    if idx and out[idx[-1]] in ("i", "u"):
        out[idx[-1]] = "e" if out[idx[-1]] == "i" else "o"
    return out


def _rep_degem(segs):
    """Repair: degemination at morpheme joins (*lim-mar → Limar,
    *kad-dun → Kadun) — the same seam-repair Sūchel's compose() applies."""
    out: List[str] = []
    for s in segs:
        if s not in BOUNDARIES and not is_vowel(s):
            prev = next((x for x in reversed(out) if x not in BOUNDARIES), None)
            if prev == s:
                continue
        out.append(s)
    return out


SEL = Deriver(
    name="Sel",
    changes=[
        Change("S-1", "k,g -> s,z before front vowels", _s1),
        Change("S-2", "w -> ∅ everywhere, with compensatory lengthening", _s2),
        Change("S-3", "intervocalic p,t,k -> b,d,g", _s3),
        Change("S-4", "h -> ∅ with lengthening, all positions", _s4),
        Change("S-5", "final short i,u lowered to e,o; finals kept", _s5),
    ],
    repairs=[Change("REP", "degemination at morpheme joins", _rep_degem)],
)


# ---------------------------------------------------------------------------
# the twenty place names (docs/05 §03)


@dataclass
class Place:
    name: str
    proto: str
    gloss: str
    what: str
    cited: Tuple[str, ...] = ()

    def derive(self) -> Derivation:
        return SEL.derive(self.proto)


PLACES: List[Place] = [
    Place("Maren", "*mar-en", "Of the Pearls",
          "the moon itself; one world-ocean, ten thousand atolls"),
    Place("Selsom", "*kel-som", "Speech-gathering",
          "the drowned forum, held at low tide", cited=("S-1",)),
    Place("Zelmor", "*gel-mor", "Seam-rock",
          "reef where the moon's first well kindled", cited=("S-1",)),
    Place("Ābel", "*hau-bel", "Upper-hearth",
          "the one cliff city above the spray line", cited=("S-2", "S-4")),
    Place("Akmar", "*ak-mar", "Ice-pearl", "the frozen shallows of the far pole"),
    Place("Pordol", "*por-dol", "Harbor-deep",
          "the trench port where hulls are pressure-cured"),
    Place("Ērstan", "*wer-stan", "Truth-station",
          "sister-city of Werstan and Verstan", cited=("S-2",)),
    Place("Limar", "*lim-mar", "Gate-pearl",
          "the tidal gate between the two great gyres"),
    Place("Galmar", "*gal-mar", "Still-pearl",
          "the becalmed lagoon; honeymooners and mutineers"),
    Place("Kadun", "*kad-dun", "Beacon-mound",
          "the lighthouse isle anchoring the moon's net"),
    Place("Nās", "*nāw-es", "Ship-place",
          "the floating yards (S-2 swallowed nearly the whole word)",
          cited=("S-2",)),
    Place("Pelagdol", "*pelag-dol", "Deep-pit", "the abyssal research station"),
    Place("Tembel", "*tem-bel", "Weave-hearth", "the net-makers' town"),
    Place("Sōmor", "*sow-mor", "Crossing-rock",
          "the departure rock; ships bless keels against it", cited=("S-2",)),
    Place("Durak", "*dur-ak", "Enduring-ice", "the old shelf that never melts"),
    Place("Renmar", "*ren-mar", "Path-pearl",
          "the strait every cargo run threads"),
    Place("Idpor", "*id-por", "Open-harbor",
          "the free anchorage; no flag, no questions"),
    Place("Ānes", "*anh-es", "Breath-place",
          "the surfacing grounds where divers decompress", cited=("S-4",)),
    Place("Zeles", "*gel-es", "Seam-place",
          "the pilgrimage buoy over deep water", cited=("S-1",)),
    Place("Ēkmar", "*hek-mar", "High-pearl",
          "the spire atoll, tallest point on the moon", cited=("S-4",)),
]


@dataclass
class Cognate:
    form: str
    proto: str
    cited: Tuple[str, ...] = ()
    note: str = ""

    def derive(self) -> Derivation:
        return SEL.derive(self.proto)


# the cognate line of docs/05 §03 (plus the rule-table examples)
COGNATES: List[Cognate] = [
    Cognate("Sūsel", "*suw-kel", cited=("S-1", "S-2"),
            note="Maren's name for the crossing-speech: the same "
                 "lengthening as Sūchel, then S-1 instead of palatalization"),
    Cognate("Sōrn", "*sow-orn", cited=("S-2",),
            note="identical to the fleet form — the good omen for engines"),
    Cognate("sel", "*kel", cited=("S-1",), note="speech"),
    Cognate("zel", "*gel", cited=("S-1",), note="the seam"),
    Cognate("kaba", "*kap-a", cited=("S-3",), note="S-3 example"),
    Cognate("kado", "*kad-u", cited=("S-5",), note="S-5 example"),
]


def derive(proto: str) -> Derivation:
    """Run a proto-form through S-1..S-5 (no adjustments)."""
    return SEL.derive(proto)
