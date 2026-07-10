"""Sūchel speech synthesizer — a stdlib source-filter formant voice.

Reads the phoneme key and articulation notes of docs/04 (``§01 PHONEME
KEY`` and :data:`odylang.phonology.PHONETIC_NOTES``) and the prosody
discovery of the same document — *the mood carries the beat* (docs/04
§02–§04): the veridical suffix seizes the stress, so a finite verb has a
pitch accent while an imperative is flat and beatless.

The engine is a classic source-filter model, implemented sample by sample
with the Python standard library only (``math`` + ``wave`` + ``struct`` +
``random``); there is no numpy and no external audio library, per the hard
project rule.

Signal chain
------------
* **Voiced source** — a band-limited pulse/impulse train at F0 (base
  :data:`BASE_F0` ≈ 120 Hz) with light period jitter, driving three
  hand-written band-pass biquad FORMANT resonators (the RBJ constant
  0 dB-peak bandpass difference equation, run one sample at a time).  A
  long vowel is the same formants *held longer*; a diphthong glides the
  formant centres from the first target to the second.
* **Unvoiced source** — noise from a SEEDED generator (``random.Random``),
  so every render is byte-reproducible; band-pass filtered per consonant.

Consonants follow docs/04's inventory: stops are a closure (silence when
voiceless, a low voiced murmur when voiced) plus a place-coded burst
(labial ~800, alveolar ~1800, velar ~1500 with a pinch); affricates a
closure plus a *sh*-like frication; fricatives a filtered noise band
(``s`` 4–8 kHz, ``sh`` 2–4 kHz, ``z``/``v`` voiced); nasals a low nasal
formant ~250 with a strong low-pass; ``r`` a brief tap, ``l`` a lateral;
and ``h`` word-initial breathy noise only — medial *h* is already vowel
length (docs/04 §01, :data:`~odylang.phonology.PHONETIC_NOTES`), so it is
voiced as silence.  The gap particle *ne* / the ``'|'`` token is a rest.

Prosody (docs/04 §02–§04): each word is syllabified
(:func:`odylang.phonology.syllabify`) and stressed through the four-rule
algorithm of :class:`odylang.word.Word`; the stressed syllable's vowel
gets F0 ×:data:`STRESS_F0_FACTOR` and ×:data:`STRESS_DUR_FACTOR`; a long
vowel is ×:data:`LONG_FACTOR` in duration; a gentle declination lowers F0
across the phrase; imperatives (``Word.is_beatless()``) get no pitch
accent — flat, as the codex directs.

The public surface (``synth``, ``voice_spec`` …) is the single source the
browser mirror reproduces, so :func:`voice_spec` returns a complete,
JSON-serializable description of every constant used here.
"""

from __future__ import annotations

import io
import math
import random
import struct
import wave
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union

from .phonology import (DIPHTHONGS, LONG_OF, LONG_VOWELS, SHORT_OF, is_vowel,
                        tokenize)
from .suchel_grammar import Sentence
from .word import Word

# ---------------------------------------------------------------------------
# voice constants (docs/04 §01 phoneme key, §02–§04 prosody)

#: default output sample rate (Hz).
DEFAULT_SAMPLE_RATE: int = 22050

#: base fundamental frequency, "a base ~120 Hz" (docs/04 voice notes).
BASE_F0: float = 120.0

#: fractional period jitter on the voiced source (light, ± this much).
JITTER: float = 0.02

#: vowel formant targets F1/F2/F3 in Hz (docs/04 §01 phoneme key, the five
#: cardinal qualities).  Long vowels ``ā ē ī ō ū`` reuse the short target
#: (length ≠ quality — docs/04 §01: "hold the sound, do not change it") and
#: the diphthongs ``ai``/``au`` glide between their two component targets.
FORMANTS: Dict[str, Tuple[float, float, float]] = {
    "a": (800.0, 1200.0, 2500.0),
    "e": (500.0, 1900.0, 2550.0),
    "i": (300.0, 2300.0, 3000.0),
    "o": (500.0,  900.0, 2400.0),
    "u": (320.0,  800.0, 2400.0),
}

#: per-formant resonator bandwidths (Hz) → biquad Q = centre / bandwidth.
FORMANT_BW: Tuple[float, float, float] = (90.0, 110.0, 170.0)

#: per-formant output weights (F1 loudest, F3 quiet).
FORMANT_AMPS: Tuple[float, float, float] = (1.0, 0.6, 0.32)

# timing (milliseconds unless noted) --------------------------------------
VOWEL_MS: float = 150.0            # base short-vowel duration
LONG_FACTOR: float = 1.7          # long vowel / diphthong: held ×this
STRESS_DUR_FACTOR: float = 1.5    # stressed syllable: +~50% duration
STRESS_F0_FACTOR: float = 1.4     # stressed syllable: F0 +~40%
DECLINATION: float = 0.18         # F0 falls this fraction across the phrase
WORD_GAP_MS: float = 55.0         # short inter-word silence
PAUSE_MS: float = 320.0           # a full pause — '|' / the gap particle ne

#: seed for the noise/jitter generator — a fixed seed makes every render
#: byte-identical (the determinism the tests assert).
_RNG_SEED: int = 0xACE1

#: peak head-room after normalisation (keeps every sample inside int16).
_HEADROOM: float = 0.89


# ---------------------------------------------------------------------------
# consonant specification table (module data; also in voice_spec())


@dataclass(frozen=True)
class ConsonantSpec:
    """One consonant's articulation recipe (docs/04 §01).

    ``manner`` selects the render path; ``burst_hz`` codes stop place
    (labial ~800, alveolar ~1800, velar ~1500); ``noise_lo``/``noise_hi``
    bound a frication band; ``formants`` gives resonator targets for the
    voiced sonorants (nasals, ``l``, the ``r`` tap).
    """

    sym: str
    manner: str            # stop|affricate|fricative|nasal|liquid|tap|aspirate
    voiced: bool
    place: str = ""
    burst_hz: float = 0.0
    closure_ms: float = 0.0
    burst_ms: float = 0.0
    noise_lo: float = 0.0
    noise_hi: float = 0.0
    dur_ms: float = 0.0
    formants: Tuple[float, ...] = ()
    velar_pinch: bool = False


#: the sixteen living consonants of Sūchel + the threshold letter ``h``
#: (docs/04 §01; the same inventory Navcher letters).
CONSONANTS: Dict[str, ConsonantSpec] = {
    "p":  ConsonantSpec("p",  "stop", False, "labial",   burst_hz=800.0,
                        closure_ms=50.0, burst_ms=12.0),
    "b":  ConsonantSpec("b",  "stop", True,  "labial",   burst_hz=800.0,
                        closure_ms=50.0, burst_ms=12.0),
    "t":  ConsonantSpec("t",  "stop", False, "alveolar", burst_hz=1800.0,
                        closure_ms=50.0, burst_ms=12.0),
    "d":  ConsonantSpec("d",  "stop", True,  "alveolar", burst_hz=1800.0,
                        closure_ms=50.0, burst_ms=12.0),
    "k":  ConsonantSpec("k",  "stop", False, "velar",    burst_hz=1500.0,
                        closure_ms=50.0, burst_ms=14.0, velar_pinch=True),
    "g":  ConsonantSpec("g",  "stop", True,  "velar",    burst_hz=1500.0,
                        closure_ms=50.0, burst_ms=14.0, velar_pinch=True),
    "ch": ConsonantSpec("ch", "affricate", False, "postalveolar",
                        closure_ms=45.0, noise_lo=2000.0, noise_hi=4000.0,
                        dur_ms=70.0),
    "j":  ConsonantSpec("j",  "affricate", True,  "postalveolar",
                        closure_ms=45.0, noise_lo=2000.0, noise_hi=4000.0,
                        dur_ms=70.0),
    "s":  ConsonantSpec("s",  "fricative", False, "alveolar",
                        noise_lo=4000.0, noise_hi=8000.0, dur_ms=130.0),
    "sh": ConsonantSpec("sh", "fricative", False, "postalveolar",
                        noise_lo=2000.0, noise_hi=4000.0, dur_ms=130.0),
    "z":  ConsonantSpec("z",  "fricative", True,  "alveolar",
                        noise_lo=4000.0, noise_hi=8000.0, dur_ms=110.0),
    "v":  ConsonantSpec("v",  "fricative", True,  "labiodental",
                        noise_lo=500.0, noise_hi=1500.0, dur_ms=100.0),
    "m":  ConsonantSpec("m",  "nasal", True, "labial",   dur_ms=75.0,
                        formants=(250.0, 1000.0, 2200.0)),
    "n":  ConsonantSpec("n",  "nasal", True, "alveolar", dur_ms=75.0,
                        formants=(250.0, 1400.0, 2500.0)),
    "r":  ConsonantSpec("r",  "tap",   True, "alveolar", dur_ms=32.0,
                        formants=(500.0, 1300.0, 2500.0)),
    "l":  ConsonantSpec("l",  "liquid", True, "alveolar", dur_ms=70.0,
                        formants=(360.0, 1300.0, 2600.0)),
    "h":  ConsonantSpec("h",  "aspirate", False, "glottal",
                        noise_lo=500.0, noise_hi=3000.0, dur_ms=55.0),
}


# ---------------------------------------------------------------------------
# the phone plan


@dataclass
class Phone:
    """One synthesis segment: kind, duration (seconds), and voice data."""

    kind: str                       # vowel|closure|burst|frication|fricative|
    #                                 nasal|liquid|tap|aspirate|silence|pause
    sym: str
    dur: float                      # seconds
    voiced: bool = False
    stressed: bool = False
    accent: float = 1.0             # F0 multiplier (>1 on a stressed vowel)
    f0: float = BASE_F0             # filled in by _assign_f0
    targets: Tuple[float, ...] = () # vowel/sonorant formant targets
    glide_to: Optional[Tuple[float, ...]] = None  # diphthong second target
    long: bool = False
    spec: Optional[ConsonantSpec] = None


@dataclass
class Rendered:
    """A rendered utterance: PCM samples plus the probes tests read."""

    pcm: List[int]
    sample_rate: int
    f0_track: List[float]
    phones: List[Phone]

    @property
    def frames(self) -> int:
        return len(self.pcm)

    @property
    def duration(self) -> float:
        return len(self.pcm) / self.sample_rate if self.sample_rate else 0.0


# ---------------------------------------------------------------------------
# a hand-written biquad (RBJ cookbook), run sample by sample


class _Biquad:
    """A single second-order section; coefficients normalised by a0."""

    __slots__ = ("b0", "b1", "b2", "a1", "a2", "x1", "x2", "y1", "y2")

    def __init__(self) -> None:
        self.b0 = 1.0
        self.b1 = self.b2 = self.a1 = self.a2 = 0.0
        self.x1 = self.x2 = self.y1 = self.y2 = 0.0

    def set_bandpass(self, fc: float, q: float, fs: int) -> None:
        w0 = 2.0 * math.pi * fc / fs
        c = math.cos(w0)
        s = math.sin(w0)
        alpha = s / (2.0 * q) if q > 0 else s
        a0 = 1.0 + alpha
        self.b0 = alpha / a0
        self.b1 = 0.0
        self.b2 = -alpha / a0
        self.a1 = (-2.0 * c) / a0
        self.a2 = (1.0 - alpha) / a0

    def set_lowpass(self, fc: float, q: float, fs: int) -> None:
        w0 = 2.0 * math.pi * fc / fs
        c = math.cos(w0)
        s = math.sin(w0)
        alpha = s / (2.0 * q) if q > 0 else s
        a0 = 1.0 + alpha
        self.b0 = ((1.0 - c) / 2.0) / a0
        self.b1 = (1.0 - c) / a0
        self.b2 = ((1.0 - c) / 2.0) / a0
        self.a1 = (-2.0 * c) / a0
        self.a2 = (1.0 - alpha) / a0

    def process(self, x: float) -> float:
        y = (self.b0 * x + self.b1 * self.x1 + self.b2 * self.x2
             - self.a1 * self.y1 - self.a2 * self.y2)
        self.x2 = self.x1
        self.x1 = x
        self.y2 = self.y1
        self.y1 = y
        return y


def _clampf(fc: float, fs: int) -> float:
    """Keep a filter centre inside a stable, sub-Nyquist band."""
    return min(max(fc, 20.0), 0.45 * fs)


def _bandpass(fc: float, q: float, fs: int) -> _Biquad:
    b = _Biquad()
    b.set_bandpass(_clampf(fc, fs), q, fs)
    return b


def _lowpass(fc: float, q: float, fs: int) -> _Biquad:
    b = _Biquad()
    b.set_lowpass(_clampf(fc, fs), q, fs)
    return b


# ---------------------------------------------------------------------------
# sources


def _samples(dur: float, fs: int) -> int:
    return max(0, int(round(dur * fs)))


def _voiced_source(n: int, f0: float, fs: int,
                   rng: random.Random, jitter: float = JITTER) -> List[float]:
    """A jittered impulse train at ``f0`` — the glottal source."""
    buf = [0.0] * n
    phase = 0.0
    cur = f0 * (1.0 + rng.uniform(-jitter, jitter))
    for i in range(n):
        phase += cur / fs
        if phase >= 1.0:
            phase -= 1.0
            buf[i] = 1.0
            cur = f0 * (1.0 + rng.uniform(-jitter, jitter))
    return buf


def _noise(n: int, rng: random.Random) -> List[float]:
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


def _band_filter(sig: Sequence[float], lo: float, hi: float,
                 fs: int) -> List[float]:
    lo = _clampf(lo, fs)
    hi = _clampf(hi, fs)
    if hi <= lo:
        hi = lo * 1.5
    fc = math.sqrt(lo * hi)
    bw = hi - lo
    q = fc / bw if bw > 0 else 2.0
    f = _bandpass(fc, q, fs)
    return [f.process(x) for x in sig]


def _run_formants(src: Sequence[float], targets: Sequence[float],
                  glide: Optional[Sequence[float]], fs: int,
                  amps: Sequence[float] = FORMANT_AMPS,
                  bws: Sequence[float] = FORMANT_BW) -> List[float]:
    """Drive parallel band-pass resonators; glide the centres if given."""
    k = len(targets)
    filts = [_Biquad() for _ in range(k)]
    for j in range(k):
        fc = _clampf(targets[j], fs)
        filts[j].set_bandpass(fc, fc / bws[j], fs)
    n = len(src)
    out = [0.0] * n
    if glide is None:
        for i in range(n):
            x = src[i]
            s = 0.0
            for j in range(k):
                s += amps[j] * filts[j].process(x)
            out[i] = s
        return out
    block = 64
    for i in range(n):
        if i % block == 0 and n > 1:
            frac = i / n
            for j in range(k):
                fc = _clampf(targets[j] + (glide[j] - targets[j]) * frac, fs)
                filts[j].set_bandpass(fc, fc / bws[j], fs)
        x = src[i]
        s = 0.0
        for j in range(k):
            s += amps[j] * filts[j].process(x)
        out[i] = s
    return out


def _apply_env(buf: List[float], fs: int,
               atk: float = 0.008, rel: float = 0.012) -> None:
    """Linear attack/release ramps in place — no clicks at phone seams."""
    n = len(buf)
    if n == 0:
        return
    a = min(int(atk * fs), n // 2)
    r = min(int(rel * fs), n // 2)
    for i in range(a):
        buf[i] *= i / a
    for i in range(r):
        buf[n - 1 - i] *= i / r


def _scale(buf: List[float], g: float) -> None:
    for i in range(len(buf)):
        buf[i] *= g


# ---------------------------------------------------------------------------
# phone construction


def _vowel_phone(nuc: str, stressed: bool) -> Phone:
    diph = nuc in DIPHTHONGS
    long = nuc in LONG_VOWELS
    if diph:
        targets = FORMANTS[nuc[0]]
        glide = FORMANTS[nuc[1]]
    else:
        base = SHORT_OF.get(nuc, nuc)
        targets = FORMANTS.get(base, FORMANTS["a"])
        glide = None
    dur = VOWEL_MS
    if long or diph:
        dur *= LONG_FACTOR
    accent = 1.0
    if stressed:
        dur *= STRESS_DUR_FACTOR
        accent = STRESS_F0_FACTOR
    return Phone("vowel", nuc, dur / 1000.0, voiced=True, stressed=stressed,
                 accent=accent, targets=targets, glide_to=glide,
                 long=long or diph)


def _consonant_phones(c: str, word_initial: bool) -> List[Phone]:
    spec = CONSONANTS.get(c)
    if spec is None:
        # letters outside the Sūchel inventory (e.g. an imported x = /ks/):
        # letter it as its nearest sounds, else a short neutral fricative.
        if c == "x":
            return (_consonant_phones("k", word_initial)
                    + _consonant_phones("s", False))
        fallback = ConsonantSpec(c, "fricative", False, noise_lo=1000.0,
                                 noise_hi=4000.0, dur_ms=60.0)
        return [Phone("fricative", c, fallback.dur_ms / 1000.0,
                      voiced=False, spec=fallback)]

    if spec.manner == "aspirate":
        # docs/04 §01: h is word-initial only; medial *h* is already length.
        if not word_initial:
            return []
        return [Phone("aspirate", c, spec.dur_ms / 1000.0, spec=spec)]
    if spec.manner == "stop":
        return [
            Phone("closure", c, spec.closure_ms / 1000.0,
                  voiced=spec.voiced, spec=spec),
            Phone("burst", c, spec.burst_ms / 1000.0, spec=spec),
        ]
    if spec.manner == "affricate":
        return [
            Phone("closure", c, spec.closure_ms / 1000.0,
                  voiced=spec.voiced, spec=spec),
            Phone("frication", c, spec.dur_ms / 1000.0,
                  voiced=spec.voiced, spec=spec),
        ]
    if spec.manner == "fricative":
        return [Phone("fricative", c, spec.dur_ms / 1000.0,
                      voiced=spec.voiced, spec=spec)]
    if spec.manner == "nasal":
        return [Phone("nasal", c, spec.dur_ms / 1000.0, voiced=True, spec=spec)]
    if spec.manner == "liquid":
        return [Phone("liquid", c, spec.dur_ms / 1000.0, voiced=True, spec=spec)]
    if spec.manner == "tap":
        return [Phone("tap", c, spec.dur_ms / 1000.0, voiced=True, spec=spec)]
    raise ValueError(f"unhandled manner {spec.manner!r}")


def _silence(ms: float) -> Phone:
    return Phone("silence", "", ms / 1000.0)


def _pause(ms: float) -> Phone:
    return Phone("pause", "", ms / 1000.0)


def _is_gap_word(w: Word) -> bool:
    return len(w.morphs) == 1 and (w.morphs[0].gloss == "GAP"
                                   or w.morphs[0].form == "ne")


def _word_phones(w: Word) -> List[Phone]:
    sylls = w.syllables()
    if not sylls:
        return []
    beatless = w.is_beatless()
    stressed_idx = w.stressed_syllable()
    phones: List[Phone] = []
    first_seg = True
    for si, syl in enumerate(sylls):
        stressed = (stressed_idx is not None and si == stressed_idx
                    and not beatless)
        for c in syl.onset:
            phones.extend(_consonant_phones(c, word_initial=first_seg))
            first_seg = False
        phones.append(_vowel_phone(syl.nucleus, stressed))
        first_seg = False
        for c in syl.coda:
            phones.extend(_consonant_phones(c, word_initial=False))
    return phones


def _phones_for_words(words: Sequence[Word],
                      sentence: Optional[Sentence] = None) -> List[Phone]:
    chunks: List[Optional[Word]] = [
        None if _is_gap_word(w) else w for w in words]
    phones: List[Phone] = []
    for i, c in enumerate(chunks):
        if i > 0 and chunks[i] is not None and chunks[i - 1] is not None:
            phones.append(_silence(WORD_GAP_MS))
        if c is None:
            phones.append(_pause(PAUSE_MS))
        else:
            phones.extend(_word_phones(c))
    if sentence is not None and getattr(sentence, "gap_final", False):
        phones.append(_pause(PAUSE_MS))
    return phones


def _token_phones(tokens: Sequence[str]) -> List[Phone]:
    """Voice a navcher-style token stream.

    Letters are phones; ``'x:'``-style ``':'`` marks a long vowel; sigil
    tokens (``'@T'``, ``'=ka'``) and the question ``'?'`` are silent for
    audio; ``' '`` a short gap and ``'|'`` a full pause (docs/03 token
    model, docs/04 the gap as a rest).
    """
    phones: List[Phone] = []
    word_start = True
    for t in tokens:
        if t == " ":
            phones.append(_silence(WORD_GAP_MS))
            word_start = True
            continue
        if t == "|":
            phones.append(_pause(PAUSE_MS))
            word_start = True
            continue
        if not t or t == "?" or t.startswith("@") or t.startswith("="):
            continue  # silent sigils / question mark
        long = t.endswith(":")
        sym = t[:-1] if long else t
        if long and sym in LONG_OF:
            sym = LONG_OF[sym]
        if is_vowel(sym):
            phones.append(_vowel_phone(sym, stressed=False))
            word_start = False
        else:
            phones.extend(_consonant_phones(sym, word_initial=word_start))
            word_start = False
    return phones


def _build_phones(x: Union[str, Sequence[str], Word, Sentence]) -> List[Phone]:
    if isinstance(x, Sentence):
        return _phones_for_words(x.words, sentence=x)
    if isinstance(x, Word):
        return _phones_for_words([x])
    if isinstance(x, str):
        words = [Word.plain(w) for w in x.split() if w]
        return _phones_for_words(words)
    if isinstance(x, (list, tuple)):
        return _token_phones(x)
    raise TypeError(
        f"synth: cannot voice {type(x).__name__}; pass a romanized str, a "
        f"token list, an odylang Word, or a Sentence")


def _assign_f0(phones: Sequence[Phone]) -> None:
    """Apply declination (and any stress accent) to every voiced phone."""
    total = sum(p.dur for p in phones)
    t = 0.0
    for p in phones:
        if p.voiced:
            pos = (t / total) if total > 0 else 0.0
            decl = 1.0 - DECLINATION * pos
            p.f0 = BASE_F0 * decl * p.accent
        t += p.dur


def plan(x: Union[str, Sequence[str], Word, Sentence]) -> List[Phone]:
    """The full phone plan for ``x``, with prosody assigned (no audio)."""
    phones = _build_phones(x)
    _assign_f0(phones)
    return phones


# ---------------------------------------------------------------------------
# rendering


def _render_phone(p: Phone, fs: int, rng: random.Random) -> List[float]:
    n = _samples(p.dur, fs)
    if n <= 0:
        return []
    if p.kind in ("silence", "pause"):
        return [0.0] * n
    spec = p.spec

    if p.kind == "vowel":
        src = _voiced_source(n, p.f0, fs, rng)
        out = _run_formants(src, p.targets, p.glide_to, fs)
        _apply_env(out, fs, 0.008, 0.012)
        _scale(out, 1.0)
        return out

    if p.kind == "closure":
        if p.voiced:
            src = _voiced_source(n, p.f0, fs, rng)
            lp = _lowpass(300.0, 0.7, fs)
            out = [lp.process(x) for x in src]
            _apply_env(out, fs, 0.005, 0.005)
            _scale(out, 0.16)
            return out
        return [0.0] * n

    if p.kind == "burst":
        noise = _noise(n, rng)
        q = 4.0 if (spec and spec.velar_pinch) else 2.2
        fc = spec.burst_hz if spec else 1500.0
        f1 = _bandpass(fc, q, fs)
        out = [f1.process(x) for x in noise]
        if spec and spec.velar_pinch:
            f2 = _bandpass(fc * 1.2, q, fs)
            o2 = [f2.process(x) for x in noise]
            out = [a + 0.7 * b for a, b in zip(out, o2)]
        _apply_env(out, fs, 0.001, 0.006)
        _scale(out, 0.5)
        return out

    if p.kind == "frication":
        lo = spec.noise_lo if spec else 2000.0
        hi = spec.noise_hi if spec else 4000.0
        out = _band_filter(_noise(n, rng), lo, hi, fs)
        if p.voiced:
            src = _voiced_source(n, p.f0, fs, rng)
            lp = _lowpass(1200.0, 0.7, fs)
            buzz = [lp.process(x) for x in src]
            out = [a + 0.5 * b for a, b in zip(out, buzz)]
        _apply_env(out, fs, 0.004, 0.010)
        _scale(out, 0.42)
        return out

    if p.kind == "fricative":
        lo = spec.noise_lo if spec else 3000.0
        hi = spec.noise_hi if spec else 6000.0
        out = _band_filter(_noise(n, rng), lo, hi, fs)
        if p.voiced:
            src = _voiced_source(n, p.f0, fs, rng)
            lp = _lowpass(1000.0, 0.7, fs)
            buzz = [lp.process(x) for x in src]
            out = [a + 0.4 * b for a, b in zip(out, buzz)]
        _apply_env(out, fs, 0.006, 0.010)
        _scale(out, 0.45)
        return out

    if p.kind == "nasal":
        src = _voiced_source(n, p.f0, fs, rng)
        forms = spec.formants if spec else (250.0, 1000.0, 2200.0)
        f0r = _bandpass(forms[0], 4.0, fs)
        f1r = _bandpass(forms[1], 3.0, fs)
        lp = _lowpass(900.0, 0.7, fs)
        out = []
        for x in src:
            v = f0r.process(x) + 0.2 * f1r.process(x)
            out.append(lp.process(v))
        _apply_env(out, fs, 0.010, 0.012)
        _scale(out, 0.34)
        return out

    if p.kind == "liquid":
        src = _voiced_source(n, p.f0, fs, rng)
        forms = spec.formants if spec else (360.0, 1300.0, 2600.0)
        out = _run_formants(src, forms, None, fs)
        _apply_env(out, fs, 0.010, 0.012)
        _scale(out, 0.55)
        return out

    if p.kind == "tap":
        src = _voiced_source(n, p.f0, fs, rng)
        forms = spec.formants if spec else (500.0, 1300.0, 2500.0)
        out = _run_formants(src, forms, None, fs)
        for i in range(n):                      # ballistic bell — brief flap
            out[i] *= math.sin(math.pi * (i + 0.5) / n)
        _scale(out, 0.6)
        return out

    if p.kind == "aspirate":
        lo = spec.noise_lo if spec else 500.0
        hi = spec.noise_hi if spec else 3000.0
        out = _band_filter(_noise(n, rng), lo, hi, fs)
        _apply_env(out, fs, 0.010, 0.015)
        _scale(out, 0.30)
        return out

    raise ValueError(f"unknown phone kind {p.kind!r}")


def _render_pcm(phones: Sequence[Phone], fs: int) -> List[int]:
    rng = random.Random(_RNG_SEED)
    buf: List[float] = []
    for p in phones:
        buf.extend(_render_phone(p, fs, rng))
    peak = 0.0
    for s in buf:
        a = s if s >= 0 else -s
        if a > peak:
            peak = a
    scale = (_HEADROOM * 32767.0 / peak) if peak > 0 else 0.0
    pcm: List[int] = []
    for s in buf:
        v = int(round(s * scale))
        if v > 32767:
            v = 32767
        elif v < -32768:
            v = -32768
        pcm.append(v)
    return pcm


def _wav_bytes(pcm: Sequence[int], fs: int) -> bytes:
    out = io.BytesIO()
    w = wave.open(out, "wb")
    try:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fs)
        w.writeframes(struct.pack("<%dh" % len(pcm), *pcm))
    finally:
        w.close()
    return out.getvalue()


# ---------------------------------------------------------------------------
# public API


def render(x: Union[str, Sequence[str], Word, Sentence], *,
           sample_rate: int = DEFAULT_SAMPLE_RATE) -> Rendered:
    """Full render of ``x`` to a :class:`Rendered` (PCM + probes)."""
    phones = plan(x)
    pcm = _render_pcm(phones, sample_rate)
    f0_track = [p.f0 for p in phones if p.kind == "vowel"]
    return Rendered(pcm=pcm, sample_rate=sample_rate,
                    f0_track=f0_track, phones=phones)


def render_word(word: Union[str, Word], *,
                sample_rate: int = DEFAULT_SAMPLE_RATE) -> Rendered:
    """Render a single word (a :class:`~odylang.word.Word` or romanized str).

    A bare string is treated as one lexical word (penult/heavy stress via
    the four-rule algorithm), so tests can probe e.g. that a long-vowel
    word has more frames than its short-vowel twin.
    """
    return render(word, sample_rate=sample_rate)


def render_phoneme(sym: str, *, sample_rate: int = DEFAULT_SAMPLE_RATE,
                   stressed: bool = False, long: bool = False) -> Rendered:
    """Render one phoneme in isolation (durations probe-able by tests).

    ``sym`` is a romanized segment (``'a'``, ``'ā'``, ``'sh'`` …); trailing
    ``':'`` or ``long=True`` lengthens a vowel; ``stressed`` gives a vowel
    the pitch/duration accent.  Consonants render word-initially.
    """
    s = sym.strip()
    if s.endswith(":"):
        long = True
        s = s[:-1]
    if long and s in LONG_OF:
        s = LONG_OF[s]
    if is_vowel(s):
        phones = [_vowel_phone(s, stressed)]
    else:
        phones = _consonant_phones(s, word_initial=True)
    _assign_f0(phones)
    pcm = _render_pcm(phones, sample_rate)
    f0_track = [p.f0 for p in phones if p.kind == "vowel"]
    return Rendered(pcm=pcm, sample_rate=sample_rate,
                    f0_track=f0_track, phones=phones)


def pitch_track(x: Union[str, Sequence[str], Word, Sentence]) -> List[float]:
    """The per-vowel F0 track (Hz) — flat for imperatives, accented for
    finite verbs (docs/04 §02: the mood carries the beat)."""
    return [p.f0 for p in plan(x) if p.kind == "vowel"]


def synth(x: Union[str, Sequence[str], Word, Sentence], *,
          sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
    """Synthesize ``x`` to complete 16-bit mono PCM WAV file bytes.

    ``x`` may be a romanized Sūchel string, a list of navcher-style tokens
    (letters, ``'u:'`` long, silent sigils like ``'@T'``/``'=ka'``, ``'|'``
    gap, ``' '``), a :class:`~odylang.word.Word`, or a
    :class:`~odylang.suchel_grammar.Sentence`.
    """
    r = render(x, sample_rate=sample_rate)
    return _wav_bytes(r.pcm, sample_rate)


def synth_sentence(sentence: Sentence, *,
                   sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
    """Synthesize a :class:`~odylang.suchel_grammar.Sentence`."""
    return synth(sentence, sample_rate=sample_rate)


def synth_text(text: str, *,
               sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
    """Synthesize a romanized Sūchel string."""
    return synth(text, sample_rate=sample_rate)


def write_wav(x: Union[str, Sequence[str], Word, Sentence], path: str, *,
              sample_rate: int = DEFAULT_SAMPLE_RATE) -> None:
    """Synthesize ``x`` and write the WAV bytes to ``path``."""
    data = synth(x, sample_rate=sample_rate)
    with open(path, "wb") as fh:
        fh.write(data)


def voice_spec() -> dict:
    """A complete, JSON-serializable description of the voice.

    The single source the browser synth reproduces: sample rate, base F0,
    the vowel :data:`FORMANTS` (identical to the module dict), resonator
    bandwidths/weights, the timing constants, and every consonant recipe.
    """
    return {
        "sampleRate": DEFAULT_SAMPLE_RATE,
        "f0": BASE_F0,
        "jitter": JITTER,
        "seed": _RNG_SEED,
        "headroom": _HEADROOM,
        "formants": FORMANTS,
        "formantBandwidths": list(FORMANT_BW),
        "formantAmps": list(FORMANT_AMPS),
        "declination": DECLINATION,
        "timing": {
            "vowelMs": VOWEL_MS,
            "longFactor": LONG_FACTOR,
            "stressDurFactor": STRESS_DUR_FACTOR,
            "stressF0Factor": STRESS_F0_FACTOR,
            "wordGapMs": WORD_GAP_MS,
            "pauseMs": PAUSE_MS,
        },
        "consonants": {k: asdict(v) for k, v in CONSONANTS.items()},
    }
