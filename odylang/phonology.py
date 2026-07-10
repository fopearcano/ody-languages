"""Family-wide phonology: segments, syllabification, IPA.

Romanization conventions (shared across the whole Old Pelagic family,
docs/01 §02, docs/04 §01):

* one symbol, one sound; digraphs ``ch sh th kh gh ts dz`` are single
  segments, as is ``x`` = /ks/ (the *nex- cluster: ``nexath`` [ˈne.ksath]).
* macron vowels ``ā ē ī ō ū`` are long ("length is quality held, not
  changed — a long vowel is a held breath").
* ``ai`` and ``au`` are diphthongs (single nuclei): ``mai``, ``hau``.
* ``ó`` (Nubhel's plain mood) is /o/; its inherent stress is handled by
  the stress rules in :mod:`odylang.word`.
* ``-`` marks a morpheme boundary and ``=`` a clitic boundary; both are
  transparent to syllabification.

The syllable canon is (C)(r/l)V(C) (docs/01 §02); the syllabifier is
deliberately permissive about codas so that documented words that exceed
the canon (``Sōrn``, ``neks``) still parse.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

# ---------------------------------------------------------------------------
# segment inventory

SHORT_VOWELS = ("a", "e", "i", "o", "u")
LONG_OF = {"a": "ā", "e": "ē", "i": "ī", "o": "ō", "u": "ū"}
SHORT_OF = {v: k for k, v in LONG_OF.items()}
LONG_VOWELS = tuple(LONG_OF.values())
DIPHTHONGS = ("ai", "au")
VOWELS = SHORT_VOWELS + LONG_VOWELS + DIPHTHONGS

FRONT_VOWELS = ("e", "i", "ē", "ī")

# multi-character consonant symbols, longest first for the tokenizer
DIGRAPHS = ("ch", "sh", "th", "kh", "gh", "ts", "dz")
BOUNDARIES = ("-", "=")

# accented vowels normalise to their plain segment (ó carries morphological
# stress, not a distinct quality)
_ACCENT_NORM = {"ó": "o", "á": "a", "é": "e", "í": "i", "ú": "u"}

_IPA = {
    "ch": "tʃ", "j": "dʒ", "sh": "ʃ", "x": "ks", "y": "j",
    "kh": "x", "gh": "ɣ", "ts": "ts", "dz": "dz", "th": "th",
    "ā": "aː", "ē": "eː", "ī": "iː", "ō": "oː", "ū": "uː",
}

#: docs/04 §01 positional and phonetic notes ("anchors for an English
#: mouth").  Transcriptions throughout the codices are broad — [r], not the
#: allophone — so these stay descriptive data rather than IPA behaviour.
PHONETIC_NOTES = {
    "r": "tapped [ɾ] between vowels, brief trill [r] at word-start; "
         "never the English glide",
    "h": "word-initial only (hōl, hau, hep); elsewhere old *h has already "
         "become vowel length",
    "k": "lightly aspirated at most",
    "g": "always hard",
    "s": "always voiceless",
    "finals": "crisp finals; no swallowed stops",
    "length": "length ≠ quality — hold the sound, do not change it. "
              "A long vowel is a held breath",
}

_ONSET_FIRST = set("pbtdkgvszfx") | {"ch", "j", "sh", "kh", "gh", "ts", "dz", "th"}


def is_vowel(seg: str) -> bool:
    return seg in VOWELS


def is_long(seg: str) -> bool:
    return seg in LONG_VOWELS or seg in DIPHTHONGS


def lengthen(seg: str) -> str:
    """Compensatory lengthening: short vowel -> long; long/diphthong stays."""
    return LONG_OF.get(seg, seg)


def tokenize(text: str) -> List[str]:
    """Split a romanized word into segments (boundaries kept).

    ``tokenize('sū-t-eshe=zu')`` -> ``['s','ū','-','t','-','e','sh','e','=','z','u']``
    """
    s = text.lower()
    for acc, plain in _ACCENT_NORM.items():
        s = s.replace(acc, plain)
    segs: List[str] = []
    i = 0
    while i < len(s):
        two = s[i:i + 2]
        if two in DIGRAPHS or two in DIPHTHONGS:
            segs.append(two)
            i += 2
            continue
        c = s[i]
        if c.isspace():
            i += 1
            continue
        segs.append(c)
        i += 1
    return segs


def strip_boundaries(segs: Sequence[str]) -> List[str]:
    return [s for s in segs if s not in BOUNDARIES]


def romanize(segs: Sequence[str]) -> str:
    return "".join(strip_boundaries(segs))


# ---------------------------------------------------------------------------
# syllabification


@dataclass
class Syllable:
    onset: List[str]
    nucleus: str
    coda: List[str]
    seg_indices: List[int]  # indices into the boundary-stripped segment list

    @property
    def text(self) -> str:
        return "".join(self.onset) + self.nucleus + "".join(self.coda)

    @property
    def heavy_by_length(self) -> bool:
        return is_long(self.nucleus)


def _legal_onset(cluster: List[str]) -> bool:
    if len(cluster) <= 1:
        return True
    if len(cluster) == 2:
        return cluster[0] in _ONSET_FIRST and cluster[1] in ("r", "l")
    return False


def syllabify(segs: Sequence[str],
              owners: Optional[Sequence[int]] = None) -> List[Syllable]:
    """Onset-maximising syllabification over the (C)(r/l)V(C) canon.

    Boundary markers are ignored.  Consonants that cannot open the next
    syllable close the previous one (permissive codas: ``Sōrn`` -> one
    syllable with coda /rn/).

    ``owners`` (aligned with the boundary-stripped segments) marks which
    morph each segment belongs to: a two-consonant onset may not span a
    compound seam — nuv+ran is [ˈnuv.ran], never [ˈnu.vran] — while a
    single consonant still resyllabifies across it (vel+osh [ˈve.loʃ]).
    """
    plain = strip_boundaries(segs)
    if owners is not None and len(owners) != len(plain):
        raise ValueError("owners must align with the boundary-stripped segments")
    nuclei = [i for i, s in enumerate(plain) if is_vowel(s)]
    if not nuclei:
        return []
    sylls: List[Syllable] = []
    for k, n in enumerate(nuclei):
        prev_n = nuclei[k - 1] if k else -1
        cons = list(range(prev_n + 1, n))  # consonant indices between nuclei
        if k == 0:
            onset = cons
        else:
            onset = []
            # maximise a legal onset from the right
            for take in (2, 1, 0):
                if take > len(cons):
                    continue
                cand = cons[len(cons) - take:]
                if not _legal_onset([plain[i] for i in cand]):
                    continue
                if (take == 2 and owners is not None
                        and owners[cand[0]] != owners[cand[1]]):
                    continue  # the seam blocks the cluster
                onset = cand
                break
            coda_prev = cons[: len(cons) - len(onset)]
            sylls[-1].coda.extend(plain[i] for i in coda_prev)
            sylls[-1].seg_indices.extend(coda_prev)
        sylls.append(Syllable([plain[i] for i in onset], plain[n], [], onset + [n]))
    tail = list(range(nuclei[-1] + 1, len(plain)))
    sylls[-1].coda.extend(plain[i] for i in tail)
    sylls[-1].seg_indices.extend(tail)
    return sylls


# ---------------------------------------------------------------------------
# IPA


def seg_ipa(seg: str) -> str:
    return _IPA.get(seg, seg)


def word_ipa(word: str, stress_index: int | None = None) -> str:
    """IPA for one romanized word.

    ``stress_index`` is the stressed syllable's index; monosyllables are
    rendered without a stress mark (doc/02 convention: [ver iˈʃol] but
    [maːn]).  The mark replaces the syllable dot: [hoːlˈte.ʃe.zu].
    """
    sylls = syllabify(tokenize(word))
    parts = []
    for i, syl in enumerate(sylls):
        body = "".join(seg_ipa(s) for s in syl.onset + [syl.nucleus] + syl.coda)
        stressed = len(sylls) > 1 and stress_index is not None and i == stress_index
        parts.append(("ˈ" if stressed else ("." if i else "")) + body)
    return "".join(parts)
