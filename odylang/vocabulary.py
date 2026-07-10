"""The vocabulary supplement — a working vocabulary for daily speech.

The six codices give Sūchel its four grammatical systems and a working
lexicon of ~95 culturally loaded entries; what they deliberately leave out
is the plain furniture of a life: *mother*, *water*, *sleep*, *knife*,
*cold*.  This module supplies it **the way the codices built everything
else**: each entry is a new Old Pelagic root (coined inside the attested
proto inventory and root canon), and every daughter form on this page is
*derived by the sound-change engines*, never typed.  Coin once, inherit
five times: a root entered here immediately exists in Sūchel, Nubhel,
Rudgar, Sel, and Beltsel, each wearing its own regular sound laws.

Provenance: this is a post-codex supplement (REV 1.2), clearly separate
from the canon lexicons in :mod:`odylang.suchel` / :mod:`odylang.nubhel`.
Where a coinage lands on an existing Sūchel surface form, the homophony is
deliberate and carries a note — tests refuse silent collisions.

Authoring rules (enforced by tests):

* proto segments only: p b t d k g s z h w m n r l dz ks + a e i o u,
  long vowels sparingly, the *au* diphthong; roots are mostly CVC like the
  attested stock (*kad-, *tem-, *dur-*), with a scatter of heavier shapes
  (*mahin*-class) so the reductive changes have something to eat;
* verbs that need the SC-7 apocope are entered with their late-OP theme
  vowel (*CVC-a*), exactly like the codex's *tem-a, *kap-a;
* front vowels are spent deliberately: a root with *k g s* + *e i* is a
  root that WANTS to come out ch/j/sh in Sūchel and h/y/s in Nubhel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .suchel import LEXICON as CANON, SUCHEL, compose
from .word import Word

# ---------------------------------------------------------------------------
# the roots — (proto, gloss, domain[, note])
#
# domains: kin · body · world · sea · sky · time · ship · tools · food
#          · beasts · qualities · verbs · mind · number

_R: List[Tuple] = [
    # -- kin & people --------------------------------------------------------
    ("*ama", "mother", "kin"),
    ("*ata", "father", "kin"),
    ("*bem-", "child", "kin"),
    ("*siru", "sibling; crossing-partner", "kin",
     "the word for a sibling is the word for the one who shares your dives"),
    ("*dam-", "friend; hearth-mate", "kin"),
    ("*gur-", "stranger; one from outside coverage", "kin"),
    ("*mahir", "captain", "kin",
     "*mahin 'hand' with the agent grade: the hand that steers"),
    ("*welan", "widow; the one left in coverage", "kin"),
    ("*nom-", "name", "kin"),
    ("*bal-", "elder; keel-laid-first", "kin"),
    # -- body -----------------------------------------------------------------
    ("*kep-", "head", "body"),
    ("*luk-", "eye", "body"),
    ("*tol-", "ear", "body"),
    ("*ned-", "heart", "body"),
    ("*bon-", "bone", "body"),
    ("*der-", "skin; hull of the body", "body"),
    ("*pod-", "foot", "body"),
    ("*gisi", "voice", "body",
     "the *isi-class shape: SC-1 twice then apocope — jish"),
    ("*mus-", "flesh; muscle", "body"),
    ("*sen-a", "to breathe (v.)", "body",
     "homophone of shen 'six' by regular change — counting is breathing, "
     "the divers say"),
    # -- world ----------------------------------------------------------------
    ("*wat-", "water (fresh); drinking water", "world"),
    ("*sal-", "salt; the sea's taste", "world"),
    ("*tir-", "earth, ground; settled land", "world"),
    ("*pir-", "fire", "world"),
    ("*luz-", "light", "world"),
    ("*dzem-", "shadow, dark", "world"),
    ("*wen-", "wind", "world"),
    ("*raud-", "storm", "world"),
    ("*sniw-", "rain; falling water", "world",
     "final glide hardens: sniv, like nav"),
    ("*kir-", "cold", "world",
     "SC-1 bites: the fleets' cold is chir"),
    ("*tep-a", "warm; kept-alive (v. 'to hold warmth')", "world",
     "the lenition chain hides the root: tepa > teva > tev"),
    # -- sea -------------------------------------------------------------------
    ("*maur-", "wave", "sea",
     "SC-5: mōr — a minimal pair with mor 'reef': the wave is the long rock"),
    ("*tid-", "tide; the breathing of the sea", "sea"),
    ("*grun-", "seafloor; the true bottom", "sea"),
    ("*skum-", "foam; spent wave", "sea"),
    ("*mig-", "fish", "sea"),
    ("*welk-", "kelp; weed of the deep", "sea"),
    ("*salm-", "current (of water); the sea's road", "sea"),
    # -- sky -------------------------------------------------------------------
    ("*ster-", "star", "sky"),
    ("*lun-", "moon; any moon", "sky"),
    ("*sol-", "sun; the home star", "sky"),
    ("*heban", "sky; the upper sea", "sky",
     "word-initial *h survives, hōl-class: the sky keeps its breath"),
    ("*nub-es", "cloud (lit. place-of-under)", "sky",
     "the *nub- root read upward: a cloud is a deep seen from below"),
    # -- time ------------------------------------------------------------------
    ("*dag-", "day; one waking", "time"),
    ("*dzun-", "night", "time",
     "the *dzu- 'adrift' family: night is the daily dark time"),
    ("*ger-", "year; one full beacon-round", "time"),
    ("*nun-", "now; this pulse", "time"),
    ("*ant-", "before; upstream in time", "time"),
    ("*pos-", "after; downstream in time", "time"),
    ("*sob-a", "to sleep (v.)", "time"),
    ("*drem-", "dream; unanchored seeing", "time",
     "what you see in =zu time without leaving your bunk"),
    ("*ald-", "old; worn smooth", "time"),
    ("*niw-", "new; unworn", "time"),
    # -- ship ------------------------------------------------------------------
    ("*kil-", "keel; the first truth of a ship", "ship"),
    ("*stur-", "mast; the ship's tower", "ship",
     "the s-grade of *tur- 'tower': every ship carries a small tower"),
    ("*stir-a", "to steer (v.)", "ship"),
    ("*sekel", "sail; wind-catcher", "ship",
     "unrecognizable by regular change alone: shechel"),
    ("*hul-", "hull", "ship"),
    ("*port-a", "hatch, door (v. 'to open a way' > n.)", "ship"),
    ("*gom-", "cargo; carried weight", "ship"),
    ("*rem-", "oar; to row", "ship"),
    # -- tools -----------------------------------------------------------------
    ("*skir-", "knife, blade", "tools",
     "four cuts of a blade wrote jel; this is the blade itself"),
    ("*ham-", "hammer; striking stone", "tools"),
    ("*sag-", "saw; toothed blade", "tools"),
    ("*seg-", "rope, line", "tools",
     "s and g both shift: sheg"),
    ("*net-", "net; woven catcher", "tools"),
    ("*kop-a", "cup, vessel (v. 'to hold liquid')", "tools",
     "lenition: kov — a minimal pair with kav, the limit Κ"),
    ("*pan-", "pan; flat vessel", "tools"),
    ("*wag-", "cart; rolling carrier", "tools"),
    # -- food ------------------------------------------------------------------
    ("*ed-a", "to eat (v.)", "food"),
    ("*bib-a", "to drink", "food"),
    ("*brod-", "bread; keel-loaf", "food"),
    ("*lem-", "milk", "food"),
    ("*sup-", "soup, broth; wet meal", "food"),
    ("*sem-", "seed", "food"),
    ("*kres-a", "to grow (v.)", "food"),
    ("*dap-", "meat, flesh-food", "food"),
    # -- beasts ----------------------------------------------------------------
    ("*hund-", "dog; hold-beast", "beasts"),
    ("*kat-", "cat; ship-cat", "beasts",
     "every hull carries one; the cat is exempt from muster"),
    ("*wurm-", "worm; hull-borer", "beasts"),
    ("*wegel", "bird; air-swimmer", "beasts",
     "two changes deep: vejel"),
    ("*kabal", "horse; ground-runner", "beasts",
     "a ground-sider loan, and the shape shows it"),
    # -- qualities --------------------------------------------------------------
    ("*mag-", "big, great", "qualities"),
    ("*min-", "small", "qualities"),
    ("*lam-", "long", "qualities"),
    ("*tuk-", "short", "qualities"),
    ("*dem-", "heavy", "qualities"),
    ("*lit-", "light (in weight)", "qualities"),
    ("*rap-a", "fast (v. 'to run hot')", "qualities",
     "lenition hides it: rav"),
    ("*hal-", "slow; held-back", "qualities"),
    ("*bon-a", "good; sound (of hulls and hearts) (v. 'to be sound')",
     "qualities", "the noun *bon- 'bone' and the verb *bon-a 'be sound' "
     "merge at the surface: soundness is bone-deep"),
    ("*mal-", "bad; unsound", "qualities"),
    ("*pol-", "full", "qualities"),
    ("*wak-", "empty; hollow", "qualities"),
    ("*lek-", "near; within hail", "qualities"),
    ("*telur", "far; at reach's end", "qualities",
     "the *tel- 'reach' root with the duration grade: far is a long reach"),
    ("*reg-i", "straight; true-cut", "qualities",
     "palatalized and clipped: rej"),
    ("*kriw-", "crooked; off-true", "qualities"),
    # -- verbs -------------------------------------------------------------------
    ("*wid-a", "to see", "verbs"),
    ("*klut-a", "to hear", "verbs"),
    ("*dot-a", "to give", "verbs"),
    ("*kap-er", "to take, seize", "verbs",
     "the *kap- 'hold' root with the active grade — the limit Κ is a "
     "taking that never completes"),
    ("*mak-a", "to make, build", "verbs"),
    ("*brek-a", "to break", "verbs"),
    ("*mend-a", "to mend, repair", "verbs"),
    ("*port-er", "to carry", "verbs"),
    ("*gek-a", "to throw", "verbs"),
    ("*bind-a", "to bind, lash", "verbs"),
    ("*snid-a", "to cut", "verbs"),
    ("*bren-a", "to burn", "verbs"),
    ("*nad-a", "to swim", "verbs"),
    ("*pal-a", "to fall", "verbs"),
    ("*stan-a", "to stand", "verbs",
     "the attested *stan 'station, stand' of Werstan, as a verb"),
    ("*sed-a", "to sit", "verbs"),
    ("*ben-a", "to come", "verbs"),
    ("*lib-a", "to live", "verbs"),
    ("*nek-a", "to die", "verbs",
     "one segment from *nex- 'the gap': to die is to almost-gap; fleet "
     "speech still prefers 'she has gone adrift'"),
    ("*wend-a", "to find (one's way to)", "verbs"),
    ("*lus-a", "to lose", "verbs"),
    # -- mind ---------------------------------------------------------------------
    ("*wis-a", "to know", "mind"),
    ("*log-a", "to think, reason", "mind",
     "the Wolori's verb: Logos conjugates as log-a=mi"),
    ("*wil-a", "to want", "mind"),
    ("*lup-a", "to love", "mind",
     "regular lenition: lupa > luva > luv"),
    ("*dred-", "fear", "mind"),
    ("*gaud-", "joy", "mind"),
    ("*trur-", "grief; the ne-shaped feeling", "mind"),
    ("*hop-a", "to hope; to hold toward T⁻", "mind",
     "the mood -im is hope conjugated; this is hope as a verb"),
    ("*mem-", "memory; what the gap cannot hold", "mind"),
    # -- number & measure ----------------------------------------------------------
    ("*kent-", "hundred", "number",
     "palatalized: chent"),
    ("*halb-", "half", "number"),
    ("*mol-i", "many", "number"),
    ("*paw-", "few", "number"),
    ("*met-ur", "measure; taken size", "number",
     "the -ur duration grade of *met-: a measure is a held count"),
]

# -- daughter-formation compounds (built from surface forms, like the codex's
#    zukad, nuvran, velosh) — (form-members, gloss, domain, note)
_C: List[Tuple] = [
    (("sal", "vat"), "seawater; brine", "sea", None),
    (("luz", "kad"), "lighthouse-pulse; a beacon's visible light", "sky", None),
    (("ster", "ren"), "star-road; a plotted course", "sky",
     "what the navigator draws before the drive speaks"),
    (("nav", "dol"), "shipyard (lit. ship-pit)", "ship", None),
    (("kil", "ver"), "keel-truth; a fact that survives docking", "mind",
     "what remains true when the voyage is over"),
    (("zem", "kad"), "eclipse; a beacon shadowed", "sky", None),
    (("tid", "kadur"), "tide-cycle; a working month", "time", None),
    (("mem", "dol"), "archive (lit. memory-pit)", "mind", None),
    (("mig", "net"), "fishing net", "tools", None),
    (("tan", "dol"), "anchor (lit. hold-pit); the held pause", "ship", None),
    (("pir", "mor"), "volcano (lit. fire-rock)", "world", None),
    (("ven", "osh"), "storm-front (lit. wind-mouth)", "world", None),
    (("luk", "mar"), "lens (lit. eye-pearl)", "tools", None),
    (("kru", "ren"), "vein (lit. blood-path)", "body", None),
    (("sol", "hau"), "dawn; sun surfacing", "time", None),
    (("sol", "nuv"), "dusk; sun diving", "time", None),
]


@dataclass
class VocabEntry:
    proto: Optional[str]        # None for daughter compounds
    suchel: str                 # derived (or composed) — never typed
    ipa: str
    gloss: str
    domain: str
    note: str = ""
    members: Tuple[str, ...] = ()
    homophone_of: str = ""      # deliberate collision with a canon form

    def trace(self) -> str:
        if self.proto:
            return SUCHEL.derive(self.proto).trace()
        return " + ".join(self.members) + f" -> {self.suchel} (compound)"


# deliberate homophones with canon forms (anything else is a test failure)
_INTENDED_HOMOPHONES = {
    "shen": "shen 'six' — counting is breathing, the divers say",
    "bon": "bon 'bone' / bon-a 'be sound' — soundness is bone-deep",
}


def _ipa_of(form: str) -> str:
    return Word.plain(form).ipa()


def _build() -> List[VocabEntry]:
    out: List[VocabEntry] = []
    seen: Dict[str, str] = {}
    for row in _R:
        proto, gloss, domain = row[0], row[1], row[2]
        note = row[3] if len(row) > 3 else ""
        form = SUCHEL.derive(proto).form
        homo = ""
        if form in CANON or form in seen:
            homo = _INTENDED_HOMOPHONES.get(form, "")
        out.append(VocabEntry(proto, form, _ipa_of(form), gloss, domain,
                              note, homophone_of=homo))
        seen.setdefault(form, gloss)
    for members, gloss, domain, note in _C:
        form = compose(*members)
        out.append(VocabEntry(None, form, _ipa_of(form), gloss, domain,
                              note or "", members=tuple(members)))
    return out


VOCAB: List[VocabEntry] = _build()
BY_FORM: Dict[str, VocabEntry] = {e.suchel: e for e in VOCAB}
DOMAINS: List[str] = sorted({e.domain for e in VOCAB})


def entries(domain: Optional[str] = None,
            search: Optional[str] = None) -> List[VocabEntry]:
    out = VOCAB
    if domain:
        out = [e for e in out if e.domain == domain]
    if search:
        q = search.lower()
        out = [e for e in out
               if q in e.suchel.lower() or q in e.gloss.lower()
               or (e.proto or "").lower().find(q) >= 0]
    return out


def reflexes(entry: VocabEntry) -> Dict[str, str]:
    """The coined root through every mouth (compounds are Sūchel-internal)."""
    if not entry.proto:
        return {"suchel": entry.suchel}
    from .family import reflexes as fam
    return fam(entry.proto)
