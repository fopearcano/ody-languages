"""Every proto-sourced Sūchel lexicon entry must fall out of SC-1..7.

The codex's promise (docs/01 §03): "Every Sūchel word descends from an Old
Pelagic form by these seven ordered changes."  For each entry we check
both the surface outcome and *which* changes fired.
"""

import pytest

from odylang.suchel import LEXICON, SUCHEL, compose, entries


PROTO_ENTRIES = [e for e in entries() if e.proto is not None]


@pytest.mark.parametrize("entry", PROTO_ENTRIES, ids=lambda e: e.form)
def test_derivation_surface(entry):
    d = entry.derive()
    expected = entry.form.lstrip("-").rstrip("-").lower()
    expected = expected.split("(")[0]
    assert d.form == expected, d.trace()


@pytest.mark.parametrize("entry", PROTO_ENTRIES, ids=lambda e: e.form)
def test_derivation_cited_changes(entry):
    d = entry.derive()
    fired = {c for c in d.fired if c != "REP"}
    assert fired == set(entry.cited), (
        f"{entry.form}: fired {sorted(fired)}, codex cites {sorted(entry.cited)}\n"
        + d.trace())


def test_canon_derivations_of_the_codex():
    """The §03 showpieces, straight from the table."""
    cases = {
        "*kel": "chel",
        "*gel": "jel",
        "*ideren-es": "idrenes",
        "*pelag-ar": "pelgar",
        "*suw-kel": "sūchel",
        "*sow-orn": "sōrn",
        "*wer": "ver",
        "*mahin": "mān",
        "*haw-ol": "hōl",
        "*kap-a": "kav",
        "*tem-a": "tem",
    }
    for proto, expect in cases.items():
        assert SUCHEL.derive(proto).form == expect


def test_kava_intermediate():
    """docs/01: *kap-a → kava → kav (SC-6 then SC-7)."""
    d = SUCHEL.derive("*kap-a")
    sc6 = [s for s in d.steps if s.change == "SC-6"][0]
    assert sc6.after == "kava"


def test_drive_and_tongue_are_cognates():
    """*sow-orn and *suw-kel share the root: engine agrees with the codex."""
    assert SUCHEL.derive("*sow-orn").form == "sōrn"
    assert SUCHEL.derive("*suw-kel").form == "sūchel"


def test_daughter_formations_compose():
    for e in entries():
        if e.kind != "daughter" or not e.members:
            continue
        if e.form in ("idren", "ka", "Pelgar Somath", "Vurel-lor", "eshe-ver"):
            continue  # back-formation / clip / spaced or hyphenated compounds
        joined = compose(*e.members)
        assert joined.lower() == e.form.lower(), e.form


def test_lexicon_has_the_codex_inventory():
    # all 80 rows of docs/01 §06 plus the 14 appendix coinages of docs/02 §F
    for form in ["Sūchel", "Pelgar", "sū", "sūath", "sīl", "Sōrn", "jel",
                 "jelmar", "jelvos", "jelsīl", "Idrenes", "idren", "kad",
                 "kadur", "zukad", "zu", "mi", "ka", "ne", "nexath", "nuv",
                 "hau", "hōl", "nuvran", "nuvi", "nuvdol", "tur", "Turmai",
                 "kav", "Kaveth", "tem", "temor", "mor", "mar", "velosh",
                 "vel", "ver", "vur", "vurel", "Vurel-lor", "eshe-ver",
                 "pevlor", "lor", "somath", "Pelgar Somath", "nav", "navmai",
                 "mān", "chel", "kel", "ran", "tel", "dur", "dol", "osh",
                 "vos", "en", "ish", "an", "eni", "enmai", "ishmai", "-mai",
                 "-ath", "-eth", "-ol", "-en", "vo", "ve", "sa", "vor",
                 "mek", "pev", "shen", "hep", "ok", "nur", "dak",
                 "jed", "tan", "id", "men", "ret", "ān", "kru", "gal",
                 "lesh", "maiel", "om", "vu", "-u", "ō"]:
        assert form in LEXICON, form
