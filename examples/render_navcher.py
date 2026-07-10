#!/usr/bin/env python3
"""Write the Navcher sample SVGs (docs/03) into examples/navcher/.

Produces the full glyph chart, the four doc samples (canon names, the
hail, careful-vs-bridge, the gap-stroke), and the showpiece — litany line
40 rebuilt from core :class:`~odylang.word.Word` objects through the
bridge hand, verified against the doc's own token stream.  All on the
doc's dark ground (#08070a) with the doc's colors: gold letters, red for
the special signs, blue for the bridge hand.

Run from anywhere:  python3 examples/render_navcher.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from odylang.navcher import (RED, SAMPLES, Line, render_glyph_chart,
                             render_sample, render_svg, tokens_bridge)
from odylang.word import ANCHOR, MAI, MOOD, PFV, STEM, Morph, Word

OUT = pathlib.Path(__file__).resolve().parent / "navcher"


def line40_words():
    """Litany line 40 (docs/02 §40, docs/03 showpiece) as core Words:
    hōl-t-eshe=zu. enmai ve-a=mi."""
    hol = Word([Morph("hōl", "surface", STEM), Morph("t", "PFV", PFV, "-"),
                Morph("eshe", "T•", MOOD, "-"), Morph("zu", "DARK", ANCHOR, "=")])
    enmai = Word([Morph("en", "1PL", STEM), Morph("mai", "ENT", MAI)])
    ve = Word([Morph("ve", "be", STEM), Morph("a", "T", MOOD, "-"),
               Morph("mi", "PROP", ANCHOR, "=")])
    return hol, enmai, ve


def showpiece_svg():
    """Line 40 through the bridge hand, locked to the doc's tokens."""
    hol, enmai, ve = line40_words()
    tokens = (tokens_bridge(hol) + [" ", " "] + tokens_bridge(enmai)
              + [" "] + tokens_bridge(ve))
    assert tokens == SAMPLES["sv-line40"].lines[0].tokens, \
        "bridge-hand tokens drifted from docs/03 sv-line40"
    lines = [
        Line(tokens, label="hōl-t-eshe=zu. enmai ve-a=mi.", color=RED),
        Line([], label='"Surfaced — seam-true, in the dark. '
                       'We are — by our own clock."'),
    ]
    return render_svg(lines, scale=SAMPLES["sv-line40"].scale)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "chart.svg": render_glyph_chart(),
        "names.svg": render_sample("sv-names"),
        "hail.svg": render_sample("sv-hail"),
        "compare.svg": render_sample("sv-compare"),
        "gap.svg": render_sample("sv-gap"),
        "line40.svg": showpiece_svg(),
    }
    for name, svg in files.items():
        path = OUT / name
        path.write_text(svg, encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
