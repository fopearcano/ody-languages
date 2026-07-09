"""The palatal shibboleth (docs/05 §01): the isogloss table, cell by
cell, through every mouth — plus the three Truth-station sister-cities.

The Nubhel column is checked only when :mod:`odylang.nubhel` is
importable (it is a separate codex, implemented independently).
"""

import pytest

from odylang import family
from odylang.family import LANGS, SHIBBOLETH, SISTER_CITIES, reflexes

NUBHEL_UP = family.nubhel_available()

ROWS = [(proto, lang, doc)
        for proto, row in SHIBBOLETH.items()
        for lang, doc in row.items()]


@pytest.mark.parametrize("proto,lang,doc", ROWS,
                         ids=[f"{p}:{l}" for p, l, _ in ROWS])
def test_isogloss_table(proto, lang, doc):
    """Every cell of the docs/05 §01 table (plus docs/06 §04's extension
    of the seam row) is the engine's own output, modulo the
    capitalization of proper names."""
    if lang == "nubhel" and not NUBHEL_UP:
        pytest.skip("odylang.nubhel not importable yet")
    got = reflexes(proto)
    assert got[lang] == doc.lower(), f"{proto} in {lang}: {got[lang]} != {doc}"


def test_table_is_the_documented_one():
    """The four columns of docs/05 §01, spelled exactly as printed."""
    assert SHIBBOLETH["*gel-"] == {
        "old_pelagic": "gel", "suchel": "jel", "rudgar": "ghel",
        "sel": "zel", "beltsel": "dzel", "nubhel": "yel"}
    assert SHIBBOLETH["*kel"] == {
        "old_pelagic": "kel", "suchel": "chel", "rudgar": "khel",
        "sel": "sel", "beltsel": "tsel", "nubhel": "hel"}
    assert SHIBBOLETH["*suw-kel"] == {
        "old_pelagic": "Suwkel", "suchel": "Sūchel", "rudgar": "Suwkhel",
        "sel": "Sūsel", "beltsel": "Suvtsel", "nubhel": "Sūhel"}
    assert SHIBBOLETH["*wer-stan"] == {
        "old_pelagic": "Werstan", "suchel": "Verstan", "rudgar": "Werstan",
        "sel": "Ērstan", "beltsel": "Verstan"}
    assert "nubhel" not in SHIBBOLETH["*wer-stan"]  # no documented deep city


def test_reflexes_row_shape():
    row = reflexes("*kel")
    for lang in ("old_pelagic", "lorkel", "suchel", "rudgar", "sel", "beltsel"):
        assert lang in row
    assert set(row) <= set(LANGS) | {"lorkel"}


def test_old_pelagic_and_lorkel_share_a_mouth():
    """One citation form, two custodians (docs/05 §01 heads the row
    'Old Pelagic / Lorkel')."""
    for proto in SHIBBOLETH:
        row = reflexes(proto)
        assert row["old_pelagic"] == row["lorkel"]


def test_wolori_tell():
    """'A Wolori says gel, the unshifted form — the order is audible in
    one syllable': the proto row differs from every daughter's."""
    row = reflexes("*gel-")
    assert row["old_pelagic"] == "gel"
    daughters = {row[l] for l in ("suchel", "rudgar", "sel", "beltsel")}
    assert "gel" not in daughters


def test_sister_cities():
    """Three worlds keep a city named 'Truth-station' from the proto era
    — the same name through three mouths (docs/05 §01 footnote)."""
    assert SISTER_CITIES == (("Mars", "rudgar", "Werstan"),
                             ("Maren", "sel", "Ērstan"),
                             ("Belgar", "beltsel", "Verstan"))
    row = reflexes("*wer-stan")
    for world, lang, name in SISTER_CITIES:
        assert row[lang] == name.lower(), world
    # the voice-test works: three distinct pronunciations
    assert len({name for _, _, name in SISTER_CITIES}) == 3


@pytest.mark.skipif(not NUBHEL_UP, reason="odylang.nubhel not importable yet")
def test_nubhel_extends_the_shibboleth():
    """docs/06 §04: 'the shibboleth row extends: gel · jel · ghel · zel ·
    dzel · yel' — and the minimal pair Sūchel/Sūhel."""
    assert reflexes("*gel-")["nubhel"] == "yel"
    assert reflexes("*kel")["nubhel"] == "hel"
    assert reflexes("*suw-kel")["nubhel"] == "sūhel"


def test_nubhel_column_absent_when_unavailable():
    """The row degrades gracefully: the key is present iff the deep
    codex is importable."""
    row = reflexes("*kel")
    assert ("nubhel" in row) == NUBHEL_UP


def test_everyone_agrees_on_the_engine():
    """docs/06 §02: *sow-orn → Sōrn 'in both — the family's most stable
    word'; and Sel agrees by accident of sound law (docs/05 §03)."""
    row = reflexes("*sow-orn")
    assert row["suchel"] == row["sel"] == "sōrn"
    if NUBHEL_UP:
        assert row["nubhel"] == "sōrn"
