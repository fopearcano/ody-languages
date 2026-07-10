"""The printable PDF manual — the dependency-free writer, locked.

The manual is generated from the rest of the package and rendered by the
from-scratch PDF/TrueType engine in :mod:`odylang.manual`.  These tests fall
into three groups:

* **structural** — assertions on the raw PDF bytes (header, trailer, the
  composite-font machinery, page count) that need no third-party reader;
* **the subsetter** — that :meth:`_TTF.subset` yields a valid, gid-preserving,
  much smaller TrueType carrying the glyphs it was asked for;
* **fidelity** — text-extraction sentinels, guarded by ``pytest.importorskip``
  on PyMuPDF, since that reader is *not* a dependency of the package.

The whole module skips cleanly when no Unicode TrueType face is installed, so a
bare CI box never fails here — it just reports the manual as unbuildable.
"""

import struct

import pytest

from odylang import manual
from odylang.cli import main


# ---------------------------------------------------------------------------
# build once (skip the whole module if there is no usable font on the box)


@pytest.fixture(scope="module")
def faces():
    try:
        return manual._load_faces()
    except RuntimeError as e:            # no FreeFont / DejaVu present
        pytest.skip(str(e))


@pytest.fixture(scope="module")
def pdf(faces):
    return manual.build_pdf()


# ---------------------------------------------------------------------------
# structural — no external reader needed


def test_pdf_header_and_trailer(pdf):
    assert pdf[:8] == b"%PDF-1.7"
    assert pdf.rstrip().endswith(b"%%EOF")
    assert b"\nxref\n" in pdf
    assert b"/Root " in pdf and b"/Size " in pdf


def test_document_object_graph(pdf):
    # a catalog pointing at a Pages tree, all uncompressed dict objects
    assert b"/Type /Catalog" in pdf
    assert b"/Type /Pages" in pdf
    assert b"/Type /Page\n" in pdf or b"/Type /Page " in pdf


def test_pages_count_is_reasonable(pdf):
    m = pdf.split(b"/Type /Pages")[1]
    count = int(m.split(b"/Count")[1].split(b">>")[0].strip())
    assert 10 <= count <= 30, count            # a real, compact multi-page book


def test_composite_font_is_wired(pdf):
    # the Type0/Identity-H + CIDFontType2 + FontFile2 + ToUnicode chain that
    # lets the manual carry macrons and IPA
    for needle in (b"/Subtype /Type0", b"/Encoding /Identity-H",
                   b"/CIDFontType2", b"/CIDToGIDMap /Identity",
                   b"/FontFile2", b"/ToUnicode"):
        assert needle in pdf, needle
    # three faces (serif, bold, mono) each become a Type0 font
    assert pdf.count(b"/Subtype /Type0") == 3


def test_build_is_deterministic(pdf):
    # no clock, no randomness — the same bytes every time (so a committed
    # artifact never spuriously churns)
    assert manual.build_pdf() == pdf


def test_length1_matches_embedded_program(pdf):
    # /Length1 is the *uncompressed* font-program length; a wrong value breaks
    # some readers.  It must be present for each embedded face.
    assert pdf.count(b"/Length1 ") == 3


# ---------------------------------------------------------------------------
# the checksum + sfnt primitives


def test_checksum_known_values():
    assert manual._checksum(b"") == 0
    assert manual._checksum(b"abcd") == 0x61626364
    # padding to a 4-byte boundary with zeros
    assert manual._checksum(b"ab") == 0x61620000


def test_build_sfnt_roundtrips_directory():
    tables = {"head": b"\x00" * 54, "glyf": b"ABCD", "loca": b"\x00\x00\x00\x04"}
    font = manual._build_sfnt(tables)
    assert font[:4] == b"\x00\x01\x00\x00"
    ntab = struct.unpack(">H", font[4:6])[0]
    assert ntab == 3
    tags = {font[12 + 16 * i:16 + 16 * i].decode("latin1") for i in range(ntab)}
    assert tags == {"head", "glyf", "loca"}


# ---------------------------------------------------------------------------
# the subsetter


def test_ttf_reads_cmap_and_widths(faces):
    t = faces["serif"]
    assert t.gid(ord("A")) > 0
    assert t.gid(0x101) > 0                 # ā — macron vowel, must be covered
    assert t.gid(0x283) > 0                 # ʃ — IPA esh
    assert t.width1000(t.gid(ord("A"))) > 0


def test_subset_is_smaller_valid_and_gid_preserving(faces):
    t = faces["serif"]
    wanted = {t.gid(c) for c in [ord("S"), ord("U"), 0x101, 0x283, 0x2C8]}
    sub = t.subset(wanted)
    # a valid sfnt, much smaller than the original
    assert sub[:4] == b"\x00\x01\x00\x00"
    assert len(sub) < len(t.data) // 4
    # the heavy, unneeded tables are gone; the load-bearing ones remain
    ntab = struct.unpack(">H", sub[4:6])[0]
    tags = {sub[12 + 16 * i:16 + 16 * i].decode("latin1") for i in range(ntab)}
    assert {"glyf", "loca", "head", "hhea", "hmtx", "maxp"} <= tags
    assert "cmap" not in tags and "kern" not in tags and "GPOS" not in tags
    # gid space is preserved (loca still has numGlyphs+1 long entries)
    loca = dict(zip(
        [sub[12 + 16 * i:16 + 16 * i].decode("latin1") for i in range(ntab)],
        [(struct.unpack(">I", sub[20 + 16 * i:24 + 16 * i])[0],
          struct.unpack(">I", sub[24 + 16 * i:28 + 16 * i])[0])
         for i in range(ntab)]))["loca"]
    assert loca[1] == (t.num_glyphs + 1) * 4


def test_subset_pulls_in_composite_components(faces):
    # ā is often a composite (a + combining macron); subsetting must keep the
    # component glyphs, or the accented form renders blank.  We assert the kept
    # set grows beyond the single requested gid.
    t = faces["serif"]
    a_macron = t.gid(0x101)
    offs = t._loca()
    if not t._components(a_macron, offs):
        pytest.skip("ā is a simple glyph in this face; nothing to pull in")
    sub = t.subset({a_macron})
    # the component 'a' glyph's outline must be present (non-empty loca span)
    # find it via the original component list
    comp = t._components(a_macron, offs)[0]
    # re-read the subset loca to confirm the component keeps its outline
    ntab = struct.unpack(">H", sub[4:6])[0]
    off = None
    for i in range(ntab):
        if sub[12 + 16 * i:16 + 16 * i] == b"loca":
            off = struct.unpack(">I", sub[20 + 16 * i:24 + 16 * i])[0]
    lo = struct.unpack(">I", sub[off + 4 * comp:off + 4 * comp + 4])[0]
    hi = struct.unpack(">I", sub[off + 4 * comp + 4:off + 4 * comp + 8])[0]
    assert hi > lo                          # the component outline is retained


# ---------------------------------------------------------------------------
# CLI


def test_cli_manual_writes_pdf(faces, tmp_path, capsys):
    out = tmp_path / "m.pdf"
    main(["manual", "-o", str(out)])
    data = out.read_bytes()
    assert data[:8] == b"%PDF-1.7"
    assert data.rstrip().endswith(b"%%EOF")
    assert "wrote" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# fidelity — needs a PDF reader, which is not a project dependency


def test_text_extraction_sentinels(pdf):
    fitz = pytest.importorskip("fitz")
    doc = fitz.open(stream=pdf, filetype="pdf")
    full = "".join(p.get_text() for p in doc)
    for s in ["SŪCHEL", "THE CROSSING-SPEECH", "Phonology",
              "veridical", "hōl-t", "ʃ", "ā ē ī ō ū", "beacon time",
              "Vocabulary", "sīli", "Sentences", "Colophon", "Navcher"]:
        assert s in full, s


def test_toc_page_numbers_match_footers(pdf):
    # the contents (on the front page, below the masthead) must reference the
    # same page numbers the running footers print — the layout's off-by-one trap
    fitz = pytest.importorskip("fitz")
    doc = fitz.open(stream=pdf, filetype="pdf")
    toc = doc[0].get_text().split("\n")        # masthead + CONTENTS share page 0
    for sec in ("The language & its family", "Phonology", "Vocabulary",
                "Sentences"):
        idx = toc.index(sec)
        claimed = int(toc[idx + 1])
        # the section heading must actually sit on that printed page ...
        page = doc[claimed]
        assert sec in page.get_text()
        # ... and that page's printed footer equals the claim
        lines = [l for l in page.get_text().split("\n") if l.strip()]
        assert lines[-1].strip() == str(claimed)
