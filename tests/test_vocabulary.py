"""The vocabulary supplement: regular by construction, collision-free."""

import pytest

from odylang.phonology import strip_boundaries, syllabify, tokenize
from odylang.suchel import LEXICON as CANON, SUCHEL
from odylang.vocabulary import BY_FORM, DOMAINS, VOCAB, entries, reflexes

DAUGHTER_ONLY = {"ch", "j", "sh", "v"}          # born from the changes
PROTO_ONLY = {"w", "dz", "f", "y", "kh", "gh", "ts"}  # must never survive


def test_size_and_domains():
    assert len(VOCAB) >= 140
    assert {"kin", "body", "world", "sea", "sky", "time", "ship", "tools",
            "food", "beasts", "qualities", "verbs", "mind",
            "number"} <= set(DOMAINS)


@pytest.mark.parametrize("e", VOCAB, ids=lambda e: e.suchel)
def test_derived_never_typed(e):
    """Every root entry re-derives to its stored surface form."""
    if e.proto:
        assert SUCHEL.derive(e.proto).form == e.suchel
    else:
        assert e.members, e.suchel


@pytest.mark.parametrize("e", VOCAB, ids=lambda e: e.suchel)
def test_phonotactics(e):
    segs = strip_boundaries(tokenize(e.suchel))
    assert not (set(segs) & PROTO_ONLY), e.suchel
    assert syllabify(segs), e.suchel
    assert e.ipa


def test_no_silent_collisions():
    seen = {}
    for e in VOCAB:
        if e.suchel in CANON:
            assert e.homophone_of, (e.suchel, "collides with canon silently")
        if e.suchel in seen:
            assert e.homophone_of or seen[e.suchel], e.suchel
        seen[e.suchel] = e.homophone_of


def test_deliberate_homophones_are_the_documented_two():
    flagged = {e.suchel for e in VOCAB if e.homophone_of}
    assert flagged == {"shen", "bon"}


def test_showpiece_outcomes():
    """The coinages that exist to show the sound laws working."""
    cases = {
        "*kep-": "chep",      # SC-1 on 'head'
        "*kir-": "chir",      # SC-1 on 'cold'
        "*sekel": "shechel",  # s->sh and k->ch in one word: 'sail'
        "*gisi": "jish",      # g->j and s->sh then apocope: 'voice'
        "*mahir": "mār",      # SC-4: the captain wears the hand's tombstone
        "*maur-": "mōr",      # SC-5: wave / reef minimal pair
        "*lup-a": "luv",      # SC-6 + SC-7: 'to love'
        "*ama": "am",         # SC-7 apocope: 'mother'
        "*wat-": "vat",       # SC-3: 'water'
        "*dzun-": "zun",      # dz-repair: 'night'
        "*heban": "heban",    # initial h survives: 'sky'
    }
    for proto, form in cases.items():
        assert BY_FORM[form].proto == proto


def test_family_reflexes_of_a_coinage():
    """Coin once, inherit five times: 'cold' through every mouth shows the
    palatal shibboleth applying to new vocabulary."""
    cold = BY_FORM["chir"]
    r = reflexes(cold)
    assert r["suchel"] == "chir"
    assert r["rudgar"] == "khir"
    assert r["sel"] == "sir"
    assert r["beltsel"] == "tsir"
    assert r["nubhel"] == "hir"
    assert r["old_pelagic"] == "kir"


def test_entries_filtering():
    assert all(e.domain == "sea" for e in entries("sea"))
    hits = entries(search="water")
    assert any(e.suchel == "vat" for e in hits)
    assert BY_FORM["salvat"].members == ("sal", "vat")


def test_compounds_compose_from_surface_forms():
    from odylang.suchel import compose
    for e in VOCAB:
        if e.members:
            assert compose(*e.members) == e.suchel


def test_traces_replayable():
    t = BY_FORM["luv"].trace()
    assert "SC-6" in t and "SC-7" in t
    assert "compound" in BY_FORM["tandol"].trace()
