"""Sūchel — the Crossing-Speech, first daughter of Old Pelagic (docs/01).

Seven ordered, regular sound changes (docs/01 §03) turn Old Pelagic into
the tongue of the fleets; every canon name — Sōrn, Idrenes, Pelgar, jel —
falls out as a regular outcome.  The full working lexicon of the codex
(docs/01 §06, 80 entries) plus the phrasebook's fourteen appendix coinages
(docs/02 §F) live in :data:`LEXICON`; each proto-sourced entry is derived
by the engine and the result is locked by tests.

Where the codex itself flags a special development (``sū`` "v., irregular";
``nuv`` "SC-6 analog"; ``nav`` "shortening in closed syll.") the entry
carries an :dataclass:`~odylang.soundchange.Adjustment` quoting the codex —
irregularity is data here, never silent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .phonology import (FRONT_VOWELS, is_long, is_vowel, lengthen, romanize)
from .soundchange import (Adjustment, Change, Derivation, Deriver, next_real,
                          parse_proto, prev_real, real_indices)

# ---------------------------------------------------------------------------
# the seven changes (docs/01 §03)


def _sc1(segs):
    """SC-1 Palatalization: *k, *g -> ch, j before front vowels — and the
    codex's 'SC-1 analog': s -> sh in the same environment (ish, lesh, shen)."""
    out = list(segs)
    i = 0
    while i < len(out):
        s = out[i]
        j = next_real(out, i)
        if j is None or out[j] not in FRONT_VOWELS:
            i += 1
            continue
        if s == "k":
            out[i] = "ch"
        elif s == "g":
            p = prev_real(out, i)
            if out[j] == "i" and p is not None and out[p] == "a":
                # the full chain of docs/01: g → j → ∅ /a_i, with coalescence
                # (*mag-i -> mai)
                del out[i]
                i -= 1
            else:
                out[i] = "j"
        elif s == "s":
            out[i] = "sh"
        i += 1
    return out


def _sc2(segs):
    """SC-2 Medial syncope: with Old Pelagic initial stress, the unstressed
    short vowel of the second syllable is lost between single consonants
    (*pelag-ar -> Pelgar, *ideren-es -> Idrenes).  Needs a following vowel
    for the stranded consonant to attach to — somath, kadur are immune."""
    idx = real_indices(segs)
    vowels = [i for i in idx if is_vowel(segs[i])]
    if len(vowels) < 3:
        return segs
    v0, v1, v2 = vowels[0], vowels[1], vowels[2]
    between01 = [i for i in idx if v0 < i < v1]
    between12 = [i for i in idx if v1 < i < v2]
    if (len(between01) == 1 and len(between12) == 1
            and segs[v1] in ("a", "e", "i", "o", "u")):
        return [s for k, s in enumerate(segs) if k != v1]
    return segs


def _sc3(segs):
    """SC-3 Glide loss: V₁wV₁ and uwi coalesce to a long vowel (Sōrn, sīl);
    *w -> ∅ before C with compensatory lengthening (Sūchel); *w -> v at
    word edges (ver, pev)."""
    out = list(segs)
    # (a) coalescence across the glide
    i = 0
    while i < len(out):
        if out[i] == "w":
            p, n = prev_real(out, i), next_real(out, i)
            if p is not None and n is not None and is_vowel(out[p]) and is_vowel(out[n]):
                if out[p] == out[n]:
                    out[p] = lengthen(out[p])
                    del out[p + 1: n + 1]
                    i = p
                elif out[p] == "u" and out[n] == "i":
                    out[p] = "ī"
                    del out[p + 1: n + 1]
                    i = p
        i += 1
    # (b) loss before a consonant, lengthening the preceding vowel
    i = 0
    while i < len(out):
        if out[i] == "w":
            p, n = prev_real(out, i), next_real(out, i)
            if (p is not None and is_vowel(out[p])
                    and n is not None and not is_vowel(out[n])):
                out[p] = lengthen(out[p])
                del out[i]
                continue
        i += 1
    # (c) fortition at word edges
    idx = real_indices(out)
    if idx and out[idx[0]] == "w":
        out[idx[0]] = "v"
    idx = real_indices(out)
    if idx and out[idx[-1]] == "w":
        out[idx[-1]] = "v"
    return out


def _sc4(segs):
    """SC-4 H-loss: non-initial *h -> ∅, lengthening a preceding vowel
    (*mahin -> mān, *anh- -> ān); /h/ survives only word-initially
    (hōl, hau, hep — docs/03 §01, docs/04 §01)."""
    out = list(segs)
    idx = real_indices(out)
    i = 0
    while i < len(out):
        if out[i] == "h" and (not idx or i != idx[0]):
            p = prev_real(out, i)
            if p is not None:
                if is_vowel(out[p]):
                    out[p] = lengthen(out[p])
                else:
                    pp = prev_real(out, p)
                    if pp is not None and is_vowel(out[pp]):
                        out[pp] = lengthen(out[pp])
            n = next_real(out, i)
            del out[i]
            # absorb an i left in hiatus after a fresh long vowel: māin -> mān
            p = prev_real(out, i) if i < len(out) else prev_real(out, len(out) - 1)
            if (p is not None and is_long(out[p])):
                n = next_real(out, p)
                if n is not None and out[n] == "i":
                    nn = next_real(out, n)
                    if nn is None or not is_vowel(out[nn]):
                        del out[n]
            idx = real_indices(out)
            continue
        i += 1
    return out


def _sc5(segs):
    """SC-5 Monophthongization: *au -> ō except word-finally (hōl, but hau
    keeps its diphthong at the word's edge); a same-quality vowel left in
    hiatus merges (*haw-ol- -> hōl)."""
    out = list(segs)
    idx = real_indices(out)
    i = 0
    while i < len(out):
        if out[i] == "au" and (not idx or i != idx[-1]):
            out[i] = "ō"
            n = next_real(out, i)
            if n is not None and out[n] == "o":
                del out[n]
            idx = real_indices(out)
        i += 1
    return out


def _sc6(segs):
    """SC-6 Lenition: intervocalic *p -> v (*kap-a -> kava)."""
    out = list(segs)
    for i, s in enumerate(out):
        if s == "p":
            p, n = prev_real(out, i), next_real(out, i)
            if (p is not None and is_vowel(out[p])
                    and n is not None and is_vowel(out[n])):
                out[i] = "v"
    return out


def _sc7(segs):
    """SC-7 Apocope: a word-final short vowel after a single consonant is
    lost once the word would stay pronounceable (*tem-a -> tem, kava -> kav).
    Monosyllables keep their vowel (sa, ve, zu)."""
    out = list(segs)
    idx = real_indices(out)
    vowels = [i for i in idx if is_vowel(out[i])]
    if len(vowels) < 2:
        return out
    last = idx[-1]
    if out[last] not in ("a", "e", "i", "o", "u"):
        return out
    prev_v = vowels[-2]
    between = [i for i in idx if prev_v < i < last]
    if len(between) == 1:
        del out[last]
    return out


def _rep_dz(segs):
    """Cleanup: the daughter inventory has no /dz/; word-initial *dz -> z
    (*dzu- -> zu, docs/01 lexicon)."""
    out = list(segs)
    idx = real_indices(out)
    if idx and out[idx[0]] == "dz":
        out[idx[0]] = "z"
    return out


SUCHEL = Deriver(
    name="Sūchel",
    changes=[
        Change("SC-1", "palatalization: k,g -> ch,j (and s -> sh) before front vowels", _sc1),
        Change("SC-2", "medial syncope of the post-tonic short vowel", _sc2),
        Change("SC-3", "glide loss: coalescence, pre-C loss with lengthening, edge w -> v", _sc3),
        Change("SC-4", "non-initial h-loss with compensatory lengthening", _sc4),
        Change("SC-5", "monophthongization au -> ō (not word-final)", _sc5),
        Change("SC-6", "lenition: intervocalic p -> v", _sc6),
        Change("SC-7", "apocope of final short vowels", _sc7),
    ],
    repairs=[Change("REP", "initial dz -> z", _rep_dz)],
)


# ---------------------------------------------------------------------------
# lexicon


@dataclass
class LexEntry:
    form: str                    # citation form as the codex spells it
    ipa: str                     # codex IPA ('' where the codex gives none)
    gloss: str
    etym: str                    # the codex's derivation column, verbatim
    domain: str                  # core/physics/fleet/argot/grammar/number
    kind: str = "proto"          # proto | daughter | register | grammar
    proto: Optional[str] = None  # proto-form fed to the engine
    cited: Tuple[str, ...] = ()  # changes expected to fire (locked by tests)
    adjustments: Tuple[Adjustment, ...] = ()
    members: Tuple[str, ...] = ()  # component forms for daughter formations
    source: str = "docs/01"

    def derive(self) -> Optional[Derivation]:
        if self.proto is None:
            return None
        return SUCHEL.derive(self.proto, self.adjustments)


def _override(form: str, note: str) -> Adjustment:
    return (note, lambda _s, _f=form: _f)


def _E(*args, **kw) -> LexEntry:
    return LexEntry(*args, **kw)


_L: List[LexEntry] = [
    # -- core / physics / fleet (docs/01 §06) --------------------------------
    _E("Sūchel", "ˈsuː.tʃel", "the crossing-speech; this language",
       "*suw-kel (zero-grade *suw- 'cross' + *kel 'speech') → SC-3, SC-1", "core",
       proto="*suw-kel", cited=("SC-1", "SC-3")),
    _E("Pelgar", "ˈpel.gar", "Old Pelagic; the Assembly's tongue",
       "*pelag-ar 'of the deep' → SC-2", "core",
       proto="*pelag-ar", cited=("SC-2",)),
    _E("sū", "suː", "to cross the seam (v., irregular)",
       "*suw-a → SC-3, SC-7", "physics",
       proto="*suw-a", cited=("SC-7",),
       adjustments=(_override("sū", "irregular verb (docs/01: 'v., irregular'); "
                                     "the codex cites SC-3, SC-7 — the glide "
                                     "resolves into length instead of v"),)),
    _E("sūath", "ˈsuː.ath", "a crossing (n.)",
       "sū + nominalizer -ath", "physics", kind="daughter", members=("sū", "-ath")),
    _E("sīl", "siːl", "crosser; seam-pilot",
       "*suw-il agent 'threader' → SC-3 (uwi → ī)", "fleet",
       proto="*suw-il", cited=("SC-3",)),
    _E("Sōrn", "soːrn", "the threading engine; the drive",
       "*sow-orn (o-grade + instrumental *-orn) → SC-3", "fleet",
       proto="*sow-orn", cited=("SC-3",)),
    _E("jel", "dʒel", "the seam 𝔍",
       "*gel- 'stitch, join' → SC-1", "physics",
       proto="*gel", cited=("SC-1",)),
    _E("jelmar", "ˈdʒel.mar", "seam-pearl",
       "jel + mar 'sea-stone, pearl' (*mar-)", "physics",
       kind="daughter", members=("jel", "mar")),
    _E("jelvos", "ˈdʒel.vos", "seam-scar",
       "jel + vos 'wound' (*wos- → SC-3 w→v)", "physics",
       kind="daughter", members=("jel", "vos")),
    _E("jelsīl", "ˈdʒel.siːl", "seam-crosser (formal)",
       "jel + sīl", "fleet", kind="daughter", members=("jel", "sīl")),
    _E("Idrenes", "iˈdre.nes", "the opened path; the bridge",
       "*id- 'open' + *ren- 'path' + *-es 'place' → SC-2", "physics",
       proto="*ideren-es", cited=("SC-2",)),
    _E("idren", "ˈi.dren", "a bridge, an opened way (common n.)",
       "back-formation from Idrenes", "core", kind="daughter", members=("Idrenes",)),
    _E("kad", "kad", "beacon; the pulse; (by extension) time-as-kept",
       "*kad- 'pulse, beat'", "fleet", proto="*kad", cited=()),
    _E("kadur", "ˈka.dur", "beacon-cycle (unit)",
       "kad + -ur duration suffix", "fleet", kind="daughter", members=("kad", "-ur")),
    _E("zukad", "ˈzu.kad", "dark time; unanchored duration",
       "zu 'adrift' (*dzu-) + kad", "argot", kind="daughter", members=("zu", "kad")),
    _E("zu", "zu", "adrift; (gram.) the dark-time anchor =zu",
       "*dzu- 'drift'", "grammar", proto="*dzu", cited=()),
    _E("mi", "mi", "self; (gram.) the proper-time anchor =mi",
       "*mei- 'self'", "grammar", proto="*mei", cited=(),
       adjustments=(_override("mi", "grammaticalized anchor clitic: *mei worn "
                                    "down to mi (docs/01)"),)),
    _E("ka", "ka", "(gram.) the beacon-time anchor =ka",
       "cliticized kad", "grammar", kind="daughter", members=("kad",),
       adjustments=(_override("ka", "cliticized kad (docs/01)"),)),
    _E("ne", "ne", "the gap-particle; the unspeakable interval",
       "*nex- 'absence' → SC-7", "grammar",
       proto="*nex", cited=(),
       adjustments=(_override("ne", "grammaticalized particle clip — the codex "
                                    "cites SC-7; the noun nexath keeps the "
                                    "cluster (docs/01)"),)),
    _E("nexath", "ˈne.ksath", "a gap (n.); a hole in a life",
       "*nex- + -ath", "core", proto="*nex-ath", cited=()),
    _E("nuv", "nuv", "down-tower; deeper (directional)",
       "*nub- 'under' → final devoicing resisted; SC-6 analog", "grammar",
       proto="*nub", cited=(),
       adjustments=(("final b → v (docs/01: 'final devoicing resisted; "
                     "SC-6 analog')", lambda f: f[:-1] + "v" if f.endswith("b") else f),)),
    _E("hau", "hau", "surfaceward; up-tower (directional)",
       "*haw- 'upper air' (diphthong kept in closed monosyll.)", "grammar",
       proto="*hau", cited=()),
    _E("hōl", "hoːl", "to surface",
       "*haw-ol- → SC-5", "fleet", proto="*haw-ol", cited=("SC-5",)),
    _E("nuvran", "ˈnuv.ran", "running under; dive-desync vertigo",
       "nuv + ran 'run' (*ran-) — pilot argot", "argot",
       kind="daughter", members=("nuv", "ran")),
    _E("nuvi", "ˈnu.vi", "diver; depth-pilot",
       "nuv + agent -i", "fleet", kind="daughter", members=("nuv", "-i")),
    _E("nuvdol", "ˈnuv.dol", "depth-well",
       "nuv + dol 'pit, well' (*dol-)", "physics",
       kind="daughter", members=("nuv", "dol")),
    _E("tur", "tur", "the Tower; the OCT",
       "*tur- 'to pile, stack' → SC-7", "physics",
       proto="*tur-a", cited=("SC-7",)),
    _E("Turmai", "ˈtur.mai", "the Tower (reverent: 'our-entangled Tower')",
       "tur + entangled -mai", "physics", kind="daughter", members=("tur", "-mai")),
    _E("kav", "kav", "tolerance; the curvature limit Κ",
       "*kap-a → SC-6, SC-7", "physics",
       proto="*kap-a", cited=("SC-6", "SC-7")),
    _E("Kaveth", "ˈka.veth", "at-the-Limit (the frontier, as a place)",
       "kav + locative -eth, lexicalized", "physics",
       kind="daughter", members=("kav", "-eth")),
    _E("tem", "tem", "pattern; woven form; (Κ5) the pattern that may cross",
       "*tem-a 'weave' → SC-7", "physics", proto="*tem-a", cited=("SC-7",)),
    _E("temor", "ˈte.mor", "information reef",
       "tem + mor 'sea-rock' (*mor-)", "physics",
       kind="daughter", members=("tem", "mor")),
    _E("mor", "mor", "reef; sea-rock", "*mor-", "core", proto="*mor", cited=()),
    _E("mar", "mar", "pearl; sea-stone", "*mar-", "core", proto="*mar", cited=()),
    _E("velosh", "ˈve.loʃ", "Formless mouth",
       "vel 'nothing' + osh 'mouth' (*os- + SC-7 analog)", "physics",
       kind="daughter", members=("vel", "osh")),
    _E("vel", "vel", "nothing; no-thing",
       "*wel- → SC-3 w→v", "core", proto="*wel", cited=("SC-3",)),
    _E("ver", "ver", "truth; to speak-true (v.)",
       "*wer- → SC-3 w→v", "core", proto="*wer", cited=("SC-3",)),
    _E("vur", "vur", "to spin, whirl; to go mad",
       "*wur- → SC-3 w→v", "core", proto="*wur", cited=("SC-3",)),
    _E("vurel", "ˈvu.rel", "madman; the spun-one",
       "vur + agent -el", "core", kind="daughter", members=("vur", "-el")),
    _E("Vurel-lor", "ˈvu.rel lor", "the Madman's Theorem",
       "vurel + lor 'rule, law' (*lor-)", "physics",
       kind="daughter", members=("vurel", "lor")),
    _E("eshe-ver", "ˈe.ʃe ver", "the Tragic Truth (lit. 'seam-true truth')",
       "mood suffix -eshe + ver, lexicalized", "physics",
       kind="daughter", members=("eshe", "ver")),
    _E("pevlor", "ˈpev.lor", "the logic ΛL (lit. 'five-rule')",
       "pev 'five' + lor", "physics", kind="daughter", members=("pev", "lor")),
    _E("lor", "lor", "rule; law", "*lor-", "core", proto="*lor", cited=()),
    _E("somath", "ˈso.math", "assembly; gathering",
       "*som- 'gather' + -ath", "core", proto="*som-ath", cited=()),
    _E("Pelgar Somath", "ˈpel.gar ˈso.math", "the Pelagian Assembly",
       "Pelgar + somath", "fleet", kind="daughter", members=("Pelgar", "somath")),
    _E("nav", "nav", "ship",
       "*nāw- → SC-3 w→v, shortening in closed syll.", "fleet",
       proto="*nāw", cited=("SC-3",),
       adjustments=(("closed-syllable shortening (docs/01: 'shortening in "
                     "closed syll.')", lambda f: f.replace("ā", "a")),)),
    _E("navmai", "ˈnav.mai", "one's own ship (entangled)",
       "nav + -mai", "fleet", kind="daughter", members=("nav", "-mai")),
    _E("mān", "maːn", "hand; crew-hand, crewmate",
       "*mahin → SC-4", "fleet", proto="*mahin", cited=("SC-4",)),
    _E("chel", "tʃel", "speech; tongue, language",
       "*kel → SC-1", "core", proto="*kel", cited=("SC-1",)),
    _E("kel", "kel", "(Old Pelagic) speech — preserved in liturgy",
       "*kel (no change: liturgical register)", "core", kind="register",
       members=("*kel",)),
    _E("ran", "ran", "to run", "*ran-", "core", proto="*ran", cited=()),
    _E("tel", "tel", "to reach, arrive at; (num.) three",
       "*tel- 'stretch to'; numeral homophone", "core", proto="*tel", cited=()),
    _E("dur", "dur", "to endure, survive", "*dur-", "core", proto="*dur", cited=()),
    _E("dol", "dol", "pit; well", "*dol-", "core", proto="*dol", cited=()),
    _E("osh", "oʃ", "mouth", "*os- + palatal excrescence", "core",
       proto="*os", cited=(),
       adjustments=(_override("osh", "palatal excrescence (docs/01)"),)),
    _E("vos", "vos", "wound", "*wos- → SC-3", "core", proto="*wos", cited=("SC-3",)),
    # -- pronouns & grammar ---------------------------------------------------
    _E("en", "en", "I (1SG)", "*en-", "grammar", proto="*en", cited=()),
    _E("ish", "iʃ", "you (2SG)",
       "*is- → SC-1 analog (s→sh/_i)", "grammar",
       proto="*isi", cited=("SC-1", "SC-7")),
    _E("an", "an", "she/he/it (3SG)", "*an-", "grammar", proto="*an", cited=()),
    _E("eni", "ˈe.ni", "we (plain plural)", "en + -i", "grammar",
       kind="daughter", members=("en", "-i")),
    _E("enmai", "ˈen.mai", "we (entangled; crew-we)", "en + -mai", "grammar",
       kind="daughter", members=("en", "-mai")),
    _E("ishmai", "ˈiʃ.mai", "you, held-as-kin (entangled 2SG)",
       "ish + -mai", "grammar", kind="daughter", members=("ish", "-mai")),
    _E("-mai", "mai", "entangled-possession suffix",
       "*mag-i 'bound' → SC-1 (g→j→∅/_i), vowel coalescence", "grammar",
       proto="*mag-i", cited=("SC-1",)),
    _E("-ath", "ath", "nominalizer (act or result)", "*-ath", "grammar",
       proto="*-ath", cited=()),
    _E("-eth", "eth", "locative case", "*-eth", "grammar", proto="*-eth", cited=()),
    _E("-ol", "ol", "dative case", "*-ol", "grammar", proto="*-ol", cited=()),
    _E("-en", "en", "genitive (alienable)", "*-en", "grammar", proto="*-en", cited=()),
    _E("vo", "vo", "not; negation particle", "*wo- → SC-3", "grammar",
       proto="*wo", cited=("SC-3",)),
    _E("ve", "ve", "to be (copula)", "*we- → SC-3", "grammar",
       proto="*we", cited=("SC-3",)),
    # -- numbers ----------------------------------------------------------------
    _E("sa", "sa", "one", "*sa-", "number", proto="*sa", cited=()),
    _E("vor", "vor", "two", "*wor- → SC-3", "number", proto="*wor", cited=("SC-3",)),
    _E("mek", "mek", "four", "*mek-", "number", proto="*mek", cited=()),
    _E("pev", "pev", "five", "*pew- → SC-3 w→v", "number",
       proto="*pew", cited=("SC-3",)),
    _E("shen", "ʃen", "six", "*sen- → s→sh/_e (SC-1 analog)", "number",
       proto="*sen", cited=("SC-1",)),
    _E("hep", "hep", "seven",
       "*hep- (h kept word-initially before e in numerals: liturgical "
       "conservatism)", "number", proto="*hep", cited=()),
    _E("ok", "ok", "eight", "*ok-", "number", proto="*ok", cited=()),
    _E("nur", "nur", "nine", "*nur-", "number", proto="*nur", cited=()),
    _E("dak", "dak", "ten", "*dak-", "number", proto="*dak", cited=()),
    # -- phrasebook appendix (docs/02 §F: "merge these into the master lexicon")
    _E("jed", "", "to go, move (always with directional)",
       "*ged- → SC-1 (g→j /_e)", "core", proto="*ged", cited=("SC-1",),
       source="docs/02"),
    _E("tan", "", "to hold, keep", "*tan-", "core", proto="*tan", cited=(),
       source="docs/02"),
    _E("id", "", "to open", "*id- (the Idrenes root, as verb)", "core",
       proto="*id", cited=(), source="docs/02"),
    _E("men", "", "to wait, remain", "*men-", "core", proto="*men", cited=(),
       source="docs/02"),
    _E("ret", "", "again", "*ret-", "core", proto="*ret", cited=(),
       source="docs/02"),
    _E("ān", "aːn", "breath", "*anh- → SC-4 (h-loss, lengthening)", "core",
       proto="*anh", cited=("SC-4",), source="docs/02"),
    _E("kru", "", "blood", "*kru-", "core", proto="*kru", cited=(),
       source="docs/02"),
    _E("gal", "", "the Still; becalmed vacuum (Dead-Sea)",
       "*gal- (no front vowel: g survives)", "core", proto="*gal", cited=(),
       source="docs/02"),
    _E("lesh", "", "alignment; fair phase; luck",
       "*les- → s→sh /_front (SC-1 analog)", "core",
       proto="*lesi", cited=("SC-1", "SC-7"), source="docs/02"),
    _E("maiel", "ˈmai.el", "kinsman; bound-one",
       "-mai 'entangled' + agent -el", "core", kind="daughter",
       members=("-mai", "-el"), source="docs/02"),
    _E("om", "", "all, every", "*om-", "core", proto="*om", cited=(),
       source="docs/02"),
    _E("vu", "", "question particle (final)", "*wu → SC-3 (w→v)", "grammar",
       proto="*wu", cited=("SC-3",), source="docs/02"),
    _E("-u", "u", "imperative (non-assertive: no mood, no anchor)",
       "*-u hortative", "grammar", proto="*-u", cited=(), source="docs/02"),
    _E("ō", "oː", "vocative particle", "*ō interjection", "grammar",
       proto="*ō", cited=(), source="docs/02"),
    # -- verb machinery (docs/01 §04–05), inherited from late Old Pelagic ----
    _E("-a", "a", "mood T: classically true; settled", "late OP *-a", "grammar",
       proto="*-a", cited=()),
    _E("-im", "im", "mood T⁻: true-as-approached (IR)", "late OP *-im", "grammar",
       proto="*-im", cited=()),
    _E("-ur", "ur", "mood T⁺: held-from-above, unaccredited (UV)",
       "late OP *-ur", "grammar", proto="*-ur", cited=()),
    _E("-eshe", "ˈe.ʃe", "mood T•: seam-true; self-dual",
       "late OP *-eshe — the mood suffix carried the stress (the truth-beat, "
       "docs/06 §03), so its final vowel resists SC-7", "grammar"),
    _E("-t-", "t", "perfective aspect", "late OP *-t-", "grammar",
       proto="*-t", cited=()),
    _E("-i", "i", "plural", "*-i", "grammar", proto="*-i", cited=()),
    _E("-el", "el", "agent suffix", "*-el", "grammar", proto="*-el", cited=()),
    _E("-ur(dur)", "ur", "duration suffix (kadur)", "*-ur", "grammar",
       proto="*-ur", cited=()),
]

LEXICON: Dict[str, LexEntry] = {e.form: e for e in _L}


def lookup(form: str) -> LexEntry:
    return LEXICON[form]


def entries(domain: Optional[str] = None) -> List[LexEntry]:
    return [e for e in _L if domain is None or e.domain == domain]


def derive(proto: str) -> Derivation:
    """Run a proto-form through the seven changes (no adjustments)."""
    return SUCHEL.derive(proto)


def compose(*forms: str) -> str:
    """Join daughter-formation members, degeminating at the seam
    (tem + mor -> temor; the same repair gives Sel Limar, Kadun)."""
    out = ""
    for f in forms:
        f = f.strip("-*")
        if out and f and out[-1] == f[0] and f[0] not in "aeiouāēīōū":
            f = f[1:]
        out += f
    return out
