"""Smoke tests locking every odylang CLI subcommand."""

import xml.etree.ElementTree as ET

import pytest

from odylang.cli import main


def run(capsys, *argv):
    main(list(argv))
    return capsys.readouterr().out


def test_derive(capsys):
    out = run(capsys, "derive", "suchel", "*suw-kel")
    assert "SC-1: suwkel -> suwchel" in out
    assert "= sūchel" in out
    out = run(capsys, "derive", "nubhel", "*nub-kel")
    assert "= nubhel" in out
    out = run(capsys, "derive", "lorkel", "*wer-stan")
    assert "= werstan" in out


@pytest.mark.parametrize("lang,proto,form", [
    ("rudgar", "*kel-som", "khelsom"),
    ("sel", "*wer-stan", "ērstan"),
    ("beltsel", "*pelag-ar", "plagar"),
])
def test_derive_sisters(capsys, lang, proto, form):
    assert f"= {form}" in run(capsys, "derive", lang, proto)


def test_family(capsys):
    out = run(capsys, "family", "*gel-")
    for form in ("gel", "jel", "ghel", "zel", "dzel", "yel"):
        assert form in out


def test_lex(capsys):
    out = run(capsys, "lex", "suchel", "--domain", "physics")
    assert "jel" in out and "the seam" in out
    out = run(capsys, "lex", "nubhel")
    assert "Nūbi" in out


def test_places(capsys):
    out = run(capsys, "places", "rudgar")
    assert "Werstan" in out and "*wer-stan" in out


def test_lorkel(capsys):
    out = run(capsys, "lorkel")
    assert "kaplor" in out and "√2" in out


def test_phrase(capsys):
    out = run(capsys, "phrase", "40")
    assert "hōl-t-eshe=zu. enmai ve-a=mi." in out
    assert "hoːlˈte.ʃe.zu · ˈen.mai veˈa.mi" in out
    out = run(capsys, "phrase", "--all")
    assert out.count("\n== ") == 5  # the five sections


def test_texts(capsys):
    out = run(capsys, "texts", "suchel")
    assert "— tem kav-eth dur-a=ka, vo?" in out  # dialogue dash carried
    assert "Κ5" in out
    out = run(capsys, "texts", "nubhel")
    assert "+mek-dok kodur" in out


def test_write_and_chart(capsys, tmp_path):
    svg = tmp_path / "hail.svg"
    run(capsys, "write", "ver ish-ol", "-o", str(svg))
    root = ET.fromstring(svg.read_text())
    assert root.tag.endswith("svg")
    svg2 = tmp_path / "l40.svg"
    run(capsys, "write", "--phrase", "40", "--hand", "bridge", "-o", str(svg2))
    assert ET.fromstring(svg2.read_text()).tag.endswith("svg")
    chart = tmp_path / "chart.svg"
    run(capsys, "chart", "-o", str(chart))
    assert ET.fromstring(chart.read_text()).tag.endswith("svg")


def test_vocab(capsys):
    out = run(capsys, "vocab", "--domain", "sea")
    assert "mōr" in out and "*maur-" in out
    out = run(capsys, "vocab", "--search", "cold", "--lang", "nubhel")
    assert "hir" in out
