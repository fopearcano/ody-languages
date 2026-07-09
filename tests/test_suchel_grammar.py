"""The Sūchel grammar engine against the codex's own example sentences.

Locks: the §04–05 examples of docs/01 (verb template, the four systems),
the three Κ5 conjugations, the docs/02 intro paradigms (imperative,
vocative, question, accusative), and the 'grammar of the culture'
contrasts (kel-en vs nav-mai; eni vs enmai) — all built generatively.
"""

import pytest

from odylang.suchel_grammar import (ANCHORS, CASES, MOODS, MOTION_STEMS,
                                    Break, MotionSatelliteError, Sentence,
                                    Word, bare_anchor, compound, directional,
                                    false_verb, imperative, lexicon_has,
                                    motion_verb, noun, particle, prohibitive,
                                    pronoun, verb, vocative)


# --------------------------------------------------------------------------
# docs/01 §04 — the verb template


def test_verb_template_the_confession():
    """an sū-t-eshe=zu — '3SG cross-PFV-T•=DARK' (docs/01 §04)."""
    s = Sentence([pronoun(3), verb("sū", "Ts", "zu", pfv=True, gloss="cross")],
                 punct="")
    assert s.text() == "an sū-t-eshe=zu"
    assert s.gloss_line() == "3SG cross-PFV-T•=DARK"


def test_verb_display_and_parts():
    w = verb("sū", "Ts", "zu", pfv=True, gloss="cross")
    assert w.display() == "sū-t-eshe=zu"
    assert w.solid() == "sūteshezu"
    assert [m.form for m in w.morphs] == ["sū", "t", "eshe", "zu"]


def test_imperfective_is_unmarked():
    assert verb("hōl", "Ts", "zu", gloss="surface").display() == "hōl-eshe=zu"


# --------------------------------------------------------------------------
# docs/01 §05 System 01 — the five veridical moods


def test_mood_suffixes():
    assert MOODS == {"T": ("a", "T"), "T-": ("im", "T⁻"),
                     "T+": ("ur", "T⁺"), "Ts": ("eshe", "T•")}


def test_unicode_mood_aliases():
    assert verb("tel", "T⁻", "zu", gloss="reach").display() == "tel-im=zu"
    assert verb("dur", "T⁺", "zu", gloss="endure").display() == "dur-ur=zu"
    assert verb("dur", "T•", "zu", gloss="endure").display() == "dur-eshe=zu"


def test_plain_T_the_safest_sentence():
    """kad ver-a=ka — 'The beacon holds true' (docs/01 §05 System 01)."""
    s = Sentence([Word.plain("kad", "beacon"),
                  verb("ver", "T", "ka", gloss="speak.true")], punct="")
    assert s.text() == "kad ver-a=ka"
    assert s.gloss_line() == "beacon speak.true-T=BEAC"


def test_mood_F_is_periphrastic():
    """docs/01 §05: F = vo + -a (negated plain) — never a suffix."""
    with pytest.raises(ValueError):
        verb("dur", "F", "ka", gloss="endure")
    vo, w = false_verb("dur", "ka", gloss="endure")
    assert vo.display() == "vo" and vo.gloss() == "NEG"
    assert w.display() == "dur-a=ka"


def test_mood_is_obligatory():
    with pytest.raises(ValueError):
        verb("ver", "??", "ka", gloss="speak.true")


# --------------------------------------------------------------------------
# docs/01 §05 System 02 — the three anchors


def test_anchor_glosses():
    assert ANCHORS == {"ka": "BEAC", "mi": "PROP", "zu": "DARK"}


def test_deep_run_log_formula():
    """enmai hōl-t-a=mi, vo =ka — with the stranded anchor (docs/01 §05)."""
    s = Sentence([pronoun(1, entangled=True),
                  verb("hōl", "T", "mi", pfv=True, gloss="surface"),
                  particle("vo"), bare_anchor("ka")],
                 punct="", breaks=[Break(1, ",", gloss=",")])
    assert s.text() == "enmai hōl-t-a=mi, vo =ka"
    assert s.gloss_line() == "1PL.ENT surface-PFV-T=PROP, NEG =BEAC"


def test_bare_anchor_word():
    w = bare_anchor("ka")
    assert w.display() == "=ka"
    assert w.gloss() == "=BEAC"


# --------------------------------------------------------------------------
# docs/01 §05 System 03 — depth directionals


def test_ship_runs_deeper():
    """nav nuv ran-eshe=mi (docs/01 §05 System 03)."""
    d, v = motion_verb("ran", "nuv", "Ts", "mi", gloss="run")
    s = Sentence([Word.plain("nav", "ship"), d, v], punct="")
    assert s.text() == "nav nuv ran-eshe=mi"
    assert s.gloss_line() == "ship DOWN run-T•=PROP"


def test_motion_verbs_demand_a_satellite():
    """'Go' bare is baby-talk (docs/01 System 03)."""
    for stem in sorted(MOTION_STEMS):
        with pytest.raises(MotionSatelliteError):
            verb(stem, "T", "mi", gloss="go")
    # the documented bare idiom must opt in explicitly (docs/02 §07)
    assert verb("jed", "T", "mi", gloss="go",
                bare_motion_ok=True).display() == "jed-a=mi"
    # zu 'adrift' patterns with the directionals in the death formula
    # (docs/02 §29)
    assert verb("jed", "T", "mi", pfv=True, gloss="go",
                directional="zu").display() == "jed-t-a=mi"


def test_directional_words():
    assert directional("nuv").gloss() == "DOWN"
    assert directional("hau").gloss() == "UP"
    assert directional("zu").gloss() == "adrift"


# --------------------------------------------------------------------------
# docs/01 §05 System 04 — the gap in syntax


def test_gap_narration():
    """en jel-eth tel-t-eshe=ka. ne. en hōl-t-eshe=zu. (docs/01 §05)."""
    s1 = Sentence([pronoun(1), noun("jel", case="LOC", gloss="seam"),
                   verb("tel", "Ts", "ka", pfv=True, gloss="reach")])
    s2 = Sentence([particle("ne")])
    s3 = Sentence([pronoun(1),
                   verb("hōl", "Ts", "zu", pfv=True, gloss="surface")])
    assert [s.text() for s in (s1, s2, s3)] == [
        "en jel-eth tel-t-eshe=ka.", "ne.", "en hōl-t-eshe=zu."]
    assert [s.gloss_line() for s in (s1, s2, s3)] == [
        "1SG seam-LOC reach-PFV-T•=BEAC", "GAP", "1SG surface-PFV-T•=DARK"]


# --------------------------------------------------------------------------
# docs/01 §05 — the Κ5 showpiece, three conjugations of one sentence


def _k5_frame(verb_words):
    return Sentence([Word.plain("tem", "pattern"),
                     noun("kav", case="LOC", gloss="limit"), *verb_words])


def test_k5_absolute_verdict():
    s = _k5_frame(false_verb("dur", "ka", gloss="endure"))
    assert s.text() == "tem kav-eth vo dur-a=ka."
    assert s.gloss_line() == "pattern limit-LOC NEG endure-T=BEAC"


def test_k5_madmans_theorem():
    s = _k5_frame([verb("dur", "T+", "zu", gloss="endure")])
    assert s.text() == "tem kav-eth dur-ur=zu."
    assert s.gloss_line() == "pattern limit-LOC endure-T⁺=DARK"


def test_k5_tragic_truth():
    s = _k5_frame([verb("dur", "Ts", "zu", gloss="endure")])
    assert s.text() == "tem kav-eth dur-eshe=zu."
    assert s.gloss_line() == "pattern limit-LOC endure-T•=DARK"


# --------------------------------------------------------------------------
# docs/02 intro — imperative, vocative, question, accusative


def test_imperative_and_prohibitive():
    """jed-u! 'go!' · vo jed-u! 'don't go!' — cited bare in the intro."""
    w = imperative("jed", "go", bare_motion_ok=True)
    assert w.display() == "jed-u"
    assert w.gloss() == "go-IMP"
    assert w.is_beatless()  # commands stay flat (docs/04 rule 4 corollary)
    vo, w2 = prohibitive("jed", "go", bare_motion_ok=True)
    assert (vo.display(), w2.display()) == ("vo", "jed-u")


def test_imperative_has_no_mood_or_anchor():
    from odylang.word import ANCHOR, MOOD
    w = imperative("tan", "hold")
    assert not any(m.cat in (MOOD, ANCHOR) for m in w.morphs)


def test_vocative():
    o, m = vocative(Word.plain("mān", "crew.hand"))
    assert (o.display(), o.gloss()) == ("ō", "VOC")
    assert Sentence([o, m], punct="!").text() == "ō mān!"
    # with entangled kin, the suffix does the warmth: ō Sōrnmai
    o2, s2 = vocative(noun("Sōrn", entangled=True, mai_sep="", gloss="drive"))
    assert s2.display() == "Sōrnmai"
    assert s2.gloss() == "drive.ENT"


def test_question_particle():
    """…ver-a=ka vu? — polar only (docs/02 intro)."""
    s = Sentence([verb("ver", "T", "ka", gloss="true"), particle("vu")],
                 punct="?")
    assert s.text() == "ver-a=ka vu?"
    assert s.gloss_line() == "true-T=BEAC Q"


def test_accusative_allomorphy():
    """en → enen; ish → ishen (docs/02 intro), written solid."""
    assert pronoun(1, case="ACC").display() == "enen"
    assert pronoun(1, case="ACC").gloss() == "1SG.ACC"
    assert pronoun(2, case="ACC").display() == "ishen"
    assert pronoun(2, case="ACC").gloss() == "2SG.ACC"
    # -n after a vowel
    assert noun("sū", case="ACC", gloss="cross").display() == "sūn"


def test_denominal_imperative_written_solid():
    """osh 'mouth' → oshu! 'swallow (it)!' (docs/02 intro, §18)."""
    w = imperative("osh", "swallow", solid=True)
    assert w.display() == "oshu"
    assert w.gloss() == "swallow-IMP"


# --------------------------------------------------------------------------
# docs/01 §04 — nouns: number, case, entangled possession


def test_plural():
    assert noun("sīl", plural=True, gloss="crosser").display() == "sīli"
    assert noun("sīl", plural=True, gloss="crosser").gloss() == "crosser.PL"


def test_case_suffixes():
    assert CASES["GEN"][:2] == ("en", "GEN")
    assert noun("jel", case="GEN", gloss="seam").display() == "jel-en"
    assert noun("jel", case="DAT", gloss="seam").display() == "jel-ol"
    assert noun("jel", case="LOC", gloss="seam").display() == "jel-eth"
    assert noun("jel", case="LOC", gloss="seam").gloss() == "seam-LOC"


def test_grammar_of_the_culture_possession():
    """kel-en 'my words' but nav-mai 'my-entangled ship' (docs/01 §04):
    -en of your own ship announces you plan to sell her."""
    words = noun("kel", case="GEN", gloss="speech")
    ship = noun("nav", entangled=True, gloss="ship")
    assert words.display() == "kel-en"
    assert words.gloss() == "speech-GEN"
    assert ship.display() == "nav-mai"
    assert ship.gloss() == "ship-ENT"


def test_grammar_of_the_culture_we():
    """enmai (crew-we) vs eni (the mere plural) — docs/01 §04: a captain
    who says eni of her own crew is understood to be resigning."""
    crew_we = pronoun(1, entangled=True)
    mere_we = pronoun(1, plural=True)
    assert crew_we.display() == "enmai"
    assert crew_we.gloss() == "1PL.ENT"
    assert mere_we.display() == "eni"
    assert mere_we.gloss() == "1PL"


def test_entangled_spelling_is_lexical_data():
    """Solid ishmai (docs/02 §02) vs hyphenated ish-mai (docs/01 §07):
    the gloss follows the spelling."""
    assert pronoun(2, entangled=True).display() == "ishmai"
    assert pronoun(2, entangled=True).gloss() == "2SG.ENT"
    assert pronoun(2, entangled=True, mai_sep="-").display() == "ish-mai"
    assert pronoun(2, entangled=True, mai_sep="-").gloss() == "2SG-ENT"


# --------------------------------------------------------------------------
# stress: the grammar output feeds the four-rule algorithm (docs/04 §02)


def test_rule2_the_mood_carries_the_beat():
    assert verb("ver", "T", "ka", gloss="true").syl_beats() == ["ve", "RA", "ka"]
    assert verb("tan", "T", "mi", gloss="hold").syl_beats() == ["ta", "NA", "mi"]
    assert verb("hōl", "Ts", "zu", pfv=True, gloss="surface").syl_beats() == \
        ["ho:l", "TE", "she", "zu"]
    assert verb("id", "Ts", "mi", gloss="open").syl_beats() == \
        ["i", "DE", "she", "mi"]


def test_rule4_corollary_imperatives_are_beatless():
    for stem, beats in (("tan", ["TA", "nu"]), ("id", ["I", "du"])):
        w = imperative(stem, "x")
        assert w.is_beatless()
        assert w.syl_beats() == beats


def test_rule1_compound_seam_syllabification():
    """nuv+ran is [ˈnuv.ran] (docs/02 §36): the seam blocks the *vr*
    onset cluster, though a lone consonant still crosses it (ve.losh)."""
    assert compound("nuv", "ran", gloss="running.under").ipa() == "ˈnuv.ran"
    assert compound("vel", "osh", gloss="Formless.mouth").ipa() == "ˈve.loʃ"
    assert compound("zu", "kad", gloss="dark.time").syl_beats() == ["ZU", "kad"]


def test_entangled_pronoun_case_stress():
    assert pronoun(2, entangled=True, case="DAT").ipa() == "iʃˈmai.ol"
    assert pronoun(1, entangled=True, case="LOC").ipa() == "enˈmai.eth"
    assert pronoun(1, entangled=True).ipa() == "ˈen.mai"


# --------------------------------------------------------------------------
# housekeeping


def test_lexicon_has_handles_affix_and_case_variants():
    assert lexicon_has("Tur")      # LEXICON keys 'tur'
    assert lexicon_has("eshe")     # LEXICON keys '-eshe'
    assert lexicon_has("mai")      # LEXICON keys '-mai'
    assert lexicon_has("Sōrn")
    assert not lexicon_has("xyzzy")


def test_sentence_syl_line_and_gap():
    s = Sentence([particle("ne")], gap_final=True)
    assert s.syl_line() == ["ne", "|"]
    s2 = Sentence([Word.plain("kad", "beacon"),
                   verb("ver", "T", "ka", gloss="true")])
    assert s2.syl_line() == ["kad", "/", "ve", "RA", "ka"]
