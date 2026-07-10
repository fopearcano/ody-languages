"""The interactive codex: a self-contained web explorer for the family.

``odylang web -o odylang.html`` renders every dataset in the package —
lexicons, derivation traces, the 41-line phrasebook with rhythm and
Navcher lettering, the texts, the sisters, the script — into ONE static
HTML file: no server, no dependencies, no network requests.  The visual
system is the codices' own (docs/01–06): terminal ground ``#08070a``,
gold/seam-red/beacon-blue signals, mono type, corner-bracket frames.

Everything shown is generated from the same Python modules the CLI uses;
nothing is retyped.  The Navcher renderer and the careful-hand tokenizer
are the only logic mirrored in JavaScript (the glyph geometry itself is
embedded as data straight from :mod:`odylang.navcher`).
"""

from __future__ import annotations

import dataclasses as dc
import json
from typing import Dict, List


# ---------------------------------------------------------------------------
# data


LANG_LABELS = {
    "old_pelagic": ("OLD PELAGIC / LORKEL", "the ancestor · liturgy & the Wolori"),
    "suchel": ("SŪCHEL", "the fleets · lingua franca"),
    "rudgar": ("RUDGAR", "Mars · old ground"),
    "sel": ("SEL", "Maren · ocean moon"),
    "beltsel": ("BELTSEL", "Belgar · the capital"),
    "nubhel": ("NUBHEL", "the diver fleet · the deep"),
}

STRESS_RULES = [
    ("RULE 1", "Compounds stress their first member.",
     "NUV-ran · JEL-mar · SŌRN-mai · E-she-ver · ZU-kad"),
    ("RULE 2", "Finite verbs: the mood seizes the stress — the truth-claim "
               "carries the beat. Anchor clitics are weightless.",
     "ve-RA-ka · ta-NA-mi · hōl-TE-she-zu · i-DE-she-mi"),
    ("RULE 3", "A long vowel seizes the stress in any other word.",
     "SŪ-chel · HŌ-lu · MĀN · ĀN"),
    ("RULE 4", "Otherwise: stress the penult of the stem — case suffixes "
               "never shift it once set. Corollary: imperatives are "
               "beatless.",
     "i-DRE-nes · PEL-gar · VU-rel → VU-re-len · TA-nu, JE-du, I-du"),
]

SUCHEL_MOODS = [
    ("T", "-a", "classically true; settled"),
    ("T⁻", "-im", "true-as-approached; provisional from below (IR)"),
    ("T⁺", "-ur", "held-from-above; theoretical, unaccredited (UV)"),
    ("T•", "-eshe", "seam-true; self-dual, both-and"),
    ("F", "vo + -a", "false (negated plain)"),
]

SUCHEL_ANCHORS = [
    ("=ka", "*kad- 'pulse'", "beacon time — shared, network-verifiable"),
    ("=mi", "*mei- 'self'", "proper time — the ship's own clock"),
    ("=zu", "*dzu- 'adrift'", "dark time — beyond coverage; unanchorable"),
]

SCRIPT_RULES = [
    ("FEATURAL", "Head position = place (labials head-left, alveolars "
                 "head-center, velars head-right); a foot-stroke = voicing; "
                 "a slash = frication. Learn six letters and you can "
                 "predict the rest."),
    ("STENCIL-SAFE", "Every stroke is straight; nothing encloses fully. The "
                     "only curve in the entire system is the =zu anchor — "
                     "the unanchored mark is the one sign that refuses to "
                     "close."),
    ("TWO HANDS", "Careful hand spells every suffix phonetically — liturgy, "
                  "law, log-of-record. Bridge hand compresses mood and "
                  "anchor into sigils — instrument panels, hull marks, "
                  "haste."),
]

SISTER_TAGLINES = {
    "rudgar": "the conservative sister — it never lost *w or *h; Martian "
              "ears are the closest living ears to Old Pelagic",
    "sel": "the liquid sister — every *w and *h drowned into vowel length; "
           "long, open, tide-paced",
    "beltsel": "the eroded prestige tongue — unstressed vowels deleted, "
               "clusters crushed, every long vowel shortened: the capital "
               "cannot hold its breath",
}


def _trace(deriver, proto: str) -> str:
    try:
        return deriver.derive(proto).trace()
    except Exception:  # a root outside this daughter's documented territory
        return ""


def collect() -> Dict:
    from . import proto
    from .beltsel import BELTSEL, COGNATES as BE_COG, PLACES as BE_PLACES
    from .cli import _sentence_tokens
    from .family import SHIBBOLETH, SISTER_CITIES, reflexes
    from .lorkel import CUSTODIANS, ENDONYM, NEO_PELAGIC, NOTATION_NAMES
    from .navcher import CHART, GLYPHS, LONGBAR
    from .nubhel import (FALSE_FRIENDS, NUBHEL, TWO_FLEETS,
                         entries as nb_entries)
    from .nubhel_grammar import ANCHORS as NB_ANCHORS, DIRECTIONALS, MOODS
    from .nubhel_texts import TEXTS as NB_TEXTS
    from .phonology import PHONETIC_NOTES
    from .phrasebook import LETTERING_NOTES, LINES, SECTIONS
    from .rudgar import COGNATES as RU_COG, PLACES as RU_PLACES, RUDGAR
    from .sel import COGNATES as SE_COG, PLACES as SE_PLACES, SEL
    from .suchel import SUCHEL, entries as su_entries
    from .suchel_texts import K5, TEXTS as SU_TEXTS

    derivers = {"suchel": SUCHEL, "nubhel": NUBHEL, "rudgar": RUDGAR,
                "sel": SEL, "beltsel": BELTSEL}

    # -- the family explorer -------------------------------------------------
    def family_word(p: str) -> Dict:
        forms = reflexes(p)
        forms.pop("lorkel", None)  # one row answers for both custodians
        return {
            "proto": p,
            "gloss": proto.gloss(p),
            "forms": forms,
            "traces": {lang: _trace(d, p) for lang, d in derivers.items()},
        }

    shib_protos = list(SHIBBOLETH)
    fam_words = [family_word(p) for p in shib_protos]
    for p in proto.ROOTS:
        if p not in SHIBBOLETH:
            fam_words.append(family_word(p))

    # -- lexicons -------------------------------------------------------------
    def lex_row(e, deriver) -> Dict:
        row = {"form": e.form, "ipa": e.ipa, "gloss": e.gloss,
               "etym": e.etym, "domain": e.domain, "kind": e.kind}
        if e.proto:
            row["trace"] = _trace_entry(e)
        return row

    def _trace_entry(e):
        d = e.derive()
        return d.trace() if d else ""

    su_lex = [lex_row(e, SUCHEL) for e in su_entries()]
    nb_lex = [lex_row(e, NUBHEL) for e in nb_entries()]

    # -- phrasebook -----------------------------------------------------------
    lines = []
    for l in LINES:
        tok_c = _sentence_tokens(l.sentence, "careful")
        tok_b = _sentence_tokens(l.sentence, "bridge")
        row = {"n": l.number, "sec": l.section, "text": l.sentence.text(),
               "ipa": l.ipa, "gloss": l.sentence.gloss_line(),
               "trans": l.translation, "note": l.note, "role": l.role,
               "star": l.star, "syl": l.sentence.syl_line(), "tokC": tok_c}
        if tok_b != tok_c:
            row["tokB"] = tok_b
        lines.append(row)

    # -- texts ----------------------------------------------------------------
    su_texts = [{"title": t.title,
                 "lines": [{"disp": p.display(), "gloss": p.sentence.gloss_line(),
                            "trans": p.translation, "lang": "Sūchel"}
                           for p in t.lines],
                 "comm": t.commentary} for t in SU_TEXTS]
    k5 = [{"title": s.title, "attr": s.attribution,
           "text": s.sentence.text(), "gloss": s.sentence.gloss_line(),
           "trans": s.translation, "comm": s.commentary} for s in K5]
    nb_texts = [{"title": t.title,
                 "lines": [{"disp": ln.display, "gloss": ln.gloss,
                            "trans": ln.translation, "lang": ln.language}
                           for ln in t.lines],
                 "comm": t.commentary} for t in NB_TEXTS]

    # -- sisters ---------------------------------------------------------------
    def sister(key, deriver, places, cognates) -> Dict:
        return {
            "key": key, "name": LANG_LABELS[key][0],
            "where": LANG_LABELS[key][1], "tagline": SISTER_TAGLINES[key],
            "changes": [{"id": c.id, "summary": c.summary}
                        for c in deriver.changes],
            "places": [{"name": p.name, "proto": p.proto, "gloss": p.gloss,
                        "what": p.what} for p in places],
            "cognates": [{"form": c.form, "proto": c.proto, "note": c.note}
                         for c in cognates],
        }

    sisters = [sister("rudgar", RUDGAR, RU_PLACES, RU_COG),
               sister("sel", SEL, SE_PLACES, SE_COG),
               sister("beltsel", BELTSEL, BE_PLACES, BE_COG)]

    # -- nubhel ----------------------------------------------------------------
    nubhel = {
        "lex": nb_lex,
        "changes": [{"id": c.id, "summary": c.summary}
                    for c in NUBHEL.changes],
        "ff": [{"proto": f.proto, "su": f.suchel, "nu": f.nubhel,
                "note": f.note} for f in FALSE_FRIENDS],
        "fleets": TWO_FLEETS,
        "moods": [{"key": k, "form": v[0], "gloss": v[1]}
                  for k, v in MOODS.items()],
        "anchors": [{"key": k, "form": v[0], "gloss": v[1]}
                    for k, v in NB_ANCHORS.items()],
        "dirs": [{"word": k, "proto": v[0], "meaning": v[1], "gloss": v[2]}
                 for k, v in DIRECTIONALS.items()],
    }

    # -- lorkel ------------------------------------------------------------------
    lorkel = {
        "terms": [{"form": t.form, "formation": " + ".join(t.formation),
                   "meaning": t.meaning, "reflex": t.suchel_reflex or "—",
                   "note": t.reflex_note} for t in NEO_PELAGIC.values()],
        "notation": list(NOTATION_NAMES),
        "custodians": [{"number": c.number, "name": c.name,
                        "register": c.register, "mode": c.mode,
                        "description": c.description}
                       for c in CUSTODIANS.values()],
        "endonym": ENDONYM if isinstance(ENDONYM, str) else str(ENDONYM),
    }

    # -- the vocabulary supplement ----------------------------------------------
    from .vocabulary import VOCAB
    vocab_rows = []
    for e in VOCAB:
        etym = e.proto or (" + ".join(e.members) + " (compound)")
        if e.note:
            etym += " — " + e.note
        if e.homophone_of:
            etym += " · homophone: " + e.homophone_of
        vocab_rows.append({"form": e.suchel, "ipa": e.ipa, "gloss": e.gloss,
                           "etym": etym, "domain": e.domain,
                           "kind": "coined", "trace": e.trace()})
    for e in VOCAB:
        if e.proto:
            fam_words.append({**family_word(e.proto), "gloss": e.gloss,
                              "coined": True})

    # -- the Current Hand (design handoff 07-E) ---------------------------------
    from .currenthand import ARCPEN, HAND, LEADIN, LEADOUT

    def _pen_glyph(g):
        d = {"w": g.w, "pen": [[list(pt) for pt in pn] for pn in g.pen]}
        if g.drop_at is not None:
            d["dropAt"] = g.drop_at
        if g.vowel:
            d["vowel"] = True
        if g.sigil:
            d["sigil"] = True
        if g.pen_acc:
            d["penAcc"] = [[list(pt) for pt in pn] for pn in g.pen_acc]
        if g.pen_acc2:
            d["penAcc2"] = [[list(pt) for pt in pn] for pn in g.pen_acc2]
        if g.pen_sub:
            d["penSub"] = [[list(pt) for pt in pn] for pn in g.pen_sub]
        return d

    current = {"glyphs": {k: _pen_glyph(g) for k, g in HAND.items()},
               "arcpen": [list(pt) for pt in ARCPEN],
               "leadin": [list(pt) for pt in LEADIN],
               "leadout": [list(pt) for pt in LEADOUT]}

    # -- script --------------------------------------------------------------------
    script = {
        "glyphs": {k: {"w": g.w, "strokes": [list(s) for s in g.strokes],
                       "paths": list(g.paths), "fills": list(g.fills)}
                   for k, g in GLYPHS.items()},
        "longbar": list(LONGBAR),
        "chart": [{"group": grp,
                   "cards": [{"key": c.key, "name": c.name, "sub": c.sub,
                              "special": c.special, "long": c.long_mark}
                             for c in cards]}
                  for grp, cards in CHART],
        "rules": [{"name": n, "text": t} for n, t in SCRIPT_RULES],
    }

    return {
        "langs": {k: {"name": v[0], "where": v[1]}
                  for k, v in LANG_LABELS.items()},
        "family": {"shibboleth": shib_protos, "words": fam_words,
                   "cities": [list(c) for c in SISTER_CITIES]},
        "suchel": {"lex": su_lex,
                   "domains": sorted({e["domain"] for e in su_lex}),
                   "stress": [{"rule": r, "text": t, "ex": e}
                              for r, t, e in STRESS_RULES],
                   "moods": [{"lam": l, "suffix": s, "meaning": m}
                             for l, s, m in SUCHEL_MOODS],
                   "anchors": [{"clitic": c, "src": s, "meaning": m}
                               for c, s, m in SUCHEL_ANCHORS],
                   "phon": PHONETIC_NOTES,
                   "vocab": vocab_rows},
        "phrasebook": {"sections": SECTIONS, "lines": lines,
                       "lettering": LETTERING_NOTES},
        "texts": {"suchel": su_texts, "k5": k5, "nubhel": nb_texts},
        "nubhel": nubhel,
        "sisters": sisters,
        "lorkel": lorkel,
        "current": current,
        "script": script,
    }


# ---------------------------------------------------------------------------
# page assembly

_TITLE = "SŪCHEL — the interactive language codex"

_MARKUP = """
<div class="shell">
<aside class="rail">
  <div class="brand">ODYLANG
    <span class="sub">NERV//PELAGIAN ASSEMBLY<br>INTERACTIVE CODEX · REV 1.1</span></div>
  <nav id="nav" aria-label="codex sections"></nav>
  <div class="styletog"><span class="lbl">GLYPH STYLE</span>
    <button id="st-carve" class="stbtn on">SHIP-CARVE</button>
    <button id="st-trace" class="stbtn">LIGHT-TRACE</button>
    <button id="st-current" class="stbtn">CURRENT HAND</button></div>
  <div class="railfoot">one proto · two fleets · four mouths<br>
  YOU CANNOT SPEAK WITHOUT<br>CONJUGATING THE TRUTH</div>
</aside>
<main>
  <section id="view"></section>
  <footer class="foot">generated by <b>odylang</b> from the six codices in
  docs/ — every form on this page is derived, not typed. The CLI speaks the
  same data: <span class="cmd">odylang phrase 40</span> · talk to the
  language and hear it: <span class="cmd">odylang serve</span> (the
  translator chat) or open <b>examples/translator.html</b></footer>
</main>
</div>
"""

_CSS = """
*{box-sizing:border-box;margin:0}
:root{
  --bg:#08070a; --panel:#0e0b10; --panel2:#131017;
  --ink:#d8d2c8; --dim:#8c8a82; --faint:#565360;
  --gold:#f5d76e; --red:#e8362a; --blue:#6fa8ff; --green:#7ec885;
  --line:rgba(232,54,42,.22); --goldline:rgba(245,215,110,.25);
  --mono:ui-monospace,'Cascadia Mono','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace;
}
html{background:var(--bg)}
body{background:var(--bg);color:var(--ink);font-family:var(--mono);
  font-size:14px;line-height:1.6;-webkit-font-smoothing:antialiased}
.shell{display:flex;min-height:100vh;max-width:1280px;margin:0 auto}
.rail{width:218px;flex:none;padding:28px 18px;border-right:1px solid var(--line);
  display:flex;flex-direction:column;gap:26px;position:sticky;top:0;
  align-self:flex-start;height:100vh}
.brand{color:var(--gold);font-size:20px;letter-spacing:.35em;font-weight:700}
.brand .sub{display:block;color:var(--faint);font-size:9px;letter-spacing:.18em;
  margin-top:10px;line-height:1.8;font-weight:400}
#nav{display:flex;flex-direction:column;gap:2px}
#nav button{all:unset;cursor:pointer;padding:7px 10px;font-family:var(--mono);
  font-size:11px;letter-spacing:.22em;color:var(--dim);border-left:2px solid transparent}
#nav button:hover{color:var(--ink)}
#nav button:focus-visible{outline:1px solid var(--gold);outline-offset:2px}
#nav button.on{color:var(--gold);border-left-color:var(--red)}
.styletog{display:flex;flex-direction:column;gap:6px}
.styletog .lbl{color:var(--faint);font-size:9px;letter-spacing:.25em}
.stbtn{all:unset;cursor:pointer;font-family:var(--mono);font-size:10px;
  letter-spacing:.2em;padding:4px 10px;border:1px solid var(--goldline);color:var(--dim)}
.stbtn.on{color:var(--bg);background:var(--gold);border-color:var(--gold)}
.stbtn:focus-visible{outline:1px solid var(--gold);outline-offset:2px}
.pgcard{background:#0E1218;border:1px solid rgba(232,227,214,0.13);border-radius:3px;
  padding:24px 26px;display:flex;flex-direction:column;gap:12px}
.pgcard .rowhead{display:flex;align-items:center;gap:12px}
.pgchip{font-size:12px;font-weight:600;letter-spacing:.08em;color:#07090C;
  background:#7FB4C0;border-radius:2px;padding:2px 8px}
.pgmeta{font-size:11px;letter-spacing:.16em;color:#7FB4C0}
.pgcard h4{margin:0;font-size:20px;letter-spacing:-.01em;color:#E8E3D6;
  font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.pgstory{margin:0;font-size:13px;line-height:1.6;color:#8B93A0;
  font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.pgpaper{background:#EDE8DC;border:1px solid rgba(34,38,43,0.3);border-radius:2px;
  padding:28px 28px 20px;display:flex;flex-direction:column;gap:16px}
.pgpaper .phead{display:flex;justify-content:space-between;font-size:10px;
  letter-spacing:.2em;color:#6B7078;border-bottom:1px solid rgba(34,38,43,0.25);
  padding-bottom:8px}
.pgpaper .pfig{display:flex;justify-content:center;overflow-x:auto}
.pgpaper .pcol{border-top:1px solid rgba(34,38,43,0.25);padding-top:8px;
  font-size:9.5px;letter-spacing:.14em;color:#6B7078}
.pgctl{display:flex;gap:18px;align-items:center;flex-wrap:wrap;color:var(--dim);font-size:11px}
.pgctl input[type=number]{width:64px;background:var(--bg);border:1px solid var(--goldline);
  color:var(--ink);font-family:var(--mono);padding:4px 8px}
.pgctl input[type=range]{accent-color:#7FB4C0}
.railfoot{margin-top:auto;color:var(--faint);font-size:9px;letter-spacing:.15em;line-height:2}
main{flex:1;min-width:0;padding:28px 30px 60px}
.frame{position:relative;background:var(--panel);padding:26px 28px;
  border:1px solid var(--line)}
.frame::before,.frame::after{content:"";position:absolute;width:14px;height:14px;pointer-events:none}
.frame::before{top:-1px;left:-1px;border-top:2px solid var(--gold);border-left:2px solid var(--gold)}
.frame::after{bottom:-1px;right:-1px;border-bottom:2px solid var(--gold);border-right:2px solid var(--gold)}
.hero h1{color:var(--gold);font-size:clamp(24px,4vw,40px);letter-spacing:.12em;
  line-height:1.25;margin:10px 0 12px;text-wrap:balance}
.eyebrow{color:var(--red);font-size:10px;letter-spacing:.3em}
.lede{color:var(--dim);max-width:62ch;margin-bottom:20px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}
.chip{all:unset;cursor:pointer;font-family:var(--mono);font-size:11px;
  padding:4px 12px;border:1px solid var(--goldline);color:var(--dim);letter-spacing:.08em}
.chip:hover{color:var(--ink);border-color:var(--gold)}
.chip:focus-visible{outline:1px solid var(--gold);outline-offset:2px}
.chip.on{color:var(--bg);background:var(--gold);border-color:var(--gold)}
select.chip{max-width:100%;background:var(--bg)}
.mouths{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.mouth{all:unset;cursor:pointer;background:var(--panel2);padding:12px 14px;
  border:1px solid transparent;display:block}
.mouth:hover{border-color:var(--goldline)}
.mouth:focus-visible{outline:1px solid var(--gold)}
.mouth.on{border-color:var(--red)}
.mouth .lang{display:block;font-size:9px;letter-spacing:.25em;color:var(--faint)}
.mouth .form{display:block;font-size:22px;color:var(--gold);margin:4px 0 2px}
.mouth.nub .form{color:var(--blue)}
.mouth .where{display:block;font-size:9px;color:var(--dim);letter-spacing:.05em}
.trace{margin-top:14px;background:var(--bg);border:1px solid var(--line);
  padding:14px 16px;color:var(--dim);font-size:12px;overflow-x:auto;white-space:pre}
.trace b{color:var(--gold)}
section#view{margin-top:34px;display:flex;flex-direction:column;gap:26px}
h2.sec{color:var(--gold);font-size:16px;letter-spacing:.3em;border-bottom:1px solid var(--line);
  padding-bottom:8px}
h3.sub{color:var(--ink);font-size:12px;letter-spacing:.25em;margin-bottom:10px}
h3.sub .n{color:var(--red)}
.panel{background:var(--panel);border:1px solid var(--line);padding:18px 20px}
.tablewrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:12.5px;font-variant-numeric:tabular-nums}
th{color:var(--faint);text-align:left;font-weight:400;letter-spacing:.15em;
  font-size:10px;padding:6px 14px 6px 0;border-bottom:1px solid var(--line)}
td{padding:6px 14px 6px 0;border-bottom:1px solid rgba(232,54,42,.08);vertical-align:top}
td.f{color:var(--gold);white-space:nowrap}
td.i{color:var(--dim)}
td.p{color:var(--blue);white-space:nowrap}
tr.hit td{background:rgba(245,215,110,.04)}
tr.exp{cursor:pointer}
tr.exp:hover td{background:rgba(245,215,110,.06)}
.search{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;align-items:center}
.search input{background:var(--bg);border:1px solid var(--goldline);color:var(--ink);
  font-family:var(--mono);font-size:13px;padding:7px 12px;width:min(340px,100%)}
.search input:focus-visible{outline:1px solid var(--gold)}
.count{color:var(--faint);font-size:11px}
.pline{border:1px solid var(--line);background:var(--panel);padding:16px 18px;position:relative}
.pline.star{border-color:rgba(232,54,42,.5)}
.pline .num{position:absolute;top:14px;right:16px;color:var(--faint);font-size:11px}
.pline.call .num{color:var(--blue)} .pline.resp .num{color:var(--green)}
.pline.star .num{color:var(--red)}
.badge{font-size:9px;letter-spacing:.2em;padding:1px 7px;border:1px solid;margin-left:8px}
.badge.call{color:var(--blue)} .badge.resp{color:var(--green)} .badge.star{color:var(--red)}
.su{color:var(--gold);font-size:19px;margin-bottom:2px}
.ipa{color:var(--dim);font-size:12px}
.gl{color:var(--blue);font-size:12px}
.tr{color:var(--ink);margin-top:6px}
.use{color:var(--dim);font-size:12px;margin-top:6px;max-width:70ch}
.beats{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px;align-items:center}
.beat{font-size:11px;padding:2px 8px;border:1px solid var(--goldline);color:var(--dim)}
.beat.hi{background:var(--gold);color:var(--bg);border-color:var(--gold)}
.beat.gap{background:var(--bg);color:var(--red);border-color:var(--red);min-width:26px;text-align:center}
.beat.sp{border:none;padding:0 2px;color:var(--faint)}
.play{all:unset;cursor:pointer;color:var(--red);border:1px solid var(--red);
  font-size:10px;letter-spacing:.15em;padding:2px 10px;font-family:var(--mono)}
.play:hover{background:var(--red);color:var(--bg)}
.play:focus-visible{outline:1px solid var(--gold);outline-offset:2px}
.navc{margin-top:12px;overflow-x:auto}
.hand{all:unset;cursor:pointer;font-size:9px;letter-spacing:.2em;color:var(--faint);
  border:1px solid var(--goldline);padding:2px 8px;margin-right:6px;font-family:var(--mono)}
.hand.on{color:var(--bg);background:var(--gold)}
.hand:focus-visible{outline:1px solid var(--gold)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px}
.card{background:var(--panel2);border:1px solid var(--line);padding:14px 16px}
.card h4{color:var(--gold);font-size:12px;letter-spacing:.2em;margin-bottom:6px}
.card p{color:var(--dim);font-size:12px}
.card .big{font-size:20px;color:var(--gold)}
.textline{margin-bottom:14px}
.textline .disp{color:var(--gold);font-size:16px}
.textline.sw .disp{color:var(--red)}
.textline .lang{font-size:9px;color:var(--red);letter-spacing:.2em;margin-left:10px}
.comm{color:var(--dim);font-size:12px;border-left:2px solid var(--line);
  padding-left:14px;max-width:70ch}
.gcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px}
.gcard{background:var(--panel2);border:1px solid var(--line);padding:10px 8px;text-align:center}
.gcard.sp{border-color:rgba(232,54,42,.5)}
.gname{color:var(--gold);font-size:13px;margin-top:4px}
.gsub{color:var(--faint);font-size:9px;line-height:1.5}
.writer input{background:var(--bg);border:1px solid var(--goldline);color:var(--gold);
  font-family:var(--mono);font-size:16px;padding:9px 12px;width:100%}
.writer input:focus-visible{outline:1px solid var(--gold)}
.writer .out{margin-top:14px;min-height:90px;overflow-x:auto}
.hint{color:var(--faint);font-size:10px;letter-spacing:.05em;margin-top:8px}
.foot{margin-top:44px;color:var(--faint);font-size:11px;border-top:1px solid var(--line);
  padding-top:14px}
.foot b{color:var(--gold);font-weight:400}
.cmd{color:var(--green)}
details{border:1px solid var(--line);background:var(--panel2)}
details summary{cursor:pointer;padding:8px 14px;color:var(--dim);font-size:11px;
  letter-spacing:.15em;list-style:none}
details summary:hover{color:var(--ink)}
details[open] summary{color:var(--gold);border-bottom:1px solid var(--line)}
details .inner{padding:12px 14px}
@media (max-width:900px){
  .shell{flex-direction:column}
  .rail{position:static;width:100%;height:auto;border-right:none;
    border-bottom:1px solid var(--line);gap:14px;padding:18px}
  #nav{flex-direction:row;flex-wrap:wrap}
  #nav button{border-left:none;border-bottom:2px solid transparent}
  #nav button.on{border-bottom-color:var(--red)}
  .railfoot{display:none}
  main{padding:20px 16px 50px}
}
@media (prefers-reduced-motion:no-preference){
  .mouth,.chip,#nav button{transition:color .15s,border-color .15s,background .15s}
}
"""

_JS = r"""
window.onerror = function(msg){
  var b = document.createElement("div");
  b.style.cssText = "position:fixed;left:0;right:0;bottom:0;background:#e8362a;"+
    "color:#08070a;font:12px monospace;padding:6px 12px;z-index:99";
  b.textContent = "codex error: " + msg;
  document.body.appendChild(b);
};
const D = window.ODY;
const esc = s => String(s === null || s === undefined ? "" : s).replace(/[&<>"]/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

/* ---------- Navcher renderer (geometry embedded from odylang.navcher) --- */
const SIGIL = {"@T":"mT","@T-":"mTm","@T+":"mTp","@Ts":"mTs","@F":"mF",
               "=ka":"aka","=mi":"ami","=zu":"azu","|":"gap","?":"q"};
/* two display hands over the same canonical geometry (docs/03):
   ship-carve — the stencil cut (7-unit square strokes, miter joints);
   light-trace — the same letters as a HUD draws them: glow underlay,
   hairline core, node points where the cuts would meet. */
let GSTYLE = "carve";
function strokeAttrs(color){
  return GSTYLE==="carve"
    ? `fill="none" stroke="${color}" stroke-width="7" stroke-linecap="square" stroke-linejoin="miter"`
    : `fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"`;
}
function glowAttrs(color){
  return `fill="none" stroke="${color}" stroke-width="9" stroke-linecap="round"`+
         ` stroke-linejoin="round" opacity="0.16"`;
}
function polyMarkup(pts,color){
  const c=[]; for(let i=0;i<pts.length;i+=2) c.push(pts[i]+","+pts[i+1]);
  let out="";
  if(GSTYLE==="trace") out+=`<polyline points="${c.join(" ")}" ${glowAttrs(color)}/>`;
  out+=`<polyline points="${c.join(" ")}" ${strokeAttrs(color)}/>`;
  if(GSTYLE==="trace")
    for(let i=0;i<pts.length;i+=2)
      out+=`<circle cx="${pts[i]}" cy="${pts[i+1]}" r="3" fill="${color}"/>`;
  return out;
}
function glyphMarkup(key,x,scale,color,long){
  const g = D.script.glyphs[key]; if(!g) return {m:"",w:0};
  let out = `<g transform="translate(${x},0) scale(${scale})">`;
  for(const pts of g.strokes) out += polyMarkup(pts,color);
  for(const d of g.paths){
    if(GSTYLE==="trace") out += `<path d="${d}" ${glowAttrs(color)}/>`;
    out += `<path d="${d}" ${strokeAttrs(color)}/>`;
  }
  for(const d of g.fills){
    if(GSTYLE==="trace") out += `<path d="${d}" fill="${color}" opacity="0.18" transform="translate(-2,-2) scale(1.02)"/>`;
    out += `<path d="${d}" fill="${color}"/>`;
  }
  if(long){
    const L=D.script.longbar;
    out += polyMarkup([L[0],L[1],L[2],L[3]],color);
  }
  return {m: out+"</g>", w: g.w*scale};
}
function wordSvg(tokens,scale,color){
  let x=6, body="";
  for(const t of tokens){
    if(t===" "){ x+=100*scale; continue; }
    let key=t, long=false;
    if(SIGIL[t]) key=SIGIL[t];
    else if(t.endsWith(":")){ key=t.slice(0,-1); long=true; }
    const r=glyphMarkup(key,x,scale,color,long);
    body+=r.m; x+=r.w;
  }
  const h=Math.ceil(150*scale)+8;
  return `<svg viewBox="0 0 ${Math.ceil(x+6)} ${Math.ceil(140*scale)+8}"`+
         ` width="${Math.ceil(x+6)}" height="${h}" role="img">`+body+`</svg>`;
}
function stripSvg(tokens,scale,color){
  return GSTYLE==="current" ? CH.lineSvg(tokens) : wordSvg(tokens,scale,color);
}
/* careful-hand tokenizer for the live writer (mirror of navcher.tokens_careful) */
function tokenizeCareful(text){
  const out=[]; const s=text.toLowerCase();
  const macron={"ā":"a","ē":"e","ī":"i","ō":"o","ū":"u"};
  const spacedCase=["ol","eth","en"];
  let i=0;
  while(i<s.length){
    const c=s[i];
    if(c===" "){ out.push(" "); i++; continue; }
    if(c==="-"){
      const rest=s.slice(i+1).split(/[^a-zāēīōū]/)[0];
      out.push(spacedCase.includes(rest) ? " " : null); i++;
      if(out[out.length-1]===null) out.pop();
      continue;
    }
    if(c==="="){ i++; continue; }
    const two=s.slice(i,i+2);
    if(two==="ch"||two==="sh"){ out.push(two); i+=2; continue; }
    if(two==="th"){ out.push("t","h"); i+=2; continue; }
    if(c==="x"){ out.push("k","s"); i++; continue; }
    if(macron[c]){ out.push(macron[c]+":"); i++; continue; }
    if(D.script.glyphs[c]) out.push(c);
    i++;
  }
  return out;
}

/* ---------- rhythm player (docs/04: stressed = higher & longer) ---------- */
let AC=null;
function playSyls(syl){
  AC = AC || new (window.AudioContext||window.webkitAudioContext)();
  let t=AC.currentTime+0.05;
  for(const tok of syl){
    if(tok==="/"){ t+=0.09; continue; }
    if(tok==="|"){ t+=0.5; continue; }
    const hi=/[A-Z]/.test(tok), long=tok.includes(":");
    const dur=(hi?0.24:0.13)+(long?0.15:0);
    const o=AC.createOscillator(), g=AC.createGain();
    o.type="triangle"; o.frequency.value=hi?520:340;
    g.gain.setValueAtTime(0.0001,t);
    g.gain.linearRampToValueAtTime(0.22,t+0.02);
    g.gain.exponentialRampToValueAtTime(0.0001,t+dur);
    o.connect(g); g.connect(AC.destination);
    o.start(t); o.stop(t+dur+0.02);
    t+=dur+0.055;
  }
}

/* ---------- the shibboleth hero (rendered inside the FAMILY tab) -------- */
const HERO_HTML =
  '<header class="hero frame">'+
  '<div class="eyebrow">THE PALATAL SHIBBOLETH</div>'+
  '<h1>ASK A STRANGER<br>TO NAME THE SEAM</h1>'+
  '<p class="lede">One proto-tongue, a conquered universe of daughters. '+
  'What each mouth did to old *k and *g files its birth certificate — '+
  'pick a proto-word, then a mouth, and watch the sound laws run.</p>'+
  '<div id="shib-chips" class="chips"></div>'+
  '<div id="shib-row" class="mouths"></div>'+
  '<pre id="shib-trace" class="trace" hidden></pre>'+
  '</header>';
const heroState={proto:D.family.shibboleth[0], mouth:null};
function findWord(p){ return D.family.words.find(w=>w.proto===p); }
function renderHero(){
  const chips=document.getElementById("shib-chips");
  if(!chips) return;
  chips.innerHTML = D.family.shibboleth.map(p=>
    `<button class="chip${p===heroState.proto?" on":""}" data-p="${esc(p)}">${esc(p)}</button>`
  ).join("") + `<select id="shib-more" class="chip" aria-label="more roots">`+
    `<option value="">more roots…</option>`+
    D.family.words.filter(w=>!D.family.shibboleth.includes(w.proto))
      .map(w=>`<option value="${esc(w.proto)}">${esc(w.proto)} — ${esc(w.gloss.split(";")[0])}</option>`).join("")+
    `</select>`;
  const w=findWord(heroState.proto);
  const row=document.getElementById("shib-row");
  row.innerHTML = Object.entries(w.forms).map(([lang,form])=>{
    const L=D.langs[lang];
    return `<button class="mouth${lang==="nubhel"?" nub":""}${heroState.mouth===lang?" on":""}" data-l="${lang}">
      <span class="lang">${esc(L.name)}</span>
      <span class="form">${esc(form)}</span>
      <span class="where">${esc(L.where)}</span></button>`;
  }).join("");
  const pre=document.getElementById("shib-trace");
  if(heroState.mouth && w.traces[heroState.mouth]){
    pre.hidden=false; pre.textContent=w.traces[heroState.mouth];
  } else if(heroState.mouth==="old_pelagic"){
    pre.hidden=false;
    pre.textContent=w.proto+"\n  (the ancestor: no changes — the liturgy and the Wolori keep it)\n  = "+w.forms.old_pelagic;
  } else { pre.hidden=true; }
  chips.querySelectorAll("button.chip").forEach(b=>b.onclick=()=>{
    heroState.proto=b.dataset.p; heroState.mouth=null; renderHero();
  });
  const more=document.getElementById("shib-more");
  more.onchange=()=>{ if(more.value){heroState.proto=more.value;heroState.mouth=null;renderHero();} };
  row.querySelectorAll(".mouth").forEach(b=>b.onclick=()=>{
    heroState.mouth = heroState.mouth===b.dataset.l ? null : b.dataset.l; renderHero();
  });
}

/* ---------- section renderers ------------------------------------------- */
function sec(title){ return `<h2 class="sec">${title}</h2>`; }

function lexTable(rows,id){
  return `<div class="tablewrap"><table id="${id}"><thead><tr>
    <th>FORM</th><th>IPA</th><th>GLOSS</th><th>DERIVATION</th><th>DOMAIN</th>
    </tr></thead><tbody>`+
    rows.map((e,i)=>`<tr class="${e.trace?"exp":""}" data-i="${i}" data-id="${id}">
      <td class="f">${esc(e.form)}</td><td class="i">${e.ipa?"["+esc(e.ipa)+"]":""}</td>
      <td>${esc(e.gloss)}</td><td class="i">${esc(e.etym)}</td>
      <td class="i">${esc(e.domain)}</td></tr>`).join("")+
    `</tbody></table></div>`;
}
function bindLex(container,rows,id){
  container.querySelectorAll(`tr[data-id="${id}"].exp`).forEach(tr=>{
    tr.onclick=()=>{
      const next=tr.nextElementSibling;
      if(next && next.classList.contains("tracerow")){ next.remove(); return; }
      const e=rows[+tr.dataset.i];
      const row=document.createElement("tr"); row.className="tracerow";
      row.innerHTML=`<td colspan="5"><pre class="trace">${esc(e.trace)}</pre></td>`;
      tr.after(row);
    };
  });
}
function bindSearch(container,input,rows,id,countEl){
  input.oninput=()=>{
    const q=input.value.toLowerCase(); let n=0;
    container.querySelectorAll(`tr[data-id="${id}"]`).forEach(tr=>{
      const e=rows[+tr.dataset.i];
      const hit=!q || (e.form+" "+e.gloss+" "+e.etym+" "+e.domain).toLowerCase().includes(q);
      tr.style.display=hit?"":"none"; if(hit)n++;
      const next=tr.nextElementSibling;
      if(next&&next.classList.contains("tracerow")) next.style.display=hit?"":"none";
    });
    countEl.textContent=n+" entries";
  };
}

function rSuchel(v){
  const s=D.suchel;
  v.innerHTML = sec("SŪCHEL — THE CROSSING-SPEECH")+
  `<div class="grid2">
    <div class="card"><h4>THE FIVE VERIDICAL MOODS · ΛL</h4>
      <div class="tablewrap"><table><thead><tr><th>ΛL</th><th>SUFFIX</th><th>MEANING</th></tr></thead><tbody>`+
      s.moods.map(m=>`<tr><td class="f">${esc(m.lam)}</td><td class="p">${esc(m.suffix)}</td><td class="i">${esc(m.meaning)}</td></tr>`).join("")+
      `</tbody></table></div></div>
    <div class="card"><h4>THE THREE TEMPORAL ANCHORS</h4>
      <div class="tablewrap"><table><thead><tr><th>CLITIC</th><th>FROM</th><th>ANCHOR</th></tr></thead><tbody>`+
      s.anchors.map(a=>`<tr><td class="f">${esc(a.clitic)}</td><td class="p">${esc(a.src)}</td><td class="i">${esc(a.meaning)}</td></tr>`).join("")+
      `</tbody></table></div></div>
  </div>
  <div class="panel"><h3 class="sub">THE STRESS ALGORITHM <span class="n">— the mood carries the beat</span></h3>
    <div class="grid2">`+
    s.stress.map(r=>`<div class="card"><h4>${esc(r.rule)}</h4><p>${esc(r.text)}</p>
      <p style="color:var(--gold);margin-top:6px">${esc(r.ex)}</p></div>`).join("")+
    `</div></div>
  <div class="panel"><h3 class="sub">LEXICON</h3>
    <div class="search"><input id="su-q" type="search" placeholder="search form · gloss · etymology…"
      aria-label="search the Sūchel lexicon"><span class="count" id="su-count">${s.lex.length} entries</span></div>
    ${lexTable(s.lex,"sulex")}
    <p class="hint">click a derived row to replay its sound changes</p></div>
  <div class="panel"><h3 class="sub">VOCABULARY SUPPLEMENT <span class="n">— coined, engine-derived (REV 1.2)</span></h3>
    <p class="use" style="margin:0 0 12px">The plain furniture of a life — mother,
    water, sleep, knife, cold — coined as new Old Pelagic roots and run through
    the same seven changes as everything else. Coin once, inherit five times:
    each of these roots also exists in Nubhel, Rudgar, Sel and Beltsel (see the
    FAMILY tab, marked +).</p>
    <div class="search"><input id="vc-q" type="search" placeholder="search…"
      aria-label="search the vocabulary supplement"><span class="count" id="vc-count">${s.vocab.length} entries</span></div>
    ${lexTable(s.vocab,"suvocab")}
    <p class="hint">click a row to replay its derivation</p></div>`;
  bindLex(v,s.lex,"sulex");
  bindSearch(v,v.querySelector("#su-q"),s.lex,"sulex",v.querySelector("#su-count"));
  bindLex(v,s.vocab,"suvocab");
  bindSearch(v,v.querySelector("#vc-q"),s.vocab,"suvocab",v.querySelector("#vc-count"));
}

function beatChips(syl){
  return `<span class="beats">`+syl.map(t=>{
    if(t==="/") return `<span class="beat sp">/</span>`;
    if(t==="|") return `<span class="beat gap">▮</span>`;
    return `<span class="beat${/[A-Z]/.test(t)?" hi":""}">${esc(t)}</span>`;
  }).join("")+`</span>`;
}
function rPhrase(v){
  const P=D.phrasebook;
  let html=sec("PHRASEBOOK — 41 LINES, READY TO LETTER");
  for(const [k,name] of Object.entries(P.sections)){
    html+=`<h3 class="sub"><span class="n">${k}</span> · ${esc(name)}</h3>`;
    html+=P.lines.filter(l=>l.sec===k).map(l=>{
      const cls=["pline",l.role,l.star?"star":""].join(" ");
      return `<div class="${cls}" data-n="${l.n}">
        <span class="num">${String(l.n).padStart(2,"0")}
          ${l.role?`<span class="badge ${l.role}">${l.role.toUpperCase()}</span>`:""}
          ${l.star?`<span class="badge star">◆</span>`:""}</span>
        <div class="su">${esc(l.text)}</div>
        <div class="ipa">${esc(l.ipa)}</div>
        <div class="gl">${esc(l.gloss)}</div>
        <div class="tr">“${esc(l.trans)}”</div>
        <div class="use">${esc(l.note)}</div>
        <div class="beats-row">${beatChips(l.syl)}
          <button class="play" data-n="${l.n}">▶ RHYTHM</button></div>
        <div class="navc" id="navc-${l.n}"></div>
        <div>${l.tokB?`<button class="hand on" data-n="${l.n}" data-h="C">CAREFUL</button>
                       <button class="hand" data-n="${l.n}" data-h="B">BRIDGE</button>`:""}</div>
      </div>`;
    }).join("");
  }
  html+=`<div class="panel"><h3 class="sub">FOR THE LETTERER</h3><div class="grid2">`+
    Object.entries(P.lettering).map(([k,t])=>
      `<div class="card"><h4>${esc(k)}</h4><p>${esc(t)}</p></div>`).join("")+
    `</div></div>`;
  v.innerHTML=html;
  for(const l of P.lines){
    const box=v.querySelector(`#navc-${l.n}`);
    if(box) box.innerHTML=stripSvg(l.tokC,0.28,l.star?"#e8362a":"#f5d76e");
  }
  v.querySelectorAll(".play").forEach(b=>b.onclick=()=>{
    const l=P.lines.find(x=>x.n===+b.dataset.n); playSyls(l.syl);
  });
  v.querySelectorAll(".hand").forEach(b=>b.onclick=()=>{
    const l=P.lines.find(x=>x.n===+b.dataset.n);
    const box=v.querySelector(`#navc-${l.n}`);
    const bridge=b.dataset.h==="B";
    box.innerHTML=stripSvg(bridge?l.tokB:l.tokC,0.28,
      bridge?"#6fa8ff":(l.star?"#e8362a":"#f5d76e"));
    b.parentElement.querySelectorAll(".hand").forEach(x=>x.classList.toggle("on",x===b));
  });
}

function quoted(tr){
  return tr.startsWith('"') ? esc(tr) : "“"+esc(tr)+"”";
}
function textBlock(t){
  return `<div class="panel"><h3 class="sub">${esc(t.title.toUpperCase())}</h3>`+
    t.lines.map(ln=>`<div class="textline${ln.sw?" sw":""}">
      <span class="disp">${esc(ln.disp)}</span>${ln.tag?`<span class="lang">[${esc(ln.tag)}]</span>`:""}
      <div class="gl">${esc(ln.gloss)}</div>
      <div class="tr">${quoted(ln.trans)}</div></div>`).join("")+
    `<p class="comm">${esc(t.comm)}</p></div>`;
}
function rTexts(v){
  let html=sec("TEXTS — THE LANGUAGE BREATHING");
  html+=D.texts.suchel.map(textBlock).join("");
  html+=`<h3 class="sub">THE SHOWPIECE <span class="n">— Κ5 AS CONJUGATION</span></h3><div class="grid2">`+
    D.texts.k5.map(s=>`<div class="card">
      <h4>${esc(s.title.toUpperCase())}</h4>
      <p style="color:var(--faint)">${esc(s.attr)}</p>
      <p class="big" style="margin:8px 0 2px">${esc(s.text)}</p>
      <p class="gl">${esc(s.gloss)}</p>
      <p style="color:var(--ink);margin-top:6px">“${esc(s.trans)}”</p>
      <p style="margin-top:8px">${esc(s.comm)}</p></div>`).join("")+`</div>`;
  html+=`<h3 class="sub">NUBHEL TEXTS <span class="n">— incl. the code-switch</span></h3>`;
  html+=D.texts.nubhel.map(t=>{
    t=JSON.parse(JSON.stringify(t));
    t.lines.forEach(ln=>{ if(ln.lang==="Sūchel"){ln.sw=true; ln.tag="SŪCHEL";} });
    return textBlock(t);
  }).join("");
  v.innerHTML=html;
}

function rNubhel(v){
  const N=D.nubhel;
  const fleets=Object.values(N.fleets);
  v.innerHTML = sec("NUBHEL — THE DEEP-SPEECH")+
  `<div class="grid2">`+
  fleets.map(f=>`<div class="card"><h4>${esc(f.name.toUpperCase())}</h4>
    <p>${esc(f.orientation)} · prestige: ${esc(f.prestige)}</p>
    <p style="margin-top:4px">wound: ${esc(f.wound)}</p>
    <p style="margin-top:4px;color:var(--red)">${esc(f.sneer)}</p></div>`).join("")+
  `</div>
  <div class="grid2">
    <div class="card"><h4>THREE MOODS — AND A HOLE</h4>
      <div class="tablewrap"><table><tbody>`+
      N.moods.map(m=>`<tr><td class="f">-${esc(m.form)}</td><td class="i">${esc(m.gloss)}</td></tr>`).join("")+
      `<tr><td class="f" style="color:var(--red)">T•</td><td class="i" style="color:var(--red)">no reflex — a diver narrating a crossing must borrow Sūchel</td></tr>
      </tbody></table></div></div>
    <div class="card"><h4>ANCHORS · THE DEBT</h4>
      <div class="tablewrap"><table><tbody>`+
      N.anchors.map(a=>`<tr><td class="f">=${esc(a.form)}</td><td class="i">${esc(a.gloss)}</td></tr>`).join("")+
      `</tbody></table></div>
      <p style="margin-top:8px;color:var(--dim);font-size:12px">formal =nu appends the
      offset: <span style="color:var(--gold)">en ōl-t-ó=nu, +mek-dok</span> — forty owed.
      Divers sign letters <span style="color:var(--gold)">Mora, +212</span>.</p></div>
    <div class="card"><h4>FIVE DEGREES OF DEPTH</h4>
      <div class="tablewrap"><table><tbody>`+
      N.dirs.map(d=>`<tr><td class="f">${esc(d.word)}</td><td class="p">${esc(d.proto)}</td><td class="i">${esc(d.meaning)}</td></tr>`).join("")+
      `</tbody></table></div></div>
    <div class="card"><h4>SEVEN CHANGES — D-3 BEFORE D-1</h4>
      <div class="tablewrap"><table><tbody>`+
      N.changes.map(c=>`<tr><td class="f">${esc(c.id)}</td><td class="i">${esc(c.summary)}</td></tr>`).join("")+
      `</tbody></table></div></div>
  </div>
  <div class="panel"><h3 class="sub">ACROSS THE COGNATE GAP <span class="n">— false friends</span></h3>
    <div class="tablewrap"><table><thead><tr><th>PROTO</th><th>SŪCHEL</th><th>NUBHEL</th><th>NOTE</th></tr></thead><tbody>`+
    N.ff.map(f=>`<tr><td class="p">${esc(f.proto)}</td><td class="f">${esc(f.su)}</td>
      <td class="f" style="color:var(--blue)">${esc(f.nu)}</td><td class="i">${esc(f.note)}</td></tr>`).join("")+
    `</tbody></table></div></div>
  <div class="panel"><h3 class="sub">WORKING LEXICON</h3>
    <div class="search"><input id="nb-q" type="search" placeholder="search…"
      aria-label="search the Nubhel lexicon"><span class="count" id="nb-count">${N.lex.length} entries</span></div>
    ${lexTable(N.lex,"nblex")}</div>`;
  bindLex(v,N.lex,"nblex");
  bindSearch(v,v.querySelector("#nb-q"),N.lex,"nblex",v.querySelector("#nb-count"));
}

function rSisters(v){
  let html=sec("THE SISTERS — ONE PROTO, FOUR MOUTHS");
  html+=D.sisters.map(s=>`<div class="panel">
    <h3 class="sub">${esc(s.name)} <span class="n">· ${esc(s.where)}</span></h3>
    <p class="use" style="margin:0 0 12px">${esc(s.tagline)}</p>
    <details><summary>SOUND CHANGES · ${s.changes.length}</summary><div class="inner">
      <div class="tablewrap"><table><tbody>`+
      s.changes.map(c=>`<tr><td class="f">${esc(c.id)}</td><td class="i">${esc(c.summary)}</td></tr>`).join("")+
      `</tbody></table></div></div></details>
    <details open><summary>TWENTY PLACE NAMES</summary><div class="inner">
      <div class="tablewrap"><table><thead><tr><th>NAME</th><th>PROTO</th><th>GLOSS</th><th>WHAT IT IS</th></tr></thead><tbody>`+
      s.places.map(p=>`<tr><td class="f">${esc(p.name)}</td><td class="p">${esc(p.proto)}</td>
        <td>${esc(p.gloss)}</td><td class="i">${esc(p.what)}</td></tr>`).join("")+
      `</tbody></table></div></div></details>
    <details><summary>COGNATE LINE</summary><div class="inner">
      <div class="tablewrap"><table><tbody>`+
      s.cognates.map(c=>`<tr><td class="f">${esc(c.form)}</td><td class="p">${esc(c.proto)}</td><td class="i">${esc(c.note)}</td></tr>`).join("")+
      `</tbody></table></div></div></details>
  </div>`).join("");
  const cities=D.family.cities.map(c=>
    `<span style="color:var(--gold)">${esc(c[2])}</span> <span class="count">(${esc(c[0])})</span>`).join(" · ");
  html+=`<div class="panel"><h3 class="sub">THE THREE TRUTH-STATIONS</h3>
    <p class="use">${cities} — the same name through three mouths; pilgrims collect
    all three pronunciations, customs officers use them as a voice-test.</p></div>`;
  const L=D.lorkel;
  html+=`<div class="panel"><h3 class="sub">LORKEL — THE ANCESTOR AT WORK <span class="n">— the Irrationals</span></h3>
    <div class="grid2">`+
    L.custodians.map(c=>`<div class="card"><h4>CUSTODIAN ${esc(c.number)} · ${esc(c.name.toUpperCase())}</h4>
      <p style="color:var(--gold)">${esc(c.register)}</p><p>${esc(c.description)}</p></div>`).join("")+
    `</div>
    <div class="tablewrap" style="margin-top:14px"><table>
    <thead><tr><th>LORKEL</th><th>FORMATION</th><th>MEANING</th><th>SŪCHEL REFLEX</th></tr></thead><tbody>`+
    L.terms.map(t=>`<tr><td class="f">${esc(t.form)}</td><td class="p">${esc(t.formation)}</td>
      <td class="i">${esc(t.meaning)}</td><td class="f">${esc(t.reflex)}</td></tr>`).join("")+
    `</tbody></table></div>
    <p class="use" style="margin-top:10px">Notation-names of the zero-tongue:
    <span style="color:var(--gold)">${L.notation.map(esc).join(" · ")}</span> —
    pronounced differently on every world, written identically on all of them.</p></div>`;
  v.innerHTML=html;
}

function rScript(v){
  const S=D.script;
  let html=sec("NAVCHER — THE FLEET SCRIPT")+
  `<div class="grid2">`+
  S.rules.map(r=>`<div class="card"><h4>${esc(r.name)}</h4><p>${esc(r.text)}</p></div>`).join("")+
  `</div>
  <p class="use" style="margin-top:4px">Why the letters look cut rather than drawn:
  Navcher is <b style="color:var(--gold)">featural</b> — the most engineered class of
  script there is (Hangul is Earth's one example): the shapes are phonetic circuit
  diagrams, and every stroke is straight because the fleets stencil them into hull
  plate. SHIP-CARVE is the knife's rendering; LIGHT-TRACE (toggle in the rail) is the
  same letters as a bridge HUD draws them.</p>
  <div class="panel writer"><h3 class="sub">CARVE YOUR OWN <span class="n">— careful hand</span></h3>
    <input id="writer-in" type="text" value="ver ish-ol" spellcheck="false"
      aria-label="text to letter in Navcher">
    <div class="out" id="writer-out"></div>
    <p class="hint">macron vowels ā ē ī ō ū take the held-breath bar · ch sh are single
    letters · case endings -ol/-eth/-en letter spaced, verb seams solid (docs/03)</p></div>`;
  html+=S.chart.map(g=>`<div class="panel"><h3 class="sub">${esc(g.group.toUpperCase())}</h3>
    <div class="gcards">`+
    g.cards.map(c=>`<div class="gcard${c.special?" sp":""}" data-k="${esc(c.key)}" data-long="${c.long?1:0}">
      <div class="g"></div><div class="gname">${esc(c.name)}</div>
      <div class="gsub">${esc(c.sub)}</div></div>`).join("")+
    `</div></div>`).join("");
  v.innerHTML=html;
  v.querySelectorAll(".gcard").forEach(card=>{
    const color=card.classList.contains("sp")?"#e8362a":"#f5d76e";
    const tok=card.dataset.k+(card.dataset.long==="1"?":":"");
    card.querySelector(".g").innerHTML=stripSvg([tok],0.42,color);
  });
  const input=v.querySelector("#writer-in"), out=v.querySelector("#writer-out");
  const draw=()=>{ out.innerHTML=stripSvg(tokenizeCareful(input.value),0.42,"#f5d76e"); };
  input.oninput=draw; draw();
}

function rFamily(v){
  v.innerHTML = HERO_HTML + sec("THE FAMILY — EVERY ROOT, EVERY MOUTH")+
  `<div class="panel"><p class="use" style="margin-bottom:12px">
    The full proto-lexicon run through every daughter's sound laws.
    Open a root for the derivation traces.</p>
    <div class="tablewrap"><table><thead><tr><th>PROTO</th><th>GLOSS</th>`+
    Object.values(D.langs).map(l=>`<th>${esc(l.name)}</th>`).join("")+
    `</tr></thead><tbody>`+
    D.family.words.map((w,i)=>`<tr class="exp" data-i="${i}" data-id="fam">
      <td class="p">${esc(w.proto)}${w.coined?' <span style="color:var(--gold)" title="coined — vocabulary supplement">+</span>':''}</td><td class="i">${esc(w.gloss.split(";")[0])}</td>`+
      Object.keys(D.langs).map(l=>`<td class="f">${esc(w.forms[l]||"—")}</td>`).join("")+
      `</tr>`).join("")+
    `</tbody></table></div>
    <p class="hint">click a row to replay each daughter's derivation</p></div>`;
  renderHero();
  v.querySelectorAll("tr.exp").forEach(tr=>{
    tr.onclick=()=>{
      const next=tr.nextElementSibling;
      if(next&&next.classList.contains("tracerow")){ next.remove(); return; }
      const w=D.family.words[+tr.dataset.i];
      const traces=Object.entries(w.traces).filter(([,t])=>t)
        .map(([l,t])=>D.langs[l].name+"\n"+t).join("\n\n");
      const row=document.createElement("tr"); row.className="tracerow";
      row.innerHTML=`<td colspan="8"><pre class="trace">${esc(traces)}</pre></td>`;
      tr.after(row);
    };
  });
}


/* ---------- The Current Hand (design handoff 07-E) ----------------------
   One unbroken pressured line per word, riding a current.  Pen data comes
   from odylang.currenthand via the payload; the engine below is the
   handoff prototype's own logic (Navcher Page Studies.dc.html), adapted. */
const CH = (function(){
  const G = D.current.glyphs, ARCPEN = D.current.arcpen,
        LEADIN = D.current.leadin, LEADOUT = D.current.leadout;
  const SLANT=0.10, LINEH=152, MAXU=1500;
  const cr1=(a,b,c,d,t)=>{const t2=t*t,t3=t2*t;return 0.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t2+(-a+3*b-3*c+d)*t3);};
  function ribbon(pts,f){
    const n=pts.length; if(n<2) return '';
    const g=i=>pts[i<0?0:(i>n-1?n-1:i)];
    const S=[],SEG=8;
    for(let i=0;i<n-1;i++){
      const p0=g(i-1),p1=g(i),p2=g(i+1),p3=g(i+2);
      const top=(i===n-2)?SEG:SEG-1;
      for(let t=0;t<=top;t++){
        const u=t/SEG;
        S.push([cr1(p0[0],p1[0],p2[0],p3[0],u),cr1(p0[1],p1[1],p2[1],p3[1],u),
                Math.max(0.3,cr1(p0[2],p1[2],p2[2],p3[2],u))*f]);
      }
    }
    const L=[],R=[];
    for(let i=0;i<S.length;i++){
      const a=S[i>0?i-1:0],b=S[i<S.length-1?i+1:S.length-1];
      const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy)||1;
      const nx=-dy/len,ny=dx/len,hw=S[i][2]/2;
      L.push((S[i][0]+nx*hw).toFixed(1)+','+(S[i][1]+ny*hw).toFixed(1));
      R.push((S[i][0]-nx*hw).toFixed(1)+','+(S[i][1]-ny*hw).toFixed(1));
    }
    R.reverse();
    return 'M'+L.join(' L')+' L'+R.join(' L')+' Z';
  }
  const DROPPEN=cx=>[[cx,100,0.8],[cx+1.5,106,5.5],[cx+0.8,113,8],[cx-1,117,3.2]];
  const sxOf=g=>g.sigil?1:(g.vowel?g.w/60:g.w/100);
  const wOf=k=>G[k.charAt(k.length-1)===':'?k.slice(0,-1):k].w;
  const isSig=k=>!!(G[k]&&G[k].sigil);
  function build(keys,o){
    o=o||{};
    const swayA=o.sway!=null?o.sway:0.4, ph=o.swayPhase||0;
    const swayF=x=>swayA*(3.4*Math.sin((x+ph)/56)+1.7*Math.sin((x+ph)/19+2.1));
    const strokes=[]; let s=0,inRun=false,wordStart=0;
    const pushPen=(pen,sx,off,sig,color,s0)=>strokes.push({color:color||'ink',rigid:!!sig,s0:s0||0,
      pts:pen.map(pt=>{
        const x=pt[0],y=pt[1],w=pt[2];
        const S=x*sx+(sig?0:(88-y)*SLANT)+off;
        let Y=y+(sig?0:swayF(S));
        if(o.wordFall&&!sig) Y+=(o.fallRate!=null?o.fallRate:0.14)*Math.max(0,S-wordStart);
        return [S,Y,w];
      })});
    keys.forEach(k=>{
      if(k===' '){
        if(o.spaceCarrier){pushPen([[0,88,4.2],[31,87.2,4.2],[62,88,4.2]],1,s,false);s+=62;return;}
        if(inRun&&!o.noTails)pushPen(LEADOUT,1,s,false); inRun=false; s+=62; return;
      }
      if(isSig(k)){
        if(inRun&&!o.noTails){pushPen(LEADOUT,1,s,false);inRun=false;}
        s+=18;
        const g=G[k],s0=s+30;
        (g.pen||[]).forEach(pn=>pushPen(pn,1,s,true,'ink',s0));
        (g.penAcc||[]).forEach(pn=>pushPen(pn,1,s,true,'acc2',s0));
        (g.penAcc2||[]).forEach(pn=>pushPen(pn,1,s,true,'acc2',s0));
        (g.penSub||[]).forEach(pn=>pushPen(pn,1,s,true,'sub',s0));
        s+=wOf(k)+18; return;
      }
      if(!inRun){wordStart=s;if(!o.noTails)pushPen(LEADIN,1,s,false);inRun=true;}
      const long=k.charAt(k.length-1)===':';
      const g=G[long?k.slice(0,-1):k]; if(!g){return;}
      const sx=sxOf(g);
      (g.pen||[]).forEach(pn=>pushPen(pn,sx,s,false));
      if(long)pushPen(ARCPEN,sx,s,false);
      if(g.dropAt!=null)pushPen(DROPPEN(g.dropAt),1,s,false,'acc');
      s+=wOf(k);
    });
    if(inRun&&!o.noTails)pushPen(LEADOUT,1,s,false);
    return {strokes,total:s};
  }
  const mapStrokes=(th,fn,rigidFn)=>th.strokes.map(st=>({color:st.color,op:st.op,ink:st.ink,
    pts:st.pts.map(p=>{const q=(st.rigid&&rigidFn)?rigidFn(p[0],p[1],st.s0):fn(p[0],p[1]);return [q[0],q[1],p[2]];})}));
  const linear=(s,y)=>[s,y];
  const mul32=a=>()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};
  /* specimen: frequency-faithful, seeded */
  const ONS=[['n',70],['l',60],['v',58],['r',55],['m',52],['t',46],['d',30],['k',30],['sh',26],['s',20],['j',16],['z',10],['p',5],['g',4],['ch',3]];
  const VOWT=[['e',140],['a',110],['u',74],['i',58],['o',53]];
  const CODA=[['n',30],['l',26],['r',18],['d',13],['s',9],['k',8],['m',8]];
  const W={hail1:['v','e','r'],hail2:['i','sh','o','l'],enmai:['e','n','m','a','i'],zukad:['z','u','k','a','d'],jel:['j','e','l'],suchel:['s','u:','ch','e','l'],hau:['h','a','u'],holt:['h','o:','l','t'],ve:['v','e']};
  const PARAS=[[0,1,2],[3,4,5],[6,7,8]];
  function makeSents(rand){
    const wpick=tbl=>{let tot=0;for(const p of tbl)tot+=p[1];let r=rand()*tot;for(const p of tbl){if((r-=p[1])<0)return p[0];}return tbl[0][0];};
    const genWord=()=>{
      const r0=rand(); const nsyl=r0<0.2?1:(r0<0.75?2:3);
      const keys=[];
      for(let i=0;i<nsyl;i++){
        if(i===0&&rand()<0.12)keys.push('h');
        else if(!(i===0&&rand()<0.15))keys.push(wpick(ONS));
        keys.push(wpick(VOWT)+(rand()<0.15?':':''));
        if(rand()<(i===nsyl-1?0.45:0.2))keys.push(wpick(CODA));
      }
      return keys;
    };
    const gen=n=>{const a=[];for(let i=0;i<n;i++)a.push(genWord());return a;};
    const ins=(arr,at,w)=>{arr.splice(at,0,w);return arr;};
    return [
      {words:[W.hail1,W.hail2]},
      {words:ins(gen(4),1,W.enmai),mood:'mT',anchor:'aka'},
      {words:ins(gen(4),2,W.zukad),mood:'mTm',anchor:'ami'},
      {words:ins(gen(3),2,W.jel),mood:'mT'},
      {words:ins(gen(3),1,W.suchel),mood:'mTp',anchor:'aka',q:true},
      {words:gen(4),mood:'mF',anchor:'aka'},
      {words:ins(gen(3),2,W.hau),mood:'mT',anchor:'ami'},
      {words:[W.holt],mood:'mTs',anchor:'azu'},
      {words:[W.ve],mood:'mT',anchor:'ami'}
    ];
  }
  const realize=(S,hand)=>{
    const words=S.words.map(w=>w.slice());
    if(S.mood==='mF')words.unshift(['v','o']);
    if(hand==='careful'){
      const suf=({mT:['a'],mTm:['i','m'],mTp:['u','r'],mTs:['e','sh','e'],mF:['a']})[S.mood]||[];
      const anc=({aka:['k','a'],ami:['m','i'],azu:['z','u']})[S.anchor]||[];
      if(suf.length||anc.length)words[words.length-1]=words[words.length-1].concat(suf,anc);
    }else{
      const tail=[];
      if(S.mood)tail.push(S.mood);
      if(S.anchor)tail.push(S.anchor);
      if(tail.length)words.push(tail);
    }
    if(S.q)words.push(['q']);
    return words;
  };
  const wordUnits=keys=>keys.reduce((a,k)=>a+wOf(k)+(isSig(k)?36:0),0)+(keys.some(k=>!isSig(k))?46:0);
  const flow=(sents,hand,maxU)=>{
    const stream=[];
    PARAS.forEach((para,pi)=>{
      para.forEach(si=>{realize(sents[si],hand).forEach(w=>stream.push(w));});
      if(pi<PARAS.length-1)stream.push(['gap']);
    });
    const lines=[]; let cur=[],u=0;
    stream.forEach(w=>{
      const wu=wordUnits(w);
      if(u>0&&u+62+wu>maxU){lines.push(cur);cur=[];u=0;}
      if(cur.length){cur.push(' ');u+=62;}
      w.forEach(k=>cur.push(k)); u+=wu;
    });
    if(cur.length)lines.push(cur);
    return lines;
  };
  const PAPER={ink:'#24282E',acc:'#33707C',acc2:'#A65B3F',sub:'#8A8478'};
  function fig(strokes,inkW,px){
    let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
    const elems=strokes.map(st=>{
      st.pts.forEach(p=>{x0=Math.min(x0,p[0]-p[2]);y0=Math.min(y0,p[1]-p[2]);
                         x1=Math.max(x1,p[0]+p[2]);y1=Math.max(y1,p[1]+p[2]);});
      const col=st.ink||PAPER[st.color]||PAPER.ink;
      return {d:ribbon(st.pts,inkW),fill:col,op:st.op};
    });
    const pad=20,bw=(x1-x0)+2*pad,bh=(y1-y0)+2*pad,py=px*bh/bw;
    return {vb:(x0-pad).toFixed(0)+' '+(y0-pad).toFixed(0)+' '+bw.toFixed(0)+' '+bh.toFixed(0),
            elems,w:px,h:py};
  }
  const shift=(strokes,dy)=>strokes.forEach(st=>st.pts.forEach(p=>{p[1]+=dy;}));
  function figRecord(sents,inkW){
    const all=[];
    flow(sents,'careful',MAXU).forEach((lineKeys,i)=>{
      all.push({color:'sub',op:0.32,pts:[[-30,88+i*LINEH,1.3],[MAXU/2,88+i*LINEH,1.3],[MAXU+30,88+i*LINEH,1.3]]});
      const m=mapStrokes(build(lineKeys,{sway:0}),linear);
      shift(m,i*LINEH); m.forEach(st=>all.push(st));
    });
    return fig(all,inkW,580);
  }
  function figScrawl(sents,inkW,seed){
    const rnd=mul32(seed*331+7);
    const R2=(a,b)=>a+(b-a)*rnd();
    const all=[],stream=[];
    PARAS.forEach((para,pi)=>{
      para.forEach(si=>realize(sents[si],'bridge').forEach(w=>stream.push(w)));
      if(pi<PARAS.length-1)stream.push(['gap']);
    });
    let x=0,lineY=0,wi=0;
    const strikeAt=7+Math.floor(rnd()*5);
    const place=(w,kw,inkK,strike)=>{
      const sigW=w.every(k=>isSig(k));
      const wu0=wordUnits(w)*kw;
      if(x>0&&x+50+wu0>MAXU){
        if(x+50+wu0<MAXU*1.06&&!sigW)kw*=0.9;
        else{lineY+=LINEH*R2(0.88,1.15);x=R2(0,46);}
      }
      if(x>0)x+=R2(38,78);
      const th=build(w,sigW?{}:{wordFall:true,fallRate:R2(0.04,0.22),sway:R2(0.5,1.5),swayPhase:R2(0,500)});
      const dy=sigW?0:R2(-9,9);
      const x0=x;
      const m=mapStrokes(th,(s2,y)=>[x0+s2*kw,lineY+dy+88+(y-88)*kw],
                            (S2,y,s0)=>[x0+s0*kw+(S2-s0),lineY+dy+y]);
      m.forEach(st=>{st.pts.forEach(p=>{p[2]*=kw*inkK;});all.push(st);});
      const wuF=wordUnits(w)*kw;
      if(strike)all.push({color:'ink',pts:[[x0-12,lineY+dy+83,2.4],[x0+wuF/2,lineY+dy+93,3.2],[x0+wuF+14,lineY+dy+80,1.8]]});
      x+=wuF;
    };
    stream.forEach(w=>{
      const sigW=w.every(k=>isSig(k));
      const doStrike=!sigW&&wi===strikeAt;
      place(w,sigW?1:R2(0.85,1.15),sigW?1:R2(0.8,1.1),doStrike);
      if(doStrike)place(w,R2(0.9,1.1),R2(0.85,1.05),false);
      if(!sigW)wi++;
    });
    return fig(all,inkW,580);
  }
  function figWatch(sents,inkW,seed){
    const all=[],rnd=mul32(seed*97+3);
    [0,1,2,3,4,5,6,7,8].forEach((si,ln)=>{
      const S=sents[si];
      const mS=mapStrokes(build([S.anchor||'ami'],{}),linear);
      shift(mS,ln*LINEH); mS.forEach(st=>all.push(st));
      const words=realize({words:S.words,mood:S.mood,q:S.q},'bridge');
      const keys=[]; words.forEach((w,i)=>{if(i)keys.push(' ');w.forEach(k=>keys.push(k));});
      const k=si===0?0.55:0.68+rnd()*0.14;
      const m=mapStrokes(build(keys,{}),(s2,y)=>[150+s2*k,y],(S2,y,s0)=>[150+s0*k+(S2-s0),y]);
      if(si===0)m.forEach(st=>{if(st.color==='ink')st.ink='#39597A';});
      shift(m,ln*LINEH); m.forEach(st=>all.push(st));
    });
    return fig(all,inkW,580);
  }
  function figVigil(sents,inkW){
    const keys=[];
    flow(sents,'bridge',1e9).forEach(line=>line.forEach(k=>keys.push(k)));
    const L=MAXU,gapH=LINEH,strokes=[];
    let line=0,sl=0,dir=1,gs=0,curW=0;
    const swayF=x=>0.4*(3.4*Math.sin(x/56)+1.7*Math.sin(x/19+2.1));
    const put=(pen,sx,sig,color)=>strokes.push({color:color||'ink',
      pts:pen.map(pt=>{
        const x=pt[0],y=pt[1],w=pt[2];
        const S=x*sx+(sig?0:(88-y)*SLANT);
        const X=sig?((dir>0?sl:L-sl-curW)+S):(dir>0?sl+S:L-sl-S);
        return [X,line*gapH+y+(sig?0:swayF(gs+S)),w];
      })});
    const turn=()=>{
      const R=gapH/2,cy=line*gapH+88+R,mx=dir>0?L:0,sgn=dir>0?1:-1;
      const pts=[];
      for(let a=-90;a<=90;a+=18){const r=a*Math.PI/180;pts.push([mx+sgn*R*Math.cos(r),cy+R*Math.sin(r),a===0?3.2:4.2]);}
      strokes.push({color:'ink',pts});
      line++;dir=-dir;sl=0;gs+=Math.PI*R;
    };
    keys.forEach(k=>{
      if(k===' '){
        if(sl+50>L){turn();return;}
        put([[0,88,4.2],[25,87.4,4.2],[50,88,4.2]],1,false);sl+=50;gs+=50;return;
      }
      const g=G[k.charAt(k.length-1)===':'?k.slice(0,-1):k];
      curW=wOf(k);
      const w=curW+(g.sigil?24:0);
      if(sl+w>L){put([[0,88,4.2],[(L-sl)/2,87.5,4.2],[L-sl,88,4.2]],1,false);gs+=(L-sl);sl=L;turn();}
      if(g.sigil)sl+=12;
      const sx=sxOf(g);
      (g.pen||[]).forEach(pn=>put(pn,sx,g.sigil));
      (g.penAcc||[]).forEach(pn=>put(pn,sx,g.sigil,'acc2'));
      (g.penAcc2||[]).forEach(pn=>put(pn,sx,g.sigil,'acc2'));
      (g.penSub||[]).forEach(pn=>put(pn,sx,g.sigil,'sub'));
      if(k.charAt(k.length-1)===':')put(ARCPEN,sx,false);
      if(g.dropAt!=null)put(DROPPEN(g.dropAt),1,false,'acc');
      sl+=curW+(g.sigil?12:0);gs+=curW;
    });
    return fig(strokes,inkW,580);
  }
  function figDisc(sents,inkW){
    const ringSent=S=>{
      const keys=[];
      realize(S,'careful').forEach((w,i)=>{if(i)keys.push(' ');w.forEach(k=>keys.push(k));});
      return build(keys,{spaceCarrier:true,noTails:true,sway:0});
    };
    const rings=[{words:[W.jel]},sents[3],sents[8],sents[0],sents[7],sents[1],sents[4]]
      .map(S=>ringSent(S)).sort((a,b)=>a.total-b.total);
    const disc=[]; let prevR=0;
    rings.forEach(th=>{
      const R=Math.max(prevR+95,th.total/(2*Math.PI));
      prevR=R;
      const need=2*Math.PI*R,padU=need-th.total,half=padU/2;
      th.strokes.forEach(st=>{st.s0+=half;st.pts.forEach(p=>{p[0]+=half;});});
      if(padU>8){
        th.strokes.push({color:'ink',pts:[[0,88,4.2],[half/2,87.6,4.2],[half,88,4.2]]});
        th.strokes.push({color:'ink',pts:[[need-half,88,4.2],[need-half/2,87.6,4.2],[need,88,4.2]]});
      }
      const fn=(s2,y)=>{const a=-Math.PI/2+(s2/need)*2*Math.PI,r=R+(88-y);return [r*Math.cos(a),r*Math.sin(a)];};
      const rigidFn=(S2,y,s0)=>{
        const a0=-Math.PI/2+(s0/need)*2*Math.PI,ds=S2-s0,rad=88-y;
        return [(R+rad)*Math.cos(a0)-ds*Math.sin(a0),(R+rad)*Math.sin(a0)+ds*Math.cos(a0)];
      };
      mapStrokes(th,fn,rigidFn).forEach(st=>disc.push(st));
    });
    return fig(disc,inkW,540);
  }
  function studies(seed,inkW){
    const sents=makeSents(mul32(seed*7919+13));
    return {record:figRecord(sents,inkW),scrawl:figScrawl(sents,inkW,seed),
            watch:figWatch(sents,inkW,seed),vigil:figVigil(sents,inkW),
            disc:figDisc(sents,inkW)};
  }
  const TOK={'@T':'mT','@T-':'mTm','@T+':'mTp','@Ts':'mTs','@F':'mF',
             '=ka':'aka','=mi':'ami','=zu':'azu','|':'gap','?':'q'};
  const DARK={'#24282E':'#E8E3D6','#33707C':'#6fa8ff','#A65B3F':'#e8362a','#8A8478':'#8c8a82'};
  function lineSvg(tokens){
    const th=build(tokens.map(t=>TOK[t]||t));
    const F=fig(mapStrokes(th,linear),0.85,560);
    let out=`<svg viewBox="${F.vb}" width="${F.w.toFixed(0)}" height="${F.h.toFixed(0)}" role="img">`;
    F.elems.forEach(e=>{
      const col=DARK[e.fill]||e.fill;
      out+=`<path d="${e.d}" fill="${col}"${e.op!=null?` opacity="${e.op}"`:''}/>`;
    });
    return out+'</svg>';
  }
  function figMarkup(F){
    let out=`<svg viewBox="${F.vb}" style="width:${F.w.toFixed(0)}px;height:${F.h.toFixed(0)}px;max-width:100%" role="img">`;
    F.elems.forEach(e=>{out+=`<path d="${e.d}" fill="${e.fill}"${e.op!=null?` opacity="${e.op}"`:''}/>`;});
    return out+'</svg>';
  }
  return {studies,lineSvg,figMarkup};
})();

const PAGE_CARDS=[
 {key:'record',id:'2a',meta:'ALPHA.1 · AT REST',title:'The record page',
  head:'LOG OF RECORD · CAREFUL HAND · RULED',
  story:'The admissible register: law, manifests, the log of record. Every suffix spelled so a clerk can verify it letter by letter decades on; ruled carriers because a record must not drift — here even the current is stilled.',
  col:'sway 0 · ruled carriers · suffixes spelled · specimen §5-faithful'},
 {key:'scrawl',id:'2b',meta:'AFTER 1a · REFRACTION',title:'The daily scrawl',
  head:'DAY LEAF · QUICK HAND',
  story:'What everyday writing actually looks like: baselines wander, words swell and shrink with the wrist, spacing crowds where the plate runs out, and one word is struck through and rewritten without apology. Chaos on top, system underneath: that is how you know it is a real hand.',
  col:'per-word size · ink · sway · fall all jittered · one strike + rewrite'},
 {key:'watch',id:'2c',meta:'AFTER 1b · DOPPLER',title:'The watch log',
  head:'BRIDGE WATCH · BRIDGE HAND · ENTRIES',
  story:'Not prose — entries. Events written the moment they happen, one line each, opened with the clock they ran on: =mi ship time, =ka beacon-checked, =zu beyond coverage. The writing is compressed because the writer is moving, and how much tells you how fast — the hail came in at a run, λ 0.55, blue.',
  col:'clock stamped first · clause-mood last · λ betrays speed · sigils at rest'},
 {key:'vigil',id:'2d',meta:'AFTER 1c · REFLECTION',title:'The vigil trace',
  head:'VIGIL · BRIDGE HAND · DO NOT LIFT',
  story:'The continuity-proof register: reactor watches, quarantine nights, long crossings — records whose validity IS the unbroken line. A reader checks not what it says but that it never lifts; a forger would have to fake the folds, and folds return mirrored. Even the silence between paragraphs is written.',
  col:'one stroke · folds mirrored · continuity is the record'},
 {key:'disc',id:'2e',meta:'AFTER 1d · CLOSURE',title:'The liturgy disc',
  head:'LITURGY · CAREFUL HAND · RUNG, NOT CUT',
  story:'Six sentences rung at their resonant radii (R = phrase ⁄ 2π), nested by length, careful hand throughout — in still time the current sleeps, so nothing sways. Short phrases hold their unused arc as written silence at the seam. jel rings innermost: one word, mostly quiet.',
  col:'R = phrase/2π · silence held at the seam · uncut'}
];
let PG_SEED=11, PG_INK=0.6;
function rPages(v){
  let html=sec("PAGE STUDIES — ONE TEXT, FIVE REGISTERS")+
  `<div class="panel"><p class="use" style="margin:0">The Current Hand (design 07-E)
   writing the same three paragraphs five ways — a frequency-faithful specimen
   generated against the codex's own letter distribution, with every attested
   word woven in: ver ish-ol, enmai, zukad, jel, Sūchel, hau, and the litany
   hōl-t-eshe=zu closing the page. Silence-marks (ne) stand between paragraphs.</p>
   <div class="pgctl" style="margin-top:12px">
     <label>SEED <input id="pg-seed" type="number" min="1" max="99" value="${PG_SEED}"></label>
     <label>INK <input id="pg-ink" type="range" min="0.45" max="1.2" step="0.05" value="${PG_INK}"></label>
     <span id="pg-inkv">${PG_INK}</span>
   </div></div>`;
  PAGE_CARDS.forEach(c=>{
    html+=`<div class="pgcard" id="pg-${c.key}">
      <div class="rowhead"><span class="pgchip">${c.id}</span><span class="pgmeta">${c.meta}</span></div>
      <h4>${c.title}</h4>
      <p class="pgstory">${c.story}</p>
      <div class="pgpaper">
        <div class="phead"><span>${c.head}</span><span>SŪCHEL</span></div>
        <div class="pfig" id="pgfig-${c.key}"></div>
        <div class="pcol">${c.col} · seed <span class="pg-seed-echo">${PG_SEED}</span></div>
      </div></div>`;
  });
  v.innerHTML=html;
  const draw=()=>{
    const figs=CH.studies(PG_SEED,PG_INK);
    PAGE_CARDS.forEach(c=>{
      const el=v.querySelector('#pgfig-'+c.key);
      if(el)el.innerHTML=CH.figMarkup(figs[c.key]);
    });
    v.querySelectorAll('.pg-seed-echo').forEach(e=>{e.textContent=PG_SEED;});
  };
  draw();
  const seedIn=v.querySelector('#pg-seed'),inkIn=v.querySelector('#pg-ink'),
        inkV=v.querySelector('#pg-inkv');
  if(seedIn)seedIn.onchange=()=>{PG_SEED=Math.max(1,Math.min(99,Math.round(+seedIn.value||11)));draw();};
  if(inkIn)inkIn.oninput=()=>{PG_INK=+inkIn.value;inkV.textContent=inkIn.value;draw();};
}

/* ---------- nav ----------------------------------------------------------- */
const TABS=[
  ["family","FAMILY",rFamily],
  ["suchel","SŪCHEL",rSuchel],
  ["phrase","PHRASEBOOK",rPhrase],
  ["texts","TEXTS",rTexts],
  ["nubhel","NUBHEL",rNubhel],
  ["sisters","SISTERS",rSisters],
  ["script","SCRIPT",rScript],
  ["pages","PAGES",rPages],
];
const nav=document.getElementById("nav");
nav.innerHTML=TABS.map(([k,name])=>
  `<button data-t="${k}">${name}</button>`).join("");
let CURRENT="family";
function show(key,keepScroll){
  CURRENT=key;
  const view=document.getElementById("view");
  nav.querySelectorAll("button").forEach(b=>b.classList.toggle("on",b.dataset.t===key));
  const tab=TABS.find(t=>t[0]===key);
  view.innerHTML=""; tab[2](view);
  if(!keepScroll) window.scrollTo(0,0);
  try{ if(location.hash!=="#"+key) history.replaceState(null,"","#"+key); }
  catch(e){ /* some browsers restrict history on file:// — cosmetic only */ }
}
for(const st of ["carve","trace","current"]){
  const btn=document.getElementById("st-"+st);
  if(!btn) continue;
  btn.onclick=()=>{
    GSTYLE=st;
    for(const other of ["carve","trace","current"]){
      const o=document.getElementById("st-"+other);
      if(o) o.classList.toggle("on",other===st);
    }
    show(CURRENT,true);
  };
}
nav.addEventListener("click",e=>{
  const b=e.target.closest("button[data-t]"); if(b) show(b.dataset.t);
});
show(TABS.some(t=>t[0]===location.hash.slice(1)) ? location.hash.slice(1) : "family");
"""


def _data_json() -> str:
    return json.dumps(collect(), ensure_ascii=False).replace("</", "<\\/")


def fragment() -> str:
    """Page content for hosting environments that supply the document
    skeleton (title + style + markup + data + app)."""
    return (f"<title>{_TITLE}</title>\n<style>{_CSS}</style>\n{_MARKUP}\n"
            f"<script>window.ODY = {_data_json()};</script>\n<script>{_JS}</script>\n")


def document() -> str:
    """A complete standalone HTML document."""
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{_TITLE}</title>\n<style>{_CSS}</style>\n"
            "</head>\n<body>\n"
            f"{_MARKUP}\n"
            f"<script>window.ODY = {_data_json()};</script>\n"
            f"<script>{_JS}</script>\n"
            "</body>\n</html>\n")


def write(path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(document())
