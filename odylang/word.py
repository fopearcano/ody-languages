"""Morpheme-structured words and the four-rule stress algorithm.

docs/04 §02 — run top to bottom, first rule that applies wins:

  RULE 1  Compounds stress their first member (on that member's own
          stressed syllable): NUV-ran, JEL-mar, SŌRN-mai, E-she-ver, ZU-kad.
  RULE 2  Finite verbs: the mood seizes the stress — stress the syllable
          containing the veridical suffix's first vowel.  Anchor clitics
          (=ka =mi =zu =nu) are weightless: ve-RA-ka, hōl-TE-she-zu.
  RULE 3  A long vowel (or diphthong: HAU) seizes the stress in any other
          word: SŪ-chel, HŌ-lu, MĀN, ĀN.
  RULE 4  Otherwise stress the penult of the stem; case suffixes never
          shift it once set: I-dre-nes, VU-rel -> VU-re-len, ZU-ka-deth.
          Corollary: imperatives are beatless — -u adds no beat.

Two attested exceptions are encoded (and only these two):

  * entangled pronouns under case inflection stress -mai:
    ishmai-ol [iʃˈmai.ol] (docs/02 §02), enmai-eth [enˈmai.eth] (§31),
    against bare [ˈen.mai]/[ˈiʃ.mai];
  * the dative hail ish-ol is [iˈʃol] (docs/02 §01, docs/04 line 01) —
    lexicalized greeting prosody.

docs/04's RULE 4 example prints 'I-dre-nes'; the capital I there is
the proper name's orthographic capital, not a stress mark — docs/01
§02 and the lexicon both fix [iˈdre.nes] (penult), which this module
follows.

For the rhythm notation of docs/04 §03 a monosyllabic *word* counts as
beat-carrying only when its nucleus is long or a diphthong (MĀN, ĀN, HAU,
Ō — but ver, kad, jel stay low).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .phonology import (Syllable, is_long, is_vowel, romanize, seg_ipa,
                        strip_boundaries, syllabify, tokenize, word_ipa)

# morph categories
STEM = "stem"          # lexical stem (first member of a compound)
STEM2 = "stem2"        # further compound members
DERIV = "deriv"        # stem-forming derivation (-el agent, -ath nominalizer, -ur duration): inside the stress domain
PFV = "pfv"            # perfective -t-
MOOD = "mood"          # veridical mood suffix (rule 2 target)
ANCHOR = "anchor"      # temporal anchor clitic (weightless)
CASE = "case"          # case suffix (outside the stress domain)
MAI = "mai"            # entangled -mai (outside the stress domain)
PLURAL = "plural"      # plural -i (outside the stress domain)
IMP = "imp"            # imperative -u (extrametrical, beatless)
PART = "part"          # particle / uninflected word

PRONOUN_STEMS = {"en", "ish", "an", "on"}


@dataclass
class Morph:
    form: str
    gloss: str = ""
    cat: str = STEM
    sep: str = ""      # '', '-', or '=' before this morph in careful spelling


@dataclass
class Word:
    morphs: List[Morph]
    gloss_join: Optional[str] = None   # override for the word-level gloss
    stress_override: Optional[int] = None  # documented lexical exception

    # -- construction helpers -------------------------------------------------
    @classmethod
    def particle(cls, form: str, gloss: str = "") -> "Word":
        return cls([Morph(form, gloss, PART)])

    @classmethod
    def plain(cls, form: str, gloss: str = "") -> "Word":
        return cls([Morph(form, gloss, STEM)])

    # -- surfaces --------------------------------------------------------------
    def display(self) -> str:
        """Careful-hand spelling with morpheme separators: sū-t-eshe=zu."""
        out = ""
        for i, m in enumerate(self.morphs):
            out += (m.sep if i else "") + m.form
        return out

    def solid(self) -> str:
        """The phonological word, separators removed."""
        return "".join(m.form for m in self.morphs)

    def gloss(self) -> str:
        if self.gloss_join is not None:
            return self.gloss_join
        out = ""
        for i, m in enumerate(self.morphs):
            if not m.gloss:
                continue
            if out:
                out += "=" if m.sep == "=" else "-"
            out += m.gloss
        return out

    # -- segment bookkeeping ---------------------------------------------------
    def _segments_with_morphs(self):
        segs: List[str] = []
        owner: List[int] = []
        for mi, m in enumerate(self.morphs):
            for s in strip_boundaries(tokenize(m.form)):
                segs.append(s)
                owner.append(mi)
        return segs, owner

    def syllables(self) -> List[Syllable]:
        segs, owner = self._segments_with_morphs()
        return syllabify(segs, owner)

    # -- the four rules ----------------------------------------------------------
    def _syll_of_segment(self, sylls: Sequence[Syllable], seg_index: int) -> int:
        for i, syl in enumerate(sylls):
            if seg_index in syl.seg_indices:
                return i
        return len(sylls) - 1

    def _domain_syllables(self, sylls, owner, cats) -> List[int]:
        """Indices of syllables whose nucleus belongs to a morph in ``cats``."""
        segs, _ = self._segments_with_morphs()
        out = []
        for i, syl in enumerate(sylls):
            for si in syl.seg_indices:
                if is_vowel(segs[si]) and owner[si] in cats:
                    out.append(i)
                    break
        return out

    def stressed_syllable(self) -> Optional[int]:
        if self.stress_override is not None:
            return self.stress_override
        segs, owner = self._segments_with_morphs()
        sylls = syllabify(segs, owner)
        if not sylls:
            return None
        cats = [m.cat for m in self.morphs]

        # documented exception: pronoun + -mai + case stresses -mai
        if MAI in cats and CASE in cats and self.morphs[0].form in PRONOUN_STEMS:
            mai_i = cats.index(MAI)
            first_seg = next(i for i, mo in enumerate(owner) if mo == mai_i)
            return self._syll_of_segment(sylls, first_seg)

        # RULE 2 — the mood seizes the stress
        if MOOD in cats:
            mood_i = cats.index(MOOD)
            for i, mo in enumerate(owner):
                if mo == mood_i and is_vowel(segs[i]):
                    return self._syll_of_segment(sylls, i)

        stem_morphs = [i for i, m in enumerate(self.morphs) if m.cat in (STEM, STEM2, DERIV, PART)]

        # RULE 1 — compounds stress their first member
        if any(m.cat == STEM2 for m in self.morphs):
            first = [i for i, m in enumerate(self.morphs) if m.cat == STEM][:1]
            member = self._domain_syllables(sylls, owner, first)
            if member:
                for i in member:  # rule 3 within the member
                    if sylls[i].heavy_by_length:
                        return i
                return member[-2] if len(member) > 1 else member[0]

        domain = self._domain_syllables(sylls, owner, stem_morphs)
        if not domain:
            domain = list(range(len(sylls)))

        # RULE 3 — a long vowel seizes the stress
        for i in domain:
            if sylls[i].heavy_by_length:
                return i

        # RULE 4 — penult of the stem
        return domain[-2] if len(domain) > 1 else domain[0]

    # -- renderings --------------------------------------------------------------
    def is_beatless(self) -> bool:
        return any(m.cat == IMP for m in self.morphs) and not any(
            m.cat == MOOD for m in self.morphs)

    def ipa(self) -> str:
        sylls = self.syllables()
        stress = self.stressed_syllable()
        parts = []
        for i, syl in enumerate(sylls):
            body = "".join(seg_ipa(s) for s in syl.onset + [syl.nucleus] + syl.coda)
            stressed = len(sylls) > 1 and stress is not None and i == stress
            parts.append(("ˈ" if stressed else ("." if i else "")) + body)
        return "".join(parts)

    def syl_beats(self) -> List[str]:
        """docs/04 rhythm notation: CAPS = stressed beat, ':' marks length.

        Monosyllabic words carry a beat only when heavy by length.
        """
        sylls = self.syllables()
        stress = self.stressed_syllable()
        out = []
        for i, syl in enumerate(sylls):
            text = syl.text.replace("ā", "a:").replace("ē", "e:").replace(
                "ī", "i:").replace("ō", "o:").replace("ū", "u:").replace("x", "ks")
            stressed = (i == stress) and (len(sylls) > 1 or syl.heavy_by_length)
            out.append(text.upper() if stressed else text)
        return out
