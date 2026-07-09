"""The sisters at naming depth (docs/05 §02–04): every documented place
name and cognate of Rudgar, Sel, and Beltsel must fall out of each
tongue's ordered changes, and the codex's rule-table examples must
reproduce exactly.
"""

import pytest

from odylang import beltsel, rudgar, sel
from odylang.beltsel import BELTSEL
from odylang.rudgar import RUDGAR
from odylang.sel import SEL

SISTERS = [
    ("rudgar", RUDGAR, rudgar.PLACES, rudgar.COGNATES),
    ("sel", SEL, sel.PLACES, sel.COGNATES),
    ("beltsel", BELTSEL, beltsel.PLACES, beltsel.COGNATES),
]

ALL_ENTRIES = [(name, e) for name, _, places, cogs in SISTERS
               for e in list(places) + list(cogs)]


def _entry_id(pair):
    name, e = pair
    return f"{name}:{getattr(e, 'name', None) or e.form}"


# ---------------------------------------------------------------------------
# every documented form, surface and fired changes


@pytest.mark.parametrize("pair", ALL_ENTRIES, ids=_entry_id)
def test_documented_form(pair):
    _, e = pair
    d = e.derive()
    expected = (getattr(e, "name", None) or e.form).lower()
    assert d.form == expected, d.trace()


@pytest.mark.parametrize("pair", ALL_ENTRIES, ids=_entry_id)
def test_cited_changes(pair):
    _, e = pair
    d = e.derive()
    fired = {c for c in d.fired if c != "REP"}
    label = getattr(e, "name", None) or e.form
    assert fired == set(e.cited), (
        f"{label}: fired {sorted(fired)}, expected {sorted(e.cited)}\n"
        + d.trace())


def test_twenty_places_each():
    """The codex charts each sister 'at naming depth' — twenty names."""
    for _, _, places, _ in SISTERS:
        assert len(places) == 20
    assert [p.name for p in rudgar.PLACES][0] == "Rudgar"
    assert [p.name for p in rudgar.PLACES][-1] == "Werstan"
    assert [p.name for p in sel.PLACES][0] == "Maren"
    assert [p.name for p in sel.PLACES][-1] == "Ēkmar"
    assert [p.name for p in beltsel.PLACES][0] == "Belgar"
    assert [p.name for p in beltsel.PLACES][-1] == "Nexbel"


# ---------------------------------------------------------------------------
# Rudgar (docs/05 §02)


def test_rudgar_rule_table_examples():
    assert RUDGAR.derive("*wer-stan").form == "werstan"    # R-1
    assert RUDGAR.derive("*kel").form == "khel"            # R-2
    assert RUDGAR.derive("*gel").form == "ghel"            # R-2
    assert RUDGAR.derive("*kap-a").form == "khap"          # R-3
    assert RUDGAR.derive("*hau").form == "hā"              # R-4 "*hau- → hā-"
    assert RUDGAR.derive("*pelag-ar").form == "pelaghar"   # R-5's cited row


def test_rudgar_r2_environment():
    """kh/gh only word-initially or after a vowel/glide — a consonant
    blocks (Rudgar, Akdol, Hekmor untouched; Suwkhel after the glide)."""
    assert RUDGAR.derive("*rud-gar").form == "rudgar"      # g after d
    assert RUDGAR.derive("*ak-dol").form == "akdol"        # k before C
    assert RUDGAR.derive("*hek-mor").form == "hekmor"      # k before C
    assert RUDGAR.derive("*suw-kel").form == "suwkhel"     # k after w!


def test_rudgar_galgar_dissimilation():
    """The one documented exception: *gal-gar keeps its initial g."""
    galgar = next(p for p in rudgar.PLACES if p.name == "Galgar")
    d = galgar.derive()
    assert d.form == "galgar"
    assert d.adjustments, "the codex's irregularity must be recorded"
    assert "dissimilation" in d.adjustments[0]
    # without the adjustment, R-2 predicts gh-
    assert RUDGAR.derive("*gal-gar").form == "ghalgar"


def test_rudgar_r4_word_final():
    """*au → ā even word-finally (*dun-hau → Dunhā) — unlike Sūchel's
    SC-5, which spares the edge (hau keeps its diphthong)."""
    assert RUDGAR.derive("*dun-hau").form == "dunhā"
    from odylang.suchel import SUCHEL
    assert SUCHEL.derive("*hau").form == "hau"


def test_rudgar_r5_dry_leveling():
    """R-5 fires on no attested name (Soworn is two syllables); a
    synthetic three-syllable form locks the rule itself."""
    d = RUDGAR.derive("*dur-en-dol")
    assert d.form == "durandol"
    assert "R-5" in d.fired
    # two-syllable cognates are untouched
    assert RUDGAR.derive("*sow-orn").form == "soworn"


def test_rudgar_spells_ks():
    """Mars writes /ks/ out as ks (Neksdol), where Sūchel keeps x (nexath)."""
    assert RUDGAR.derive("*nex-dol").form == "neksdol"
    from odylang.suchel import LEXICON
    assert "x" in LEXICON["nexath"].form


def test_rudgar_conservatism():
    """R-1: the sounds every other daughter killed survive on Mars."""
    for proto in ("*wel-dol", "*wer-stan", "*suw-ren", "*sow-orn"):
        assert "w" in RUDGAR.derive(proto).form
    for proto in ("*hek-mor", "*dun-hau"):
        assert "h" in RUDGAR.derive(proto).form


# ---------------------------------------------------------------------------
# Sel (docs/05 §03)


def test_sel_rule_table_examples():
    assert SEL.derive("*kel").form == "sel"                # S-1
    assert SEL.derive("*gel").form == "zel"                # S-1
    assert SEL.derive("*wer-stan").form == "ērstan"        # S-2
    assert SEL.derive("*kap-a").form == "kaba"             # S-3
    assert SEL.derive("*hek-mar").form == "ēkmar"          # S-4
    assert SEL.derive("*kad-u").form == "kado"             # S-5


def test_sel_s2_directions_of_lengthening():
    """Word-initial *w lengthens the following vowel, otherwise the
    preceding one; hiatus after a long vowel is absorbed."""
    assert SEL.derive("*wer-stan").form == "ērstan"        # following
    assert SEL.derive("*sow-mor").form == "sōmor"          # preceding
    assert SEL.derive("*sow-orn").form == "sōrn"           # + absorption
    assert SEL.derive("*nāw-es").form == "nās"             # swallowed whole
    assert SEL.derive("*hau-bel").form == "ābel"           # offglide counts


def test_sel_good_omen():
    """*sow-orn comes out Sōrn — identical to the fleet form."""
    from odylang.suchel import SUCHEL
    assert SEL.derive("*sow-orn").form == SUCHEL.derive("*sow-orn").form == "sōrn"


def test_sel_susel_vs_suchel():
    """Sūsel: the same lengthening as Sūchel, then S-1 instead of
    palatalization (docs/05 §03 cognate line)."""
    from odylang.suchel import SUCHEL
    assert SEL.derive("*suw-kel").form == "sūsel"
    assert SUCHEL.derive("*suw-kel").form == "sūchel"


def test_sel_degemination_repair():
    assert SEL.derive("*lim-mar").form == "limar"
    assert SEL.derive("*kad-dun").form == "kadun"


def test_sel_finals_kept():
    """S-5: finals otherwise KEPT — Sel drops nothing (kaba keeps its -a
    where Rudgar khap and Sūchel kav lose it)."""
    assert SEL.derive("*kap-a").form == "kaba"
    assert RUDGAR.derive("*kap-a").form == "khap"


# ---------------------------------------------------------------------------
# Beltsel (docs/05 §04)


def test_beltsel_rule_table_examples():
    assert BELTSEL.derive("*kel").form == "tsel"           # B-1
    assert BELTSEL.derive("*gel").form == "dzel"           # B-1
    assert BELTSEL.derive("*pelag-ar").form == "plagar"    # B-2
    assert BELTSEL.derive("*kad-stan").form == "kadtan"    # B-3
    assert BELTSEL.derive("*wer-stan").form == "verstan"   # B-4
    assert BELTSEL.derive("*hek").form == "ek"             # B-5
    assert BELTSEL.derive("*nāw-ren").form == "navren"     # B-6


def test_beltsel_names_itself():
    """Beltsel = *bel-kel 'hearth-speech', by its own B-1."""
    assert BELTSEL.derive("*bel-kel").form == "beltsel"


def test_beltsel_b2_pronounceability():
    """B-2 deletes only where the result stays pronounceable: pe- goes
    (legal onset pl-), dzeles' second e goes (falling coda -ls), but
    *plagr is blocked (rising -gr) and CVC-CVC compounds survive."""
    assert BELTSEL.derive("*pelag-ar").form == "plagar"    # not plagr
    assert BELTSEL.derive("*gel-es").form == "dzels"
    for proto, form in [("*bel-gar", "belgar"), ("*tur-dol", "turdol"),
                        ("*ran-ren", "ranren"), ("*tem-tur", "temtur"),
                        ("*id-gar", "idgar")]:
        assert BELTSEL.derive(proto).form == form


def test_beltsel_b3_syllable_contact():
    """B-3's middle drops only where the contact rises in sonority: the
    codex's own table gives Kadtan but keeps Morstan and Verstan."""
    assert BELTSEL.derive("*kad-stan").form == "kadtan"    # d.st rises
    assert BELTSEL.derive("*mor-stan").form == "morstan"   # r.st falls
    assert BELTSEL.derive("*wer-stan").form == "verstan"


def test_beltsel_x_is_one_segment():
    """x = /ks/ is one segment, so Nexbel is no three-consonant cluster."""
    assert BELTSEL.derive("*nex-bel").form == "nexbel"


def test_beltsel_cannot_hold_its_breath():
    """B-6: no derived Beltsel form contains a long vowel."""
    for e in list(beltsel.PLACES) + list(beltsel.COGNATES):
        form = e.derive().form
        assert not any(v in form for v in "āēīōū"), form


def test_beltsel_files_suchel_as_suvtsel():
    """'Say Sūchel to a Belgar clerk and they will file it as Suvtsel.'"""
    assert BELTSEL.derive("*suw-kel").form == "suvtsel"
    assert BELTSEL.derive("*sow-orn").form == "sovorn"
