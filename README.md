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
* **The interactive codex** (`odylang.webgen`) — `odylang web -o codex.html`
  builds the whole system into ONE self-contained web page (no server, no
  dependencies, no network): the shibboleth explorer with live derivation
  traces, searchable lexicons, the 41 lines with playable rhythm and
  Navcher lettering in both hands, the texts, the sisters, and a
  ship-carve-your-own writer. A prebuilt copy ships as
  `examples/odylang-web.html` — just open it in a browser.
* **Core** — `phonology` (segments, seam-aware syllabification, IPA),
  `word` (the four-rule stress algorithm: *the mood carries the beat*),
  `soundchange` (the ordered rewrite engine with full derivation traces),
  `proto` (the Old Pelagic root lexicon).

## Quickstart

The implementation lives on the `claude/peterson-language-system-q2z1l9`
branch — check it out first if you cloned `main`.

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
tests/                ~840 tests locking every documented fact
examples/             rendered Navcher SVGs + the render script
```
