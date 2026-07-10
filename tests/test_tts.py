"""The Sūchel formant synthesizer: valid WAV output, byte-for-byte
determinism, phonemic length, the mood-carries-the-beat pitch accent
(docs/04), the gap as a rest, no clipping, and a complete voice_spec()."""

import io
import json
import wave

import pytest

from odylang import tts
from odylang.phrasebook import line
from odylang.suchel_grammar import Sentence, imperative, particle, verb


# ---------------------------------------------------------------------------
# helpers


def _open(data):
    w = wave.open(io.BytesIO(data), "rb")
    return w


def _samples(data):
    """Every int16 sample of a mono WAV, as Python ints."""
    w = _open(data)
    n = w.getnframes()
    raw = w.readframes(n)
    import struct
    return list(struct.unpack("<%dh" % n, raw))


# ---------------------------------------------------------------------------
# WAV validity


def test_output_is_valid_mono_16bit_wav():
    data = tts.synth("Sūchel")
    w = _open(data)
    assert w.getnchannels() == 1
    assert w.getsampwidth() == 2          # 16-bit
    assert w.getframerate() == tts.DEFAULT_SAMPLE_RATE
    assert w.getnframes() > 0


def test_sample_rate_parameter_is_honored():
    data = tts.synth("ver", sample_rate=16000)
    assert _open(data).getframerate() == 16000


def test_sentence_and_text_and_token_paths_all_valid():
    sent = line(1).sentence                       # ver ish-ol.
    for x in (sent, "ver ishol", ["v", "e", "r"]):
        w = _open(tts.synth(x))
        assert w.getnchannels() == 1 and w.getsampwidth() == 2

    # the dedicated entry points agree with synth()
    assert tts.synth_sentence(sent) == tts.synth(sent)
    assert tts.synth_text("ver ishol") == tts.synth("ver ishol")


# ---------------------------------------------------------------------------
# determinism


def test_identical_input_gives_identical_bytes():
    a = tts.synth("hōl-t-eshe=zu enmai")
    b = tts.synth("hōl-t-eshe=zu enmai")
    assert a == b

    sent = line(38).sentence
    assert tts.synth_sentence(sent) == tts.synth_sentence(sent)


def test_silent_sigils_do_not_change_audio():
    # '@T' and '=ka' are silent for audio, so the two token streams voice
    # the identical phone plan and therefore the identical bytes.
    assert tts.synth(["v", "e", "r", "@T", "=ka"]) == tts.synth(["v", "e", "r"])
    assert tts.synth(["i", "?", "d"]) == tts.synth(["i", "d"])


# ---------------------------------------------------------------------------
# phonemic length (docs/04 §01: length is quality held, not changed)


def test_long_vowel_word_is_longer_than_short_twin():
    short = tts.render_word("mal")
    long = tts.render_word("māl")
    assert long.frames > short.frames


def test_long_phoneme_and_stress_extend_a_vowel():
    plain = tts.render_phoneme("a")
    held = tts.render_phoneme("ā")
    stressed = tts.render_phoneme("a", stressed=True)
    assert held.frames > plain.frames
    assert stressed.frames > plain.frames
    # the ':' spelling lengthens exactly like the macron
    assert tts.render_phoneme("a:").frames == held.frames


# ---------------------------------------------------------------------------
# the mood carries the beat (docs/04 §02): imperatives are flat/beatless


def test_imperative_pitch_is_flatter_than_a_finite_verb():
    imp = tts.pitch_track(imperative("tan", "swallow"))     # beatless
    fin = tts.pitch_track(verb("ver", "T", "ka", gloss="hold"))  # moody

    imp_range = max(imp) - min(imp)
    fin_range = max(fin) - min(fin)
    assert imp_range < fin_range

    # the imperative never rises above the base (only gentle declination),
    # while the finite verb's mood syllable spikes well above it.
    assert max(imp) <= tts.BASE_F0 + 1e-6
    assert max(fin) > tts.BASE_F0 * 1.25


# ---------------------------------------------------------------------------
# the gap is a rest (docs/04: line 38 plays as silence)


def test_gap_token_is_near_silence():
    for data in (tts.synth(["|"]), tts.synth([" ", "|", " "])):
        w = _open(data)
        assert w.getnframes() > 0                 # it occupies real time
        assert max((abs(s) for s in _samples(data)), default=0) == 0

    # a Sentence whose only word is the gap particle *ne* is likewise a rest
    ne = Sentence([particle("ne")])
    assert max((abs(s) for s in _samples(tts.synth_sentence(ne))),
               default=0) == 0


# ---------------------------------------------------------------------------
# no clipping — every sample stays inside int16


def test_no_sample_exceeds_int16_range():
    for x in ("hōl-t-eshe=zu enmai ve-a=mi", "Sūchel Sōrn zukad",
              line(40).sentence):
        for s in _samples(tts.synth(x)):
            assert -32768 <= s <= 32767
        # and normalisation keeps a real peak just under full-scale
        peak = max(abs(s) for s in _samples(tts.synth(x)))
        assert peak <= 32767


# ---------------------------------------------------------------------------
# voice_spec()


def test_voice_spec_is_json_serializable_and_matches_formants():
    spec = tts.voice_spec()
    dumped = json.dumps(spec)                     # must not raise
    assert isinstance(dumped, str)

    assert spec["formants"] == tts.FORMANTS
    assert spec["sampleRate"] == tts.DEFAULT_SAMPLE_RATE
    assert spec["f0"] == tts.BASE_F0
    # the five cardinal vowels, exactly the documented targets
    assert set(tts.FORMANTS) == {"a", "e", "i", "o", "u"}
    assert tts.FORMANTS["a"] == (800.0, 1200.0, 2500.0)

    # every consonant of the inventory is described
    assert set(spec["consonants"]) == set(tts.CONSONANTS)
    assert spec["consonants"]["k"]["burst_hz"] == 1500.0


def test_voice_spec_roundtrips_through_json():
    spec = tts.voice_spec()
    back = json.loads(json.dumps(spec))
    # tuples become lists across JSON; compare structurally
    assert back["formants"]["a"] == [800.0, 1200.0, 2500.0]
    assert back["timing"]["longFactor"] == tts.LONG_FACTOR


# ---------------------------------------------------------------------------
# performance guard


def test_short_phrase_synthesizes_quickly():
    import time
    t0 = time.perf_counter()
    tts.synth(line(1).sentence)
    assert time.perf_counter() - t0 < 1.0


# ---------------------------------------------------------------------------
# write_wav


def test_write_wav_produces_a_readable_file(tmp_path):
    path = tmp_path / "out.wav"
    tts.write_wav("ver ishol", str(path))
    assert path.exists() and path.stat().st_size > 44   # header + data
    w = wave.open(str(path), "rb")
    assert w.getnchannels() == 1 and w.getsampwidth() == 2
