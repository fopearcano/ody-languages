# odylang — the languages of the crossable universe

A working implementation of the language family described in the
NERV//Pelagian Assembly codices (`docs/`), built the way David J. Peterson
builds languages (*The Art of Language Invention*, also in `docs/`): one
proto-tongue, ordered regular sound changes per daughter, and grammars that
encode what each speaker community cannot afford to be vague about.

Every documented form in the six codices — every lexicon row, place name,
phrasebook line, interlinear gloss, IPA transcription, stress pattern, and
glyph coordinate — is reproduced by this package and locked by the test
suite (~840 tests).

## The family

```
                 OLD PELAGIC (Pelgar) — the tongue before the seam
                 SOV, fully inflected · no moods, no anchors, no ne
   ┌──────────┬───────────┬──────────┬───────────┬─────────────┐
 Sūchel     Nubhel      Rudgar      Sel        Beltsel      Lorkel
 the fleets the divers  Mars        Maren      Belgar       the Wolori
 says jel   says yel    says ghel   says zel   says dzel    says gel
 7 changes  7 changes   keeps *w,*h drowns *w  cannot hold  no changes:
 5 moods    3 moods     (conserva-  (liquid)   its breath   the ancestor
 3 anchors  debt anchor  tive)                 (eroded)     at work
```

* **Sūchel** (`odylang.suchel`, `suchel_grammar`, `phrasebook`,
  `suchel_texts`) — the Crossing-Speech. Seven sound changes (SC-1…7);
  verb template `STEM-(PFV)-MOOD=ANCHOR`; the four systems no human
  language has: five veridical moods (T `-a`, T⁻ `-im`, T⁺ `-ur`,
  T• `-eshe`, F `vo … -a`), three temporal anchors (`=ka` beacon, `=mi`
  proper, `=zu` dark), tower-absolute depth directionals (`nuv`/`hau`),
  and the gap particle `ne` that stands where a verb may not. Includes
  the full 41-line phrasebook and the three glossed texts.
* **Nubhel** (`odylang.nubhel`, `nubhel_grammar`, `nubhel_texts`) — the
  Deep-Speech of the rival vertical fleet. Seven changes with D-3 ordered
  before D-1 (every medial *h* is secondary); three moods and **no**
  seam-truth (narrating a crossing forces a code-switch into Sūchel); the
  debt anchor `=nu` with the offset signature (`Mora, +212`); five degrees
  of depth; `neks`, the gap as courtesy.
* **Rudgar, Sel, Beltsel** (`odylang.rudgar`, `sel`, `beltsel`) — the
  sisters at naming depth: full sound-change sets and twenty derived place
  names each.
* **Lorkel & Notation** (`odylang.lorkel`) — working Old Pelagic, the
  Wolori's living technical register, with the eight Neo-Pelagic coinages;
  and the zero-tongue's notation-names.
* **The shibboleth** (`odylang.family`) — one proto-word through every
  mouth: ask a stranger to name the seam and their mouth files their birth
  certificate.
* **Navcher** (`odylang.navcher`) — the fleet script, ported glyph-for-glyph
  from the script codex (one curve in the whole system, and it refuses to
  close), rendered to SVG in both careful hand and bridge hand.
  Samples in `examples/navcher/`.
* **The vocabulary supplement** (`odylang.vocabulary`) — ~150 words of
  daily speech (kin, body, sea, time, tools, everyday verbs…), coined as
  new Old Pelagic roots and **derived by the engines, never typed** — so
  every word automatically exists in all five daughters with its regular
  sound laws applied (*kir- 'cold' → Sūchel chir, Nubhel hir, Rudgar khir,
  Sel sir, Beltsel tsir). Homophone collisions with the canon lexicon are
  engine-checked; the two that exist are deliberate and documented.
  `odylang vocab --domain sea`, full table in
  `docs/09_vocabulary-supplement.md`.
* **The Current Hand** (`odylang.currenthand`) — the redesigned script,
  implemented from a Claude Design handoff (design 07-E): one connected,
  pressured pen-line per word riding a "current", the featural system
  re-expressed (knot height = place, a released drop = voicing, ripples =
  vowels, a breath-arc = length; upright sigils — T• the filled eye, =zu
  the one straight uniform stroke). The Python engine is byte-exact with
  the design prototype (locked by tests against digests generated from the
  handoff's own JS). `odylang write --hand current` letters any line; its
  faceted sacred sibling, the **Logos hand** (`--hand logos`), is the same
  skeleton cut into straight facets — the old carved script of the ancestral
  tongue. `odylang page record|scrawl|watch|vigil|disc --seed N` renders the
  five page registers (samples in `examples/currenthand/`).
* **The translator** (`odylang.translate`, `tts`, `translator_web`, `server`)
  — a full English↔Sūchel translation system you can talk to and hear.
  The engine generates Sūchel *through the grammar* (SOV, the verb carries
  mood + temporal anchor) and indexes its bilingual dictionary from the
  *derived* lexicon, so it never invents words; it tries the attested
  phrasebook first, composes otherwise, and is honest about confidence and
  unknown words. `odylang.tts` is a dependency-free **formant speech
  synthesizer** — real WAV audio for a language no human speaks, with the
  codex's prosody (the mood carries the beat). `odylang serve` runs a
  stdlib HTTP service (`/translate`, `/tts`, `/openapi.json`) that hosts a
  **translator chat page** and doubles as a **LibreChat tool** — a drop-in
  OpenAPI Action + "Sūchel Translator" agent config in
  `integrations/librechat/` (works with a local model via LM Studio/Ollama
  or with the Anthropic/OpenAI cloud APIs). A prebuilt offline chat page
  ships as `examples/translator.html`.

  ```console
  $ odylang translate "the beacon holds"
  kad tan-a=ka.
    IPA    kad taˈna.ka
    GLOSS  beacon hold-T=BEAC
    conf   0.90  (en2su)
  $ odylang say "surface again" -o hail.wav   # synthesize speech to WAV
  $ odylang serve                              # chat page + LibreChat tool API
  ```
* **The interactive codex** (`odylang.webgen`) — `odylang web -o codex.html`
  builds the whole system into ONE self-contained web page (no server, no
  dependencies, no network): the shibboleth explorer with live derivation
  traces, searchable lexicons, the 41 lines with playable rhythm and
  Navcher lettering in both hands, the texts, the sisters, and a
  write-your-own Navcher box — plus the Current Hand page studies (seeded
  and tweakable) and a SCRIPT HAND toggle (the flowing **Current Hand** or
  the old sacred **Logos** carving) on every lettered line. A prebuilt copy
  ships as
  `examples/odylang-web.html` — just open it in a browser.
* **The printable manual** (`odylang.manual`) — `odylang manual -o
  odylang-manual.pdf` renders the whole language into a real, multi-page
  **PDF grammar, vocabulary & sentence book**: title page, contents,
  phonology and stress, the noun and the verb, the four grammaticalized
  systems, the full lexicon and coined vocabulary in balanced columns, the
  forty-one phrasebook lines and the texts as interlinear glosses, and the
  family shibboleth — every form generated from the package, nothing
  retyped. The PDF is written by a **dependency-free** engine built here from
  scratch: a tiny object/xref writer plus a TrueType reader and *subsetter*
  that embeds a Type0 / Identity-H composite font, so the macrons and IPA
  (`ā`, `ʃ`, `ˈ`, `ː`, `T•`, `Κ`) render true. A prebuilt copy ships as
  `examples/odylang-manual.pdf`.
* **Core** — `phonology` (segments, seam-aware syllabification, IPA),
  `word` (the four-rule stress algorithm: *the mood carries the beat*),
  `soundchange` (the ordered rewrite engine with full derivation traces),
  `proto` (the Old Pelagic root lexicon).

## Quickstart

The implementation lives on the `claude/peterson-language-system-q2z1l9`
branch — check it out first if you cloned `main`.

**Full setup guide (all entry points, LibreChat, troubleshooting): [`SETUP.md`](SETUP.md).**

No dependencies (Python ≥ 3.9), so no install is required: from the repo
root, `python3 -m odylang.cli phrase 40` just works.  For the `odylang`
command, install with `python3 -m pip install -e .` (macOS/zsh usually has
no bare `pip` on PATH); if your Python is externally managed
(Homebrew/PEP 668), use a venv first:

```console
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

```console
$ odylang derive suchel '*suw-kel'
*suw-kel
  SC-1: suwkel -> suwchel
  SC-3: suwchel -> sūchel
  = sūchel

$ odylang family '*gel-'
*gel- through every mouth:
  old pelagic  gel
  lorkel       gel
  suchel       jel
  rudgar       ghel
  sel          zel
  beltsel      dzel
  nubhel       yel

$ odylang phrase 40
40  hōl-t-eshe=zu. enmai ve-a=mi.
    IPA    hoːlˈte.ʃe.zu · ˈen.mai veˈa.mi
    GLOSS  surface-PFV-T•=DARK · 1PL.ENT be-T=PROP
    RHYTHM ho:l TE she zu / EN mai / ve A mi
    “Surfaced. We are — by our own clock.”

$ odylang write --phrase 40 --hand bridge -o line40.svg   # Navcher lettering
$ odylang chart -o navcher.svg                            # the glyph chart
$ odylang phrase --all      # all 41 lines   · odylang texts nubhel
$ odylang lex suchel --domain physics --etym
$ odylang places beltsel    # the capital's twenty names
$ odylang vocab --search water --lang nubhel   # the coined vocabulary
```

As a library:

```python
from odylang.suchel_grammar import verb, pronoun, Sentence
from odylang.suchel import SUCHEL

s = Sentence([pronoun(3), verb("sū", mood="Ts", anchor="zu", pfv=True,
                               gloss="cross")])
s.text()        # 'an sū-t-eshe=zu.'
s.gloss_line()  # '3SG cross-PFV-T•=DARK'
s.ipa()         # 'an suːˈte.ʃe.zu'

SUCHEL.derive("*pelag-ar").trace()   # SC-2: pelagar -> pelgar ...
```

## Fidelity rules

* The codices are the single source of truth. Proto-derived words are
  **derived by the engine**, not transcribed — tests assert both the
  surface form and *which* changes fired, against the codex's own
  derivation column.
* Where a codex flags an irregularity (`sū` "v., irregular"; `nav`
  "shortening in closed syll."; Nubhel `ve` for expected †`be`), it is
  encoded as data carrying the codex's note — irregularity is never
  silent.
* Where the codices disagree with each other on a detail (comma
  renderings in IPA, `ish-mai` vs `ishmai` spacing, the one anchor
  glossed `=BEACON`), the implementation follows the majority reading and
  documents the choice in the owning module's docstring.
* The phrasebook and texts are **generated through the grammar API**, not
  stored as strings: if a documented sentence failed to come out of the
  morphology, the tests would fail. Grammar rules with teeth: building a
  Nubhel verb in T• raises `SeamTruthError`; a motion verb without its
  depth satellite raises `MotionSatelliteError`.

## Layout

```
docs/                 the six codices + Peterson's book (source of truth)
odylang/              the package (stdlib only)
tests/                1400+ tests locking every documented fact
examples/             rendered artifacts: Navcher/Current-Hand SVGs, the web
                      codex, the translator page, audio, the PDF manual
```
