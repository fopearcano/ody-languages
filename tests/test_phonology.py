"""Segments, syllables, stress, IPA — checked against codex transcriptions."""

import pytest

from odylang.phonology import syllabify, tokenize, word_ipa
from odylang.word import (ANCHOR, CASE, DERIV, IMP, MAI, MOOD, PART, PFV,
                          PLURAL, STEM, STEM2, Morph, Word)


def syls(word):
    return ["".join(s.onset) + s.nucleus + "".join(s.coda)
            for s in syllabify(tokenize(word))]


def test_tokenize_digraphs_and_length():
    assert tokenize("sūchel") == ["s", "ū", "ch", "e", "l"]
    assert tokenize("nexath") == ["n", "e", "x", "a", "th"]
    assert tokenize("hau") == ["h", "au"]
    assert tokenize("enmai") == ["e", "n", "m", "ai"]


def test_syllabification_matches_codex():
    assert syls("sūchel") == ["sū", "chel"]
    assert syls("idrenes") == ["i", "dre", "nes"]
    assert syls("nexath") == ["ne", "xath"]
    assert syls("sōrn") == ["sōrn"]
    assert syls("jedtami") == ["jed", "ta", "mi"]
    assert syls("veaka") == ["ve", "a", "ka"]
    assert syls("ishmaiol") == ["ish", "mai", "ol"]


# -- the four rules (docs/04 §02), one word each ------------------------------

def _verb(stem, pfv, mood, anchor):
    m = [Morph(stem, cat=STEM)]
    if pfv:
        m.append(Morph("t", "PFV", PFV, "-"))
    m.append(Morph(mood[0], mood[1], MOOD, "-"))
    m.append(Morph(anchor[0], anchor[1], ANCHOR, "="))
    return Word(m)


def test_rule1_compounds():
    for first, second, expect in [("nuv", "ran", 0), ("jel", "mar", 0),
                                  ("zu", "kad", 0)]:
        w = Word([Morph(first, cat=STEM), Morph(second, cat=STEM2)])
        assert w.stressed_syllable() == expect
    # E-she-ver: first member's own stress
    w = Word([Morph("eshe", cat=STEM), Morph("ver", cat=STEM2)])
    assert w.syl_beats() == ["E", "she", "ver"]
    # jelsīl: rule 1 outranks the long vowel of the second member
    w = Word([Morph("jel", cat=STEM), Morph("sīl", cat=STEM2)])
    assert w.syl_beats() == ["JEL", "si:l"]


def test_rule2_mood_seizes_stress():
    assert _verb("ver", False, ("a", "T"), ("ka", "BEAC")).syl_beats() == \
        ["ve", "RA", "ka"]
    assert _verb("tan", False, ("a", "T"), ("mi", "PROP")).syl_beats() == \
        ["ta", "NA", "mi"]
    assert _verb("hōl", True, ("eshe", "T•"), ("zu", "DARK")).syl_beats() == \
        ["ho:l", "TE", "she", "zu"]
    assert _verb("id", False, ("eshe", "T•"), ("mi", "PROP")).syl_beats() == \
        ["i", "DE", "she", "mi"]
    # rule 2 outranks the long vowel (rule 3): hōl-eshe=zu
    assert _verb("hōl", False, ("eshe", "T•"), ("zu", "DARK")).syl_beats() == \
        ["ho:", "LE", "she", "zu"]


def test_rule3_long_vowel_seizes_stress():
    assert Word([Morph("sūchel", cat=STEM)]).syl_beats() == ["SU:", "chel"]
    assert Word([Morph("hōl", cat=STEM), Morph("u", "IMP", IMP, "-")]
                ).syl_beats() == ["HO:", "lu"]
    assert Word([Morph("mān", cat=STEM)]).syl_beats() == ["MA:N"]
    assert Word([Morph("hau", cat=PART)]).syl_beats() == ["HAU"]


def test_rule4_penult_of_stem_case_never_shifts():
    assert Word([Morph("idrenes", cat=STEM)]).syl_beats() == ["i", "DRE", "nes"]
    w = Word([Morph("vur", cat=STEM), Morph("el", "AGT", DERIV),
              Morph("en", "GEN", CASE, "-")])
    assert w.syl_beats() == ["VU", "re", "len"]
    w = Word([Morph("zu", cat=STEM), Morph("kad", cat=STEM2),
              Morph("eth", "LOC", CASE, "-")])
    assert w.syl_beats() == ["ZU", "ka", "deth"]


def test_imperatives_are_beatless_but_stem_stressed():
    w = Word([Morph("tan", cat=STEM), Morph("u", "IMP", IMP, "-")])
    assert w.syl_beats() == ["TA", "nu"]
    assert w.is_beatless()


def test_monosyllables_beat_only_when_long():
    assert Word.particle("ver").syl_beats() == ["ver"]
    assert Word.particle("kad").syl_beats() == ["kad"]
    assert Word.particle("ō").syl_beats() == ["O:"]
    assert Word.plain("ān").syl_beats() == ["A:N"]


def test_entangled_pronoun_exception():
    """[ˈen.mai] bare, but [enˈmai.eth] under case (docs/02 §28, §31)."""
    bare = Word([Morph("en", "1PL", STEM), Morph("mai", "ENT", MAI)])
    assert bare.syl_beats() == ["EN", "mai"]
    assert bare.ipa() == "ˈen.mai"
    cased = Word([Morph("en", "1PL", STEM), Morph("mai", "ENT", MAI),
                  Morph("eth", "LOC", CASE, "-")])
    assert cased.syl_beats() == ["en", "MAI", "eth"]
    assert cased.ipa() == "enˈmai.eth"
    cased2 = Word([Morph("ish", "2SG", STEM), Morph("mai", "ENT", MAI),
                   Morph("ol", "DAT", CASE, "-")])
    assert cased2.ipa() == "iʃˈmai.ol"


def test_noun_mai_does_not_shift():
    w = Word([Morph("nexath", "gap", STEM), Morph("mai", "ENT", MAI, "-")])
    assert w.syl_beats() == ["NE", "ksath", "mai"]
    assert w.ipa() == "ˈne.ksath.mai"
    w = Word([Morph("nav", "ship", STEM), Morph("mai", "ENT", MAI)])
    assert w.ipa() == "ˈnav.mai"


def test_ipa_examples_from_codex():
    assert _verb("ver", False, ("a", "T"), ("ka", "BEAC")).ipa() == "veˈra.ka"
    assert _verb("jed", True, ("a", "T"), ("mi", "PROP")).ipa() == "dʒedˈta.mi"
    assert _verb("hōl", True, ("eshe", "T•"), ("zu", "DARK")).ipa() == \
        "hoːlˈte.ʃe.zu"
    assert Word([Morph("sōrn", cat=STEM), Morph("mai", "ENT", MAI)]).ipa() == \
        "ˈsoːrn.mai"
