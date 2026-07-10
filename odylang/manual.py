"""The Sūchel manual — a printable PDF grammar, vocabulary & sentence book.

Everything in this module is generated from the rest of the package (the
grammar, the phonology, the lexicon and vocabulary, the phrasebook and
texts, the translator) — nothing is retyped — and rendered to a real,
multi-page PDF by a **dependency-free** writer built here from scratch:

* :class:`_TTF` reads a TrueType font's ``cmap`` (formats 4 and 12), advance
  widths (``hmtx``) and units-per-em, enough to embed it as a PDF Type0 /
  Identity-H composite font — so the manual can carry the macrons and IPA
  (``ā``, ``ʃ``, ``ˈ``, ``ː``, ``T•``, ``Κ``) that no base-14 PDF font has.
* :class:`_PDF` is a tiny object/xref/trailer writer; :class:`_Doc` is a
  small flowing-layout engine (headings, wrapped paragraphs, interlinear
  glosses, one- and two-column tables, running headers, a paged table of
  contents) on top of it.

The system fonts embedded are GNU FreeFont (FreeSerif / FreeSerifBold /
FreeMono), which are broadly installed on Linux; :func:`build_pdf` falls
back to whatever it can find and raises a clear error only if no usable
Unicode TrueType face is present.

    >>> from odylang.manual import build_pdf
    >>> pdf = build_pdf()          # -> bytes, a complete PDF
    >>> pdf[:8]
    b'%PDF-1.7'

Only the standard library is used.
"""

from __future__ import annotations

import io
import struct
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# font search — GNU FreeFont first (great IPA + macron coverage), then others

_FONT_DIRS = [
    "/usr/share/fonts/truetype/freefont",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/TTF",
    "/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
]
_FACE_CANDIDATES = {
    "serif": ["FreeSerif.ttf", "DejaVuSerif.ttf", "LiberationSerif-Regular.ttf",
              "Georgia.ttf", "Times New Roman.ttf"],
    "bold": ["FreeSerifBold.ttf", "DejaVuSerif-Bold.ttf",
             "LiberationSerif-Bold.ttf", "Georgia Bold.ttf"],
    "mono": ["FreeMono.ttf", "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf",
             "Menlo.ttc", "Courier New.ttf"],
}


def _find_face(names: Sequence[str]) -> Optional[str]:
    import os
    for d in _FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    # last resort: scan the dirs for anything matching a stem
    import glob
    for d in _FONT_DIRS:
        for n in names:
            hits = glob.glob(os.path.join(d, n))
            if hits:
                return hits[0]
    return None


# ---------------------------------------------------------------------------
# minimal TrueType reader (cmap + widths), enough for embedding


def _u16(b, o):
    return struct.unpack(">H", b[o:o + 2])[0]


def _u32(b, o):
    return struct.unpack(">I", b[o:o + 4])[0]


def _checksum(data: bytes) -> int:
    data = data + b"\x00" * ((4 - len(data) % 4) % 4)
    s = 0
    for i in range(0, len(data), 4):
        s = (s + struct.unpack(">I", data[i:i + 4])[0]) & 0xFFFFFFFF
    return s


def _build_sfnt(tables: Dict[str, bytes]) -> bytes:
    """Assemble a valid TrueType font from a ``{tag: bytes}`` table map,
    computing the table directory, per-table checksums and the head
    ``checkSumAdjustment``."""
    tags = sorted(tables)
    num = len(tags)
    max_pow = 1 << (num.bit_length() - 1)
    search_range = max_pow * 16
    entry_selector = max_pow.bit_length() - 1
    range_shift = num * 16 - search_range
    header = struct.pack(">IHHHH", 0x00010000, num, search_range,
                         entry_selector, range_shift)
    offset = 12 + 16 * num
    body = bytearray()
    offsets = {}
    for tag in tags:
        offsets[tag] = offset
        data = tables[tag]
        pad = (4 - len(data) % 4) % 4
        body += data + b"\x00" * pad
        offset += len(data) + pad
    directory = bytearray()
    for tag in tags:
        data = tables[tag]
        directory += struct.pack(">4sIII", tag.encode("latin1"),
                                 _checksum(data), offsets[tag], len(data))
    font = bytearray(header + bytes(directory) + bytes(body))
    adj = (0xB1B0AFBA - _checksum(bytes(font))) & 0xFFFFFFFF
    struct.pack_into(">I", font, offsets["head"] + 8, adj)
    return bytes(font)


class _TTF:
    def __init__(self, path: str):
        self.data = open(path, "rb").read()
        b = self.data
        ntab = _u16(b, 4)
        tabs: Dict[str, Tuple[int, int]] = {}
        for i in range(ntab):
            o = 12 + 16 * i
            tag = b[o:o + 4].decode("latin1")
            tabs[tag] = (_u32(b, o + 8), _u32(b, o + 12))
        self.tabs = tabs
        self.upm = _u16(b, tabs["head"][0] + 18)
        self.num_glyphs = _u16(b, tabs["maxp"][0] + 4)
        self.loc_fmt = _u16(b, tabs["head"][0] + 50)
        self.num_h = _u16(b, tabs["hhea"][0] + 34)
        hmtx = tabs["hmtx"][0]
        self.adv = [_u16(b, hmtx + 4 * i) for i in range(self.num_h)]
        self.cmap = self._read_cmap()

    def gid(self, cp: int) -> int:
        return self.cmap.get(cp, 0)

    def width1000(self, gid: int) -> int:
        a = self.adv[gid] if gid < self.num_h else (self.adv[-1] if self.adv else 500)
        return int(round(a * 1000.0 / self.upm))

    # -- subsetting ----------------------------------------------------------
    def _loca(self) -> List[int]:
        b = self.data
        off, _ = self.tabs["loca"]
        n = self.num_glyphs + 1
        if self.loc_fmt == 0:
            return [_u16(b, off + 2 * i) * 2 for i in range(n)]
        return [_u32(b, off + 4 * i) for i in range(n)]

    def _components(self, gid: int, offs: List[int]) -> List[int]:
        """The glyph indices a composite glyph references (empty if simple)."""
        b = self.data
        glyf = self.tabs["glyf"][0]
        start, end = glyf + offs[gid], glyf + offs[gid + 1]
        if end <= start:
            return []
        if struct.unpack(">h", b[start:start + 2])[0] >= 0:
            return []                                    # simple glyph
        out, p = [], start + 10
        while True:
            flags, comp = _u16(b, p), _u16(b, p + 2)
            out.append(comp)
            p += 4
            p += 4 if (flags & 0x0001) else 2            # args
            if flags & 0x0008:
                p += 2                                   # scale
            elif flags & 0x0040:
                p += 4                                   # x & y scale
            elif flags & 0x0080:
                p += 8                                   # 2x2
            if not (flags & 0x0020):                     # MORE_COMPONENTS
                break
        return out

    def subset(self, gids) -> bytes:
        """A minimal embeddable TrueType carrying only ``gids`` (and the
        components they need). Glyph ids are preserved, so Identity-H mapping
        and ``/CIDToGIDMap /Identity`` keep working; unused outlines and the
        heavy layout/name tables are dropped."""
        b = self.data
        offs = self._loca()
        keep = {0}
        stack = list(set(gids) | {0})
        while stack:
            g = stack.pop()
            keep.add(g)
            if g >= self.num_glyphs:
                continue
            for comp in self._components(g, offs):
                if comp not in keep:
                    stack.append(comp)
        glyf = self.tabs["glyf"][0]
        new_glyf = bytearray()
        new_offs = [0] * (self.num_glyphs + 1)
        for g in range(self.num_glyphs):
            if g in keep and offs[g + 1] > offs[g]:
                new_glyf += b[glyf + offs[g]:glyf + offs[g + 1]]
                if len(new_glyf) % 2:
                    new_glyf += b"\x00"
            new_offs[g + 1] = len(new_glyf)
        tables: Dict[str, bytes] = {}
        for tag in ("cvt ", "fpgm", "prep", "hhea", "hmtx", "maxp"):
            if tag in self.tabs:
                o, l = self.tabs[tag]
                tables[tag] = b[o:o + l]
        ho, hl = self.tabs["head"]
        head = bytearray(b[ho:ho + hl])
        head[8:12] = b"\x00\x00\x00\x00"                 # checkSumAdjustment
        struct.pack_into(">h", head, 50, 1)              # long loca
        tables["head"] = bytes(head)
        tables["loca"] = b"".join(struct.pack(">I", o) for o in new_offs)
        tables["glyf"] = bytes(new_glyf)
        return _build_sfnt(tables)

    def _read_cmap(self) -> Dict[int, int]:
        b = self.data
        base = self.tabs["cmap"][0]
        n = _u16(b, base + 2)
        best = None
        best_score = -1
        for i in range(n):
            o = base + 4 + 8 * i
            pid, eid, off = _u16(b, o), _u16(b, o + 2), _u32(b, o + 4)
            score = {(3, 10): 5, (0, 6): 4, (0, 4): 4, (3, 1): 3,
                     (0, 3): 3, (0, 2): 2, (0, 1): 1}.get((pid, eid), 0)
            if score > best_score:
                best_score, best = score, base + off
        fmt = _u16(b, best)
        out: Dict[int, int] = {}
        if fmt == 4:
            seg_x2 = _u16(b, best + 6)
            seg = seg_x2 // 2
            end = best + 14
            start = end + seg_x2 + 2
            delta = start + seg_x2
            roff = delta + seg_x2
            for s in range(seg):
                e = _u16(b, end + 2 * s)
                st = _u16(b, start + 2 * s)
                dl = _u16(b, delta + 2 * s)
                ro = _u16(b, roff + 2 * s)
                for c in range(st, e + 1):
                    if c == 0xFFFF:
                        continue
                    if ro == 0:
                        g = (c + dl) & 0xFFFF
                    else:
                        gi = roff + 2 * s + ro + 2 * (c - st)
                        g = _u16(b, gi)
                        if g:
                            g = (g + dl) & 0xFFFF
                    if g:
                        out[c] = g
        elif fmt == 12:
            ng = _u32(b, best + 12)
            for gi in range(ng):
                o = best + 16 + 12 * gi
                sc, ec, sg = _u32(b, o), _u32(b, o + 4), _u32(b, o + 8)
                for c in range(sc, ec + 1):
                    out[c] = sg + (c - sc)
        return out


# ---------------------------------------------------------------------------
# low-level PDF writer


class _PDF:
    def __init__(self):
        self.objs: List[bytes] = []

    def add(self, body: bytes) -> int:
        self.objs.append(body)
        return len(self.objs)

    def add_stream(self, dict_prefix: bytes, data: bytes,
                   compress: bool = True) -> int:
        if compress:
            data = zlib.compress(data)
            dict_prefix = dict_prefix + b" /Filter /FlateDecode"
        body = (b"<< " + dict_prefix + b" /Length %d >>" % len(data)
                + b"\nstream\n" + data + b"\nendstream")
        return self.add(body)

    def build(self, root: int) -> bytes:
        out = io.BytesIO()
        out.write(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
        offs = [0] * (len(self.objs) + 1)
        for i, body in enumerate(self.objs, start=1):
            offs[i] = out.tell()
            out.write(b"%d 0 obj\n" % i + body + b"\nendobj\n")
        xref = out.tell()
        out.write(b"xref\n0 %d\n" % (len(self.objs) + 1))
        out.write(b"0000000000 65535 f \n")
        for i in range(1, len(self.objs) + 1):
            out.write(b"%010d 00000 n \n" % offs[i])
        out.write(b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF"
                  % (len(self.objs) + 1, root, xref))
        return out.getvalue()


# ---------------------------------------------------------------------------
# embedded composite font (Type0 / Identity-H)


class _Font:
    def __init__(self, name: str, ttf: _TTF):
        self.name = name
        self.ttf = ttf
        self.used: Dict[int, int] = {}  # codepoint -> gid

    def hexstr(self, s: str) -> str:
        g = self.ttf.gid
        out = []
        for ch in s:
            cp = ord(ch)
            gid = g(cp)
            self.used[cp] = gid
            out.append("%04X" % gid)
        return "".join(out)

    def width(self, s: str, size: float) -> float:
        w = 0
        for ch in s:
            w += self.ttf.width1000(self.ttf.gid(ord(ch)))
        return w * size / 1000.0

    def emit(self, pdf: _PDF) -> int:
        ttf = self.ttf
        raw = ttf.subset(set(self.used.values()))
        ff = pdf.add_stream(b"/Length1 %d" % len(raw), raw)
        cps = sorted(self.used)
        wparts = []
        for cp in cps:
            gid = self.used[cp]
            wparts.append("%d [%d]" % (gid, ttf.width1000(gid)))
        warr = "[ " + " ".join(wparts) + " ]"
        desc = pdf.add(
            (b"<< /Type /FontDescriptor /FontName /%s /Flags 4 "
             b"/FontBBox [-1000 -400 2000 1100] /ItalicAngle 0 /Ascent 900 "
             b"/Descent -200 /CapHeight 700 /StemV 80 /FontFile2 %d 0 R >>"
             % (self.name.encode(), ff)))
        bf = "\n".join("<%04X> <%04X>" % (self.used[cp], cp) for cp in cps)
        tu = ("/CIDInit /ProcSet findresource begin 12 dict begin begincmap "
              "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def "
              "/CMapName /Adobe-Identity-UCS def /CMapType 2 def "
              "1 begincodespacerange <0000> <FFFF> endcodespacerange "
              "%d beginbfchar %s endbfchar endcmap CMapEnd end end"
              % (len(cps), bf))
        tuo = pdf.add_stream(b"", tu.encode())
        cid = pdf.add(
            (b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /%s "
             b"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
             b"/FontDescriptor %d 0 R /CIDToGIDMap /Identity /DW 500 /W %s >>"
             % (self.name.encode(), desc, warr.encode())))
        t0 = pdf.add(
            (b"<< /Type /Font /Subtype /Type0 /BaseFont /%s /Encoding /Identity-H "
             b"/DescendantFonts [%d 0 R] /ToUnicode %d 0 R >>"
             % (self.name.encode(), cid, tuo)))
        return t0


# ---------------------------------------------------------------------------
# colour palette (printable on cream/white)

INK = (0.11, 0.11, 0.13)
DIM = (0.42, 0.42, 0.46)
FAINT = (0.62, 0.62, 0.66)
GOLD = (0.62, 0.42, 0.15)      # bronze — Sūchel forms
RED = (0.72, 0.20, 0.16)       # seam-red — T•, moods, the gap
BLUE = (0.18, 0.34, 0.52)      # beacon — glosses, links
RULE = (0.80, 0.62, 0.30)

PAGE_W, PAGE_H = 595.28, 841.89
ML, MR, MT, MB = 52.0, 48.0, 58.0, 46.0
CW = PAGE_W - ML - MR


@dataclass
class _Op:
    kind: str                    # 'text' | 'line' | 'rect'
    a: tuple = ()                # payload


class _Doc:
    """A flowing-layout PDF page builder over :class:`_PDF`."""

    def __init__(self, faces: Dict[str, _TTF]):
        self.fonts = {k: _Font("F" + k[:3].title(), t) for k, t in faces.items()}
        self.fkey = {"serif": "F0", "bold": "F1", "mono": "F2"}
        self.pages: List[List[_Op]] = []
        self.headers: List[str] = []
        self.y = 0.0
        self.title = "SŪCHEL"
        self.section = ""
        self._new_page(header=False)

    # -- pages ---------------------------------------------------------------
    def _new_page(self, header: bool = True):
        self.pages.append([])
        self.headers.append(self.section if header else "")
        self.y = MT
        if header and self.section:
            self._raw_text(ML, MT - 22, self.title, "serif", 8, FAINT)
            w = self.fonts["serif"].width(self.section.upper(), 8)
            self._raw_text(PAGE_W - MR - w, MT - 22, self.section.upper(),
                           "serif", 8, FAINT)
            self._raw_line(ML, MT - 16, PAGE_W - MR, MT - 16, 0.4, RULE)
            self.y = MT + 6

    def _ensure(self, need: float):
        if self.y + need > PAGE_H - MB:
            self._new_page()

    def page_break(self):
        self._new_page()

    # -- raw draws (top-origin coords) ---------------------------------------
    def _raw_text(self, x, y_top, s, face, size, color):
        self.pages[-1].append(_Op("text", (x, PAGE_H - y_top, s, face, size, color)))

    def _raw_line(self, x1, y1t, x2, y2t, w, color):
        self.pages[-1].append(
            _Op("line", (x1, PAGE_H - y1t, x2, PAGE_H - y2t, w, color)))

    def _raw_rect(self, x, y_top, w, h, color):
        self.pages[-1].append(_Op("rect", (x, PAGE_H - y_top - h, w, h, color)))

    # -- measurement + wrapping ----------------------------------------------
    def wrap(self, s: str, face: str, size: float, width: float) -> List[str]:
        font = self.fonts[face]
        out, line = [], ""
        for word in s.split():
            trial = word if not line else line + " " + word
            if font.width(trial, size) <= width or not line:
                line = trial
            else:
                out.append(line)
                line = word
        if line:
            out.append(line)
        return out or [""]

    # -- flowing blocks ------------------------------------------------------
    def space(self, h: float):
        self.y += h

    def title_page(self, lines: Sequence[Tuple[str, str, float, tuple]]):
        y = 250
        for text, face, size, color in lines:
            for ln in text.split("\n"):
                w = self.fonts[face].width(ln, size)
                self._raw_text((PAGE_W - w) / 2, y, ln, face, size, color)
                y += size * 1.35
            y += size * 0.5

    def masthead(self, lines: Sequence[Tuple[str, str, float, tuple]]):
        """A compact centred title block at the top of the current page,
        leaving the rest of the page free (for the contents).  Returns the y
        just below it."""
        y = MT + 22
        for text, face, size, color in lines:
            for ln in text.split("\n"):
                w = self.fonts[face].width(ln, size)
                self._raw_text((PAGE_W - w) / 2, y, ln, face, size, color)
                y += size * 1.28
            y += size * 0.3
        y += 6
        self._raw_line(ML, y, PAGE_W - MR, y, 0.8, RULE)
        self.y = y + 18
        return self.y

    def heading(self, text: str, level: int = 1):
        sizes = {1: 15, 2: 12, 3: 10.5}
        size = sizes.get(level, 10.5)
        if level == 1:
            # sections flow continuously to save paper: break to a new page
            # only when the heading plus a few lines would not fit; otherwise
            # just leave breathing room above it
            if self.y + size * 5.0 > PAGE_H - MB:
                self._new_page()
            elif self.pages[-1]:
                self.space(size * 1.15)
            self.section = text
            self.headers[-1] = text
        else:
            self._ensure(size * 3.0)
            self.space(size * 0.6)
        color = INK if level == 1 else GOLD
        self._raw_text(ML, self.y + size, text, "bold", size, color)
        self.y += size * 1.2
        if level <= 2:
            self._raw_line(ML, self.y, PAGE_W - MR, self.y,
                           0.8 if level == 1 else 0.4, RULE)
            self.y += size * 0.4
        else:
            self.y += size * 0.2

    def para(self, s: str, face: str = "serif", size: float = 9.3,
             color: tuple = INK, lead: float = 1.32, indent: float = 0.0,
             width: Optional[float] = None):
        width = (width or CW) - indent
        for ln in self.wrap(s, face, size, width):
            self._ensure(size * lead)
            self._raw_text(ML + indent, self.y + size, ln, face, size, color)
            self.y += size * lead
        self.y += size * 0.28

    def gloss(self, suchel: str, gloss: str, translation: str,
              ipa: str = "", label: str = ""):
        """One interlinear example: Sūchel line, morpheme gloss, translation."""
        need = 10 * 3.4 + (9.5 if ipa else 0)
        self._ensure(need)
        x = ML + 9
        if label:
            self._raw_text(ML, self.y + 8.5, label, "mono", 7.6, FAINT)
        for ln in self.wrap(suchel, "mono", 10, CW - 11):
            self._raw_text(x, self.y + 10, ln, "mono", 10, GOLD)
            self.y += 11.5
        if ipa:
            for ln in self.wrap(ipa, "serif", 8.4, CW - 11):
                self._raw_text(x, self.y + 8.4, ln, "serif", 8.4, DIM)
                self.y += 9.6
        for ln in self.wrap(gloss, "mono", 8.2, CW - 11):
            self._raw_text(x, self.y + 8.2, ln, "mono", 8.2, BLUE)
            self.y += 9.6
        for ln in self.wrap("“" + translation + "”", "serif", 9.1, CW - 11):
            self._raw_text(x, self.y + 9.1, ln, "serif", 9.1, INK)
            self.y += 10.8
        self.y += 4.5

    def table(self, rows: Sequence[Sequence[str]], cols: Sequence[float],
              faces: Sequence[str], sizes: Sequence[float],
              colors: Sequence[tuple], header: bool = False):
        """A simple left-aligned table; each cell wraps within its column."""
        x0 = ML
        for r, row in enumerate(rows):
            wrapped = []
            maxlines = 1
            for c, cell in enumerate(row):
                w = cols[c] - 8
                lines = self.wrap(str(cell), faces[c], sizes[c], w)
                wrapped.append(lines)
                maxlines = max(maxlines, len(lines))
            rowh = maxlines * (max(sizes) * 1.32) + 3
            self._ensure(rowh)
            if header or r == 0 and header:
                pass
            y0 = self.y
            for c, lines in enumerate(wrapped):
                cx = x0 + sum(cols[:c])
                col = FAINT if (header and r == 0) else colors[c]
                face = "bold" if (header and r == 0) else faces[c]
                yy = y0
                for ln in lines:
                    self._raw_text(cx + 2, yy + sizes[c], ln, face, sizes[c], col)
                    yy += sizes[c] * 1.32
            self.y = y0 + rowh
            if header and r == 0:
                self._raw_line(x0, self.y - 1, x0 + sum(cols), self.y - 1,
                               0.4, RULE)
        self.y += 4

    def two_column(self, items: Sequence, render, gap: float = 22):
        """Flow ``items`` into two *balanced* columns, page by page, reading
        column-major (down the left, then down the right).  ``render(self,
        item, colw, measure)`` draws at the current cursor within the active
        column (``self._col_x``) when ``measure`` is false, and returns the
        item's height when it is true.  Each page is filled with as many items
        as two full-height columns can hold, then the split between the columns
        is chosen to make the two sides as even as possible."""
        colw = (CW - gap) / 2
        col_x = [ML, ML + colw + gap]
        heights = [render(self, it, colw, measure=True) for it in items]
        n = len(items)
        i = 0
        first = True
        while i < n:
            if not first:
                self._new_page()
            top = self.y
            avail = (PAGE_H - MB) - top
            # gather the largest run i..j-1 that fits in two columns of height
            # `avail` (a prefix in the left, the remainder in the right)
            j = i
            while j < n:
                run = heights[i:j + 1]
                # greedily fill the left as far as it goes, test the remainder
                s = kmax = 0
                for idx, h in enumerate(run):
                    if s + h <= avail:
                        s += h
                        kmax = idx + 1
                    else:
                        break
                if sum(run[kmax:]) <= avail:
                    j += 1
                else:
                    break
            if j == i:                       # one item taller than the page
                j = i + 1
            run = heights[i:j]
            # pick the split that best balances the two column heights
            best_k, best_diff = len(run), None
            for k in range(1, len(run) + 1):
                left, right = sum(run[:k]), sum(run[k:])
                if left <= avail and right <= avail:
                    diff = abs(left - right)
                    if best_diff is None or diff < best_diff:
                        best_diff, best_k = diff, k
            # draw the two columns
            self._col_w = colw
            self._col_x = col_x[0]
            self.y = top
            for idx in range(i, i + best_k):
                render(self, items[idx], colw, measure=False)
            bottom = self.y
            self._col_x = col_x[1]
            self.y = top
            for idx in range(i + best_k, j):
                render(self, items[idx], colw, measure=False)
            bottom = max(bottom, self.y)
            self.y = bottom
            i = j
            first = False
        self._col_x = ML
        self._col_w = CW

    # a cursor-relative text draw honoring the active column (for two_column)
    def col_text(self, s, face, size, color, lead=1.3):
        x = getattr(self, "_col_x", ML)
        w = getattr(self, "_col_w", CW)
        for ln in self.wrap(s, face, size, w):
            self._raw_text(x, self.y + size, ln, face, size, color)
            self.y += size * lead
        return size

    # -- table of contents ---------------------------------------------------
    def toc(self, entries: Sequence[Tuple[str, int]]):
        self._raw_text(ML, self.y + 15, "CONTENTS", "bold", 15, INK)
        self.y += 26
        self._raw_line(ML, self.y, PAGE_W - MR, self.y, 0.9, RULE)
        self.y += 14
        for title, page in entries:
            self._ensure(15)
            self._raw_text(ML + 4, self.y + 10.5, title, "serif", 10.5, INK)
            num = str(page)
            w = self.fonts["serif"].width(num, 10.5)
            self._raw_text(PAGE_W - MR - w, self.y + 10.5, num, "serif", 10.5, DIM)
            self.y += 16

    # -- serialise -----------------------------------------------------------
    def render(self) -> bytes:
        pdf = _PDF()
        # page numbers footer (skip title page 0)
        for i, ops in enumerate(self.pages):
            if i == 0:
                continue
            num = str(i)
            w = self.fonts["serif"].width(num, 8.5)
            ops.append(_Op("text", ((PAGE_W - w) / 2, MB - 30, num,
                                    "serif", 8.5, FAINT)))
        streams = [self._content(ops) for ops in self.pages]
        font_objs = {k: f.emit(pdf) for k, f in self.fonts.items()}
        res = pdf.add(
            b"<< /Font << /F0 %d 0 R /F1 %d 0 R /F2 %d 0 R >> >>"
            % (font_objs["serif"], font_objs["bold"], font_objs["mono"]))
        page_ids = []
        content_ids = [pdf.add_stream(b"", s.encode()) for s in streams]
        pages_obj = len(pdf.objs) + len(streams) + 1  # placeholder, patched
        for cid in content_ids:
            pid = pdf.add(
                b"<< /Type /Page /Parent __PAGES__ 0 R /Resources %d 0 R "
                b"/MediaBox [0 0 %.2f %.2f] /Contents %d 0 R >>"
                % (res, PAGE_W, PAGE_H, cid))
            page_ids.append(pid)
        kids = b" ".join(b"%d 0 R" % p for p in page_ids)
        pages = pdf.add(b"<< /Type /Pages /Kids [%s] /Count %d >>"
                        % (kids, len(page_ids)))
        for pid in page_ids:
            pdf.objs[pid - 1] = pdf.objs[pid - 1].replace(
                b"__PAGES__", b"%d" % pages)
        cat = pdf.add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages)
        return pdf.build(cat)

    def _content(self, ops: Sequence[_Op]) -> str:
        out = []
        for op in ops:
            if op.kind == "text":
                x, y, s, face, size, color = op.a
                fk = self.fkey[face]
                hx = self.fonts[face].hexstr(s)
                out.append("%.3f %.3f %.3f rg BT /%s %.2f Tf %.2f %.2f Td <%s> Tj ET"
                           % (color[0], color[1], color[2], fk, size, x, y, hx))
            elif op.kind == "line":
                x1, y1, x2, y2, w, c = op.a
                out.append("%.3f %.3f %.3f RG %.2f w %.2f %.2f m %.2f %.2f l S"
                           % (c[0], c[1], c[2], w, x1, y1, x2, y2))
            elif op.kind == "rect":
                x, y, w, h, c = op.a
                out.append("%.3f %.3f %.3f rg %.2f %.2f %.2f %.2f re f"
                           % (c[0], c[1], c[2], x, y, w, h))
        return "\n".join(out)


# ---------------------------------------------------------------------------
# the manual content — assembled from the rest of the package


def _load_faces() -> Dict[str, _TTF]:
    faces = {}
    for key, names in _FACE_CANDIDATES.items():
        p = _find_face(names)
        if p is None:
            raise RuntimeError(
                "no usable TrueType face for '%s' found; install GNU FreeFont "
                "(fonts-freefont-ttf) or DejaVu" % key)
        faces[key] = _TTF(p)
    return faces


def _sections():
    return ["The language & its family", "Phonology", "Stress — the mood "
            "carries the beat", "Nouns & pronouns", "The verb", "The four "
            "systems", "Vocabulary", "Sentences", "The script & the family"]


def build_pdf() -> bytes:
    """Render the whole manual and return the PDF as bytes."""
    from . import proto
    from .family import SHIBBOLETH, reflexes
    from .phonology import PHONETIC_NOTES
    from .phrasebook import LINES, SECTIONS
    from .suchel import entries as su_entries
    from .suchel_texts import K5, TEXTS
    from .vocabulary import VOCAB

    d = _Doc(_load_faces())

    # -- masthead + contents share the first page (compact front matter) -----
    d.masthead([
        ("SŪCHEL", "bold", 32, GOLD),
        ("THE CROSSING-SPEECH", "serif", 11, DIM),
        ("A Grammar, Vocabulary & Sentence Manual", "bold", 15, INK),
        ("daughter of Old Pelagic · tongue of the fleets", "serif", 9.5, DIM),
        ("You cannot speak without conjugating the truth.", "serif", 9.5, RED),
    ])
    toc_page_index = len(d.pages) - 1     # the contents fill this page's tail
    toc_y = d.y

    # content flows from a fresh page after the front matter
    d._new_page(header=False)

    # -- 1. the family -------------------------------------------------------
    d.heading("The language & its family", 1)
    sec_pages = {"The language & its family": len(d.pages) - 1}
    d.para("Sūchel is a full language built the way languages are really "
           "built: it eroded out of an older tongue, Old Pelagic, by seven "
           "regular sound changes, and it grew grammar for what its speakers "
           "cannot afford to be vague about. Every finite verb takes a "
           "position on the truth of what it says (a veridical mood) and "
           "declares which of three clocks it happened in (a temporal "
           "anchor). Word order is verb-final (SOV); the noun is simple and "
           "the verb carries the world on its back.")
    d.para("Old Pelagic left five other daughters, and each did something "
           "different to the ancestral *k and *g before front vowels. Ask a "
           "stranger to name the seam and their mouth files their birthplace:")
    shib = reflexes("*gel-")
    d.table(
        [["mouth", "the seam (*gel-)"]]
        + [[k.replace("_", " ").title(), v] for k, v in shib.items()],
        [150, CW - 150], ["serif", "mono"], [9.2, 10], [INK, GOLD],
        header=True)

    # -- 2. phonology --------------------------------------------------------
    d.heading("Phonology", 1)
    sec_pages["Phonology"] = len(d.pages) - 1
    d.para("Romanization is one symbol, one sound. The digraphs ch, sh are "
           "single consonants; macron vowels ā ē ī ō ū are long — length is "
           "quality held, not changed, a held breath. Stress is marked in the "
           "IPA with ˈ before the stressed syllable.")
    d.heading("Consonants — 17", 2)
    cons = [
        ["p", "p", "labial stop"], ["b", "b", "labial stop, voiced"],
        ["t", "t", "alveolar stop"], ["d", "d", "alveolar stop, voiced"],
        ["k", "k", "velar stop"], ["g", "g", "velar stop, voiced"],
        ["ch", "tʃ", "affricate (church)"], ["j", "dʒ", "affricate, voiced (judge)"],
        ["v", "v", "labial fricative"], ["s", "s", "alveolar fricative (voiceless)"],
        ["z", "z", "alveolar fricative, voiced"], ["sh", "ʃ", "postalveolar fricative"],
        ["m", "m", "nasal"], ["n", "n", "nasal"],
        ["r", "ɾ ~ r", "tap / trill; never the English glide"],
        ["l", "l", "lateral"],
        ["h", "h", "word-initial only (hōl, hau, hep)"],
    ]
    d.table([["letter", "IPA", "note"]] + cons, [70, 70, CW - 140],
            ["mono", "serif", "serif"], [10, 9.4, 9.2],
            [GOLD, DIM, INK], header=True)
    d.heading("Vowels — 5 + length", 2)
    vows = [["a", "a", "father (short)"], ["e", "e", "bed"],
            ["i", "i", "machine (short)"], ["o", "o", "story (short)"],
            ["u", "u", "rude (short)"],
            ["ā ē ī ō ū", "aː eː iː oː uː", "the same vowels, held"]]
    d.table([["letter", "IPA", "as in"]] + vows, [90, 110, CW - 200],
            ["mono", "serif", "serif"], [10, 9.4, 9.2],
            [GOLD, DIM, INK], header=True)
    d.para("Syllable canon: (C)(r/l)V(C); no clusters of three. The old *w "
           "and *h died in Sūchel, leaving long vowels as their tombstones.",
           size=9.2, color=DIM)

    # -- 3. stress -----------------------------------------------------------
    d.heading("Stress — the mood carries the beat", 1)
    sec_pages["Stress — the mood carries the beat"] = len(d.pages) - 1
    d.para("Four rules, applied in order; the first that applies wins. In a "
           "finite verb the veridical suffix seizes the stress — you can hear "
           "the truth-claim, because the mood carries the beat. Commands "
           "assert nothing, so imperatives are beatless.")
    for rule, text, ex in [
        ("Rule 1", "Compounds stress their first member.",
         "NUV-ran · JEL-mar · SŌRN-mai · ZU-kad"),
        ("Rule 2", "Finite verbs: the mood seizes the stress; anchor clitics "
         "are weightless.", "ve-RA-ka · ta-NA-mi · hōl-TE-she-zu"),
        ("Rule 3", "A long vowel seizes the stress in any other word.",
         "SŪ-chel · HŌ-lu · MĀN · ĀN"),
        ("Rule 4", "Otherwise stress the penult of the stem; case suffixes "
         "never shift it. Imperatives add no beat.",
         "i-DRE-nes · VU-re-len · TA-nu, JE-du"),
    ]:
        d._ensure(38)
        d._raw_text(ML, d.y + 10, rule, "bold", 10, GOLD)
        d.y += 13
        d.para(text, size=9.2, indent=12)
        d.para(ex, face="mono", size=9.2, color=RED, indent=12)

    # -- 4. nouns ------------------------------------------------------------
    d.heading("Nouns & pronouns", 1)
    sec_pages["Nouns & pronouns"] = len(d.pages) - 1
    d.para("Number: plural -i (sīl 'crosser' → sīli). Case clitics attach to "
           "the noun: accusative -(e)n, genitive -en, dative -ol, locative "
           "-eth. Possession splits two ways. Alienable things take the "
           "genitive -en; but kin, one's ship, and one's gaps take the "
           "entangled suffix -mai — possession as shared amplitude, not "
           "ownership. You say kel-en 'my words' but nav-mai 'my-entangled "
           "ship'; to use -en of your own ship is to announce you plan to "
           "sell her.")
    d.table([["case", "clitic", "example"],
             ["accusative", "-(e)n", "ishen 'you (obj.)'"],
             ["genitive", "-en", "somath-en 'of the assembly'"],
             ["dative", "-ol", "ish-ol 'to you'"],
             ["locative", "-eth", "jel-eth 'at the seam'"],
             ["entangled", "-mai", "nav-mai 'my own ship'"]],
            [96, 76, CW - 172], ["serif", "mono", "mono"],
            [9.2, 9.6, 9.6], [INK, GOLD, GOLD], header=True)
    d.heading("Pronouns", 2)
    d.table([["", "singular", "plural", "entangled"],
             ["1", "en", "eni", "enmai (crew-we)"],
             ["2", "ish", "ishi", "ishmai"],
             ["3", "an", "ani", "—"]],
            [40, 90, 90, CW - 220], ["bold", "mono", "mono", "mono"],
            [9.2, 9.6, 9.6, 9.6], [FAINT, GOLD, GOLD, GOLD], header=True)

    # -- 5. the verb ---------------------------------------------------------
    d.heading("The verb", 1)
    sec_pages["The verb"] = len(d.pages) - 1
    d.para("The verb template is STEM – (ASPECT) – MOOD = ANCHOR. Aspect: "
           "perfective -t-, imperfective unmarked. Mood is one of five and is "
           "obligatory; anchor is one of three and is obligatory on every "
           "finite verb. Negation is the particle vo before the verb.")
    d.heading("The five veridical moods", 2)
    d.table([["ΛL", "suffix", "meaning"],
             ["T", "-a", "classically true; settled"],
             ["T⁻", "-im", "true-as-approached; provisional from below"],
             ["T⁺", "-ur", "held-from-above; theoretical, unaccredited"],
             ["T•", "-eshe", "seam-true; self-dual, both-and"],
             ["F", "vo + -a", "false (negated plain)"]],
            [50, 70, CW - 120], ["bold", "mono", "serif"],
            [9.6, 9.6, 9.2], [RED, GOLD, INK], header=True)
    d.heading("The three temporal anchors", 2)
    d.table([["clitic", "from", "anchor"],
             ["=ka", "*kad- 'pulse'", "beacon time — shared, verifiable"],
             ["=mi", "*mei- 'self'", "proper time — the ship's own clock"],
             ["=zu", "*dzu- 'adrift'", "dark time — beyond coverage"]],
            [64, 110, CW - 174], ["mono", "mono", "serif"],
            [9.6, 9.2, 9.2], [GOLD, DIM, INK], header=True)
    d.para("Motion verbs are ungrammatical without a depth satellite: nuv "
           "'down-tower, deeper' or hau 'surfaceward'. And it is forbidden to "
           "place a verb inside the narration of a crossing: the particle ne "
           "stands where the verb cannot.", size=9.2)
    d.heading("Worked examples", 2)
    d.gloss("an sū-t-eshe=zu.", "3SG cross-PFV-T•=DARK",
            "She crossed — seam-true, in time no beacon reached.",
            ipa="an suːˈte.ʃe.zu")
    d.gloss("kad ver-a=ka.", "beacon speak.true-T=BEAC",
            "The beacon holds true. — the safest sentence in the language.",
            ipa="kad veˈra.ka")
    d.gloss("jed-u!", "go-IMP", "Go! — an order asserts nothing, so it takes "
            "no mood and no anchor.", ipa="ˈdʒe.du")

    # -- 6. the four systems / K5 -------------------------------------------
    d.heading("The four systems", 1)
    sec_pages["The four systems"] = len(d.pages) - 1
    d.para("Sūchel grammaticalizes what its world makes unignorable: the "
           "truth-value of the limit, the anchor of time, the direction of "
           "depth, and the place where narration fails. The showpiece is one "
           "sentence conjugated three ways — doctrine, heresy, and the tragic "
           "truth differ only by their morphology:")
    for s in K5:
        d.gloss(s.sentence.text(), s.sentence.gloss_line(), s.translation,
                label=s.title.upper())

    # -- 7. vocabulary -------------------------------------------------------
    d.heading("Vocabulary", 1)
    sec_pages["Vocabulary"] = len(d.pages) - 1
    d.para("The core lexicon of the codex, followed by the working "
           "vocabulary of daily speech. Every form is derived from an Old "
           "Pelagic root by the seven sound changes — nothing is invented at "
           "the surface. Forms are given with IPA where the codex records it.")

    def _render_entry(doc, item, colw, measure=False):
        form, ipa, gloss = item
        if measure:
            g_lines = len(doc.wrap(gloss, "serif", 8.4, colw))
            return 11 + g_lines * 10 + 4
        x = doc._col_x
        doc._raw_text(x, doc.y + 9.4, form, "mono", 9.4, GOLD)
        if ipa:
            fw = doc.fonts["mono"].width(form + "  ", 9.4)
            doc._raw_text(x + fw, doc.y + 8.2, "[" + ipa + "]", "serif", 7.8, FAINT)
        doc.y += 11
        for ln in doc.wrap(gloss, "serif", 8.4, colw):
            doc._raw_text(x + 6, doc.y + 8.4, ln, "serif", 8.4, INK)
            doc.y += 10
        doc.y += 4

    d.heading("Core lexicon", 2)
    core = [(e.form, e.ipa, e.gloss) for e in su_entries()
            if e.kind != "register" or e.ipa]
    d.two_column(core, _render_entry)

    d.heading("Working vocabulary (coined, derived)", 2)
    by_domain: Dict[str, list] = {}
    for e in VOCAB:
        by_domain.setdefault(e.domain, []).append((e.suchel, e.ipa, e.gloss))
    for dom in sorted(by_domain):
        d.heading(dom, 3)
        d.two_column(by_domain[dom], _render_entry)

    # -- 8. sentences --------------------------------------------------------
    d.heading("Sentences", 1)
    sec_pages["Sentences"] = len(d.pages) - 1
    d.para("The phrasebook — forty-one lines composed from the grammar, each "
           "with its morpheme gloss and translation — then the three texts. "
           "Every Sūchel line here is generated through the grammar, not "
           "stored as a string.")
    cur = None
    for l in LINES:
        if l.section != cur:
            cur = l.section
            d.heading(SECTIONS[cur], 3)
        d.gloss(l.sentence.text(), l.sentence.gloss_line(), l.translation,
                ipa=l.ipa.strip("[]"), label=str(l.number))
    for t in TEXTS:
        d.heading(t.title, 3)
        for p in t.lines:
            d.gloss(p.display() if hasattr(p, "display") else p.sentence.text(),
                    p.sentence.gloss_line(), p.translation)
        d.para(t.commentary, size=8.8, color=DIM, indent=10)

    # -- 9. script & family --------------------------------------------------
    d.heading("The script & the family", 1)
    sec_pages["The script & the family"] = len(d.pages) - 1
    d.para("Sūchel is written in Navcher, the fleet script — a featural "
           "alphabet in which letterforms encode phonetics. This manual sets "
           "the language in the Latin romanization; the script itself, in its "
           "living Current Hand and its sacred carved Logos hand, is rendered "
           "in the interactive codex (odylang web) and by the command "
           "odylang write.")
    d.para("Old Pelagic survives beyond Sūchel in four settled sisters and "
           "the Wolori's working register. The same proto-word wears each "
           "mouth's sound laws — the family, audible in a single syllable.")
    for proto_form in list(SHIBBOLETH)[:4]:
        r = reflexes(proto_form)
        row = " · ".join("%s %s" % (k[:3], v) for k, v in r.items())
        d.para("%s  →  %s" % (proto_form, row), face="mono", size=8.6,
               color=INK, indent=8)
    d.space(16)
    d.para("Colophon. Generated by odylang from the NERV//Pelagian Assembly "
           "language codices. The grammar, every lexical and phrasebook form, "
           "and the interlinear glosses are produced by the package; the PDF "
           "itself is written by a dependency-free engine that embeds a "
           "TrueType face so the macrons and IPA render true.",
           size=8.6, color=FAINT)

    # -- fill the contents onto the front page, below the masthead -----------
    saved = d.pages
    d.pages = [saved[toc_page_index]]  # draw onto the front page
    d.y = toc_y
    order = ["The language & its family", "Phonology",
             "Stress — the mood carries the beat", "Nouns & pronouns",
             "The verb", "The four systems", "Vocabulary", "Sentences",
             "The script & the family"]
    d.toc([(t, sec_pages[t]) for t in order])
    d.pages = saved

    return d.render()


def write(path: str) -> None:
    with open(path, "wb") as fh:
        fh.write(build_pdf())
