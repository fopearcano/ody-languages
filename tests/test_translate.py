"""The bidirectional English⇄Sūchel translator, locked against the codices.

Every Sūchel string the engine produces is built through the grammar API
(never typed), and the bilingual dictionary is the *indexed* lexicon; these
tests assert both properties, plus the round-trips: the phrasebook as an
idiom table, morphology recovery over all 41 attested lines, the named
compositional cases, honest unknown-word handling, direction auto-detect,
and that everything it emits re-parses without crashing — deterministically.
"""

import re

import pytest

from odylang import translate as T
from odylang.translate import (Translation, TWord, from_suchel, to_suchel,
                               translate)
from odylang.phrasebook import LINES, line
from odylang.suchel import LEXICON
from odylang.suchel_grammar import Sentence, noun, verb
from odylang import vocabulary as _vocab

NUMBERS = list(range(1, 42))

# --------------------------------------------------------------------------
# 0 · dataclass shape (downstream binds to this exact API)


def test_tword_fields():
    w = TWord(english="hold", suchel="tan-u", gloss="hold-IMP", ipa="ˈta.nu",
              known=True, domain="core")
    assert (w.english, w.suchel, w.gloss, w.ipa, w.known, w.domain) == (
        "hold", "tan-u", "hold-IMP", "ˈta.nu", True, "core")
    assert TWord("x", "—", "?", "", False).domain == ""   # default


def test_translation_fields():
    tr = to_suchel("the beacon holds")
    for attr in ("source", "direction", "text", "ipa", "gloss", "tokens",
                 "syl", "words", "notes", "confidence"):
        assert hasattr(tr, attr)
    assert isinstance(tr.tokens, list)
    assert isinstance(tr.syl, list)
    assert isinstance(tr.words, list) and all(isinstance(w, TWord) for w in tr.words)
    assert isinstance(tr.notes, list)
    assert isinstance(tr.confidence, float)


# --------------------------------------------------------------------------
# 1 · the dictionary is INDEXED, and no root is ever invented


def test_reverse_index_is_built_from_glosses():
    # canon wins over vocab; forms come straight from the derived lexicon
    assert T.REVERSE["hold"].form == "tan"           # docs/02 §F: tan
    assert T.REVERSE["hold"].source == "canon"
    assert T.REVERSE["see"].form == "vid"            # vocabulary *wid-a
    assert T.REVERSE["see"].source == "vocab"
    assert T.REVERSE["truth"].form == "ver"


def test_every_verb_stem_is_lexicon_backed():
    """No root is coined: each mapped verb stem is an attested/derived form."""
    for spec in T.VERBS.values():
        assert T._forward(spec.stem) is not None, spec


def test_core_map_points_only_at_attested_forms():
    for form in T._CORE_NOUNS.values():
        assert T._forward(form) is not None, form


# --------------------------------------------------------------------------
# 2 · English -> Sūchel: the phrasebook idiom table


IDIOM_SAMPLE = [1, 3, 4, 6, 9, 11, 14, 17, 25, 28, 36, 41]  # a dozen, all sections


@pytest.mark.parametrize("n", IDIOM_SAMPLE)
def test_idiom_round_trip_sample(n):
    ln = line(n)
    tr = to_suchel(ln.translation)
    assert tr.text == ln.sentence.text()
    assert tr.confidence == 1.0
    assert tr.notes == [f"attested phrasebook line {n}"]


def test_idiom_round_trip_all_attested_lines():
    """Every phrasebook English translation returns its attested Sūchel."""
    for ln in LINES:
        if not T._norm_idiom(ln.translation):
            continue                     # the gap line has no English idiom
        tr = to_suchel(ln.translation)
        assert tr.text == ln.sentence.text(), ln.number
        assert tr.confidence == 1.0


def test_idiom_surfaces_are_generated_not_typed():
    """The idiom result carries generated IPA / gloss / rhythm / tokens."""
    ln = line(14)
    tr = to_suchel(ln.translation)
    assert tr.ipa == ln.sentence.ipa()
    assert tr.gloss == ln.sentence.gloss_line()
    assert tr.syl == ln.sentence.syl_line()
    assert tr.tokens and " " not in "".join(tr.tokens[:1])


# --------------------------------------------------------------------------
# 3 · English -> Sūchel: compositional clauses (built through the grammar)


def test_i_surfaced():
    tr = to_suchel("I surfaced")
    assert tr.text == "en hōl-t-a=mi."          # 1SG, perfective, proper-time
    assert tr.direction == "en2su"
    assert "PFV" in tr.gloss and "PROP" in tr.gloss


def test_the_beacon_holds():
    tr = to_suchel("the beacon holds")
    # factual, beacon-anchored — and identical to the same clause built by hand
    expected = Sentence([noun("kad", gloss="beacon"),
                         verb("tan", "T", "ka", gloss="hold")]).text()
    assert tr.text == expected == "kad tan-a=ka."


def test_we_cross_is_seam_true():
    tr = to_suchel("we cross")
    assert tr.text == "eni sū-eshe=mi."         # crossing verb -> T• mood
    assert "T•" in tr.gloss


def test_do_not_go_is_a_prohibitive():
    tr = to_suchel("do not go")
    assert tr.text == "vo jed-u."               # NEG + beatless imperative
    assert tr.gloss == "NEG go-IMP"


def test_negated_statement():
    tr = to_suchel("I do not see the ship")
    assert tr.text == "en naven vo vid-a=mi."   # SOV, vo pre-verbal
    assert "NEG" in tr.gloss


def test_polar_question_appends_vu():
    tr = to_suchel("does the beacon hold?")
    # this happens to be attested (line 13) — the idiom table catches it
    assert tr.text.endswith("vu?")
    assert "Q" in tr.gloss


def test_polar_question_compositional():
    tr = to_suchel("does the ship hold?")   # not attested -> composed
    assert tr.text.endswith("vu?")
    assert tr.text.split()[-1] == "vu?"
    assert "Q" in tr.gloss


def test_modal_mood_cues():
    assert to_suchel("maybe the ship holds").text == "nav tan-ur=ka."   # T+
    assert "T⁺" in to_suchel("maybe the ship holds").gloss


def test_motion_verb_with_direction():
    tr = to_suchel("she goes down")
    assert tr.text == "an nuv jed-a=ka."        # depth satellite present


def test_compositional_confidence_below_one():
    # a fully-composed clause is confident but never claims the 1.0 of attestation
    assert to_suchel("the beacon holds").confidence == 0.9


# --------------------------------------------------------------------------
# 4 · unknown words are reported, never fabricated


def test_unknown_content_word():
    tr = to_suchel("I frobnicate the ship")
    assert tr.confidence < 1.0
    ub = [w for w in tr.words if not w.known]
    assert ub and ub[0].suchel == "—"
    assert any("frobnicate" in n for n in tr.notes)


def test_no_lexical_match_returns_scaffold():
    tr = to_suchel("frobnicate qux")
    assert tr.confidence < 0.5
    assert tr.notes
    assert not tr.words or all(not w.known for w in tr.words)


# --------------------------------------------------------------------------
# 5 · Sūchel -> English: recover stems, mood, anchor from all 41 lines

_MOOD_ANCHOR = re.compile(r"(T[•⁻⁺]?)=(BEAC|PROP|DARK)")


@pytest.mark.parametrize("n", NUMBERS)
def test_from_suchel_recovers_mood_and_anchor(n):
    ln = line(n)
    tr = from_suchel(ln.sentence.text())
    assert tr.direction == "su2en"
    assert tr.syl == []                          # su2en carries no rhythm array
    for mood, anchor in _MOOD_ANCHOR.findall(ln.sentence.gloss_line()):
        assert f"{mood}={anchor}" in tr.gloss, (n, mood, anchor, tr.gloss)


@pytest.mark.parametrize("n", NUMBERS)
def test_from_suchel_recognises_every_stem(n):
    """Every content word of every attested line peels to a known stem."""
    tr = from_suchel(line(n).sentence.text())
    assert tr.confidence == 1.0, (n, tr.notes)
    assert all(w.known for w in tr.words), (n, [w.suchel for w in tr.words])


def test_from_suchel_specific_glosses():
    # the death formula: 3SG · go · PFV · plain-T · proper-time
    g = from_suchel("an zu jed-t-a=mi.").gloss
    assert "PFV" in g and "T=PROP" in g and "DOWN" not in g
    # the far-side call: surfaced, seam-true, dark time, a question
    g2 = from_suchel("hōl-t-eshe=zu vu?").gloss
    assert "PFV" in g2 and "T•=DARK" in g2 and "Q" in g2
    # the gap
    assert from_suchel("ne.").gloss == "GAP"


def test_from_suchel_unknown_stem_kept_verbatim():
    tr = from_suchel("en floog-a=mi")
    assert tr.confidence < 1.0
    bad = [w for w in tr.words if not w.known]
    assert bad and bad[0].suchel == "floog-a=mi"
    assert any("floog" in n for n in tr.notes)


def test_from_suchel_paraphrase_surfaces_adverbials():
    txt = from_suchel("hōl-eshe=zu, maiel.").text
    assert "seam-true" in txt and "dark time" in txt


# --------------------------------------------------------------------------
# 6 · direction auto-detect


@pytest.mark.parametrize("text,expected", [
    ("kad ver-a=ka vu?", "su2en"),
    ("en jed-a=mi", "su2en"),
    ("ver ish-ol", "su2en"),
    ("ne", "su2en"),
    ("hōl-t-eshe=zu", "su2en"),
    ("the beacon holds", "en2su"),
    ("we cross", "en2su"),
    ("I do not see the ship", "en2su"),
    ("do not go", "en2su"),
])
def test_direction_auto(text, expected):
    assert T.detect_direction(text) == expected
    assert translate(text).direction == expected


def test_translate_dispatch_and_override():
    assert translate("the beacon holds", "en2su").direction == "en2su"
    assert translate("kad tan-a=ka", "su2en").direction == "su2en"
    with pytest.raises(ValueError):
        translate("x", "sideways")


# --------------------------------------------------------------------------
# 7 · fuzz: everything the engine emits re-parses without crashing


@pytest.mark.parametrize("n", NUMBERS)
def test_phrasebook_lines_reparse(n):
    from_suchel(line(n).sentence.text())        # must not raise


COMPOSITIONAL = [
    "I surfaced", "the beacon holds", "we cross", "do not go",
    "she goes down", "I do not see the ship", "we hold the pattern",
    "you know", "they run up", "give me the pearl", "I want water",
    "maybe the ship holds", "does the ship hold?", "the mother sleeps",
]


@pytest.mark.parametrize("english", COMPOSITIONAL)
def test_compositional_outputs_reparse(english):
    tr = to_suchel(english)
    assert tr.direction == "en2su"
    back = from_suchel(tr.text)                  # round-trip through the parser
    assert isinstance(back, Translation)


# --------------------------------------------------------------------------
# 8 · determinism: byte-reproducible output


@pytest.mark.parametrize("text", [
    "the beacon holds", "I surfaced", "kad ver-a=ka vu?", "we cross",
    "hōl-t-eshe=zu vu?",
])
def test_deterministic(text):
    a, b = translate(text), translate(text)
    assert a == b                                # dataclass equality, field by field
    assert a.text == b.text and a.gloss == b.gloss and a.tokens == b.tokens


def test_reverse_index_stable_and_prefers_canon():
    # rebuild the index: identical, and canon precedence is honoured
    rebuilt = T._build_reverse()
    assert rebuilt == T.REVERSE
    # 'hold' is glossed by canon *tan*; the vocab never overrides it
    assert T.REVERSE["hold"].source == "canon"
