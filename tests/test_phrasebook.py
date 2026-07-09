"""The 41 phrasebook lines, locked four ways against the codices.

For every line of docs/02 the module must reproduce, generatively:
(a) the romanized line — including medial punctuation — exactly as the
    codex letters it;
(b) the Leipzig morpheme gloss of docs/02 (raised dots and commas
    included where the codex shows them);
(c) the codex IPA of docs/02;
(d) the syllable/stress rhythm array embedded in docs/04 as
    ``const LINES`` (CAPS = stressed, ':' = long vowel, '/' = word break,
    '|' = the gap), verbatim.

The expected strings below are transcribed from docs/02 and docs/04 and
are the authority; odylang/phrasebook.py builds everything through the
grammar API.
"""

import pytest

from odylang.phrasebook import LINES, SECTIONS, line
from odylang.suchel_grammar import lexicon_has
from odylang.word import STEM, STEM2

# --------------------------------------------------------------------------
# docs/02 — romanized line (lat), morpheme gloss, IPA

LAT = {
    1: "ver ish-ol.",
    2: "ver ishmai-ol.",
    3: "ō mān!",
    4: "kad ishen tan-u.",
    5: "zukad-eth, lesh ishen tan-u.",
    6: "hōl-u ret.",
    7: "en jed-a=mi.",
    8: "men-u, mān.",
    9: "nuv jed-u!",
    10: "hau jed-u!",
    11: "jel id-u.",
    12: "Sōrnmai, tan-u.",
    13: "kad ver-a=ka vu?",
    14: "ver-a=ka.",
    15: "vo ver-a=ka. zukad.",
    16: "tem tan-u, eni om.",
    17: "jelvos!",
    18: "velosh ishen oshu!",
    19: "vo-tem!",
    20: "kru jel-eth!",
    21: "an vo hōl-u!",
    22: "gal ishen tan-u!",
    23: "vurel-en chel!",
    24: "en ver-a=mi: …",
    25: "Turmai, enen tan-u.",
    26: "kad om-ol ver-u.",
    27: "jel lesh-eth id-u.",
    28: "enmai nexath-mai tan-a=mi.",
    29: "an zu jed-t-a=mi.",
    30: "hōl-eshe=zu, maiel.",
    31: "ver enmai-eth ve-a=ka.",
    32: "eshe-ver men-a=zu.",
    33: "Sōrnmai, ān tan-u.",
    34: "ān tan-a=mi.",
    35: "nuv, nuv, jel-ol.",
    36: "nuvran ve-a=mi.",
    37: "jel id-eshe=mi.",
    38: "ne.",
    39: "hōl-t-eshe=zu vu?",
    40: "hōl-t-eshe=zu. enmai ve-a=mi.",
    41: "kad ret ver-a=ka.",
}

GLOSS = {
    1: "truth 2SG-DAT",
    2: "truth 2SG.ENT-DAT",
    3: "VOC crew.hand",
    4: "beacon 2SG.ACC hold-IMP",
    5: "dark.time-LOC alignment 2SG.ACC hold-IMP",
    6: "surface-IMP again",
    7: "1SG go-T=PROP",
    8: "wait-IMP crew.hand",
    9: "DOWN go-IMP",
    10: "UP go-IMP",
    11: "seam open-IMP",
    12: "drive.ENT hold-IMP",
    13: "beacon speak.true-T=BEAC Q",
    14: "true-T=BEAC",
    15: "NEG true-T=BEAC · dark.time",
    16: "pattern hold-IMP · 1PL all",
    17: "seam.scar",
    18: "Formless.mouth 2SG.ACC swallow-IMP",
    19: "NEG-pattern",
    20: "blood seam-LOC",
    21: "3SG NEG surface-IMP",
    22: "the.still 2SG.ACC hold-IMP",
    23: "madman-GEN speech",
    24: "1SG speak.true-T=PROP",
    25: "Tower.ENT 1SG.ACC hold-IMP",
    26: "beacon all-DAT speak.true-IMP",
    27: "seam alignment-LOC open-IMP",
    28: "1PL.ENT gap-ENT hold-T=PROP",
    29: "3SG adrift go-PFV-T=PROP",
    30: "surface-T•=DARK kinsman",
    31: "truth 1PL.ENT-LOC be-T=BEAC",
    32: "seam.true-truth wait-T=DARK",
    33: "drive.ENT breath hold-IMP",
    34: "breath hold-T=PROP",
    35: "DOWN DOWN seam-DAT",
    36: "running.under be-T=PROP",
    37: "seam open-T•=PROP",
    38: "GAP",
    39: "surface-PFV-T•=DARK Q",
    40: "surface-PFV-T•=DARK · 1PL.ENT be-T=PROP",
    41: "beacon again true-T=BEAC",
}

IPA = {
    1: "[ver iˈʃol]",
    2: "[ver iʃˈmai.ol]",
    3: "[oː maːn]",
    4: "[kad ˈi.ʃen ˈta.nu]",
    5: "[ˈzu.ka.deth · leʃ ˈi.ʃen ˈta.nu]",
    6: "[ˈhoː.lu ret]",
    7: "[en dʒeˈda.mi]",
    8: "[ˈme.nu maːn]",
    9: "[nuv ˈdʒe.du]",
    10: "[hau ˈdʒe.du]",
    11: "[dʒel ˈi.du]",
    12: "[ˈsoːrn.mai ˈta.nu]",
    13: "[kad veˈra.ka vu]",
    14: "[veˈra.ka]",
    15: "[vo veˈra.ka · ˈzu.kad]",
    16: "[tem ˈta.nu · ˈe.ni om]",
    17: "[ˈdʒel.vos]",
    18: "[ˈve.loʃ ˈi.ʃen ˈo.ʃu]",
    19: "[ˈvo.tem]",
    20: "[kru ˈdʒe.leth]",
    21: "[an vo ˈhoː.lu]",
    22: "[gal ˈi.ʃen ˈta.nu]",
    23: "[ˈvu.re.len tʃel]",
    24: "[en veˈra.mi]",
    25: "[ˈtur.mai ˈe.nen ˈta.nu]",
    26: "[kad ˈo.mol ˈve.ru]",
    27: "[dʒel ˈle.ʃeth ˈi.du]",
    28: "[ˈen.mai ˈne.ksath.mai taˈna.mi]",
    29: "[an zu dʒedˈta.mi]",
    30: "[hoːˈle.ʃe.zu ˈmai.el]",
    31: "[ver enˈmai.eth veˈa.ka]",
    32: "[ˈe.ʃe.ver meˈna.zu]",
    33: "[ˈsoːrn.mai aːn ˈta.nu]",
    34: "[aːn taˈna.mi]",
    35: "[nuv nuv ˈdʒe.lol]",
    36: "[ˈnuv.ran veˈa.mi]",
    37: "[dʒel iˈde.ʃe.mi]",
    38: "[ne]",
    39: "[hoːlˈte.ʃe.zu vu]",
    40: "[hoːlˈte.ʃe.zu · ˈen.mai veˈa.mi]",
    41: "[kad ret veˈra.ka]",
}

# --------------------------------------------------------------------------
# docs/04 — "const LINES" syllable/stress arrays, verbatim

SYL = {
    1: ["ver", "/", "i", "SHOL"],
    2: ["ver", "/", "ish", "MAI", "ol"],
    3: ["O:", "/", "MA:N"],
    4: ["kad", "/", "I", "shen", "/", "TA", "nu"],
    5: ["ZU", "ka", "deth", "/", "lesh", "/", "I", "shen", "/", "TA", "nu"],
    6: ["HO:", "lu", "/", "ret"],
    7: ["en", "/", "je", "DA", "mi"],
    8: ["ME", "nu", "/", "MA:N"],
    9: ["nuv", "/", "JE", "du"],
    10: ["HAU", "/", "JE", "du"],
    11: ["jel", "/", "I", "du"],
    12: ["SO:RN", "mai", "/", "TA", "nu"],
    13: ["kad", "/", "ve", "RA", "ka", "/", "vu"],
    14: ["ve", "RA", "ka"],
    15: ["vo", "/", "ve", "RA", "ka", "/", "ZU", "kad"],
    16: ["tem", "/", "TA", "nu", "/", "E", "ni", "/", "om"],
    17: ["JEL", "vos"],
    18: ["VE", "losh", "/", "I", "shen", "/", "O", "shu"],
    19: ["VO", "tem"],
    20: ["kru", "/", "JE", "leth"],
    21: ["an", "/", "vo", "/", "HO:", "lu"],
    22: ["gal", "/", "I", "shen", "/", "TA", "nu"],
    23: ["VU", "re", "len", "/", "chel"],
    24: ["en", "/", "ve", "RA", "mi"],
    25: ["TUR", "mai", "/", "E", "nen", "/", "TA", "nu"],
    26: ["kad", "/", "O", "mol", "/", "VE", "ru"],
    27: ["jel", "/", "LE", "sheth", "/", "I", "du"],
    28: ["EN", "mai", "/", "NE", "ksath", "mai", "/", "ta", "NA", "mi"],
    29: ["an", "/", "zu", "/", "jed", "TA", "mi"],
    30: ["ho:", "LE", "she", "zu", "/", "MAI", "el"],
    31: ["ver", "/", "en", "MAI", "eth", "/", "ve", "A", "ka"],
    32: ["E", "she", "ver", "/", "me", "NA", "zu"],
    33: ["SO:RN", "mai", "/", "A:N", "/", "TA", "nu"],
    34: ["A:N", "/", "ta", "NA", "mi"],
    35: ["nuv", "/", "nuv", "/", "JE", "lol"],
    36: ["NUV", "ran", "/", "ve", "A", "mi"],
    37: ["jel", "/", "i", "DE", "she", "mi"],
    38: ["ne", "|"],
    39: ["ho:l", "TE", "she", "zu", "/", "vu"],
    40: ["ho:l", "TE", "she", "zu", "/", "EN", "mai", "/", "ve", "A", "mi"],
    41: ["kad", "/", "ret", "/", "ve", "RA", "ka"],
}

NUMBERS = list(range(1, 42))


# --------------------------------------------------------------------------
# the four locks


@pytest.mark.parametrize("n", NUMBERS)
def test_romanized_line_matches_codex(n):
    assert line(n).sentence.text() == LAT[n]


@pytest.mark.parametrize("n", NUMBERS)
def test_gloss_matches_codex(n):
    assert line(n).sentence.gloss_line() == GLOSS[n]


@pytest.mark.parametrize("n", NUMBERS)
def test_ipa_matches_codex(n):
    assert line(n).sentence.ipa() == IPA[n].strip("[]")


@pytest.mark.parametrize("n", NUMBERS)
def test_ipa_data_is_codex_verbatim(n):
    assert line(n).ipa == IPA[n]


@pytest.mark.parametrize("n", NUMBERS)
def test_rhythm_array_matches_docs04(n):
    assert line(n).sentence.syl_line() == SYL[n]


# --------------------------------------------------------------------------
# inventory and structure


def test_all_41_lines_in_order():
    assert [ln.number for ln in LINES] == NUMBERS


def test_sections():
    expected = dict.fromkeys(range(1, 9), "A")
    expected.update(dict.fromkeys(range(9, 17), "B"))
    expected.update(dict.fromkeys(range(17, 25), "C"))
    expected.update(dict.fromkeys(range(25, 33), "D"))
    expected.update(dict.fromkeys(range(33, 42), "E"))
    for ln in LINES:
        assert ln.section == expected[ln.number]
        assert ln.section in SECTIONS


def test_section_titles():
    assert SECTIONS == {
        "A": "HAILS & PARTINGS",
        "B": "BRIDGE CHATTER",
        "C": "CURSES & OATHS",
        "D": "PRAYERS & BLESSINGS",
        "E": "THE DRIVE-LITANY",
    }


def test_line_38_is_the_gap():
    ln = line(38)
    assert ln.sentence.gap_final
    assert ln.sentence.syl_line()[-1] == "|"
    assert ln.sentence.gloss_line() == "GAP"


def test_every_stem_is_lexicon_backed():
    """docs/02: 'every one composed from the grammar' — and every stem
    from the master lexicon (docs/01 §06 + the §F appendix)."""
    for ln in LINES:
        for w in ln.sentence.words:
            for m in w.morphs:
                if m.cat in (STEM, STEM2):
                    assert lexicon_has(m.form), (ln.number, m.form)


def test_translations_and_notes_present():
    for ln in LINES:
        assert ln.translation
        assert ln.note
        # abridged: at most ~2 sentences
        assert ln.note.count(". ") <= 2


def test_ish_ol_is_the_documented_exception():
    """docs/02 §01 / docs/04 line 01: [iˈʃol], lexicalized greeting
    prosody — carried as a stress override, not an algorithm change."""
    w = line(1).sentence.words[1]
    assert w.stress_override == 1
    assert w.ipa() == "iˈʃol"


def test_entangled_case_stress_is_automatic():
    """ishmai-ol [iʃˈmai.ol] and enmai-eth [enˈmai.eth] need no override
    (docs/02 §02, §31): the -mai-under-case shift is core behaviour."""
    for n, idx in ((2, 1), (31, 1)):
        w = line(n).sentence.words[idx]
        assert w.stress_override is None
