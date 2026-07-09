"""Lorkel, the Wolori's working Old Pelagic (docs/05 §05): coinage with
no sound changes, the eight Neo-Pelagic terms with their Sūchel-reflex
column, the three custodians, and the notation-names.
"""

import pytest

from odylang import lorkel
from odylang.lorkel import (CUSTODIANS, ENDONYM, NEO_PELAGIC, NOTATION_NAMES,
                            OPEN_PROPOSAL, coin)
from odylang.proto import citation
from odylang.suchel import LEXICON, SUCHEL

TERMS = list(NEO_PELAGIC.values())


# ---------------------------------------------------------------------------
# coinage: proto morphology, no sound changes


def test_coin_is_citation_compounding():
    assert coin("*kap-", "*lor-") == "kaplor"
    assert coin("*suw-", "*-ath") == "suwath"
    assert coin("*gel-") == "gel"
    # no daughter changes ever apply: *w and *h survive
    assert coin("*wer-", "*stan") == "werstan"


@pytest.mark.parametrize("term", TERMS, ids=lambda t: t.form)
def test_neo_pelagic_coinage(term):
    """Each of the eight standard terms is its own formation, coined."""
    assert term.coined() == term.form


def test_eight_standard_terms():
    assert len(NEO_PELAGIC) == 8
    assert list(NEO_PELAGIC) == ["gel", "kaplor", "pewlor", "gelwer",
                                 "turom", "nexlor", "suwath", "wolor"]


# ---------------------------------------------------------------------------
# the Sūchel-reflex column


def test_gel_reflex_is_engine_derivable():
    """The one true cognate row: Lorkel gel is unshifted *gel-, whose
    regular Sūchel outcome is jel."""
    t = NEO_PELAGIC["gel"]
    assert t.reflex_kind == "cognate"
    assert SUCHEL.derive(t.formation[0]).form == t.suchel_reflex == "jel"


@pytest.mark.parametrize("term", [t for t in TERMS if t.reflex_kind == "formation"],
                         ids=lambda t: t.form)
def test_formation_reflexes_exist_in_suchel(term):
    """Where the codex's comparison column is a different formation
    (kaplor~kav, pewlor~pevlor, gelwer~eshe-ver, turom~Turmai, nexlor~ne,
    suwath~sūath), the reflex must exist in the Sūchel lexicon; the
    relationship is data, not derivation."""
    assert term.suchel_reflex in LEXICON, term.suchel_reflex


def test_pewlor_reflex_is_the_daughter_compound():
    """pevlor is 'its regular reflex' in the sense that the fleets
    compound the daughter forms pev + lor (docs/01: pevlor is a daughter
    formation, not a *pew-lor derivation)."""
    assert LEXICON["pevlor"].kind == "daughter"
    assert LEXICON["pevlor"].members == ("pev", "lor")


def test_wolor_has_no_reflex():
    t = NEO_PELAGIC["wolor"]
    assert t.reflex_kind == "none"
    assert t.suchel_reflex is None
    assert "wolor" not in LEXICON


# ---------------------------------------------------------------------------
# custodians & notation


def test_two_custodians_and_the_zero_tongue():
    assert set(CUSTODIANS) == {"assembly", "wolori", "notation"}
    assert CUSTODIANS["assembly"].number == "01"
    assert CUSTODIANS["wolori"].number == "02"
    assert CUSTODIANS["notation"].number == "00"
    assert "frozen" in CUSTODIANS["assembly"].mode
    assert "living" in CUSTODIANS["wolori"].mode
    assert CUSTODIANS["notation"].mode == "no moods, no anchors, no native speakers"
    assert CUSTODIANS["wolori"].register.startswith("Lorkel")


def test_notation_names_as_documented():
    """√2, π, φ, √−1, z — written identically on every world."""
    assert NOTATION_NAMES == ("√2", "π", "φ", "√−1", "z")


def test_lorkel_names_itself():
    """*lor-kel 'ratio-speech' — a coinage like any other."""
    assert coin("*lor-", "*kel") == "lorkel"


# ---------------------------------------------------------------------------
# the Wolori


def test_endonym():
    assert ENDONYM["proto"] == "*wo-lor-i"
    assert citation(ENDONYM["proto"]) == ENDONYM["form"].lower() == "wolori"
    assert ENDONYM["gloss"] == "the un-ratioed"


def test_wolori_shibboleth_is_unshifted():
    """A Wolori lector says gel, kel, Suwkel — the unshifted proto-forms;
    the order is audible in a single syllable (docs/05 §05)."""
    assert lorkel.SHIBBOLETH == (("gel", "*gel-"), ("kel", "*kel"),
                                 ("Suwkel", "*suw-kel"))
    for form, proto in lorkel.SHIBBOLETH:
        assert citation(proto) == form.lower()


def test_open_proposal_is_not_canon():
    """The Pelaghar motherhouse is explicitly flagged 'not yet canon'."""
    assert OPEN_PROPOSAL["canon"] is False
    assert "Pelaghar" in OPEN_PROPOSAL["proposal"]
