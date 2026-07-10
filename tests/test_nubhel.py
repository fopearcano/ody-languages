"""Nubhel D-1..7 (docs/06 §02), the §05 lexicon, and the §04 table.

The codex's ordering claim is tested both ways: D-3 before D-1 gives
Nubhel (the secondary h survives); the misordered counterfactual eats
it (†nūbel).  Every proto-sourced lexicon entry is locked to its
surface form and to exactly the changes the codex cites; the
false-friends table is checked against BOTH derivers.
"""

import pytest

from odylang.nubhel import FALSE_FRIENDS, LEXICON, NUBHEL, entries
from odylang.soundchange import Deriver
from odylang.suchel import LEXICON as SUCHEL_LEXICON
from odylang.suchel import SUCHEL, compose
from odylang.word import MAI, STEM, Morph, Word


# ---------------------------------------------------------------------------
# §02 — the seven changes


def test_canon_derivations_of_the_codex():
    """Every §02 example, straight from the table."""
    cases = {
        "*kel": "hel",          # D-1
        "*gel": "yel",          # D-1
        "*ged": "yed",          # D-1
        "*wer": "ber",          # D-2
        "*wur": "bur",          # D-2
        "*haw-ol": "ōl",        # D-3
        "*suw-kel": "sūhel",    # D-3, D-1
        "*kad": "kod",          # D-4
        "*tan": "ton",          # D-4
        "*ran": "ron",          # D-4
        "*nub-i": "nūbi",       # D-5
        "*hau": "ū",            # D-3, D-6 — a single exhaled vowel
        "*hau-tel": "ūtel",     # D-3, D-6
        "*tem-a": "tem",        # D-7
        "*nub-kel": "nubhel",   # D-3 ordered before D-1
    }
    for proto, expect in cases.items():
        d = NUBHEL.derive(proto)
        assert d.form == expect, d.trace()


def test_change_order_is_d3_first():
    """docs/06 §02: 'Note D-3 is ordered before D-1.'"""
    ids = [c.id for c in NUBHEL.changes]
    assert ids == ["D-3", "D-1", "D-2", "D-4", "D-5", "D-6", "D-7"]


def test_ordering_visible_in_the_trace():
    """*suw-kel fires both rules, D-3 strictly before D-1."""
    d = NUBHEL.derive("*suw-kel")
    assert d.fired == ["D-3", "D-1"], d.trace()
    assert [ (s.before, s.after) for s in d.steps ] == [
        ("suwkel", "sūkel"), ("sūkel", "sūhel")]


def test_misordered_counterfactual_eats_the_secondary_h():
    """'original *h dies first, then new h is born from *k — so every
    medial h in Nubhel is secondary': run D-1 before D-3 and breath-loss
    devours the newborn h (with compensatory lengthening, †nūbel)."""
    swapped = [NUBHEL.changes[1], NUBHEL.changes[0]] + list(NUBHEL.changes[2:])
    mis = Deriver("misordered", swapped, list(NUBHEL.repairs))
    assert mis.derive("*nub-kel").form == "nūbel"
    # the real order keeps the diagnostic medial h
    assert NUBHEL.derive("*nub-kel").form == "nubhel"
    assert NUBHEL.derive("*nub-kel").fired == ["D-1"]  # D-3 fires vacuously


def test_minimal_pair_of_the_rivalry():
    """*suw-kel: Sūchel in one mouth, Sūhel in the other — and *sow-orn
    is Sōrn in both: everyone agrees on the engine (docs/06 §02)."""
    assert SUCHEL.derive("*suw-kel").form == "sūchel"
    assert NUBHEL.derive("*suw-kel").form == "sūhel"
    assert SUCHEL.derive("*sow-orn").form == "sōrn"
    assert NUBHEL.derive("*sow-orn").form == "sōrn"


def test_breath_loss_details():
    """D-3: all *h dies (even initial: hōl vs ōl, hep vs ep); coalescence
    follows the u > o > a hierarchy; post-consonantal h lengthens."""
    assert NUBHEL.derive("*hep").form == "ep"
    assert NUBHEL.derive("*suw-il").form == "sūl"    # u beats i
    assert NUBHEL.derive("*haw-ol").form == "ōl"     # o beats a
    assert NUBHEL.derive("*anh").form == "ān"        # SC-4 pattern
    assert NUBHEL.derive("*nāw").form == "nā"


def test_pressure_rounding_is_initial_stress_only():
    """D-4 rounds the stressed (first-syllable) short a; D-3's fresh
    length protects ā (ān, nā not †ōn, †nō)."""
    for proto, expect in [("*an", "on"), ("*sa", "so"), ("*dak", "dok"),
                          ("*mar", "mor"), ("*mor", "mor")]:
        assert NUBHEL.derive(proto).form == expect
    assert NUBHEL.derive("*anh").form == "ān"


def test_held_breath_drift_scope():
    """D-5 lengthens the high vowel of an open stressed non-final
    syllable — and only there: so, hel, yed untouched, tem stays short
    (see module docstring in odylang.nubhel for the reading)."""
    assert NUBHEL.derive("*nub-i").form == "nūbi"
    assert NUBHEL.derive("*nub-i").fired == ["D-5"]
    for proto, expect in [("*sa", "so"), ("*kel", "hel"), ("*ged", "yed"),
                          ("*tem-a", "tem"), ("*nub", "nub"),
                          ("*dol-nub", "dolnub")]:
        assert NUBHEL.derive(proto).form == expect


def test_apocope_blocked_after_long_vowel():
    """D-7 clips *tem-a but never creates superheavy CVːC: Nūbi keeps
    its -i after the drift."""
    assert NUBHEL.derive("*tem-a").fired == ["D-7"]
    assert NUBHEL.derive("*nub-i").form == "nūbi"


def test_neks_cluster_kept_and_spelled_ks():
    d = NUBHEL.derive("*nex")
    assert d.form == "neks"


# ---------------------------------------------------------------------------
# §05 — the working lexicon


PROTO_ENTRIES = [e for e in entries() if e.proto is not None]


@pytest.mark.parametrize("entry", PROTO_ENTRIES, ids=lambda e: e.form)
def test_derivation_surface(entry):
    d = entry.derive()
    expected = entry.form.lstrip("-").rstrip("-").lower()
    assert d.form == expected, d.trace()


@pytest.mark.parametrize("entry", PROTO_ENTRIES, ids=lambda e: e.form)
def test_derivation_cited_changes(entry):
    d = entry.derive()
    fired = {c for c in d.fired if c != "REP"}
    assert fired == set(entry.cited), (
        f"{entry.form}: fired {sorted(fired)}, codex cites "
        f"{sorted(entry.cited)}\n" + d.trace())


def test_lexicon_has_the_codex_inventory():
    # the §05 rows (so … dok split into its two numerals) plus the
    # shared items the §03 examples, §04 table and texts lean on
    for form in ["Nubhel", "Nūbi", "Sūl", "Sūhel", "hel", "yel", "yed",
                 "kod", "kodur", "ber", "bur", "bos", "bel", "mor", "ton",
                 "ron", "ōl", "ū", "ūtel", "len", "nub", "dolnub", "neks",
                 "tem", "ān", "nā", "nāmai", "enmai", "on", "so", "dok",
                 "en", "mek", "ep", "-mai", "-ur", "ve"]:
        assert form in LEXICON, form


def _lex_word(form: str) -> Word:
    """Word object for an entry, morph-structured where stress needs it
    (the -mai formations stress their first member: ˈen.mai, ˈnaː.mai)."""
    if form in ("enmai", "nāmai"):
        stem = form[:-3]
        return Word([Morph(stem, "", STEM), Morph("mai", "", MAI)])
    return Word.plain(form.lstrip("-"))


@pytest.mark.parametrize(
    "entry", [e for e in entries() if e.ipa], ids=lambda e: e.form)
def test_codex_ipa(entry):
    assert _lex_word(entry.form).ipa() == entry.ipa


def test_daughter_formations_compose():
    assert compose("kod", "-ur") == "kodur"
    assert compose("nā", "-mai") == "nāmai"
    assert compose("en", "-mai") == "enmai"
    assert compose("ū", "tel") == "ūtel"
    for e in entries():
        if e.kind == "daughter" and e.members:
            assert compose(*e.members).lower() == e.form.lower(), e.form


def test_mai_is_shared_not_rederived():
    """docs/06 §05: -mai '(*mag-i, shared)', 'kin-words are
    family-stable' — the entry is register data, not an engine run
    (D-4 would have wrecked it)."""
    e = LEXICON["-mai"]
    assert e.proto is None and e.kind == "register"
    assert "*mag-i" in e.etym


def test_copula_ve_is_flagged_data():
    """TEXT 01 attests ve against D-2's expected †be — carried as a
    register entry with the codex's evidence, never silently."""
    e = LEXICON["ve"]
    assert e.proto is None and e.kind == "register"
    assert "†be" in e.etym
    # and the regular machine really would say be:
    assert NUBHEL.derive("*we").form == "be"


# ---------------------------------------------------------------------------
# §04 — across the cognate gap, checked in BOTH mouths


@pytest.mark.parametrize("row", FALSE_FRIENDS, ids=lambda r: r.proto)
def test_false_friends_both_ways(row):
    for proto, expected in row.suchel_checks:
        d = SUCHEL.derive(proto)
        assert d.form == expected, f"Sūchel {proto}: " + d.trace()
    for proto, expected in row.nubhel_checks:
        d = NUBHEL.derive(proto)
        assert d.form == expected, f"Nubhel {proto}: " + d.trace()
    for key, expected in row.suchel_lexicon:
        # codex-flagged irregular on the Sūchel side: adjustment applies
        assert SUCHEL_LEXICON[key].derive().form == expected
        assert row.skip_note
    for key, expected in row.suchel_compose:
        assert compose(*SUCHEL_LEXICON[key].members) == expected
        assert row.skip_note


def test_false_friends_covers_the_codex_rows():
    assert [r.proto for r in FALSE_FRIENDS] == [
        "*gel-", "*kel", "*suw-kel", "*sow-orn", "*kad", "*wer-", "*nub-",
        "*ged-", "*tan-", "*mar / *mor", "*wel / *bel", "*nex-",
        "*sa, *dak", "*hep", "*suw-il / *nub-i"]


def test_the_two_mergers_two_jokes():
    """D-2 merges *wel with *bel; D-4 merges *mar into *mor (docs/06)."""
    assert NUBHEL.derive("*wel").form == NUBHEL.derive("*bel").form == "bel"
    assert NUBHEL.derive("*mar").form == NUBHEL.derive("*mor").form == "mor"


def test_two_fleets_data():
    """docs/06 §01: the rivalry's cultural data is carried, both sneers
    verbatim."""
    from odylang.nubhel import TWO_FLEETS
    assert set(TWO_FLEETS) == {"sili", "nubi"}
    assert TWO_FLEETS["sili"]["sneer"] == \
        '"divers go fast to stay in one universe"'
    assert TWO_FLEETS["nubi"]["sneer"] == \
        '"crossing is a shortcut; depth is the truth"'
    assert "the aged" in TWO_FLEETS["sili"]["calls_the_others"]
    assert "the gapped" in TWO_FLEETS["nubi"]["calls_the_others"]
