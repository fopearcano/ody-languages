"""Nubhel — the Deep-Speech, second daughter of Old Pelagic (docs/06).

Seven ordered changes (docs/06 §02) turn Old Pelagic into the tongue of
the vertical fleet.  The codex's one explicit ordering statement is the
module's spine: **D-3 is ordered before D-1** — "original *h dies first,
then new h is born from *k — so every medial h in Nubhel is secondary."
The application order is therefore D-3, D-1, D-2, D-4, D-5, D-6, D-7.

The §05 working lexicon lives in :data:`LEXICON` (each proto-sourced
entry derived by the engine and locked by tests) and the §04
false-friends table in :data:`FALSE_FRIENDS`, checked against *both*
derivers.

Two readings distilled from the attested data, where the codex's prose
is looser than its forms (documented here, locked by tests):

* **D-5** ("vowels lengthen in open stressed syllables").  Taken
  literally this would give †tēm for *tem-a (§02 cites tem) and †kōdur
  for kodur (§05 gives [ˈko.dur]).  The forms show the drift affects the
  *high* vowels in open stressed non-final syllables — *nub-i → Nūbi is
  the codex's own example, and every mid/low vowel in that position
  stays short.  The held breath is a close vowel's.
* **D-7** ("final short vowel lost after a heavy syllable", like Sūchel
  SC-7).  *tem-a → tem, but *nub-i keeps its -i after D-5's fresh ū:
  apocope never creates a superheavy CVːC syllable — the
  drift-lengthened vowel protects the final vowel.  Nubhel is the
  tongue that holds its breath; it does not clip what it holds.

Codex-flagged specials encoded as data, never silently:

* ``-mai`` is "*mag-i, shared" / "kin-words are family-stable" (§05):
  it is inherited as data, not re-derived (the deep chain D-4 never
  operated on it).
* ``ve`` "to be" is attested in TEXT 01 against D-2's expected †be —
  the copula cliticized before fortition; carried as a register entry
  with the note.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .phonology import (FRONT_VOWELS, SHORT_OF, SHORT_VOWELS, is_vowel,
                        lengthen, syllabify)
from .soundchange import (Adjustment, Change, Derivation, Deriver, next_real,
                          prev_real, real_indices)

# ---------------------------------------------------------------------------
# the seven changes (docs/06 §02), applied D-3, D-1, D-2, D-4, D-5, D-6, D-7


# coalescence hierarchy for V₁wV₂ → one long vowel (docs/06 §02 data:
# *suw-il → Sūl (u beats i), *haw-ol- → ōl (o beats a)); e and i extend
# the codex's "u > o > a" at the bottom, unattested but harmless.
_COALESCE_RANK = {"u": 0, "o": 1, "a": 2, "e": 3, "i": 4}


def _quality(v: str) -> str:
    return SHORT_OF.get(v, v)


def _coalesce(v1: str, v2: str) -> str:
    """Two vowel qualities in contact across a dead glide merge to ONE
    long vowel, the hierarchy u > o > a choosing the survivor."""
    q1, q2 = _quality(v1), _quality(v2)
    win = q1 if _COALESCE_RANK.get(q1, 9) <= _COALESCE_RANK.get(q2, 9) else q2
    return lengthen(win)


def _d3(segs):
    """D-3 Breath-loss: ALL *h → ∅ (even word-initial — *hep → ep, hōl
    vs ōl, docs/06 §04) and non-initial *w → ∅, with compensatory
    lengthening.  V₁wV₂ coalesces to one long vowel by the hierarchy
    u > o > a (*suw-il → Sūl, *haw-ol- → ōl); h after a consonant
    lengthens the vowel before it (*anh- → ān, the Sūchel SC-4 pattern);
    a dead final/preconsonantal *w leaves length (*nāw- → nā,
    *suw-kel → Sūkel, → Sūhel at D-1).  Ordered before D-1: original *h
    dies first, then new h is born from *k."""
    out = list(segs)
    # (a) h-loss, everywhere
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
            del out[i]
            continue
        i += 1
    # (b) an /au/ diphthong whose glide meets a following vowel is
    # a+w+V: coalesce (*haw-ol- → ōl); a closed-off au survives to D-6
    i = 0
    while i < len(out):
        if out[i] == "au":
            n = next_real(out, i)
            if n is not None and is_vowel(out[n]):
                out[i] = _coalesce("a", out[n])
                del out[i + 1: n + 1]
                continue
        i += 1
    # (c) non-initial w-loss
    i = 0
    while i < len(out):
        idx = real_indices(out)
        if out[i] == "w" and (not idx or i != idx[0]):
            p, n = prev_real(out, i), next_real(out, i)
            if (p is not None and is_vowel(out[p])
                    and n is not None and is_vowel(out[n])):
                out[p] = _coalesce(out[p], out[n])
                del out[p + 1: n + 1]
                i = p
                continue
            if p is not None and is_vowel(out[p]):
                out[p] = lengthen(out[p])
                del out[i]
                continue
            del out[i]
            continue
        i += 1
    return out


def _d1(segs):
    """D-1 Deep palatalization: *k → h, *g → y before front vowels —
    ordered after D-3, so the new h survives (*kel → hel, *gel → yel,
    *ged- → yed, *nub-kel → Nubhel: every medial h is secondary).

    *mag-i is NOT fed through this chain: the codex calls -mai
    "shared, family-stable" (§05) — the suffix is inherited as data."""
    out = list(segs)
    i = 0
    while i < len(out):
        s = out[i]
        j = next_real(out, i)
        if j is not None and out[j] in FRONT_VOWELS:
            if s == "k":
                out[i] = "h"
            elif s == "g":
                out[i] = "y"
        i += 1
    return out


def _d2(segs):
    """D-2 Fortition: word-initial *w → b (*wer- → ber, *wur- → bur,
    *wos- → bos; merges *wel 'nothing' with *bel 'hearth' — 'the hearth
    is nothing to us', docs/06 §02)."""
    out = list(segs)
    idx = real_indices(out)
    if idx and out[idx[0]] == "w":
        out[idx[0]] = "b"
    return out


def _d4(segs):
    """D-4 Pressure-rounding: stressed *a → o, with Old Pelagic INITIAL
    stress — the first-syllable short a only (*kad → kod, *tan- → ton,
    *ran- → ron, *an- → on, *sa → so, *dak → dok; merges *mar 'pearl'
    into *mor 'rock').  Long ā is a held breath and resists (nā, ān —
    D-3's fresh length runs first and protects).  The OTHER stressed *a
    is the plain-mood suffix, whose -ó lives in the grammar module
    (docs/06 §03, the reconstruction proof)."""
    out = list(segs)
    for i in real_indices(out):
        if is_vowel(out[i]):
            if out[i] == "a":
                out[i] = "o"
            break
    return out


def _d5(segs):
    """D-5 Held-breath drift: a high vowel lengthens in an open stressed
    (initial) non-final syllable (*nub-i → Nūbi).  Monosyllables are
    untouched (so, hel, yed); closed syllables are untouched (Nubhel,
    dolnub); and the attested mid vowels in exactly this position stay
    short (*tem-a → tem, not †tēm; kodur [ˈko.dur]) — see the module
    docstring for why the codex's 'vowels lengthen' reads as the high
    vowels here."""
    sylls = syllabify(segs)
    if len(sylls) < 2:
        return segs
    first = sylls[0]
    if first.coda or first.nucleus not in ("u", "i"):
        return segs
    out = list(segs)
    for i in real_indices(out):
        if is_vowel(out[i]):
            out[i] = lengthen(out[i])
            break
    return out


def _d6(segs):
    """D-6 Sinking: *au → ū everywhere (*hau → ū 'a single exhaled
    vowel', *hau-tel → ūtel)."""
    return ["ū" if s == "au" else s for s in segs]


def _d7(segs):
    """D-7 Apocope: final short vowel lost after a heavy syllable, the
    Sūchel SC-7 pattern (*tem-a → tem) — but never after a long vowel:
    apocope does not create superheavy CVːC (Nūbi keeps its -i)."""
    out = list(segs)
    idx = real_indices(out)
    vowels = [i for i in idx if is_vowel(out[i])]
    if len(vowels) < 2:
        return out
    last = idx[-1]
    if out[last] not in SHORT_VOWELS:
        return out
    prev_v = vowels[-2]
    if out[prev_v] not in SHORT_VOWELS:
        return out
    between = [i for i in idx if prev_v < i < last]
    if len(between) == 1:
        del out[last]
    return out


def _rep_ks(segs):
    """Romanization repair: Nubhel spells /ks/ as 'ks' (*nex- → neks,
    'cluster kept', docs/06 §05) where family orthography writes x."""
    out: List[str] = []
    for s in segs:
        if s == "x":
            out.extend(["k", "s"])
        else:
            out.append(s)
    return out


NUBHEL = Deriver(
    name="Nubhel",
    changes=[
        Change("D-3", "breath-loss: all h -> 0, non-initial w -> 0, with "
                      "compensatory lengthening (ordered before D-1)", _d3),
        Change("D-1", "deep palatalization: k -> h, g -> y before front "
                      "vowels (ordered after D-3)", _d1),
        Change("D-2", "fortition: word-initial w -> b", _d2),
        Change("D-4", "pressure-rounding: stressed (initial) a -> o", _d4),
        Change("D-5", "held-breath drift: high vowel lengthens in an open "
                      "stressed non-final syllable", _d5),
        Change("D-6", "sinking: au -> ū everywhere", _d6),
        Change("D-7", "apocope of a final short vowel (blocked after a "
                      "long vowel)", _d7),
    ],
    repairs=[Change("REP", "romanization: x spelled ks (cluster kept)", _rep_ks)],
)


# ---------------------------------------------------------------------------
# lexicon (docs/06 §05, plus the shared items the texts and §03–04 use)


@dataclass
class LexEntry:
    """One codex row — same shape as :class:`odylang.suchel.LexEntry`,
    but :meth:`derive` runs the NUBHEL deriver."""

    form: str                    # citation form as the codex spells it
    ipa: str                     # codex IPA ('' where the codex gives none)
    gloss: str
    etym: str                    # the codex's derivation column, verbatim
    domain: str                  # core/physics/fleet/grammar/number
    kind: str = "proto"          # proto | daughter | register | grammar
    proto: Optional[str] = None  # proto-form fed to the engine
    cited: Tuple[str, ...] = ()  # changes expected to fire (locked by tests)
    adjustments: Tuple[Adjustment, ...] = ()
    members: Tuple[str, ...] = ()  # component forms for daughter formations
    source: str = "docs/06"

    def derive(self) -> Optional[Derivation]:
        if self.proto is None:
            return None
        return NUBHEL.derive(self.proto, self.adjustments)


def _E(*args, **kw) -> LexEntry:
    return LexEntry(*args, **kw)


_L: List[LexEntry] = [
    # -- §05 working lexicon, in codex order ---------------------------------
    _E("Nubhel", "ˈnub.hel", "the deep-speech; this language",
       "*nub-kel → D-3 then D-1 (secondary h survives)", "core",
       proto="*nub-kel", cited=("D-1",)),
       # D-3 fires vacuously on *nub-kel (no old *h to kill) — the codex
       # cites it for its ORDERING: run D-1 first and D-3 eats the new h
       # (†nūbel).  The counterfactual is locked by tests.
    _E("Nūbi", "ˈnuː.bi", "the divers; the vertical fleet",
       "*nub-i → D-5", "fleet", proto="*nub-i", cited=("D-5",)),
    _E("Sūl", "suːl", "crosser (their word for the Sīli)",
       "*suw-il → D-3", "fleet", proto="*suw-il", cited=("D-3",)),
    _E("Sūhel", "ˈsuː.hel", "Sūchel, the crossing-speech",
       "*suw-kel → D-3, D-1", "core", proto="*suw-kel", cited=("D-3", "D-1")),
    _E("hel", "hel", "speech; tongue", "*kel → D-1", "core",
       proto="*kel", cited=("D-1",)),
    _E("yel", "jel", "the seam 𝔍", "*gel- → D-1", "physics",
       proto="*gel", cited=("D-1",)),
    _E("yed", "jed", "to go (with directional)", "*ged- → D-1", "core",
       proto="*ged", cited=("D-1",)),
    _E("kod", "kod", "beacon; kept time", "*kad- → D-4", "fleet",
       proto="*kad", cited=("D-4",)),
    _E("kodur", "ˈko.dur", "beacon-cycle (the unit of the offset)",
       "kod + -ur", "fleet", kind="daughter", members=("kod", "-ur")),
    _E("ber", "ber", "truth; to speak-true", "*wer- → D-2", "core",
       proto="*wer", cited=("D-2",)),
    _E("bur", "bur", "to spin; to go mad", "*wur- → D-2", "core",
       proto="*wur", cited=("D-2",)),
    _E("bos", "bos", "wound", "*wos- → D-2", "core",
       proto="*wos", cited=("D-2",)),
    _E("bel", "bel", "nothing; hearth (merged)", "*wel- → D-2, = *bel-",
       "core", proto="*wel", cited=("D-2",)),
    _E("mor", "mor", "rock; pearl (merged)", "*mor- / *mar- → D-4", "core",
       proto="*mar", cited=("D-4",)),
    _E("ton", "ton", "to hold, keep", "*tan- → D-4", "core",
       proto="*tan", cited=("D-4",)),
    _E("ron", "ron", "to run", "*ran- → D-4", "core",
       proto="*ran", cited=("D-4",)),
    _E("ōl", "oːl", "to surface", "*haw-ol- → D-3", "fleet",
       proto="*haw-ol", cited=("D-3",)),
    _E("ū", "uː", "up; surfaceward (directional)", "*hau → D-3, D-6",
       "grammar", proto="*hau", cited=("D-3", "D-6")),
    _E("ūtel", "ˈuː.tel", "breach-up; overshooting ascent", "*hau-tel",
       "grammar", proto="*hau-tel", cited=("D-3", "D-6"),
       members=("ū", "tel")),
    _E("len", "len", "level; along this depth", "*len-", "grammar",
       proto="*len", cited=()),
    _E("nub", "nub", "down (directional)", "*nub-", "grammar",
       proto="*nub", cited=()),
    _E("dolnub", "ˈdol.nub", "pitward; a committed deep dive", "*dol-nub",
       "grammar", proto="*dol-nub", cited=()),
       # treated as proto-derived: the compound is old enough to feed the
       # engine, which passes it through unchanged (no rule applies).
    _E("neks", "neks", "the gap-particle; unshared time",
       "*nex- (cluster kept)", "grammar", proto="*nex", cited=()),
    _E("tem", "tem", "pattern", "*tem-a → D-7", "physics",
       proto="*tem-a", cited=("D-7",)),
    _E("ān", "aːn", "breath", "*anh- → D-3", "core",
       proto="*anh", cited=("D-3",)),
    _E("nā", "naː", "ship", "*nāw- → D-3", "fleet",
       proto="*nāw", cited=("D-3",)),
    _E("nāmai", "ˈnaː.mai", "one's own ship (entangled)",
       "nā + -mai (*mag-i, shared)", "fleet", kind="daughter",
       members=("nā", "-mai")),
    _E("enmai", "ˈen.mai", "we, crew-we (entangled)",
       "shared inheritance — kin-words are family-stable", "grammar",
       kind="daughter", members=("en", "-mai")),
    _E("on", "on", "she/he/it (3SG)", "*an- → D-4", "grammar",
       proto="*an", cited=("D-4",)),
    _E("so", "so", "one", "*sa → D-4 (the counting test)", "number",
       proto="*sa", cited=("D-4",)),
    _E("dok", "dok", "ten", "*dak → D-4 (the counting test)", "number",
       proto="*dak", cited=("D-4",)),
    # -- shared items the §03 examples, §04 table and §06 texts use ----------
    _E("en", "en", "I (1SG)", "*en- (shared)", "grammar",
       proto="*en", cited=(), source="docs/06 §03/§06"),
    _E("mek", "mek", "four (mek-dok 'four-ten' = forty, the offset "
       "signature)", "*mek- (shared)", "number",
       proto="*mek", cited=(), source="docs/06 §03"),
    _E("ep", "ep", "seven", "*hep → D-3 (Nubhel killed all h: the divers "
       "surface without breath, hōl vs ōl)", "number",
       proto="*hep", cited=("D-3",), source="docs/06 §04"),
    _E("-mai", "mai", "entangled-possession suffix",
       "*mag-i 'bound' — shared, family-stable (docs/06 §05): inherited "
       "as data, not re-derived (D-4 never operated on kin-words)",
       "grammar", kind="register", members=("*mag-i",)),
    _E("-ur", "ur", "duration suffix (kodur)", "*-ur", "grammar",
       proto="*-ur", cited=()),
    _E("ve", "ve", "to be (copula)",
       "*we- — attested ve (TEXT 01) against D-2's expected †be: the "
       "copula cliticized before fortition", "grammar", kind="register",
       members=("*we-",), source="docs/06 §06 TEXT 01"),
]

LEXICON: Dict[str, LexEntry] = {e.form: e for e in _L}


def lookup(form: str) -> LexEntry:
    return LEXICON[form]


def entries(domain: Optional[str] = None) -> List[LexEntry]:
    return [e for e in _L if domain is None or e.domain == domain]


def derive(proto: str) -> Derivation:
    """Run a proto-form through the seven deep changes (no adjustments)."""
    return NUBHEL.derive(proto)


# ---------------------------------------------------------------------------
# §04 — ACROSS THE COGNATE GAP: the false-friends table
#
# Each row records the codex's three display columns and its note, plus
# machine-checkable pairs: *_checks run raw through the derivers;
# suchel_lexicon rows go through odylang.suchel.LEXICON (where the Sūchel
# codex itself flags the form irregular — adjustment applied);
# suchel_compose rows are Sūchel daughter formations (compose of members).


@dataclass(frozen=True)
class FalseFriend:
    proto: str
    suchel: str
    nubhel: str
    note: str
    suchel_checks: Tuple[Tuple[str, str], ...] = ()
    nubhel_checks: Tuple[Tuple[str, str], ...] = ()
    suchel_lexicon: Tuple[Tuple[str, str], ...] = ()
    suchel_compose: Tuple[Tuple[str, str], ...] = ()
    skip_note: str = ""


#: docs/06 §01 THE TWO FLEETS — one rivalry, two grammars.  Each fleet
#: grammaticalized the regime it lives in (the DESIGN THESIS): Sūchel built
#: its verb around the seam, Nubhel around the dive.
TWO_FLEETS = {
    "sili": {
        "name": "The Sīli · crossers · Sūchel",
        "orientation": "horizontal; seam-oriented",
        "prestige": "the crossing and the T• mood",
        "wound": "the gap — lives punctuated by ne-holes no one can narrate",
        "regime": "indeterminate",
        "calls_the_others": ("nuvi", "the aged"),
        "sneer": '"divers go fast to stay in one universe"',
    },
    "nubi": {
        "name": "The Nūbi · divers · Nubhel",
        "orientation": "vertical; depth-oriented",
        "prestige": "class — how deep a hull can hold",
        "wound": "the offset — they age past everyone they love, "
                 "by a measurable count",
        "regime": "determinate",
        "calls_the_others": ("Sūl", "the gapped", "hollow-lived"),
        "sneer": '"crossing is a shortcut; depth is the truth"',
    },
}

FALSE_FRIENDS: Tuple[FalseFriend, ...] = (
    FalseFriend("*gel-", "jel", "yel",
                "the seam — the shibboleth row extends: gel · jel · ghel · "
                "zel · dzel · yel",
                suchel_checks=(("*gel", "jel"),),
                nubhel_checks=(("*gel", "yel"),)),
    FalseFriend("*kel", "chel", "hel",
                "speech — in the deep tongue, to speak is to breathe out",
                suchel_checks=(("*kel", "chel"),),
                nubhel_checks=(("*kel", "hel"),)),
    FalseFriend("*suw-kel", "Sūchel", "Sūhel",
                "the crossing-speech — one phoneme apart; the minimal pair "
                "of the rivalry",
                suchel_checks=(("*suw-kel", "sūchel"),),
                nubhel_checks=(("*suw-kel", "sūhel"),)),
    FalseFriend("*sow-orn", "Sōrn", "Sōrn",
                "the drive — identical. Everyone agrees on the engine.",
                suchel_checks=(("*sow-orn", "sōrn"),),
                nubhel_checks=(("*sow-orn", "sōrn"),)),
    FalseFriend("*kad", "kad", "kod",
                "beacon — close enough to catch, far enough to mark the "
                "accent",
                suchel_checks=(("*kad", "kad"),),
                nubhel_checks=(("*kad", "kod"),)),
    FalseFriend("*wer-", "ver", "ber",
                'truth — crossers joke that divers "bury the truth"; divers '
                'reply that crossers "thin it"',
                suchel_checks=(("*wer", "ver"),),
                nubhel_checks=(("*wer", "ber"),)),
    FalseFriend("*nub-", "nuv", "nub",
                "down — one consonant of drift on the family's favorite "
                "direction",
                suchel_lexicon=(("nuv", "nuv"),),
                nubhel_checks=(("*nub", "nub"),),
                skip_note="Sūchel nuv is codex-flagged irregular ('final "
                          "devoicing resisted; SC-6 analog') — checked via "
                          "the Sūchel lexicon entry's adjustment"),
    FalseFriend("*ged-", "jed", "yed",
                "to go — transparent both ways",
                suchel_checks=(("*ged", "jed"),),
                nubhel_checks=(("*ged", "yed"),)),
    FalseFriend("*tan-", "tan", "ton",
                "to hold — trap: Nubhel ton sounds like Sūchel tem-adjacent "
                "noise on a bad channel; hold vs pattern confusions are a "
                "known accident class",
                suchel_checks=(("*tan", "tan"),),
                nubhel_checks=(("*tan", "ton"),)),
    FalseFriend("*mar / *mor", "mar · mor", "mor",
                'merger: pearl and rock are one word to divers — "they '
                'cannot tell a pearl from a stone"',
                suchel_checks=(("*mar", "mar"), ("*mor", "mor")),
                nubhel_checks=(("*mar", "mor"), ("*mor", "mor"))),
    FalseFriend("*wel / *bel", "vel · bel", "bel",
                'merger: nothing and hearth are one word — "the hearth is '
                'nothing to us"',
                suchel_checks=(("*wel", "vel"), ("*bel", "bel")),
                nubhel_checks=(("*wel", "bel"), ("*bel", "bel"))),
    FalseFriend("*nex-", "ne", "neks",
                "the gap — physics in one mouth, courtesy in the other",
                suchel_lexicon=(("ne", "ne"),),
                nubhel_checks=(("*nex", "neks"),),
                skip_note="Sūchel ne is a grammaticalized particle clip "
                          "(the codex: the noun nexath keeps the cluster) — "
                          "checked via the Sūchel lexicon entry's adjustment"),
    FalseFriend("*sa, *dak", "sa … dak", "so … dok",
                "one … ten — the counting test: customs makes you count to "
                "ten; the vowels file your fleet",
                suchel_checks=(("*sa", "sa"), ("*dak", "dak")),
                nubhel_checks=(("*sa", "so"), ("*dak", "dok"))),
    FalseFriend("*hep", "hep", "ep",
                "seven — Sūchel keeps initial h; Nubhel killed all h. The "
                "divers surface without breath: hōl vs ōl",
                suchel_checks=(("*hep", "hep"), ("*haw-ol", "hōl")),
                nubhel_checks=(("*hep", "ep"), ("*haw-ol", "ōl"))),
    FalseFriend("*suw-il / *nub-i", "sīl · nuvi", "Sūl · Nūbi",
                "crosser · diver — each fleet's name for itself and the "
                "other; four words, one rivalry",
                suchel_checks=(("*suw-il", "sīl"),),
                suchel_compose=(("nuvi", "nuvi"),),
                nubhel_checks=(("*suw-il", "sūl"), ("*nub-i", "nūbi")),
                skip_note="Sūchel nuvi is a daughter formation (nuv + "
                          "agent -i), not a direct reflex of *nub-i — "
                          "checked via compose"),
)
