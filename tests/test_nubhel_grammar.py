"""Nubhel grammar (docs/06 §03): three moods and a hole, the debt
anchor and the offset signature, five depths, and neks as courtesy."""

import pytest

from odylang import nubhel_grammar as G
from odylang.nubhel import LEXICON
from odylang.word import ANCHOR


# ---------------------------------------------------------------------------
# SYSTEM 01 — three moods, and a hole


def test_verb_template_plain():
    w = G.verb("yed", "go", mood="plain", anchor="mi")
    assert w.display() == "yed-ó=mi"
    assert w.gloss() == "go-PLAIN=PROP"
    assert w.ipa() == "jeˈdo.mi"     # rule 2: the mood seizes the stress


def test_verb_template_pfv():
    w = G.verb("ōl", "surface", anchor="nu", pfv=True)
    assert w.display() == "ōl-t-ó=nu"
    assert w.gloss() == "surface-PFV-PLAIN=DEEP"


def test_three_moods():
    assert G.verb("ton", "hold", mood="plain").display() == "ton-ó=mi"
    assert G.verb("ton", "hold", mood="appr").display() == "ton-im=mi"
    assert G.verb("ton", "hold", mood="appr").gloss() == "hold-APPR=PROP"
    assert G.verb("ton", "hold", mood="hearsay").display() == "ton-ur=mi"
    assert G.verb("ton", "hold", mood="hearsay").gloss() == "hold-HEARSAY=PROP"
    # aliases from the family's ΛL notation
    assert G.verb("ton", "hold", mood="T⁻").display() == "ton-im=mi"
    assert G.verb("ton", "hold", mood="T⁺").display() == "ton-ur=mi"


def test_seam_truth_is_a_hole():
    """*-eshe left no reflex: Nubhel cannot conjugate the seam-truth."""
    for key in ("Ts", "T•", "eshe", "-eshe", "seam-true"):
        with pytest.raises(G.SeamTruthError):
            G.verb("yed", "go", mood=key)
    with pytest.raises(ValueError):
        G.verb("yed", "go", mood="nonsense")


def test_code_switch_builds_the_borrowed_clause():
    """The documented pattern: a Sūchel T• clause embedded mid-narration
    — the rival's mood, the rival's anchor, in the rival's color."""
    cs = G.code_switch()
    assert cs.language == "Sūchel"
    assert cs.display() == "an sū-t-eshe=zu"
    assert cs.gloss() == "[SŪCHEL] 3SG cross-PFV-T•=DARK"
    assert cs.words[1].ipa() == "suːˈte.ʃe.zu"


# ---------------------------------------------------------------------------
# SYSTEM 02 — the debt anchor & the signature


def test_anchors_deep_not_dark():
    assert G.verb("ber", "speak.true", anchor="ka").display() == "ber-ó=ka"
    assert G.verb("ber", "speak.true", anchor="mi").display() == "ber-ó=mi"
    assert G.verb("ber", "speak.true", anchor="nu").display() == "ber-ó=nu"
    with pytest.raises(G.DarkAnchorError):
        G.verb("ber", "speak.true", anchor="zu")
    with pytest.raises(G.DarkAnchorError):
        G.anchor_morph("=zu")
    with pytest.raises(ValueError):
        G.anchor_morph("xx")


def test_offset_numerals():
    assert G.offset(1) == "+so"
    assert G.offset(40) == "+mek-dok"
    assert G.offset(10) == "+dok"
    assert G.offset_gloss(40) == "+four-ten"
    assert G.offset_gloss(1) == "+one"
    with pytest.raises(ValueError):
        G.offset(212)   # beyond the counting row: digits instead


def test_offset_signature():
    assert G.signature("Mora", 212) == "Mora, +212"
    assert G.SIGNATURE_EXAMPLE == "Mora, +212"


def test_sign_deep_appends_the_debt():
    words = G.sign_deep(
        G.clause("en", "ōl", "surface", pfv=True, anchor="nu"), 40)
    assert [w.display() for w in words] == ["en", "ōl-t-ó=nu", "+mek-dok"]
    with_unit = G.sign_deep(
        G.clause("on", "ōl", "surface", pfv=True, anchor="nu"), 1,
        cycles=True)
    assert [w.display() for w in with_unit] == [
        "on", "ōl-t-ó=nu", "+so", "kodur"]
    assert with_unit[-1].ipa() == "ˈko.dur"


def test_sign_deep_requires_the_deep_anchor():
    with pytest.raises(G.DarkAnchorError):
        G.sign_deep(G.clause("en", "ōl", "surface", anchor="mi"), 40)


# ---------------------------------------------------------------------------
# SYSTEM 03 — five degrees of depth


def test_five_directionals():
    assert sorted(G.DIRECTIONALS) == sorted(
        ["len", "nub", "dolnub", "ū", "ūtel"])
    for form in G.DIRECTIONALS:
        assert form in LEXICON                 # each is a lexicon word
    assert G.DIRECTIONALS["ū"][0] == "*hau"    # up: one exhaled vowel


def test_motion_verbs_require_a_directional():
    with pytest.raises(G.MissingDirectionalError):
        G.clause("on", "yed", "go")
    with pytest.raises(G.MissingDirectionalError):
        G.clause("en", "ron", "run", anchor="ka")
    with pytest.raises(ValueError):
        G.clause("on", "yed", "go", directional="left")   # no such depth
    words = G.clause("on", "yed", "go", directional="nub")
    assert [w.display() for w in words] == ["on", "nub", "yed-ó=mi"]


def test_surface_verb_incorporates_its_direction():
    """ōl is exempt: *haw-ol- contains *hau 'up' (both attested ōl
    clauses in docs/06 are directional-less)."""
    assert "ōl" not in G.MOTION_VERBS
    G.clause("on", "ōl", "surface", pfv=True, anchor="nu")   # no raise


def test_bare_motion_needs_the_homecoming_licence():
    """TEXT 01's 'en yed-t-ó=mi. neks.' — the codex's own bare yed,
    licensed by the following gap; the builder demands the flag."""
    words = G.clause("en", "yed", "go", pfv=True, allow_bare=True)
    assert [w.display() for w in words] == ["en", "yed-t-ó=mi"]


# ---------------------------------------------------------------------------
# SYSTEM 04 — neks, and the assembled §03 examples


def test_neks_particle():
    w = G.neks()
    assert w.display() == "neks"
    assert w.gloss() == "GAP"
    assert "courtesy" in G.NEKS_PRAGMATICS or "did not share" in G.NEKS_PRAGMATICS


def test_pronoun_on():
    assert G.PRONOUNS["on"] == "3SG"
    assert G.pronoun("on").display() == "on"
    assert G.pronoun("enmai").ipa() == "ˈen.mai"


def test_template_unchanged():
    assert G.TEMPLATE == "STEM – (ASPECT) – MOOD = ANCHOR"


def _joined(words):
    return " ".join(w.display() for w in words)


def test_example_she_went_down():
    ex = G.EXAMPLES[0]
    assert ex.display == "on nub yed-ó=mi."
    assert ex.gloss == "3SG DOWN go-PLAIN=PROP"
    assert ex.translation == '"She went down."'
    words = G.clause("on", "yed", "go", directional="nub")
    assert _joined(words) + "." == ex.display
    assert " ".join(w.gloss() for w in words) == ex.gloss


def test_example_offset_signature_clause():
    ex = G.EXAMPLES[1]
    assert ex.display == "en ōl-t-ó=nu, +mek-dok."
    assert ex.gloss == "1SG surface-PFV-PLAIN=DEEP, +four-ten"
    words = G.sign_deep(
        G.clause("en", "ōl", "surface", pfv=True, anchor="nu"), 40)
    assert _joined(words) == "en ōl-t-ó=nu +mek-dok"
    assert ex.display.replace(",", "").rstrip(".") == _joined(words)


def test_example_homecoming_formula():
    ex = G.EXAMPLES[2]
    assert ex.display == "en yed-t-ó=mi. neks. en len ve-ó=ka."
    words = (G.clause("en", "yed", "go", pfv=True, allow_bare=True)
             + [G.neks()]
             + [G.pronoun("en"), G.directional_word("len", "level"),
                G.verb(G.COPULA, "be", anchor="ka")])
    assert _joined(words) == "en yed-t-ó=mi neks en len ve-ó=ka"


def test_verb_anchor_morphs_are_weightless():
    """Rule 2 stress sits on the mood, never the clitic."""
    w = G.verb("ōl", "surface", pfv=True, anchor="nu")
    anchors = [m for m in w.morphs if m.cat == ANCHOR]
    assert [m.form for m in anchors] == ["nu"]
    assert w.syl_beats()[-1] == "nu"      # unstressed, lower-case beat
