"""Navcher: the G table locked byte-for-byte against docs/03, the two
hands' token streams, and the DOM-free SVG renderer."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from odylang.navcher import (ANCHOR_SIGILS, ANCHOR_TOKEN_GLYPH, CHART,
                             CONSONANTS, GLYPHS, LONGBAR, MOOD_SIGILS,
                             MOOD_TOKEN_GLYPH, SAMPLES, VOWEL_LETTERS, Line,
                             render_glyph_chart, render_sample, render_svg,
                             tokens_bridge, tokens_careful)
from odylang.word import (ANCHOR, CASE, MAI, MOOD, PFV, STEM, Morph, Word)

DOC = Path(__file__).resolve().parents[1] / "docs" / "03_qtr-script.html"

_SVG = "{http://www.w3.org/2000/svg}"


# ---------------------------------------------------------------------------
# core Words used by docs/03's own samples (built from the core API only)


def _verb(stem, mood_form, mood_gloss, anchor, pfv=False):
    m = [Morph(stem, cat=STEM)]
    if pfv:
        m.append(Morph("t", "PFV", PFV, "-"))
    m.append(Morph(mood_form, mood_gloss, MOOD, "-"))
    m.append(Morph(anchor[0], anchor[1], ANCHOR, "="))
    return Word(m)


def _ver_a_ka():
    return _verb("ver", "a", "T", ("ka", "BEAC"))


def _hol_t_eshe_zu():
    return _verb("hōl", "eshe", "T•", ("zu", "DARK"), pfv=True)


def _enmai():
    return Word([Morph("en", "1PL", STEM), Morph("mai", "ENT", MAI)])


def _ve_a_mi():
    return _verb("ve", "a", "T", ("mi", "PROP"))


# ---------------------------------------------------------------------------
# G-table integrity


def _parse_doc_g_table():
    """Extract 'const G = {...}' and 'const LONGBAR' from docs/03 verbatim."""
    text = DOC.read_text(encoding="utf-8")
    block = re.search(r"const G=\{(.*?)\n\};", text, re.S).group(1)
    glyphs = {}
    for m in re.finditer(r"^\s*(\w+):\{(.*)\},?\s*$", block, re.M):
        key, body = m.group(1), m.group(2)
        entry = {"w": int(re.search(r"w:(\d+)", body).group(1)),
                 "strokes": (), "paths": (), "fills": ()}
        sm = re.search(r"strokes:\[(.*)\]", body)
        if sm:
            entry["strokes"] = tuple(
                tuple(int(n) for n in grp.split(","))
                for grp in re.findall(r"\[([^\[\]]+)\]", sm.group(1)))
        pm = re.search(r"(paths|fills):\[(.*)\]", body)
        if pm:
            entry[pm.group(1)] = tuple(re.findall(r"'([^']*)'", pm.group(2)))
        glyphs[key] = entry
    longbar = tuple(int(n) for n in re.search(
        r"const LONGBAR=\[([\d,]+)\]", text).group(1).split(","))
    return glyphs, longbar


def test_g_table_is_byte_identical_to_docs_03():
    doc_glyphs, doc_longbar = _parse_doc_g_table()
    assert set(doc_glyphs) == set(GLYPHS)
    for key, entry in doc_glyphs.items():
        g = GLYPHS[key]
        assert g.w == entry["w"], key
        assert g.strokes == entry["strokes"], key
        assert g.paths == entry["paths"], key
        assert g.fills == entry["fills"], key
    assert LONGBAR == doc_longbar


def test_seventeen_consonants_five_vowels_and_names():
    assert CONSONANTS == ("p", "b", "t", "d", "k", "g", "ch", "j",
                          "s", "z", "sh", "v", "m", "n", "r", "l", "h")
    assert len(CONSONANTS) == 17
    assert VOWEL_LETTERS == ("a", "e", "i", "o", "u")
    # widths: consonants 100, vowels/ops 60 — the gap-stroke alone is
    # "wide-set" at 70 (docs/03 sv-gap note)
    for c in CONSONANTS:
        assert GLYPHS[c].w == 100, c
    for k in ("a", "e", "i", "o", "u", "mT", "mTm", "mTp", "mTs", "mF",
              "aka", "ami", "azu", "q"):
        assert GLYPHS[k].w == 60, k
    assert GLYPHS["gap"].w == 70
    # chart letter names, as the doc's cards give them: h is named 'he'
    chart_names = {e.key: e.name for _, entries in CHART for e in entries}
    assert chart_names["h"] == "he"
    for c in CONSONANTS:
        if c != "h":
            assert chart_names[c] == c
    # the full census: 17 + 5 + 5 moods + 3 anchors + gap + question
    assert len(GLYPHS) == 32
    # footer tally: '17 CONSONANTS · 5 VOWELS · 5 MOOD SIGILS · 3 ANCHORS · 1 GAP'
    assert len(MOOD_TOKEN_GLYPH) == 5
    assert len(ANCHOR_TOKEN_GLYPH) == 3


def test_zu_is_the_only_curve_and_eshe_the_only_fill():
    # "The only curve in the entire system is the =zu anchor" (rule 02)
    assert GLYPHS["azu"].paths == ("M46,84 A22,22 0 1 0 46,114",)
    for key, g in GLYPHS.items():
        if key != "azu":
            assert g.paths == (), f"{key} must not use paths — only =zu curves"
    # the seam-mark T• is the only filled glyph, and its outline is straight
    assert GLYPHS["mTs"].fills == ("M14,82 L46,82 L46,116 L14,116 Z",)
    for key, g in GLYPHS.items():
        if key != "mTs":
            assert g.fills == (), f"{key} must not be filled — only T• is"
    commands = set(re.findall(r"[A-Za-z]", GLYPHS["mTs"].fills[0]))
    assert commands <= {"M", "L", "Z"}  # no arcs hiding in the fill


def test_token_maps_match_the_docs_renderword():
    assert MOOD_TOKEN_GLYPH == {"@T": "mT", "@T-": "mTm", "@T+": "mTp",
                                "@Ts": "mTs", "@F": "mF"}
    assert ANCHOR_TOKEN_GLYPH == {"=ka": "aka", "=mi": "ami", "=zu": "azu"}
    assert MOOD_SIGILS == {"a": "@T", "im": "@T-", "ur": "@T+", "eshe": "@Ts"}
    assert ANCHOR_SIGILS == {"ka": "=ka", "mi": "=mi", "zu": "=zu"}


# ---------------------------------------------------------------------------
# careful hand


def test_tokens_careful_canon_names_match_sv_names():
    rows = {"Sūchel": ["s", "u:", "ch", "e", "l"],
            "Sōrn": ["s", "o:", "r", "n"],
            "jel": ["j", "e", "l"],
            "zukad": ["z", "u", "k", "a", "d"]}
    for word, tokens in rows.items():
        assert tokens_careful(word) == tokens
    # the doc's own rows carry two trailing word-spaces of padding
    for line, tokens in zip(SAMPLES["sv-names"].lines, rows.values()):
        assert line.tokens == tokens + [" ", " "]


def test_tokens_careful_hail_letters_the_dative_spaced():
    """sv-hail: 'ver ish-ol' — the codex letters the dative spaced."""
    expected = ["v", "e", "r", " ", "i", "sh", " ", "o", "l"]
    assert tokens_careful("ver ish-ol") == expected
    assert SAMPLES["sv-hail"].lines[0].tokens == expected
    # from a core Word, the CASE morph carries the same spacing
    ish_ol = Word([Morph("ish", "2SG", STEM), Morph("ol", "DAT", CASE, "-")])
    assert tokens_careful(ish_ol) == ["i", "sh", " ", "o", "l"]
    # the solid accusative stays solid (docs/01 §04: 'ishen' written solid)
    ishen = Word([Morph("ish", "2SG", STEM), Morph("en", "ACC", CASE, "")])
    assert tokens_careful(ishen) == ["i", "sh", "e", "n"]


def test_tokens_careful_decompositions():
    # diphthongs are two small letters (sv-line40: enmai = e-n-m-a-i)
    assert tokens_careful("enmai") == ["e", "n", "m", "a", "i"]
    assert tokens_careful(_enmai()) == ["e", "n", "m", "a", "i"]
    assert tokens_careful("hau") == ["h", "a", "u"]
    # x -> k,s (docs/01 §02: x = /ks/); th -> t,h (documented choice)
    assert tokens_careful("nexath") == ["n", "e", "k", "s", "a", "t", "h"]
    assert tokens_careful("sūath") == ["s", "u:", "a", "t", "h"]
    # macron vowels become ':' tokens; separators letter solid
    assert tokens_careful("sū-t-eshe=zu") == \
        ["s", "u:", "t", "e", "sh", "e", "z", "u"]
    with pytest.raises(ValueError):
        tokens_careful("wol")  # proto *w has no fleet letter


# ---------------------------------------------------------------------------
# bridge hand


def test_sv_compare_careful_vs_bridge():
    """ver-a=ka: v-e-r-a-k-a careful, v-e-r-@T-=ka bridge (docs/03)."""
    careful = ["v", "e", "r", "a", "k", "a"]
    bridge = ["v", "e", "r", "@T", "=ka"]
    assert tokens_careful("ver-a=ka") == careful
    assert tokens_careful(_ver_a_ka()) == careful
    assert tokens_bridge(_ver_a_ka()) == bridge
    assert SAMPLES["sv-compare"].lines[0].tokens == careful
    assert SAMPLES["sv-compare"].lines[1].tokens == bridge
    # bridge hand is the blue register in the doc's own render
    assert SAMPLES["sv-compare"].lines[1].color == "#6fa8ff"


def test_sv_line40_bridge_tokens():
    """hōl-t-eshe=zu. enmai ve-a=mi. — the whole Resurrection in four sigils."""
    assert tokens_bridge(_hol_t_eshe_zu()) == ["h", "o:", "l", "t", "@Ts", "=zu"]
    assert tokens_bridge(_enmai()) == ["e", "n", "m", "a", "i"]
    assert tokens_bridge(_ve_a_mi()) == ["v", "e", "@T", "=mi"]
    rebuilt = (tokens_bridge(_hol_t_eshe_zu()) + [" ", " "]
               + tokens_bridge(_enmai()) + [" "] + tokens_bridge(_ve_a_mi()))
    assert rebuilt == SAMPLES["sv-line40"].lines[0].tokens
    assert SAMPLES["sv-line40"].lines[0].color == "#e8362a"
    assert SAMPLES["sv-line40"].scale == 0.46


def test_bridge_refuses_unknown_sigils():
    bad = Word([Morph("ver", cat=STEM), Morph("osh", "??", MOOD, "-"),
                Morph("ka", "BEAC", ANCHOR, "=")])
    with pytest.raises(ValueError):
        tokens_bridge(bad)


# ---------------------------------------------------------------------------
# SVG output


def _polylines(svg_text):
    root = ET.fromstring(svg_text)
    return list(root.iter(_SVG + "polyline"))


def test_render_svg_is_well_formed_with_expected_polylines():
    # Sūchel: s(1) + ū(1 + held-breath bar) + ch(3) + e(1) + l(2) = 9
    svg = render_svg([Line(tokens_careful("Sūchel"))])
    root = ET.fromstring(svg)
    assert root.tag == _SVG + "svg"
    assert root.get("viewBox", "").startswith("0 0 ")
    assert len(_polylines(svg)) == 9
    # jel: j(4) + e(1) + l(2) = 7 — "four cuts of a blade" for j alone
    assert len(_polylines(render_svg([Line(tokens_careful("jel"))]))) == 7
    assert len(GLYPHS["j"].strokes) == 4


def test_render_svg_line40_has_one_arc_and_one_fill():
    svg = render_sample("sv-line40")
    root = ET.fromstring(svg)
    paths = list(root.iter(_SVG + "path"))
    arcs = [p for p in paths if "A" in p.get("d", "")]
    assert len(arcs) == 1                        # =zu, the only curve
    assert arcs[0].get("fill") == "none"         # the hook refuses to close
    fills = [p for p in paths if p.get("fill") not in (None, "none")]
    assert len(fills) == 1                       # T•, the seam-mark
    assert fills[0].get("d") == "M14,82 L46,82 L46,116 L14,116 Z"


def test_gap_renders_as_the_single_full_height_stroke():
    svg = render_sample("sv-gap")
    polys = _polylines(svg)
    assert len(polys) == 1
    assert polys[0].get("points") == "35,4 35,136"   # full height, alone
    assert polys[0].get("stroke") == "#e8362a"


def test_stroke_style_matches_drawglyph():
    svg = render_svg([Line(["m"])], scale=1, color="#f5d76e",
                     background=None)
    poly = _polylines(svg)[0]
    assert poly.get("stroke-width") == "7"
    assert poly.get("stroke-linecap") == "square"
    assert poly.get("stroke-linejoin") == "miter"
    assert poly.get("fill") == "none"
    assert poly.get("stroke") == "#f5d76e"


def test_all_samples_render_and_parse():
    for key in ("sv-names", "sv-hail", "sv-compare", "sv-line40", "sv-gap"):
        root = ET.fromstring(render_sample(key))
        assert root.tag == _SVG + "svg"
    # labels survive as text nodes (sv-names carries four)
    names = ET.fromstring(render_sample("sv-names"))
    texts = [t.text for t in names.iter(_SVG + "text")]
    assert texts == ["Sūchel", "Sōrn", "jel — the seam", "zukad — dark time"]


def test_glyph_chart_is_well_formed_and_complete():
    svg = render_glyph_chart()
    root = ET.fromstring(svg)
    assert root.tag == _SVG + "svg"
    # every group of the doc appears, with its caption
    labels = [t.text for t in root.iter(_SVG + "text")]
    for caption, _entries in CHART:
        assert caption.upper() in labels
    # one arc (=zu), one filled sigil (T•) in the whole chart
    paths = list(root.iter(_SVG + "path"))
    assert sum("A" in p.get("d", "") for p in paths) == 1
    assert sum(p.get("fill") not in (None, "none") for p in paths) == 1
    # 33 cards: 32 glyphs + the ā demo card
    assert sum(len(entries) for _c, entries in CHART) == 33
