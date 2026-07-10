"""The translator chat web app: document shape and embedded-snapshot fidelity.

The page is offline and self-contained, so these tests assert on the emitted
HTML string and on :func:`odylang.translator_web.collect` — no browser, no
network.  The client behaviour (compose/peel/synth) is exercised as data:
we prove the snapshot carries everything the JS runs on.
"""

import json
import re

import pytest

from odylang import translator_web as tw


@pytest.fixture(scope="module")
def snap():
    return tw.collect()


@pytest.fixture(scope="module")
def doc():
    return tw.page()


# ---------------------------------------------------------------------------
# document shape


def test_page_is_a_standalone_document(doc):
    assert doc.startswith("<!DOCTYPE html>")
    assert doc.rstrip().endswith("</html>")
    assert doc.count("<title>") == 1
    assert "window.ODYT" in doc


def test_fragment_has_no_skeleton():
    frag = tw.page_fragment()
    for tag in ("<!DOCTYPE", "<html", "<head>", "<body>"):
        assert tag not in frag
    # but it still carries the four pieces a host needs
    assert "<title>" in frag
    assert "<style>" in frag
    assert "window.ODYT" in frag
    assert "<script>" in frag


def test_sentinels_present(doc):
    for needle in ("ver ish-ol", "translator", "VOICE", "RHYTHM", "SPEAK",
                   "SHIP-CARVE", "CURRENT HAND", "hōl-t-eshe=zu"):
        assert needle in doc, needle


def test_page_under_size_budget(doc):
    kb = len(doc.encode("utf-8")) / 1024
    assert kb < 500, f"page is {kb:.0f} KB, over the ~500 KB budget"


def test_write_roundtrips(tmp_path):
    out = tmp_path / "translator.html"
    tw.write(str(out))
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert text.startswith("<!DOCTYPE html>")
    assert text == tw.page()


# ---------------------------------------------------------------------------
# the embedded snapshot round-trips out of the page


def _extract_blob(doc):
    m = re.search(r"window\.ODYT = (\{.*?\});</script>", doc, re.S)
    assert m, "embedded data blob not found"
    assert "</" not in m.group(1), "unescaped close-tag inside the data blob"
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_embedded_json_roundtrips(doc):
    payload = _extract_blob(doc)
    # normalise both sides through JSON (tuples -> lists) before comparing
    assert payload == json.loads(json.dumps(tw.collect(), ensure_ascii=False))


def test_voice_has_formants(snap):
    v = snap["VOICE"]
    assert "formants" in v
    for vowel in ("a", "e", "i", "o", "u"):
        assert vowel in v["formants"]
        assert len(v["formants"][vowel]) == 3
    # the resonator + timing constants the browser synth reproduces
    assert len(v["formantBandwidths"]) == 3
    assert len(v["formantAmps"]) == 3
    assert "vowelMs" in v["timing"] and "longFactor" in v["timing"]
    assert v["consonants"]["s"]["manner"] == "fricative"


def test_idioms_cover_all_41_lines_and_more(snap):
    idioms = snap["IDIOMS"]
    assert len(idioms) >= 60
    lines = [c for c in idioms if c.get("line")]
    assert {c["line"] for c in lines} == set(range(1, 42))  # all 41, no gaps
    # every attested line hits at confidence 1.0
    assert all(c["conf"] == 1.0 for c in lines)
    # the canonical opener is there, lettered and voiced
    hello = next(c for c in idioms if c.get("line") == 1)
    assert hello["su"] == "ver ish-ol."
    assert hello["tokens"] and hello["syl"]
    # aliases let a greeting resolve to an attested line
    keys = set()
    for c in idioms:
        keys.add(c["key"])
        keys.update(tw._tr._norm_idiom(a) for a in c.get("aliases", []))
    assert "hello" in keys and "goodbye" in keys


def test_idiom_cards_are_complete(snap):
    for c in snap["IDIOMS"]:
        for field in ("en", "key", "su", "ipa", "gloss", "tokens", "syl",
                      "conf", "notes", "src"):
            assert field in c, (c.get("en"), field)
        assert isinstance(c["tokens"], list)
        assert isinstance(c["syl"], list)
        assert 0.0 <= c["conf"] <= 1.0


def test_lexicon_and_reverse_index(snap):
    lex = snap["LEX"]
    assert len(lex) >= 200
    sample = next(iter(lex.values()))
    assert set(sample) == {"ipa", "gloss", "domain"}
    # the reverse index and the forward stems power the two directions
    assert snap["REV"]["friend"] == "dam"   # english gloss -> Sūchel form
    assert snap["REV"]["go"]                 # verb lemma -> stem
    assert "jel" in set(snap["REV"].values())
    assert snap["CORE"]["seam"] == "jel"     # the codex-symbol core nouns
    assert snap["STEMS"]["ver"]["gl"]        # Sūchel stem -> english gloss
    # pronoun stems are resolvable for the su2en peel
    assert snap["STEMS"]["en"]["gl"] == "I"


def test_script_and_hand_geometry(snap):
    assert len(snap["GLYPHS"]) == 32
    a = snap["GLYPHS"]["a"]
    assert "w" in a and "strokes" in a
    assert len(snap["LONGBAR"]) == 4
    # the current-hand pen data (for lettering any token stream)
    ch = snap["CURRENT"]
    assert len(ch["glyphs"]) == 32
    assert ch["glyphs"]["b"]["dropAt"] == 86        # voicing = the pen drop
    assert ch["arcpen"] and ch["leadin"] and ch["leadout"]


def test_compose_tables_present(snap):
    # the morpheme machinery the client mirrors from the engine
    assert snap["MOODSUF"] == {"T": "a", "Tm": "im", "Tp": "ur", "Ts": "eshe"}
    assert snap["MOOD_PEEL"]["a"] == "T"
    assert snap["ANCHOR_GLOSS"] == {"ka": "BEAC", "mi": "PROP", "zu": "DARK"}
    # subject pronouns carry person (for anchor selection) and a gloss tag
    i = snap["PRON_SUBJ"]["i"]
    assert i["person"] == 1 and i["tag"] == "1SG" and i["su"]
    assert snap["PRON_OBJ"]["me"]["su"]
    assert snap["VERBS"]["go"]["stem"]
    assert snap["DIR"]["down"] == "nuv"


def test_client_engine_functions_are_wired(doc):
    # the three translation paths and three audio engines must be in the app
    for fn in ("composeEN", "peelSU", "detectDir", "normIdiom",
               "playVoice", "playRhythm", "speak", "wordSvg", "lineSvg",
               "voicedVowel", "createBiquadFilter"):
        assert fn in doc, fn
    # honest fallbacks are labelled
    assert "word-by-word" in doc
    assert "odylang serve" in doc


def test_page_and_fragment_share_the_snapshot(doc):
    frag = tw.page_fragment()
    frag_blob = re.search(r"window\.ODYT = (\{.*?\});</script>", frag, re.S)
    doc_blob = re.search(r"window\.ODYT = (\{.*?\});</script>", doc, re.S)
    assert frag_blob and doc_blob
    assert frag_blob.group(1) == doc_blob.group(1)
