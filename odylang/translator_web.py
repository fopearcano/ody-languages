"""The translator chat — a self-contained web app you *talk* to.

``page()`` emits ONE standalone HTML document: a conversational translator
for English⇄Sūchel that runs entirely client-side, offline, with no network
and no dependencies.  Everything the browser needs is precomputed here in
Python from the finished engines and embedded as a single JSON snapshot:

* the voice model — :func:`odylang.tts.voice_spec` — reproduced by a WebAudio
  formant synth (buzz source → three bandpass resonators tuned to the vowel
  formants), so a Sūchel line can be *heard*;
* a phrasebook of attested + composed idioms — every one of the 41 lines plus
  ~30 useful prompts run through :func:`odylang.translate.to_suchel`, each with
  its Sūchel text, IPA, interlinear gloss, Navcher tokens, rhythm and
  confidence;
* the bilingual dictionary — the derived lexicon
  (:func:`odylang.suchel.entries` + :data:`odylang.vocabulary.VOCAB`) and the
  reverse index (:data:`odylang.translate.REVERSE`/``VERBS``) — for
  word-by-word lookup and the client-side compose/peel;
* the script — the :mod:`odylang.navcher` glyph geometry and the
  :mod:`odylang.currenthand` pen data — so the page can letter *any* token
  stream in any of the three hands.

The visual system is the codices' own (terminal ground ``#08070a``, gold,
seam-red, beacon-blue, mono type), matching :mod:`odylang.webgen`.

The grammar is real: the client mirrors the engine's small morpheme tables
(mood ``-a``, anchors ``=mi``/``=ka``/``=zu``, accusative ``-(e)n``, plural
``-i``, perfective ``-t-``) to *compose* simple pronoun-verb-(noun) clauses
and to *peel* Sūchel morphology back to an interlinear gloss.  Anything it
cannot compose it reports honestly, word by word, and lowers the confidence
chip — it never fakes a root.

Public API — :func:`page`, :func:`page_fragment`, :func:`write`,
:func:`collect` (the embedded snapshot, so tests and the orchestrator can
inspect it).
"""

from __future__ import annotations

import json
import re
from typing import Dict, List

from . import suchel as _suchel
from . import translate as _tr
from . import tts as _tts
from . import vocabulary as _vocab
from .cli import _sentence_tokens
from .currenthand import ARCPEN, HAND, LEADIN, LEADOUT
from .navcher import GLYPHS, LONGBAR
from .phrasebook import LINES
from .suchel_grammar import pronoun


# ---------------------------------------------------------------------------
# snapshot helpers


def _short_gloss(gloss: str) -> str:
    """A concise ascii-ish English gloss for a Sūchel form (mirror of the
    engine's gloss normaliser: drop parentheticals, keep the first clause,
    strip a leading *to/the/a/an*)."""
    g = re.sub(r"\([^)]*\)", "", gloss)
    part = re.split(r"[;,]", g)[0].strip()
    low = part.lower()
    for pre in ("to ", "the ", "a ", "an "):
        if low.startswith(pre):
            part = part[len(pre):]
            break
    return part.strip() or gloss.strip()


def _pre_dash(s: str) -> str:
    return re.split(r"[—–]", s)[0].strip()


def _post_dash(s: str) -> str:
    parts = re.split(r"[—–]", s, 1)
    return parts[1].strip() if len(parts) > 1 else ""


#: extra English keys that should resolve to an attested line at confidence
#: 1.0 (greetings, affirmations, the everyday openers the codex phrases carry).
_LINE_ALIASES: Dict[int, List[str]] = {
    1: ["hello", "hi", "hey there", "greetings", "truth to you"],
    2: ["hello kin", "well met"],
    3: ["hey mate", "hey"],
    4: ["stay safe", "safe travels", "keep well"],
    6: ["goodbye", "bye", "farewell", "see you", "see you again"],
    8: ["hold on", "wait a moment", "one moment"],
    9: ["dive", "take us down"],
    10: ["surface us", "bring us up"],
    11: ["open it"],
    13: ["status", "do you copy", "are we in range", "beacon check"],
    14: ["yes", "affirmative", "confirmed", "lock confirmed"],
    15: ["no", "negative", "we are dark"],
    16: ["all hands", "hold position"],
    22: ["rest now"],
    41: ["we are back in range"],
}

#: ~40 everyday prompts run through the engine; the ones that duplicate a line
#: key/alias are folded in as aliases, the rest become their own idiom cards.
_PROMPTS: List[str] = [
    "hello", "hi", "good morning", "goodbye", "farewell", "thank you", "thanks",
    "yes", "no", "help", "who are you", "where are we", "what is this",
    "are you there", "do you hear me", "I go down", "I go up", "she holds",
    "we surface", "I see you", "you see me", "hold the line", "open the seam",
    "we crossed", "I cross the seam", "they run down", "I want water",
    "we found the gap", "the beacon holds", "breath held", "surface again",
    "take her down", "bring her up", "I am off", "hold on mate",
    "do not surface", "we keep our gaps", "I hold the seam", "we speak true",
    "she has gone adrift", "come to me", "I hear you",
]


def _card_from_translation(en: str, key: str, aliases, t, src: str) -> Dict:
    return {
        "en": en, "key": key, "aliases": list(aliases),
        "su": t.text, "ipa": t.ipa, "gloss": t.gloss,
        "tokens": list(t.tokens), "syl": list(t.syl),
        "conf": t.confidence, "notes": list(t.notes), "src": src,
    }


def _line_card(ln, aliases) -> Dict:
    s = ln.sentence
    en = _pre_dash(ln.translation) or "(the silent interval)"
    key = _tr._norm_idiom(ln.translation) or f"line{ln.number}"
    card = {
        "en": en, "key": key, "aliases": list(aliases),
        "use": _post_dash(ln.translation),
        "su": s.text(), "ipa": s.ipa(), "gloss": s.gloss_line(),
        "tokens": _sentence_tokens(s, "careful"), "syl": s.syl_line(),
        "conf": 1.0, "notes": [f"attested phrasebook line {ln.number}"],
        "src": "attested", "line": ln.number, "section": ln.section,
    }
    return card


def _build_idioms() -> List[Dict]:
    cards: List[Dict] = []
    seen = set()

    def claim(k):
        k = (k or "").strip()
        if k:
            seen.add(k)

    for ln in LINES:
        aliases = _LINE_ALIASES.get(ln.number, [])
        card = _line_card(ln, aliases)
        claim(card["key"])
        for a in aliases:
            claim(_tr._norm_idiom(a))
        cards.append(card)

    for prompt in _PROMPTS:
        key = _tr._norm_idiom(prompt)
        if key in seen:
            continue                    # already an attested line or alias
        t = _tr.to_suchel(prompt)
        if t.confidence >= 1.0:
            src = "attested"
        elif t.confidence >= 0.9:
            src = "composed"
        elif t.confidence >= 0.4:
            src = "word-by-word"
        else:
            src = "scaffold"
        cards.append(_card_from_translation(prompt, key, [], t, src))
        claim(key)

    return cards


def _pron(person: int, plural: bool, case=None) -> Dict:
    w = pronoun(person, plural=plural, case=case)
    return {"su": w.display(), "ipa": w.ipa(), "person": person}


def _build_lex() -> Dict[str, Dict]:
    lex: Dict[str, Dict] = {}
    for e in _suchel.entries():
        lex.setdefault(e.form, {"ipa": e.ipa, "gloss": _short_gloss(e.gloss),
                                "domain": e.domain})
    for e in _vocab.VOCAB:
        lex.setdefault(e.suchel, {"ipa": e.ipa, "gloss": _short_gloss(e.gloss),
                                  "domain": e.domain})
    return lex


def _pen_glyph(g) -> Dict:
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


def collect() -> Dict:
    """The embedded snapshot: everything the offline page runs on."""
    lex = _build_lex()

    # the derived reverse index: english key -> Sūchel form.
    rev: Dict[str, str] = {k: r.form for k, r in _tr.REVERSE.items()}
    for lemma, spec in _tr.VERBS.items():
        rev.setdefault(lemma, spec.stem)

    verbs = {lemma: {"stem": s.stem, "ipa": s.ipa, "kind": s.kind,
                     "gl": s.gloss} for lemma, s in _tr.VERBS.items()}
    irreg = {w: [lemma, pfv] for w, (lemma, pfv) in _tr._IRREGULAR.items()}

    subj = {}
    for tok, (person, plural) in _tr._SUBJ_PRON.items():
        d = _pron(person, plural)
        d["tag"] = f"{person}{'PL' if plural else 'SG'}"
        d["gl"] = {"i": "I", "we": "we", "you": "you", "he": "he",
                   "she": "she", "it": "it", "they": "they"}.get(tok, tok)
        subj[tok] = d
    obj = {}
    for tok, (person, plural) in _tr._OBJ_PRON.items():
        d = _pron(person, plural, case="ACC")
        d["tag"] = f"{person}{'PL' if plural else 'SG'}.ACC"
        d["gl"] = tok
        obj[tok] = d

    # forward-lookup stems for the su2en peel (lexicon + pronoun stems).
    stems = {f.lower(): {"gl": m["gloss"], "ipa": m["ipa"],
                         "domain": m["domain"]} for f, m in lex.items()}
    pron_english = dict(_tr._PRON_ENGLISH)
    pron_english.setdefault("ani", "they")
    for f, g in pron_english.items():
        stems.setdefault(f.lower(),
                         {"gl": g, "ipa": "", "domain": "grammar", "pron": True})

    # Navcher script geometry (stencil hands) + current-hand pen data.
    glyphs = {k: {"w": g.w, "strokes": [list(s) for s in g.strokes],
                  "paths": list(g.paths), "fills": list(g.fills)}
              for k, g in GLYPHS.items()}
    current = {"glyphs": {k: _pen_glyph(g) for k, g in HAND.items()},
               "arcpen": [list(pt) for pt in ARCPEN],
               "leadin": [list(pt) for pt in LEADIN],
               "leadout": [list(pt) for pt in LEADOUT]}

    return {
        "VOICE": _tts.voice_spec(),
        "IDIOMS": _build_idioms(),
        "LEX": lex,
        "REV": rev,
        "STEMS": stems,
        "PRON_ENGLISH": pron_english,
        "GLYPHS": glyphs,
        "LONGBAR": list(LONGBAR),
        "SIGIL": {"@T": "mT", "@T-": "mTm", "@T+": "mTp", "@Ts": "mTs",
                  "@F": "mF", "=ka": "aka", "=mi": "ami", "=zu": "azu",
                  "|": "gap", "?": "q"},
        "CURRENT": current,
        # --- the compose tables (mirrors of the engine's small maps) --------
        "VERBS": verbs,
        "IRREG": irreg,
        "PRON_SUBJ": subj,
        "PRON_OBJ": obj,
        "CORE": dict(_tr._CORE_NOUNS),
        "DIR": dict(_tr._DIR_WORDS),
        "NEG": sorted(_tr._NEG_WORDS),
        "QLEAD": sorted(_tr._Q_LEAD),
        "DARK": sorted(_tr._DARK_WORDS),
        "TPLUS": sorted(_tr._MODAL_TPLUS),
        "TMINUS": sorted(_tr._MODAL_TMINUS),
        "DROP": sorted(_tr._DROP_WORDS),
        "ENMARK": sorted(_tr._EN_MARKERS),
        "MOODSUF": {"T": "a", "Tm": "im", "Tp": "ur", "Ts": "eshe"},
        "MOODTAG": {"T": "T", "Tm": "T⁻", "Tp": "T⁺", "Ts": "T•"},
        # --- the peel tables ------------------------------------------------
        "MOOD_PEEL": {"a": "T", "im": "T⁻", "ur": "T⁺",
                      "eshe": "T•"},
        "ANCHOR_GLOSS": {"ka": "BEAC", "mi": "PROP", "zu": "DARK"},
        "HCASE": {"ol": "DAT", "eth": "LOC", "en": "GEN"},
        "DIRPEEL": {"nuv": "DOWN", "hau": "UP", "zu": "adrift"},
        "FUNC": {"vo": "NEG", "vu": "Q"},
        "SOLID": [["mai", "ENT", "ENT"], ["eshe", "MOOD", "T•"],
                  ["en", "ACC", "ACC"], ["u", "IMP", "IMP"],
                  ["i", "PL", "PL"], ["n", "ACC", "ACC"]],
        "MOOD_ADV": {"T": "", "T⁻": "true-as-approached",
                     "T⁺": "held from above", "T•": "seam-true"},
        "ANCHOR_ADV": {"BEAC": "in beacon time", "PROP": "by our own clock",
                       "DARK": "in dark time"},
    }


# ---------------------------------------------------------------------------
# page text

_TITLE = "SŪCHEL TRANSLATOR — talk to the crossing-speech"

_MARKUP = """
<div class="wrap">
  <header class="head">
    <div class="brandrow">
      <div class="brand">SŪCHEL <span class="tr">TRANSLATOR</span></div>
      <a class="codexlink" href="__CODEX_URL__" target="_blank" rel="noopener"
         title="the interactive codex: the whole language family, lexicons, script and grammar behind this translator">THE CODEX ↗</a>
    </div>
    <p class="tag">A translator you <b>talk to</b>. Type English or Sūchel and the
      agent answers. The grammar is real — SOV, and the verb carries both its
      <b>veridical mood</b> and its <b>temporal anchor</b>. Every Sūchel line can be
      heard: the audio is synthesized from the phoneme model, not recorded.
      The whole knowledge system behind it — every root, sound change, and
      glyph — lives in <a class="codexinline" href="__CODEX_URL__" target="_blank"
      rel="noopener">the codex</a>.</p>
    <div class="ctl">
      <div class="seg" id="dir" role="group" aria-label="translation direction">
        <button data-d="auto" class="on">AUTO</button>
        <button data-d="en2su">EN &rarr; SŪ</button>
        <button data-d="su2en">SŪ &rarr; EN</button>
      </div>
      <div class="seg" id="hand" role="group" aria-label="Navcher hand">
        <button data-h="current" class="on">CURRENT HAND</button>
        <button data-h="logos">LOGOS</button>
      </div>
    </div>
  </header>

  <main class="chat" id="chat" aria-live="polite" aria-label="conversation"></main>

  <div class="starters" id="starters"></div>

  <form class="dock" id="dock" autocomplete="off">
    <input id="in" type="text" placeholder="say something to the translator…"
      aria-label="your message" spellcheck="false">
    <button type="submit" id="send">SEND</button>
  </form>
  <footer class="foot">offline · self-contained · lettered in Navcher · voiced from
    <span class="mono">voice_spec()</span> — one proto, two fleets, four mouths</footer>
</div>
"""

_CSS = r"""
*{box-sizing:border-box;margin:0}
:root{
  --bg:#08070a; --panel:#0e0b10; --panel2:#131017; --bubble:#12141b;
  --ink:#d8d2c8; --dim:#8c8a82; --faint:#565360;
  --gold:#f5d76e; --red:#e8362a; --blue:#6fa8ff; --green:#7ec885;
  --line:rgba(232,54,42,.22); --goldline:rgba(245,215,110,.25);
  --mono:ui-monospace,'Cascadia Mono','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace;
}
html{background:var(--bg)}
body{background:var(--bg);color:var(--ink);font-family:var(--mono);font-size:14px;
  line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden}
.mono{font-family:var(--mono)}
.wrap{max-width:860px;margin:0 auto;min-height:100vh;display:flex;flex-direction:column;
  padding:0 16px}
.head{padding:26px 0 14px;border-bottom:1px solid var(--line)}
.brandrow{display:flex;align-items:baseline;justify-content:space-between;gap:16px;flex-wrap:wrap}
.brand{color:var(--gold);font-size:22px;letter-spacing:.28em;font-weight:700}
.brand .tr{color:var(--red);letter-spacing:.24em}
.codexlink{color:var(--blue);text-decoration:none;font-size:11px;letter-spacing:.22em;
  border:1px solid var(--goldline);padding:5px 12px;white-space:nowrap}
.codexlink:hover{color:var(--gold);border-color:var(--gold)}
.codexlink:focus-visible{outline:1px solid var(--gold);outline-offset:2px}
.codexinline{color:var(--blue);text-decoration:none;border-bottom:1px solid var(--goldline)}
.codexinline:hover{color:var(--gold)}
.tag{color:var(--dim);font-size:12.5px;max-width:66ch;margin:10px 0 16px;line-height:1.65}
.tag b{color:var(--ink);font-weight:400}
.ctl{display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.seg{display:inline-flex;border:1px solid var(--goldline);flex-wrap:wrap}
.seg button{all:unset;cursor:pointer;font-family:var(--mono);font-size:10px;
  letter-spacing:.14em;padding:6px 11px;color:var(--dim);border-right:1px solid var(--goldline)}
.seg button:last-child{border-right:none}
.seg button:hover{color:var(--ink)}
.seg button:focus-visible{outline:1px solid var(--gold);outline-offset:2px}
.seg button.on{color:var(--bg);background:var(--gold)}
#hand button.on{background:var(--blue);color:var(--bg)}
.chat{flex:1;display:flex;flex-direction:column;gap:16px;padding:22px 0}
.msg{max-width:100%;display:flex;flex-direction:column;gap:4px}
.msg.you{align-items:flex-end}
.bub{max-width:88%;padding:9px 14px;border:1px solid var(--line);border-radius:3px;
  overflow-wrap:break-word;word-break:break-word}
.msg.you .bub{background:var(--bubble);border-color:var(--goldline);color:var(--ink)}
.msg.you .who{color:var(--faint)}
.who{font-size:9px;letter-spacing:.22em;color:var(--red)}
.card{max-width:96%;background:var(--panel);border:1px solid var(--line);
  padding:14px 16px;display:flex;flex-direction:column;gap:10px;position:relative}
.card::before{content:"";position:absolute;top:-1px;left:-1px;width:12px;height:12px;
  border-top:2px solid var(--gold);border-left:2px solid var(--gold)}
.su{color:var(--gold);font-size:22px;letter-spacing:.01em;line-height:1.3}
.card.su2en .para{color:var(--ink);font-size:16px}
.ipa{color:var(--dim);font-size:12px}
.eng{color:var(--blue);font-size:12px}
.gloss{display:flex;flex-wrap:wrap;gap:10px;overflow-x:auto;padding-bottom:2px}
.gunit{display:flex;flex-direction:column;gap:1px;border-left:1px solid var(--line);
  padding-left:7px;min-width:0}
.gunit .g-su{color:var(--gold);font-size:13px;white-space:nowrap}
.gunit.unk .g-su{color:var(--red)}
.gunit .g-gl{color:var(--dim);font-size:10px;white-space:nowrap;letter-spacing:.04em}
.navc{overflow-x:auto;padding:6px 0;max-width:100%}
.navc svg{max-width:100%;height:auto}
.audio{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.ab{all:unset;cursor:pointer;font-family:var(--mono);font-size:10px;letter-spacing:.14em;
  padding:4px 11px;border:1px solid var(--red);color:var(--red)}
.ab:hover{background:var(--red);color:var(--bg)}
.ab:focus-visible{outline:1px solid var(--gold);outline-offset:2px}
.ab[disabled]{opacity:.35;cursor:default;border-color:var(--faint);color:var(--faint)}
.ab.blue{border-color:var(--blue);color:var(--blue)} .ab.blue:hover{background:var(--blue);color:var(--bg)}
.ab.gold{border-color:var(--goldline);color:var(--gold)} .ab.gold:hover{background:var(--gold);color:var(--bg)}
.meta{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:11px}
.chip{font-size:9px;letter-spacing:.16em;padding:2px 9px;border:1px solid}
.chip.attested{color:var(--bg);background:var(--gold);border-color:var(--gold)}
.chip.composed{color:var(--blue);border-color:var(--blue)}
.chip.wbw{color:var(--dim);border-color:var(--goldline)}
.chip.scaffold{color:var(--red);border-color:var(--red)}
.note{color:var(--faint);font-size:11px;line-height:1.55}
.note code{color:var(--green)}
.rhythm{display:inline-flex;flex-wrap:wrap;gap:4px;align-items:center}
.beat{font-size:10px;padding:1px 7px;border:1px solid var(--goldline);color:var(--dim)}
.beat.hi{background:var(--gold);color:var(--bg);border-color:var(--gold)}
.beat.gap{color:var(--red);border-color:var(--red);min-width:20px;text-align:center}
.beat.sp{border:none;padding:0 1px;color:var(--faint)}
.starters{display:flex;flex-wrap:wrap;gap:6px;padding:2px 0 12px}
.starters .s{all:unset;cursor:pointer;font-size:10px;letter-spacing:.06em;color:var(--dim);
  border:1px solid var(--goldline);padding:4px 10px}
.starters .s:hover{color:var(--bg);background:var(--gold)}
.starters .s:focus-visible{outline:1px solid var(--gold);outline-offset:2px}
.dock{display:flex;gap:10px;position:sticky;bottom:0;background:var(--bg);
  padding:12px 0 10px;border-top:1px solid var(--line)}
.dock input{flex:1;min-width:0;background:var(--panel2);border:1px solid var(--goldline);
  color:var(--ink);font-family:var(--mono);font-size:15px;padding:11px 14px}
.dock input:focus-visible{outline:1px solid var(--gold);outline-offset:1px}
.dock button{all:unset;cursor:pointer;font-family:var(--mono);font-size:12px;
  letter-spacing:.16em;padding:0 20px;color:var(--bg);background:var(--gold)}
.dock button:hover{background:#ffe58a}
.dock button:focus-visible{outline:1px solid var(--red);outline-offset:2px}
.foot{color:var(--faint);font-size:10px;letter-spacing:.06em;padding:6px 0 20px;
  border-top:1px solid var(--line);margin-top:4px}
.foot .mono{color:var(--green)}
.toast{position:fixed;left:50%;bottom:82px;transform:translateX(-50%);background:var(--panel2);
  border:1px solid var(--goldline);color:var(--ink);font-size:11px;padding:7px 14px;z-index:50}
@media (max-width:560px){
  .brand{font-size:18px}
  .su{font-size:19px}
  .bub,.card{max-width:100%}
}
@media (prefers-reduced-motion:no-preference){
  .seg button,.ab,.starters .s,.dock button{transition:color .14s,background .14s,border-color .14s}
  .msg{animation:rise .18s ease both}
  @keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
}
"""

_JS = r"""
window.onerror=function(msg){
  var b=document.createElement("div");
  b.style.cssText="position:fixed;left:0;right:0;bottom:0;background:#e8362a;color:#08070a;"+
    "font:12px monospace;padding:6px 12px;z-index:99";
  b.textContent="translator error: "+msg; document.body.appendChild(b);
};
const D=window.ODYT;
const esc=s=>String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);

/* =====================================================================
   Navcher — two living hands: the flowing CURRENT HAND (default) and the
   old sacred LOGOS carving (the same skeleton cut into straight facets).
   Both are rendered by the CH engine below.
   ===================================================================== */
let GSTYLE="current";
/* careful-hand tokenizer for free text (mirror of navcher.tokens_careful) */
function tokenizeCareful(text){
  const out=[],s=text.toLowerCase();
  const macron={"ā":"a","ē":"e","ī":"i","ō":"o","ū":"u"};
  const spacedCase=["ol","eth","en"];
  let i=0;
  while(i<s.length){
    const c=s[i];
    if(c===" "){ out.push(" "); i++; continue; }
    if(c==="-"){
      const rest=s.slice(i+1).split(/[^a-zāēīōū]/)[0];
      if(spacedCase.includes(rest)) out.push(" ");
      i++; continue;
    }
    if(c==="="){ i++; continue; }
    const two=s.slice(i,i+2);
    if(two==="ch"||two==="sh"){ out.push(two); i+=2; continue; }
    if(two==="th"){ out.push("t","h"); i+=2; continue; }
    if(c==="x"){ out.push("k","s"); i++; continue; }
    if(macron[c]){ out.push(macron[c]+":"); i++; continue; }
    if(D.GLYPHS[c]) out.push(c);
    i++;
  }
  return out;
}

/* =====================================================================
   Current Hand ribbon engine (compact port of odylang.currenthand)
   ===================================================================== */
const CH=(function(){
  const G=D.CURRENT.glyphs, ARCPEN=D.CURRENT.arcpen, LEADIN=D.CURRENT.leadin, LEADOUT=D.CURRENT.leadout;
  const SLANT=0.10;
  const cr1=(a,b,c,d,t)=>{const t2=t*t,t3=t2*t;return 0.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t2+(-a+3*b-3*c+d)*t3);};
  const lin=(a,b,c,d,t)=>b+(c-b)*t;  /* Logos: straight facets */
  function ribbon(pts,f,squared){
    const n=pts.length; if(n<2) return "";
    const g=i=>pts[i<0?0:(i>n-1?n-1:i)];
    const S=[],SEG=squared?1:8,ip=squared?lin:cr1;
    for(let i=0;i<n-1;i++){
      const p0=g(i-1),p1=g(i),p2=g(i+1),p3=g(i+2),top=(i===n-2)?SEG:SEG-1;
      for(let t=0;t<=top;t++){const u=t/SEG;
        S.push([ip(p0[0],p1[0],p2[0],p3[0],u),ip(p0[1],p1[1],p2[1],p3[1],u),Math.max(0.3,ip(p0[2],p1[2],p2[2],p3[2],u))*f]);}
    }
    const L=[],R=[];
    for(let i=0;i<S.length;i++){
      const a=S[i>0?i-1:0],b=S[i<S.length-1?i+1:S.length-1];
      const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy)||1,nx=-dy/len,ny=dx/len,hw=S[i][2]/2;
      L.push((S[i][0]+nx*hw).toFixed(1)+","+(S[i][1]+ny*hw).toFixed(1));
      R.push((S[i][0]-nx*hw).toFixed(1)+","+(S[i][1]-ny*hw).toFixed(1));
    }
    R.reverse();
    return "M"+L.join(" L")+" L"+R.join(" L")+" Z";
  }
  const DROPPEN=cx=>[[cx,100,0.8],[cx+1.5,106,5.5],[cx+0.8,113,8],[cx-1,117,3.2]];
  const sxOf=g=>g.sigil?1:(g.vowel?g.w/60:g.w/100);
  const wOf=k=>G[k.charAt(k.length-1)===":"?k.slice(0,-1):k].w;
  const isSig=k=>!!(G[k]&&G[k].sigil);
  function build(keys){
    const swayF=x=>0.4*(3.4*Math.sin(x/56)+1.7*Math.sin(x/19+2.1));
    const strokes=[]; let s=0,inRun=false;
    const pushPen=(pen,sx,off,sig,color,s0)=>strokes.push({color:color||"ink",rigid:!!sig,s0:s0||0,
      pts:pen.map(pt=>{const x=pt[0],y=pt[1],w=pt[2];const S=x*sx+(sig?0:(88-y)*SLANT)+off;return [S,y+(sig?0:swayF(S)),w];})});
    keys.forEach(k=>{
      if(k===" "){ if(inRun)pushPen(LEADOUT,1,s,false); inRun=false; s+=62; return; }
      if(isSig(k)){
        if(inRun){pushPen(LEADOUT,1,s,false);inRun=false;}
        s+=18; const g=G[k],s0=s+30;
        (g.pen||[]).forEach(pn=>pushPen(pn,1,s,true,"ink",s0));
        (g.penAcc||[]).forEach(pn=>pushPen(pn,1,s,true,"acc2",s0));
        (g.penAcc2||[]).forEach(pn=>pushPen(pn,1,s,true,"acc2",s0));
        (g.penSub||[]).forEach(pn=>pushPen(pn,1,s,true,"sub",s0));
        s+=wOf(k)+18; return;
      }
      if(!inRun){pushPen(LEADIN,1,s,false);inRun=true;}
      const long=k.charAt(k.length-1)===":", g=G[long?k.slice(0,-1):k];
      if(!g) return;
      const sx=sxOf(g);
      (g.pen||[]).forEach(pn=>pushPen(pn,sx,s,false));
      if(long)pushPen(ARCPEN,sx,s,false);
      if(g.dropAt!=null)pushPen(DROPPEN(g.dropAt),1,s,false,"acc");
      s+=wOf(k);
    });
    if(inRun)pushPen(LEADOUT,1,s,false);
    return {strokes,total:s};
  }
  const linear=(s,y)=>[s,y];
  const mapStrokes=(th,fn)=>th.strokes.map(st=>({color:st.color,pts:st.pts.map(p=>{const q=fn(p[0],p[1]);return [q[0],q[1],p[2]];})}));
  /* living hand: bone-white ink.  Logos hand: illuminated gold, sacred. */
  const PAPER={ink:"#E8E3D6",acc:"#6fa8ff",acc2:"#e8362a",sub:"#8c8a82"};
  const GOLD={ink:"#f5d76e",acc:"#e8362a",acc2:"#e8362a",sub:"#8c8a82"};
  function fig(strokes,inkW,px,squared,cmap){
    let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
    const elems=strokes.map(st=>{st.pts.forEach(p=>{x0=Math.min(x0,p[0]-p[2]);y0=Math.min(y0,p[1]-p[2]);x1=Math.max(x1,p[0]+p[2]);y1=Math.max(y1,p[1]+p[2]);});
      return {d:ribbon(st.pts,inkW,squared),fill:cmap[st.color]||cmap.ink};});
    const pad=18,bw=(x1-x0)+2*pad,bh=(y1-y0)+2*pad,py=px*bh/bw;
    return {vb:(x0-pad).toFixed(0)+" "+(y0-pad).toFixed(0)+" "+bw.toFixed(0)+" "+bh.toFixed(0),elems,w:px,h:py};
  }
  const TOK={"@T":"mT","@T-":"mTm","@T+":"mTp","@Ts":"mTs","@F":"mF","=ka":"aka","=mi":"ami","=zu":"azu","|":"gap","?":"q"};
  /* Logos: snap every segment to one of 8 compass directions — carved cuts */
  function carve(strokes){
    const step=2*Math.PI/8;
    strokes.forEach(st=>{
      const pts=st.pts; if(pts.length<2) return;
      const out=[pts[0].slice()];
      for(let i=1;i<pts.length;i++){
        const dx=pts[i][0]-pts[i-1][0], dy=pts[i][1]-pts[i-1][1], L=Math.hypot(dx,dy), w=pts[i][2];
        if(L<1e-6){ out.push([out[out.length-1][0],out[out.length-1][1],w]); continue; }
        const a=Math.round(Math.atan2(dy,dx)/step)*step;
        out.push([out[out.length-1][0]+L*Math.cos(a), out[out.length-1][1]+L*Math.sin(a), w]);
      }
      st.pts=out;
    });
    return strokes;
  }
  function _svg(tokens,squared,cmap,doCarve){
    const keys=tokens.map(t=>TOK[t]||(t.endsWith(":")?t:t)).filter(k=>k===" "||k==="gap"||G[k.charAt(k.length-1)===":"?k.slice(0,-1):k]);
    const th=build(keys.length?keys:[" "]);
    let mapped=mapStrokes(th,linear);
    if(doCarve) carve(mapped);
    const F=fig(mapped,squared?0.92:0.85, Math.min(560, Math.max(120, th.total*0.5)),squared,cmap);
    let out=`<svg viewBox="${F.vb}" width="${F.w.toFixed(0)}" height="${F.h.toFixed(0)}" role="img">`;
    F.elems.forEach(e=>{out+=`<path d="${e.d}" fill="${e.fill}"/>`;});
    return out+"</svg>";
  }
  function lineSvg(tokens){ return _svg(tokens,false,PAPER,false); }
  function logosSvg(tokens){ return _svg(tokens,true,GOLD,true); }
  return {lineSvg,logosSvg};
})();

function stripSvg(tokens){
  const clean=(tokens||[]).filter(t=>t!=null);
  try{ return GSTYLE==="logos" ? CH.logosSvg(clean) : CH.lineSvg(clean); }
  catch(e){ return ""; }
}

/* =====================================================================
   audio 1 — RHYTHM : the codex beat player (docs/04)
   ===================================================================== */
let AC=null;
function actx(){ AC=AC||new (window.AudioContext||window.webkitAudioContext)(); if(AC.state==="suspended")AC.resume(); return AC; }
function playRhythm(syl){
  const ctx=actx(); let t=ctx.currentTime+0.05;
  for(const tok of (syl||[])){
    if(tok==="/"){ t+=0.09; continue; }
    if(tok==="|"){ t+=0.5; continue; }
    const hi=/[A-Z]/.test(tok), long=tok.includes(":"), dur=(hi?0.24:0.13)+(long?0.15:0);
    const o=ctx.createOscillator(), g=ctx.createGain();
    o.type="triangle"; o.frequency.value=hi?520:340;
    g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(0.22,t+0.02);
    g.gain.exponentialRampToValueAtTime(0.0001,t+dur);
    o.connect(g); g.connect(ctx.destination); o.start(t); o.stop(t+dur+0.02);
    t+=dur+0.055;
  }
}

/* =====================================================================
   audio 2 — VOICE : a WebAudio formant synth mirroring voice_spec()
   buzz source -> three BiquadFilter bandpass resonators (Q = f/bw),
   noise buffers for fricatives + stop bursts, long-vowel timing.
   ===================================================================== */
let NOISE=null;
function noiseBuf(ctx){
  if(NOISE&&NOISE.sampleRate===ctx.sampleRate) return NOISE;
  const n=Math.floor(ctx.sampleRate*0.6), b=ctx.createBuffer(1,n,ctx.sampleRate), d=b.getChannelData(0);
  let x=99173; for(let i=0;i<n;i++){ x=(x*1103515245+12345)&0x7fffffff; d[i]=(x/0x3fffffff)-1; }
  NOISE=b; return b;
}
function voicedVowel(ctx,dest,t,dur,F,f0,V){
  const osc=ctx.createOscillator(); osc.type="sawtooth"; osc.frequency.setValueAtTime(f0,t);
  osc.frequency.linearRampToValueAtTime(f0*(1-(V.declination||0.15)*0.12),t+dur);
  const amp=ctx.createGain();
  amp.gain.setValueAtTime(0.0001,t); amp.gain.linearRampToValueAtTime(0.9,t+Math.min(0.03,dur*0.3));
  amp.gain.setValueAtTime(0.9,Math.max(t+0.03,t+dur-0.04)); amp.gain.exponentialRampToValueAtTime(0.0001,t+dur);
  const bw=V.formantBandwidths||[90,110,170], ga=V.formantAmps||[1,0.6,0.32];
  for(let i=0;i<3;i++){
    const bp=ctx.createBiquadFilter(); bp.type="bandpass"; bp.frequency.value=F[i]||500;
    bp.Q.value=Math.max(2,(F[i]||500)/(bw[i]||110));
    const g=ctx.createGain(); g.gain.value=ga[i]||0.4;
    osc.connect(bp); bp.connect(g); g.connect(amp);
  }
  amp.connect(dest); osc.start(t); osc.stop(t+dur+0.02);
}
function noiseSeg(ctx,dest,t,dur,lo,hi,center,gain){
  const src=ctx.createBufferSource(); src.buffer=noiseBuf(ctx); src.loop=true;
  const bp=ctx.createBiquadFilter(); bp.type="bandpass";
  if(lo&&hi){ bp.frequency.value=(lo+hi)/2; bp.Q.value=Math.max(0.7,((lo+hi)/2)/Math.max(1,hi-lo)); }
  else { bp.frequency.value=center||3000; bp.Q.value=3; }
  const g=ctx.createGain();
  g.gain.setValueAtTime(0.0001,t); g.gain.linearRampToValueAtTime(gain,t+0.008);
  g.gain.exponentialRampToValueAtTime(0.0001,t+dur);
  src.connect(bp); bp.connect(g); g.connect(dest); src.start(t); src.stop(t+dur+0.02);
}
function playVoice(tokens){
  const V=D.VOICE; if(!V){ toast("no voice model"); return; }
  const ctx=actx(); const master=ctx.createGain(); master.gain.value=V.headroom||0.85; master.connect(ctx.destination);
  const tm=V.timing||{}; let t=ctx.currentTime+0.06, f0=V.f0||120;
  const vs=V.formants||{};
  for(const raw of (tokens||[])){
    if(raw===" "){ t+=(tm.wordGapMs||55)/1000; continue; }
    if(raw==="|"){ t+=(tm.pauseMs||320)/1000; continue; }
    const long=raw.endsWith(":"), base=long?raw.slice(0,-1):raw;
    if(has(vs,base)){
      let dur=((tm.vowelMs||150)/1000)*(long?(tm.longFactor||1.7):1);
      voicedVowel(ctx,master,t,dur,vs[base],f0,V);
      t+=dur; f0*=(1-(V.declination||0.15)*0.05); continue;
    }
    const c=V.consonants&&V.consonants[base];
    if(c){
      if(c.manner==="stop"||c.manner==="affricate"){
        const clo=(c.closure_ms||45)/1000, bd=c.manner==="affricate"?(c.dur_ms||70)/1000:0.028;
        noiseSeg(ctx,master,t+clo,bd,c.noise_lo,c.noise_hi,c.burst_hz||1500,c.voiced?0.26:0.42);
        t+=clo+bd; continue;
      }
      if(c.manner==="fricative"||c.manner==="aspirate"){
        const dur=(c.dur_ms||90)/1000; noiseSeg(ctx,master,t,dur,c.noise_lo,c.noise_hi,3000,c.voiced?0.24:0.36);
        if(c.voiced){ voicedVowel(ctx,master,t,dur,[300,900,2200],f0,V); }
        t+=dur; continue;
      }
      /* nasal / liquid / tap : a short voiced formant segment */
      const dur=(c.dur_ms||60)/1000, F=(c.formants&&c.formants.length)?c.formants:[400,1200,2400];
      voicedVowel(ctx,master,t,dur,F,f0*0.98,V); t+=dur; continue;
    }
    t+=0.02;
  }
}

/* =====================================================================
   audio 3 — SPEAK : window.speechSynthesis on an English respelling
   ===================================================================== */
function respellIpa(ipa){
  if(!ipa) return "";
  return ipa.replace(/[ˈˌ]/g,"").replace(/tʃ/g,"ch").replace(/dʒ/g,"j")
    .replace(/ʃ/g,"sh").replace(/ʒ/g,"zh").replace(/ŋ/g,"ng")
    .replace(/θ/g,"th").replace(/ð/g,"th").replace(/ː/g,"")
    .replace(/ɛ/g,"e").replace(/ə/g,"uh").replace(/ɑ/g,"ah")
    .replace(/ɔ/g,"aw").replace(/ʊ/g,"oo").replace(/[.]/g," ")
    .replace(/[^A-Za-z ]/g," ").replace(/\s+/g," ").trim();
}
function respellSuchel(su){
  if(!su) return "";
  const m={"ā":"aa","ē":"ay","ī":"ee","ō":"oh","ū":"oo"};
  return su.replace(/[āēīōū]/g,c=>m[c]||c).replace(/[-=]/g," ").replace(/[.!?]/g,"").trim();
}
function speak(text){
  if(!("speechSynthesis" in window)){ toast("speech synthesis is unavailable in this browser"); return; }
  const u=new SpeechSynthesisUtterance(text); u.rate=0.82; u.pitch=0.9;
  try{ window.speechSynthesis.cancel(); window.speechSynthesis.speak(u); }
  catch(e){ toast("speech synthesis failed"); }
}

/* =====================================================================
   idiom lookup + normalisation (mirror of translate._norm_idiom)
   ===================================================================== */
function normIdiom(s){
  s=String(s||"").split(/[—–]/)[0].toLowerCase();
  s=s.replace(/[^a-z0-9\s]/g," ");
  return s.replace(/\s+/g," ").trim();
}
const IDIOM_MAP={};
for(const c of D.IDIOMS){
  if(c.key) IDIOM_MAP[c.key]=c;
  for(const a of (c.aliases||[])){ const k=normIdiom(a); if(k) IDIOM_MAP[k]=c; }
}

/* =====================================================================
   EN -> SU compose (compact port of translate._compose)
   ===================================================================== */
function enWords(s){ return (s.toLowerCase().replace(/['’]/g,"").match(/[a-z0-9]+/g))||[]; }
function inSet(arr,w){ return arr.indexOf(w)>=0; }
function singular(w){
  if(w.endsWith("ies")) return w.slice(0,-3)+"y";
  if(w.endsWith("ses")||w.endsWith("shes")||w.endsWith("ches")) return w.slice(0,-2);
  if(w.endsWith("s")&&!w.endsWith("ss")) return w.slice(0,-1);
  return w;
}
function lemmaVerb(w){
  if(D.IRREG[w]){ const a=D.IRREG[w],s=D.VERBS[a[0]]; return s?{spec:s,pfv:a[1],lemma:a[0],word:w}:null; }
  if(D.VERBS[w]) return {spec:D.VERBS[w],pfv:false,lemma:w,word:w};
  const cands=[];
  if(w.endsWith("ies")) cands.push([w.slice(0,-3)+"y",false]);
  if(w.endsWith("ing")){ cands.push([w.slice(0,-3),false]); cands.push([w.slice(0,-3)+"e",false]); }
  if(w.endsWith("ed")){ cands.push([w.slice(0,-2),true]); cands.push([w.slice(0,-2)+"e",true]); cands.push([w.slice(0,-1),true]); }
  if(w.endsWith("d")) cands.push([w.slice(0,-1),true]);
  if(w.endsWith("es")) cands.push([w.slice(0,-2),false]);
  if(w.endsWith("s")) cands.push([w.slice(0,-1),false]);
  for(const [c,pfv] of cands) if(D.VERBS[c]) return {spec:D.VERBS[c],pfv:pfv,lemma:c,word:w};
  return null;
}
function nounRef(w){
  for(const c of [w,singular(w)]){
    if(D.CORE[c]){ const f=D.CORE[c],l=D.LEX[f]; if(l) return {form:f,ipa:l.ipa,gloss:l.gloss,domain:l.domain,en:w}; }
    if(D.REV[c]){ const f=D.REV[c],l=D.LEX[f]||{}; return {form:f,ipa:l.ipa||"",gloss:l.gloss||c,domain:l.domain||"",en:w}; }
  }
  return null;
}
function accForm(stem){ return /[aeiouāēīōū]$/.test(stem)?stem+"-n":stem+"-en"; }
function tword(en,su,gloss,ipa,known){ return {en:en,su:su,gloss:gloss,ipa:ipa,known:known!==false}; }

function composeEN(src){
  const words=enWords(src);
  const notes=[];
  if(!words.length) return scaffold(src,[],"empty input");
  const neg=words.some(w=>inSet(D.NEG,w));
  const tplus=words.some(w=>inSet(D.TPLUS,w));
  const tminus=words.some(w=>inSet(D.TMINUS,w));
  const dark=words.some(w=>inSet(D.DARK,w));
  const qMark=/\?/.test(src), exMark=/!/.test(src);
  const leadingQ=inSet(D.QLEAD,words[0]);
  let direction=null;
  for(const w of words){ if(has(D.DIR,w)){ direction=D.DIR[w]; break; } }

  /* classify (functional cues consumed) */
  const seq=[];
  for(const w of words){
    if(inSet(D.DROP,w)||inSet(D.NEG,w)||inSet(D.QLEAD,w)||inSet(D.TPLUS,w)||inSet(D.TMINUS,w)||has(D.DIR,w)||inSet(D.DARK,w)) continue;
    if(has(D.PRON_SUBJ,w)||has(D.PRON_OBJ,w)){ seq.push({role:"pron",text:w}); continue; }
    const lv=lemmaVerb(w); if(lv){ seq.push({role:"verb",text:w,data:lv}); continue; }
    const nn=nounRef(w); if(nn){ seq.push({role:"noun",text:w,data:nn}); continue; }
    seq.push({role:"unknown",text:w});
  }
  const verbIdx=seq.findIndex(t=>t.role==="verb");
  const nominals=seq.filter(t=>t.role==="pron"||t.role==="noun");
  const unknowns=seq.filter(t=>t.role==="unknown");
  if(verbIdx<0 && !nominals.length) return wordByWord(src,words);

  const before=verbIdx>=0?seq.slice(0,verbIdx):seq;
  const after=verbIdx>=0?seq.slice(verbIdx+1):[];
  let subject=null; for(let i=before.length-1;i>=0;i--){ if(before[i].role==="pron"||before[i].role==="noun"){ subject=before[i]; break; } }
  const objects=after.filter(t=>t.role==="pron"||t.role==="noun");

  let subjPerson=null;
  if(subject){ subjPerson=subject.role==="pron"?(D.PRON_SUBJ[subject.text]||D.PRON_OBJ[subject.text]).person:3; }
  const anchor=dark?"zu":(subjPerson===1?"mi":"ka");
  const anchorTag={ka:"BEAC",mi:"PROP",zu:"DARK"}[anchor];
  const isImperative=verbIdx>=0 && (exMark || subject===null);
  const isQuestion=(leadingQ||qMark) && !isImperative;

  const tw=[], surf=[];
  let punct=".";

  function pushSubj(t){
    const p=D.PRON_SUBJ[t.text]||D.PRON_OBJ[t.text];
    if(t.role==="pron"&&p){ surf.push(p.su); tw.push(tword(t.text,p.su,p.tag,p.ipa,true)); }
    else if(t.role==="noun"){ const r=t.data; surf.push(r.form); tw.push(tword(t.text,r.form,r.gloss,r.ipa,true)); }
  }
  function pushObj(t){
    if(t.role==="pron"){ const p=D.PRON_OBJ[t.text]||D.PRON_SUBJ[t.text]; surf.push(p.su); tw.push(tword(t.text,p.su,p.tag,p.ipa,true)); }
    else { const r=t.data, f=accForm(r.form); surf.push(f); tw.push(tword(t.text,f,r.gloss+".ACC",r.ipa,true)); }
  }
  function pushDir(){ if(direction){ const tag=D.DIRPEEL[direction]||direction.toUpperCase(); surf.push(direction); tw.push(tword(direction,direction,tag,"",true)); } }
  function pushNeg(){ surf.push("vo"); tw.push(tword("not","vo","NEG","",true)); }

  if(verbIdx<0){
    for(const t of nominals){ (t===subject)?pushSubj(t):pushObj(t); }
    for(const t of unknowns){ tw.push(tword(t.text,"—","?","",false)); notes.push("no Sūchel word for '"+t.text+"'"); }
    return finish(src,surf,tw,notes,nominals.length,unknowns.length,punct,"composed");
  }

  const spec=seq[verbIdx].data.spec, pfv=seq[verbIdx].data.pfv, motion=spec.kind==="motion";
  let mood="T"; if(tplus)mood="Tp"; if(tminus)mood="Tm"; if(spec.kind==="seam")mood="Ts";
  const moodTag=D.MOODTAG[mood];

  if(isImperative){
    if(neg) pushNeg();
    if(motion) pushDir();
    for(const t of objects) pushObj(t);
    const imp=spec.stem+"-u";
    surf.push(imp); tw.push(tword(seq[verbIdx].text,imp,spec.gl+"-IMP",spec.ipa,true));
    if(exMark) punct="!";
  } else {
    if(subject) pushSubj(subject);
    for(const t of objects) pushObj(t);
    if(motion) pushDir();
    if(neg) pushNeg();
    let v=spec.stem+(pfv?"-t":"")+"-"+D.MOODSUF[mood]+"="+anchor;
    let vg=spec.gl+(pfv?"-PFV":"")+"-"+moodTag+"="+anchorTag;
    surf.push(v); tw.push(tword(seq[verbIdx].text,v,vg,spec.ipa,true));
    if(isQuestion){ surf.push("vu"); tw.push(tword("?","vu","Q","",true)); punct="?"; }
  }
  for(const t of unknowns){ tw.push(tword(t.text,"—","?","",false)); notes.push("no Sūchel word for '"+t.text+"'"); }
  const content=nominals.length+1;
  return finish(src,surf,tw,notes,content,unknowns.length,punct,"composed");
}

function finish(src,surf,tw,notes,content,unknownN,punct,src_kind){
  if(!surf.length) return wordByWord(src,enWords(src));
  const total=content+unknownN, conf=Math.round(90*content/(total||1))/100;
  const text=surf.join(" ")+punct;
  const gloss=tw.map(w=>w.gloss).join(" ");
  const ipa=surf.join(" ");
  if(unknownN) notes.push("some words were left untranslated; confidence lowered");
  notes.push("composed client-side — run ‘odylang serve’ for the full grammar engine");
  return {dir:"en2su",su:text,ipa:"",gloss:gloss,tokens:tokenizeCareful(text),
    syl:syllabify(surf),words:tw,conf:conf,notes:notes,src:conf>=0.9?"composed":(conf>=0.4?"word-by-word":"scaffold"),en:src};
}
function scaffold(src,unknowns,why){
  return {dir:"en2su",su:"[?]",ipa:"",gloss:"[?]",tokens:[],syl:[],words:[],
    conf:0.1,notes:[why+": could not compose a Sūchel clause"],src:"scaffold",en:src};
}
function wordByWord(src,words){
  const tw=[]; let known=0;
  for(const w of words){
    if(inSet(D.DROP,w)) continue;
    const nn=nounRef(w), lv=lemmaVerb(w);
    if(nn){ tw.push(tword(w,nn.form,nn.gloss,nn.ipa,true)); known++; }
    else if(lv){ tw.push(tword(w,lv.spec.stem,lv.spec.gl,lv.spec.ipa,true)); known++; }
    else if(has(D.PRON_SUBJ,w)){ const p=D.PRON_SUBJ[w]; tw.push(tword(w,p.su,p.gl,p.ipa,true)); known++; }
    else tw.push(tword(w,"—","?","",false));
  }
  if(!tw.length) return scaffold(src,[],"no lexical match");
  const conf=Math.round(60*known/(tw.length||1))/100;
  const su=tw.filter(w=>w.known).map(w=>w.su).join(" ");
  return {dir:"en2su",su:su||"—",ipa:"",gloss:tw.map(w=>w.su+"="+w.gloss).join(" "),
    tokens:tokenizeCareful(su),syl:syllabify(tw.filter(w=>w.known).map(w=>w.su)),words:tw,conf:conf,
    notes:["word-by-word gloss — run ‘odylang serve’ for the full grammar engine"],
    src:"word-by-word",en:src};
}
/* a light syllable/rhythm array for composed lines: one beat per surface word,
   stress the verb-ish final beat, mark long vowels. */
function syllabify(surf){
  const out=[];
  surf.forEach((w,i)=>{ if(i)out.push("/"); const long=/[āēīōū:]/.test(w);
    let s=w.replace(/[-=]/g,"").replace(/[āēīōū]/g,"a"); if(long)s+=":";
    out.push(i===surf.length-1?s.toUpperCase():s); });
  return out;
}

/* =====================================================================
   SU -> EN peel (compact port of translate.from_suchel)
   ===================================================================== */
const PUNCT=" \t\r\n.,!?:;…—–\"'“”‘’()[]{}";
function fwd(form){ return form?D.STEMS[form.toLowerCase()]:null; }
function stripPunct(s){ let a=0,b=s.length; while(a<b&&PUNCT.indexOf(s[a])>=0)a++; while(b>a&&PUNCT.indexOf(s[b-1])>=0)b--; return s.slice(a,b); }
function peel(core){
  if(fwd(core)) return [core,[]];
  const tags=[];
  while(core.indexOf("-")>=0){
    const idx=core.lastIndexOf("-"), head=core.slice(0,idx), last=core.slice(idx+1).toLowerCase();
    if(has(D.MOOD_PEEL,last)) tags.push(["MOOD",D.MOOD_PEEL[last]]);
    else if(last==="t") tags.push(["PFV","PFV"]);
    else if(last==="u") tags.push(["IMP","IMP"]);
    else if(has(D.HCASE,last)) tags.push(["CASE",D.HCASE[last]]);
    else if(last==="mai") tags.push(["ENT","ENT"]);
    else if(last==="i") tags.push(["PL","PL"]);
    else break;
    core=head; if(fwd(core)) break;
  }
  let guard=0;
  while(!fwd(core)&&guard<6){
    guard++; let did=false;
    for(const [suf,ktag,label] of D.SOLID){
      if(core.toLowerCase().endsWith(suf)&&core.length>suf.length&&fwd(core.slice(0,-suf.length))){
        tags.push([ktag,label]); core=core.slice(0,-suf.length); did=true; break;
      }
    }
    if(!did) break;
  }
  return [core,tags.reverse()];
}
function parseWord(raw){
  const tok=stripPunct(raw); if(!tok||tok==="|") return null;
  const low=tok.toLowerCase();
  if(has(D.FUNC,low)) return {kind:"func",raw:tok,tag:D.FUNC[low]};
  if(low==="ne") return {kind:"gap",raw:tok,tag:"GAP"};
  if(has(D.DIRPEEL,low)&&tok.indexOf("=")<0) return {kind:"dir",raw:tok,tag:D.DIRPEEL[low]};
  let anchor="",core=tok;
  if(core.indexOf("=")>=0){ const i=core.lastIndexOf("="); const anc=core.slice(i+1).toLowerCase(); core=core.slice(0,i); anchor=D.ANCHOR_GLOSS[anc]||anc; }
  let neg=false;
  if(core.toLowerCase().indexOf("vo-")===0){ neg=true; core=core.slice(3); }
  const [stem,tags]=peel(core);
  const ref=fwd(stem), known=!!ref;
  const gl=(D.PRON_ENGLISH[stem]||(ref?ref.gl:stem));
  return {kind:"word",raw:tok,known:known,stem:stem,gl:gl,tags:tags,anchor:anchor,neg:neg,ipa:ref?ref.ipa:"",domain:ref?ref.domain:""};
}
function chunkGloss(p){
  if(p.kind==="func"||p.kind==="gap"||p.kind==="dir") return p.tag;
  let out=(p.neg?"NEG-":"")+(p.gl||p.stem);
  for(const [,label] of p.tags) out+="-"+label;
  if(p.anchor) out+="="+p.anchor;
  return out;
}
function paraphrase(parsed){
  if(!parsed.length) return "";
  const main=[],adv=[]; let q=false,neg=false;
  for(const p of parsed){
    if(p.kind==="gap"){ main.push("— (the gap)"); continue; }
    if(p.kind==="func"){ if(p.tag==="NEG")neg=true; else if(p.tag==="Q")q=true; continue; }
    if(p.kind==="dir"){ adv.push("("+p.tag.toLowerCase()+")"); continue; }
    let w=p.gl||p.stem; if(p.neg)neg=true;
    if(p.tags.some(t=>t[0]==="PFV")) w+=" (perfective)";
    main.push(w);
    for(const [,label] of p.tags){ const a=D.MOOD_ADV[label]; if(a)adv.push(a); }
    if(p.anchor){ const a=D.ANCHOR_ADV[p.anchor]; if(a&&adv.indexOf(a)<0)adv.push(a); }
  }
  let body=main.join(" "); if(neg) body=body?("not "+body):"not";
  let text=body; if(adv.length) text+=" — "+adv.join(", "); text+=q?"?":"."; return text.trim();
}
function peelSU(src){
  const parsed=[];
  for(const raw of src.split(/\s+/)){ const p=parseWord(raw); if(p)parsed.push(p); }
  if(!parsed.length) return {dir:"su2en",para:"",gloss:"",tokens:[],words:[],conf:0,notes:["nothing to parse"],su:src};
  const gloss=parsed.map(chunkGloss).join(" ");
  const words=parsed.map(p=>{
    if(p.kind!=="word") return tword(p.tag,p.raw,chunkGloss(p),"",true);
    return tword(p.gl||p.stem,p.raw,chunkGloss(p),p.ipa,p.known);
  });
  const total=parsed.length, known=parsed.filter(p=>p.known||p.kind==="func"||p.kind==="dir"||p.kind==="gap").length;
  const conf=total?Math.round(100*known/total)/100:0;
  const notes=[];
  for(const p of parsed){ if(p.kind==="word"&&!p.known) notes.push("unknown stem '"+p.stem+"' kept verbatim"); }
  notes.push("morphology peeled client-side from the phoneme grammar");
  const tokens=[]; parsed.forEach((p,i)=>{ if(i)tokens.push(" "); if(p.kind==="gap"){tokens.push("|");return;} tokenizeCareful(p.raw).forEach(t=>tokens.push(t)); });
  return {dir:"su2en",para:paraphrase(parsed),gloss:gloss,tokens:tokens,words:words,conf:conf,notes:notes,su:src};
}

/* =====================================================================
   direction detection (mirror of translate.detect_direction)
   ===================================================================== */
function detectDir(text){
  let su=0,en=0,tot=0;
  for(const raw of text.split(/\s+/)){
    const t=stripPunct(raw); if(!t||t==="|") continue;
    const low=t.toLowerCase(); let flag=null;
    if(/[āēīōū]/.test(low)||t.indexOf("=")>=0) flag=true;
    else if(has(D.FUNC,low)||has(D.DIRPEEL,low)) flag=true;
    else { const p=parseWord(t); if(p){ flag=(p.kind!=="word")?true:!!p.known; } }
    if(flag===null) continue; tot++; if(flag)su++; else if(inSet(D.ENMARK,low))en++;
  }
  return (tot&&su>0&&su>=en)?"su2en":"en2su";
}

/* =====================================================================
   rendering the transcript
   ===================================================================== */
const chat=document.getElementById("chat");
const CARDS=[];   /* keep result objects so re-lettering on hand-switch works */
function toast(m){
  const t=document.createElement("div"); t.className="toast"; t.textContent=m;
  document.body.appendChild(t); setTimeout(()=>t.remove(),2600);
}
function confChip(conf,src){
  let cls="composed",label="COMPOSED "+conf.toFixed(2);
  if(conf>=1){ cls="attested"; label="ATTESTED 1.00"; }
  else if(src==="word-by-word"){ cls="wbw"; label="WORD-BY-WORD "+conf.toFixed(2); }
  else if(conf<0.4){ cls="scaffold"; label="SCAFFOLD "+conf.toFixed(2); }
  else if(conf<0.9){ cls="wbw"; label="PARTIAL "+conf.toFixed(2); }
  return `<span class="chip ${cls}">${label}</span>`;
}
function glossUnits(words){
  if(!words||!words.length) return "";
  return `<div class="gloss">`+words.map(w=>
    `<div class="gunit${w.known?"":" unk"}"><span class="g-su">${esc(w.su)}</span><span class="g-gl">${esc(w.gloss)}</span></div>`
  ).join("")+`</div>`;
}
function beatRow(syl){
  if(!syl||!syl.length) return "";
  return `<span class="rhythm">`+syl.map(t=>{
    if(t==="/") return `<span class="beat sp">/</span>`;
    if(t==="|") return `<span class="beat gap">▮</span>`;
    return `<span class="beat${/[A-Z]/.test(t)?" hi":""}">${esc(t)}</span>`;
  }).join("")+`</span>`;
}
function addYou(text){
  const m=document.createElement("div"); m.className="msg you";
  m.innerHTML=`<span class="who">YOU</span><div class="bub">${esc(text)}</div>`;
  chat.appendChild(m); scrollDown();
}
function addCard(res){
  const idx=CARDS.push(res)-1;
  const m=document.createElement("div"); m.className="msg agent";
  const su2en=res.dir==="su2en";
  const speakText=su2en?respellSuchel(res.su):(res.ipa?respellIpa(res.ipa):respellSuchel(res.su));
  const hasRhythm=!su2en && res.syl && res.syl.length;
  const hasVoice=res.tokens && res.tokens.length;
  let inner=`<span class="who">TRANSLATOR</span><div class="card ${su2en?"su2en":""}" data-i="${idx}">`;
  if(su2en){
    inner+=`<div class="para">${esc(res.para||"(no reading)")}</div>`;
    inner+=`<div class="eng">source: <span style="color:var(--gold)">${esc(res.su)}</span></div>`;
    inner+=glossUnits(res.words);
  } else {
    inner+=`<div class="su">${esc(res.su)}</div>`;
    if(res.ipa) inner+=`<div class="ipa">[${esc(res.ipa)}]</div>`;
    if(res.en) inner+=`<div class="eng">for: “${esc(res.en)}”</div>`;
    inner+=glossUnits(res.words);
  }
  inner+=`<div class="navc" data-navc="${idx}"></div>`;
  inner+=`<div class="audio">`+
    `<button class="ab" data-act="voice" data-i="${idx}"${hasVoice?"":" disabled"}>▶ VOICE</button>`+
    `<button class="ab gold" data-act="rhythm" data-i="${idx}"${hasRhythm?"":" disabled"}>▶ RHYTHM</button>`+
    `<button class="ab blue" data-act="speak" data-i="${idx}"${speakText?"":" disabled"}>▶ SPEAK</button>`+
    (hasRhythm?beatRow(res.syl):"")+`</div>`;
  inner+=`<div class="meta">${confChip(res.conf,res.src)}</div>`;
  if(res.notes&&res.notes.length) inner+=`<div class="note">`+res.notes.map(n=>esc(n).replace(/‘odylang serve’/g,"<code>odylang serve</code>")).join(" · ")+`</div>`;
  inner+=`</div>`;
  m.innerHTML=inner; chat.appendChild(m);
  letterCard(idx);
  scrollDown();
}
function letterCard(idx){
  const box=chat.querySelector(`[data-navc="${idx}"]`); if(!box) return;
  const res=CARDS[idx];
  box.innerHTML=stripSvg(res.tokens);
}
function reletterAll(){ CARDS.forEach((_,i)=>letterCard(i)); }
function scrollDown(){ requestAnimationFrame(()=>{ chat.scrollTop=chat.scrollHeight; window.scrollTo(0,document.body.scrollHeight); }); }

/* the translate dispatcher */
let DIR="auto";
function respondTo(text){
  addYou(text);
  let dir=DIR==="auto"?detectDir(text):DIR;
  let res;
  if(dir==="su2en"){ res=peelSU(text.trim()); }
  else {
    const hit=IDIOM_MAP[normIdiom(text)];
    if(hit){ res={dir:"en2su",su:hit.su,ipa:hit.ipa,gloss:hit.gloss,tokens:hit.tokens,syl:hit.syl,
                  words:idiomWords(hit),conf:hit.conf,notes:hit.notes.slice(),src:hit.src,en:hit.en}; }
    else res=composeEN(text);
  }
  addCard(res);
}
function idiomWords(hit){
  /* rebuild interlinear units from the precomputed gloss + tokens split by spaces */
  const glosses=(hit.gloss||"").split(/\s+/), forms=(hit.su||"").replace(/[.!?]$/,"").split(/\s+/);
  const out=[];
  for(let i=0;i<Math.max(glosses.length,forms.length);i++){
    out.push(tword("",forms[i]||"",glosses[i]||"","",true));
  }
  return out;
}

/* =====================================================================
   audio button + control wiring
   ===================================================================== */
chat.addEventListener("click",e=>{
  const b=e.target.closest(".ab"); if(!b||b.disabled) return;
  const res=CARDS[+b.dataset.i]; if(!res) return;
  const act=b.dataset.act;
  if(act==="voice") playVoice(res.tokens);
  else if(act==="rhythm") playRhythm(res.syl);
  else if(act==="speak"){ const t=res.dir==="su2en"?respellSuchel(res.su):(res.ipa?respellIpa(res.ipa):respellSuchel(res.su)); speak(t); }
});

const dirSeg=document.getElementById("dir");
dirSeg.addEventListener("click",e=>{ const b=e.target.closest("button"); if(!b)return;
  DIR=b.dataset.d; dirSeg.querySelectorAll("button").forEach(x=>x.classList.toggle("on",x===b));
  document.getElementById("in").focus();
});
const handSeg=document.getElementById("hand");
handSeg.addEventListener("click",e=>{ const b=e.target.closest("button"); if(!b)return;
  GSTYLE=b.dataset.h; handSeg.querySelectorAll("button").forEach(x=>x.classList.toggle("on",x===b));
  reletterAll();
});

const dock=document.getElementById("dock"), input=document.getElementById("in");
dock.addEventListener("submit",e=>{ e.preventDefault(); const v=input.value.trim(); if(!v)return;
  respondTo(v); input.value=""; input.focus(); });

/* starter chips: a friendly spread across attested + composed */
const STARTERS=["hello","take her down","open the seam","we crossed","I go down",
  "do you hear me","surface again","she has gone adrift","ver ish-ol.","hōl-t-eshe=zu.","kad ver-a=ka vu?"];
const stEl=document.getElementById("starters");
stEl.innerHTML=STARTERS.map(s=>`<button class="s">${esc(s)}</button>`).join("");
stEl.addEventListener("click",e=>{ const b=e.target.closest(".s"); if(!b)return; respondTo(b.textContent); });

/* opening line from the agent */
(function greet(){
  const hi=IDIOM_MAP[normIdiom("hello")]||D.IDIOMS[0];
  addCard({dir:"en2su",su:hi.su,ipa:hi.ipa,gloss:hi.gloss,tokens:hi.tokens,syl:hi.syl,
    words:idiomWords(hi),conf:hi.conf,notes:["I am the Sūchel translator. Say hello, or try a phrase — EN↔SŪCHEL, AUTO-detected. "+(D.IDIOMS.length)+" phrases loaded offline."],
    src:hi.src,en:"hello"});
})();
"""


# ---------------------------------------------------------------------------
# assembly


def _data_json() -> str:
    return json.dumps(collect(), ensure_ascii=False).replace("</", "<\\/")


#: where the "THE CODEX ↗" link points by default — the sibling file that
#: ``odylang web`` writes.  ``odylang serve`` overrides it with ``/codex``;
#: the published artifact overrides it with the codex's artifact URL.
DEFAULT_CODEX_URL = "odylang-web.html"


def _markup(codex_url: str) -> str:
    return _MARKUP.replace("__CODEX_URL__", codex_url)


def page_fragment(codex_url: str = DEFAULT_CODEX_URL) -> str:
    """Title + style + markup + data + script, WITHOUT the html/head/body
    skeleton — for a host that supplies the document shell (mirrors
    :func:`odylang.webgen.fragment`).  ``codex_url`` is where the header's
    "THE CODEX" link points."""
    return (f"<title>{_TITLE}</title>\n<style>{_CSS}</style>\n{_markup(codex_url)}\n"
            f"<script>window.ODYT = {_data_json()};</script>\n"
            f"<script>{_JS}</script>\n")


def page(codex_url: str = DEFAULT_CODEX_URL) -> str:
    """A COMPLETE standalone HTML document (offline; embedded snapshot).
    ``codex_url`` sets the target of the header's link to the codex."""
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{_TITLE}</title>\n<style>{_CSS}</style>\n"
            "</head>\n<body>\n"
            f"{_markup(codex_url)}\n"
            f"<script>window.ODYT = {_data_json()};</script>\n"
            f"<script>{_JS}</script>\n"
            "</body>\n</html>\n")


def write(path: str, codex_url: str = DEFAULT_CODEX_URL) -> None:
    """Write the standalone document to ``path``."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page(codex_url))
