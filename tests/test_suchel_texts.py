"""The docs/01 §07 texts and the §05 Κ5 showpieces, line by line.

Expected romanizations and Leipzig glosses are transcribed from docs/01
and are the authority; odylang/suchel_texts.py must generate them through
the grammar API.  One normalization, documented in that module: the
Absolute Verdict's gloss writes the beacon anchor '=BEAC' (the codices'
usual spelling, ~a dozen attestations) where docs/01 §05 once prints
'=BEACON'.
"""

import pytest

from odylang import suchel_texts as st
from odylang.suchel_grammar import lexicon_has
from odylang.word import STEM, STEM2

# --------------------------------------------------------------------------
# docs/01 §07 — expected (text, gloss) per line, verbatim

PILOTS_LOG = [
    ("enmai kad tel-eth sū-t-eshe=ka.",
     "1PL.ENT beacon three-LOC cross-PFV-T•=BEAC"),
    ("ne.", "GAP"),
    ("enmai hōl-t-eshe=zu.", "1PL.ENT surface-PFV-T•=DARK"),
]

CATECHISM = [
    ("tem kav-eth dur-a=ka, vo?", "pattern limit-LOC endure-T=BEAC, NEG"),
    ("vo dur-a=ka, somath-en ver-eth.",
     "NEG endure-T=BEAC, assembly-GEN truth-LOC"),
    ("dur-eshe=zu.", "endure-T•=DARK"),
]

NE_LITURGY = [
    ("sīli sū-eshe=mi.", "crosser.PL cross-T•=PROP"),
    ("ne.", "GAP"),
    ("kad vel ver-a=ka.", "beacon nothing speak.true-T=BEAC"),
    ("ne.", "GAP"),
    ("enmai ish-mai tel-im=zu.", "1PL.ENT 2SG-ENT reach-T⁻=DARK"),
]

EXPECTED = {
    "pilots_log": PILOTS_LOG,
    "catechism": CATECHISM,
    "ne_liturgy": NE_LITURGY,
}

TRANSLATION_STARTS = {
    "pilots_log": ["We crossed at the third beacon.", "—",
                   "We surfaced, in dark time."],
    "catechism": ['"Does a pattern endure at the limit — no?"',
                  '"It does not endure — in the Assembly\'s truth."',
                  '"It endures — seam-true, in the dark."'],
    "ne_liturgy": ["The crossers cross, by their own clocks.", "—",
                   "The beacon vouches for nothing.", "—",
                   "We reach toward you — approaching-true, in the dark."],
}


@pytest.mark.parametrize("text", st.TEXTS, ids=lambda t: t.key)
def test_text_lines_and_glosses(text):
    expected = EXPECTED[text.key]
    assert len(text.lines) == len(expected)
    for passage, (lat, gloss) in zip(text.lines, expected):
        assert passage.sentence.text() == lat
        assert passage.sentence.gloss_line() == gloss


@pytest.mark.parametrize("text", st.TEXTS, ids=lambda t: t.key)
def test_text_translations(text):
    for passage, start in zip(text.lines, TRANSLATION_STARTS[text.key]):
        assert passage.translation.startswith(start)


def test_three_texts_in_codex_order():
    assert [t.key for t in st.TEXTS] == ["pilots_log", "catechism",
                                         "ne_liturgy"]
    assert st.TEXTS[0] is st.PILOTS_LOG
    assert st.TEXTS[1] is st.CATECHISM
    assert st.TEXTS[2] is st.NE_LITURGY


def test_pilots_log_arc():
    """docs/01 §07: crossing =ka (inside coverage), return =zu (beyond),
    the gap between — a censor could reconstruct the flight plan."""
    first, gap, last = st.PILOTS_LOG.lines
    assert first.sentence.words[-1].display().endswith("=ka")
    assert last.sentence.words[-1].display().endswith("=zu")
    assert gap.sentence.gloss_line() == "GAP"


def test_catechism_dialogue_form():
    """docs/01 §07 TEXT 02: every turn opens with a dash, and the third
    translation carries its full parenthetical."""
    for p in st.CATECHISM.lines:
        assert p.dash
        assert p.display().startswith("— ")
    assert st.CATECHISM.lines[0].display() == "— tem kav-eth dur-a=ka, vo?"
    assert st.CATECHISM.lines[2].translation == (
        '"It endures — seam-true, in the dark." (the pupil who will not '
        "pass; the answer that cannot be graded, only punished)")
    for text in (st.PILOTS_LOG, st.NE_LITURGY):
        assert not any(p.dash for p in text.lines)


def test_catechism_heresy_is_two_morphemes():
    """-eshe for -a, =zu for =ka: doctrine and its undoing differ by a
    conjugation (docs/01 §07 text 02)."""
    orthodox = st.CATECHISM.lines[1].sentence.words[1]
    heretic = st.CATECHISM.lines[2].sentence.words[0]
    assert orthodox.display() == "dur-a=ka"
    assert heretic.display() == "dur-eshe=zu"
    o = {(m.cat, m.form) for m in orthodox.morphs}
    h = {(m.cat, m.form) for m in heretic.morphs}
    assert len(o ^ h) == 4  # exactly two morphs swapped


def test_ne_liturgy_every_second_line_is_the_gap():
    for i, passage in enumerate(st.NE_LITURGY.lines):
        is_gap = passage.sentence.gloss_line() == "GAP"
        assert is_gap == (i % 2 == 1)


def test_liturgy_keeps_the_dead_as_kin():
    """The entangled -mai on 'you' (ish-mai, hyphenated per docs/01 §07)
    declares the dead still possessed as kin."""
    you = st.NE_LITURGY.lines[4].sentence.words[1]
    assert you.display() == "ish-mai"
    assert you.gloss() == "2SG-ENT"


# --------------------------------------------------------------------------
# docs/01 §05 — the Κ5 showpieces

K5_EXPECTED = {
    "absolute_verdict": ("tem kav-eth vo dur-a=ka.",
                         "pattern limit-LOC NEG endure-T=BEAC",
                         "No pattern endures at the limit.",
                         "Pelagian Assembly · doctrine"),
    "madmans_theorem": ("tem kav-eth dur-ur=zu.",
                        "pattern limit-LOC endure-T⁺=DARK",
                        "A pattern endures at the limit",
                        "the mythical ship · heresy"),
    "tragic_truth": ("tem kav-eth dur-eshe=zu.",
                     "pattern limit-LOC endure-T•=DARK",
                     "A pattern endures — seam-true — in dark time.",
                     "what actually happens · unsayable-as-fact"),
}


@pytest.mark.parametrize("piece", st.K5, ids=lambda p: p.key)
def test_k5_showpieces(piece):
    lat, gloss, translation, attribution = K5_EXPECTED[piece.key]
    assert piece.sentence.text() == lat
    assert piece.sentence.gloss_line() == gloss
    assert piece.translation == translation
    assert piece.attribution == attribution
    assert piece.commentary


def test_k5_one_sentence_three_moods():
    """Same frame, same stem — only the conjugation moves (docs/01 §05)."""
    frames = [[w.display() for w in p.sentence.words[:2]] for p in st.K5]
    assert frames[0] == frames[1] == frames[2] == ["tem", "kav-eth"]
    verbs = [p.sentence.words[-1] for p in st.K5]
    assert all(v.morphs[0].form == "dur" for v in verbs)


# --------------------------------------------------------------------------
# housekeeping


def test_every_stem_is_lexicon_backed():
    sentences = [p.sentence for t in st.TEXTS for p in t.lines]
    sentences += [p.sentence for p in st.K5]
    for s in sentences:
        for w in s.words:
            for m in w.morphs:
                if m.cat in (STEM, STEM2):
                    assert lexicon_has(m.form), m.form


def test_commentaries_present_and_abridged():
    for t in st.TEXTS:
        assert t.commentary
    for p in st.K5:
        assert p.commentary
