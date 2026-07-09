"""The three §06 texts, verbatim, with their words replaying the lines."""

import pytest

from odylang import nubhel_texts as T
from odylang.nubhel_texts import (PARALLEL_CONTRASTS, TEXT_01, TEXT_02,
                                  TEXT_03, TEXTS, strip_punct)


def test_three_texts():
    assert [t.id for t in TEXTS] == ["TEXT 01", "TEXT 02", "TEXT 03"]
    assert [t.title for t in TEXTS] == [
        "A DIVER'S HOMECOMING",
        "THE PARALLEL SENTENCE — HALF-UNDERSTANDING",
        "THE CODE-SWITCH — SHOWPIECE"]
    assert [t.jp for t in TEXTS] == ["帰還", "対訳", "切替"]


@pytest.mark.parametrize("text", TEXTS, ids=lambda t: t.id)
def test_words_replay_every_line(text):
    """The morph-built words reproduce each verbatim line exactly
    (punctuation aside)."""
    for line in text.lines:
        assert line.words_display() == strip_punct(line.display), line.display


# ---------------------------------------------------------------------------
# TEXT 01 — a diver's homecoming


def test_text_01_verbatim():
    l1, l2 = TEXT_01.lines
    assert l1.display == "en yed-t-ó=mi. neks."
    assert l1.gloss == "1SG go-PFV-PLAIN=PROP · GAP"
    assert l1.translation == "I left. — ."
    assert l2.display == "en len ve-ó=ka, +mek-dok kodur."
    assert l2.gloss == "1SG level be-PLAIN=BEAC · +four-ten cycle"
    assert l2.translation == ("I am here, level, in shared time — forty "
                              "cycles owed.")
    assert "ends in an invoice" in TEXT_01.commentary


def test_text_01_grammar():
    l1, l2 = TEXT_01.lines
    # the gap folded to one mark, the debt declared as a number
    assert l1.words[-1].display() == "neks"
    assert [w.display() for w in l2.words[-2:]] == ["+mek-dok", "kodur"]
    # the return is beacon-anchored, the departure proper-time
    assert l1.words[1].display().endswith("=mi")
    assert l2.words[2].display().endswith("=ka")


# ---------------------------------------------------------------------------
# TEXT 02 — the parallel sentence


def test_text_02_verbatim():
    su, nu = TEXT_02.lines
    assert su.language == "Sūchel"
    assert su.display == "enmai nav-mai nuv jed-a=mi."
    assert su.gloss == "SŪCHEL — 1PL.ENT ship-ENT DOWN go-T=PROP"
    assert su.translation == '"We take our ship down, by our own clock."'
    assert nu.language == "Nubhel"
    assert nu.display == "enmai nā-mai nub yed-ó=mi."
    assert nu.gloss == "NUBHEL — 1PL.ENT ship-ENT DOWN go-PLAIN=PROP"
    assert nu.translation == "The same sentence, the sister's mouth."
    assert "nav/nā, nuv/nub, jed/yed, -a/-ó" in TEXT_02.commentary


def test_text_02_suchel_line_is_core_word_built():
    su = TEXT_02.lines[0]
    verb = su.words[-1]
    assert verb.display() == "jed-a=mi"
    assert verb.gloss() == "go-T=PROP"
    assert su.words[0].ipa() == "ˈen.mai"     # shared bones, shared stress
    assert su.words[1].display() == "nav-mai"


def test_text_02_contrasts():
    assert PARALLEL_CONTRASTS == (
        ("nav", "nā"), ("nuv", "nub"), ("jed", "yed"), ("-a", "-ó"))
    # the shared bones really are shared
    su, nu = TEXT_02.lines
    assert su.words[0].display() == nu.words[0].display() == "enmai"


# ---------------------------------------------------------------------------
# TEXT 03 — the code-switch showpiece


def test_text_03_verbatim():
    l1, l2, l3 = TEXT_03.lines
    assert l1.display == "on dolnub yed-t-ó=mi, yel-ol —"
    assert l1.gloss == "3SG PITWARD go-PFV-PLAIN=PROP · seam-DAT"
    assert l1.translation == "She dove pitward, to the seam —"
    assert l2.display == "an sū-t-eshe=zu."
    assert l2.gloss == "[SŪCHEL] 3SG cross-PFV-T•=DARK"
    assert l2.translation == "— she crossed: seam-true, in the dark."
    assert l3.display == "on ōl-t-ó=nu, +so kodur."
    assert l3.gloss == "3SG surface-PFV-PLAIN=DEEP · +one cycle"
    assert l3.translation == "She surfaced, in dive-time — one cycle owed."
    assert "the language shift is the seam" in TEXT_03.commentary


def test_text_03_the_middle_balloon_is_suchel():
    l1, l2, l3 = TEXT_03.lines
    assert (l1.language, l2.language, l3.language) == (
        "Nubhel", "Sūchel", "Nubhel")
    # built via the grammar's code_switch helper, core Word morphs direct
    from odylang.nubhel_grammar import code_switch
    assert l2.words_display() == code_switch().display()
    assert l2.words[1].ipa() == "suːˈte.ʃe.zu"


def test_text_03_frame():
    l1, _, l3 = TEXT_03.lines
    # pitward in, one cycle owed out
    assert l1.words[1].display() == "dolnub"
    assert l1.words[-1].display() == "yel-ol"
    assert l1.words[-1].gloss() == "seam-DAT"
    assert [w.display() for w in l3.words] == [
        "on", "ōl-t-ó=nu", "+so", "kodur"]
