"""The interactive web codex: structure and embedded-data fidelity."""

import json
import re

import pytest

from odylang import webgen


@pytest.fixture(scope="module")
def data():
    return webgen.collect()


@pytest.fixture(scope="module")
def doc():
    return webgen.document()


def test_document_shape(doc):
    assert doc.startswith("<!DOCTYPE html>")
    assert doc.rstrip().endswith("</html>")
    assert "<title>" in doc and "window.ODY" in doc
    # a fragment must not carry the document skeleton
    frag = webgen.fragment()
    for tag in ("<!DOCTYPE", "<html", "<head>", "<body>"):
        assert tag not in frag


def test_embedded_json_roundtrips(doc):
    m = re.search(r"window\.ODY = (\{.*?\});</script>", doc, re.S)
    assert m, "embedded data blob not found"
    payload = json.loads(m.group(1).replace("<\\/", "</"))
    assert len(payload["phrasebook"]["lines"]) == 41
    assert len(payload["script"]["glyphs"]) == 32
    assert "</" not in m.group(1), "unescaped close-tag inside the data blob"


def test_data_carries_the_whole_system(data):
    assert set(data["langs"]) == {"old_pelagic", "suchel", "rudgar", "sel",
                                  "beltsel", "nubhel"}
    # the shibboleth row
    gel = next(w for w in data["family"]["words"] if w["proto"] == "*gel-")
    assert gel["forms"] == {"old_pelagic": "gel", "suchel": "jel",
                            "rudgar": "ghel", "sel": "zel",
                            "beltsel": "dzel", "nubhel": "yel"}
    assert "SC-1" in gel["traces"]["suchel"]
    assert len(data["family"]["words"]) >= 50
    # lexicons, sisters, texts
    assert len(data["suchel"]["lex"]) >= 90
    assert len(data["nubhel"]["lex"]) >= 30
    assert [len(s["places"]) for s in data["sisters"]] == [20, 20, 20]
    assert len(data["texts"]["suchel"]) == 3
    assert len(data["texts"]["k5"]) == 3
    assert len(data["texts"]["nubhel"]) == 3
    # the code-switch line survives with its language tag
    langs = {ln["lang"] for t in data["texts"]["nubhel"] for ln in t["lines"]}
    assert "Sūchel" in langs
    assert len(data["lorkel"]["terms"]) == 8


def test_phrasebook_lines_carry_tokens_and_rhythm(data):
    lines = {l["n"]: l for l in data["phrasebook"]["lines"]}
    assert lines[38]["tokC"] == ["|"]  # ne is not spelled
    assert lines[14]["tokB"] == ["v", "e", "r", "@T", "=ka"]
    assert lines[40]["syl"][:4] == ["ho:l", "TE", "she", "zu"]
    assert lines[40]["star"] and lines[40]["role"] == "resp"
    assert all(l["ipa"].startswith("[") for l in lines.values())


def test_document_sentinels(doc):
    for needle in ("ver ish-ol", "hōl-t-eshe=zu", "Ērstan", "Suwkhel",
                   "dzel", "Nūbi", "kaplor", "√2", "ASK A STRANGER"):
        assert needle in doc, needle


def test_cli_web(tmp_path, capsys):
    from odylang.cli import main
    out = tmp_path / "codex.html"
    main(["web", "-o", str(out)])
    assert out.exists() and out.stat().st_size > 50_000
    assert "wrote" in capsys.readouterr().out


def test_current_hand_in_payload(data, doc):
    ch = data["current"]
    assert len(ch["glyphs"]) == 32
    assert ch["glyphs"]["b"]["dropAt"] == 86       # voicing = the drop
    assert len(ch["glyphs"]["h"]["pen"]) == 2      # the ink runs dry
    assert "penAcc2" in ch["glyphs"]["mTs"]        # the filled eye
    for needle in ("The record page", "The vigil trace", "The liturgy disc",
                   "CURRENT HAND", "PAGE STUDIES"):
        assert needle in doc, needle
