# Navcher — character & sound reference (redesign brief)

A complete inventory of the fleet script of Sūchel: every character, its
sound, its structural role, and its current geometry — everything needed
to **redesign the letterforms without breaking the writing system**.
All values are generated from `odylang` (which derives them from the
script codex, `docs/03_qtr-script.html`); nothing here is hand-copied.

---

## 1. How the script works (read before redesigning)

Navcher is **featural**: letter shapes systematically encode phonetic
features, the way Korean Hangul does. The current forms use three rules:

| feature | current encoding |
|---|---|
| **place of articulation** | head position: labials head-left · alveolars head-center · velars head-right |
| **voicing** | add a foot-stroke |
| **frication** | add a slash |

Learn six letters and you can predict the rest. Any redesign should keep
*some* systematic feature encoding — the specific visual devices (head
position, foot, slash) are yours to reinvent.

**The em box.** Glyphs live in a 140-unit-tall box, baseline at 120.
Consonants are full-height (10–120) and 100 units wide; vowels sit
half-height (76–120, the fossil of their diacritic past) and are 60 units
wide; operators are 60 wide; the gap-stroke is 70 and full-height (4–136).
A word-space is one full consonant width of silence.

**Two hands, one alphabet.** *Careful hand* spells every suffix
phonetically (liturgy, law, log-of-record). *Bridge hand* compresses the
verb's mood and anchor into sigils (instrument panels, hull marks, haste):
`ver-a=ka` letters as v·e·r·a·k·a in careful hand, v·e·r·[T-sigil]·[ka-sigil]
in bridge hand. A redesign must keep letters and sigils visually distinct
classes.

**Digraph policy.** `ch sh` are single letters. `x` /ks/ letters as k+s;
`th` letters as t+h; the diphthongs `ai au` letter as two vowels.

---

## 2. Consonants — 17 letters

| letter | sound | anchor for an English mouth | featural slot | current form | strokes | freq ‰ |
|---|---|---|---|---|---|---|
| **p** | /p/ | as English | labial stop | head-left box on a stem | 2 | 6 |
| **b** | /b/ | as English | labial stop, voiced | p + voice-foot | 3 | 0 |
| **t** | /t/ | as English | alveolar stop | head-center box under a bar | 3 | 49 |
| **d** | /d/ | as English | alveolar stop, voiced | t + voice-foot | 4 | 32 |
| **k** | /k/ | sky (light aspiration at most) | velar stop | head-right box on a stem | 2 | 32 |
| **g** | /g/ | go (always hard) | velar stop, voiced | k + voice-foot | 3 | 5 |
| **ch** | /tʃ/ | church | postalveolar affricate | T-frame + frication slash | 3 | 4 |
| **j** | /dʒ/ | judge (jel = 'jell') | postalveolar affricate, voiced | ch + voice-foot | 4 | 19 |
| **v** | /v/ | vine | labial fricative, voiced | slash + foot | 2 | 62 |
| **s** | /s/ | sea (always voiceless) | alveolar fricative | the zigzag | 1 | 22 |
| **z** | /z/ | zoo | alveolar fricative, voiced | s reversed + foot | 2 | 12 |
| **sh** | /ʃ/ | ship | postalveolar fricative | zigzag + top bar | 2 | 29 |
| **m** | /m/ | as English | labial nasal | double stem, bridged | 3 | 58 |
| **n** | /n/ | as English | alveolar nasal | half-frame | 3 | 81 |
| **r** | /ɾ ~ r/ | Italian/Spanish r — tapped between vowels, brief trill word-initially; never the English glide | alveolar tap/trill | stem + mid-tick | 2 | 62 |
| **l** | /l/ | as English (crisp finals) | alveolar lateral | stem + long foot | 2 | 64 |
| **h** | /h/ | hold — word-initial only; elsewhere old *h is already vowel length | glottal ('the threshold letter') | a stem with a gap in it — the letter that is mostly absence | 2 | 27 |

Frequency 0 for **b** is real: the letter exists (the alphabet is
family-wide; *bel- 'hearth' lives in the sisters) but the attested Sūchel
corpus barely touches p/b/g/ch — rare letters can afford complex shapes.

Voicing pairs to preserve as visual pairs: p/b · t/d · k/g · ch/j · s/z
(and v patterns with the voiced set). **he** (h) is special: /h/ survives
only word-initially (hōl, hau, hep) — everywhere else old *h has already
become vowel length — so its letter is drawn as presence interrupted by
absence. Keep that idea; it is the best letter in the script.

## 3. Vowels — 5 letters + the held-breath bar

| letter | sound | anchor for an English mouth | current form | freq ‰ |
|---|---|---|---|---|
| **a** | /a/ | father (short) — never as in 'cat' | the wedge | 110 |
| **e** | /e/ | bed — crisp, never 'ay'-glided | the level | 140 |
| **i** | /i/ | machine (short) — never as in 'bit' | the tick | 58 |
| **o** | /o/ | story (short) — pure, no 'ow' glide | the diamond | 53 |
| **u** | /u/ | rude (short) — never as in 'cut' | the cup | 74 |

**Length** (ā ē ī ō ū = /aː eː iː oː uː/) is a bar drawn above the vowel:
*length is quality held, not changed — a long vowel is a held breath.*
One stroke of patience; a redesign may restyle the bar but should keep
length as a diacritic operation on the short vowel, not five new letters.

## 4. Operator sigils — grammar you can carve in two strokes

Every finite verb carries a mood and an anchor, so bridge hand gives each
a sigil. The five moods are variations on ONE base shape (currently a
square) — keep that family resemblance, whatever the new base shape is.

| token | glyph key | writes | meaning | current form |
|---|---|---|---|---|
| `@T` | `mT` | mood T  ·  -a | classically true; settled | the plain square |
| `@T-` | `mTm` | mood T⁻ ·  -im | true-as-approached (IR) | square + tick left |
| `@T+` | `mTp` | mood T⁺ ·  -ur | held-from-above, unaccredited (UV) | square + tick right |
| `@Ts` | `mTs` | mood T• ·  -eshe | seam-true; self-dual | the seam-mark — the only FILLED shape in the script |
| `@F` | `mF` | mood F  ·  vo …-a | false (negated plain) | square crossed out |
| `=ka` | `aka` | anchor =ka | beacon time — shared, verifiable | the beacon pulse (zigzag wave) |
| `=mi` | `ami` | anchor =mi | proper time — the ship's own clock | the chest-stroke (single diagonal) |
| `=zu` | `azu` | anchor =zu | dark time — beyond coverage | the open hook — the ONLY CURVE in the system, unclosed because unanchored |
| `|` | `gap` | ne — the gap | the interval that has no sentence | a full-height bar; written, ne is not spelled |
| `?` | `q` | vu — question | final polar-question particle | the rising pair |

## 5. Letter frequency (design weight)

Computed over the full 41-line phrasebook letter stream plus every lexicon
citation form — frequent letters deserve the simplest, fastest shapes:

```
  e:140  a:110  n:81  u:74  l:64  v:62  r:62  i:58  m:58  o:53  t:49
  k:32  d:32  sh:29  h:27  s:22  j:19  z:12  p:6  g:5  ch:4   (per-mille)
```

## 6. Hard invariants vs. degrees of freedom

**Must survive any redesign** (the writing system itself):

1. One letter per phoneme: 17 consonants, 5 vowels, length as a diacritic.
2. Featural logic: voicing pairs look like pairs; some visible feature
   system maps sound structure to shape structure.
3. The five mood sigils are one family; **T• is maximally marked** (today:
   the only filled shape — 'the seam-mark').
4. **=zu is the outlier by construction** (today: the only curve, and it
   refuses to close — unanchored). Whatever your style, =zu must break
   its rule.
5. The gap-mark ne is not a letter: a mark that is a held silence,
   full-height, wide-set. It must read as *absence*, not as writing.
6. Vowels visually subordinate to consonants (their diacritic ancestry).
7. Letters ≠ sigils at a glance (careful vs bridge hand must never blur).

**Free to change** (the current rendering, not the system):

- The stencil aesthetic. Straight-only strokes exist because the fleets
  cut letters from hull plate ('stencil-safe'); a display-grade or HUD
  hand may use curves, weights, joins, glow, connection — see the
  CURRENT HAND / LOGOS toggle in the web codex for a presentational
  precedent. If you add curves, consider what that does to invariant 4:
  =zu's specialness must be re-expressed, not lost.
- Proportions, stroke count, the em-box metrics, head/foot/slash devices,
  the specific vowel shapes.

## 7. Deliverable format (drop-in)

A redesign is machine-usable if each glyph is supplied in the schema of
`odylang/navcher.py` `GLYPHS` — the renderer, the CLI (`odylang write`,
`odylang chart`) and the web codex all consume it directly:

```python
Glyph(w=<advance width>,
      strokes=(<polyline as flat x,y,x,y,... tuple>, ...),
      paths=(<SVG path d string, for curves>, ...),
      fills=(<SVG path d string, filled>, ...))
```

Test any candidate set against these words (they exercise every device):
**Sūchel** (long vowel + digraph) · **Sōrn** (long + cluster) · **jel**
(the seam: 'the humblest word in the cosmology is four cuts of a blade')
· **zukad** · `ver ish-ol.` (the hail) · `hōl-t-eshe=zu. enmai ve-a=mi.`
(litany line 40 in bridge hand: T•-sigil, =zu hook, plain-T, chest-stroke).

## Appendix — current geometry, verbatim

Long-vowel bar (drawn above a vowel): polyline `8,62 → 52,62`.

```json
{
 "p": {
  "w": 100,
  "strokes": [
   [
    70,
    10,
    70,
    120
   ],
   [
    70,
    10,
    30,
    10,
    30,
    45,
    70,
    45
   ]
  ]
 },
 "b": {
  "w": 100,
  "strokes": [
   [
    70,
    10,
    70,
    120
   ],
   [
    70,
    10,
    30,
    10,
    30,
    45,
    70,
    45
   ],
   [
    70,
    120,
    45,
    120
   ]
  ]
 },
 "t": {
  "w": 100,
  "strokes": [
   [
    10,
    10,
    90,
    10
   ],
   [
    50,
    10,
    50,
    120
   ],
   [
    35,
    10,
    35,
    40,
    65,
    40,
    65,
    10
   ]
  ]
 },
 "d": {
  "w": 100,
  "strokes": [
   [
    10,
    10,
    90,
    10
   ],
   [
    50,
    10,
    50,
    120
   ],
   [
    35,
    10,
    35,
    40,
    65,
    40,
    65,
    10
   ],
   [
    50,
    120,
    75,
    120
   ]
  ]
 },
 "k": {
  "w": 100,
  "strokes": [
   [
    30,
    10,
    30,
    120
   ],
   [
    30,
    10,
    70,
    10,
    70,
    45,
    30,
    45
   ]
  ]
 },
 "g": {
  "w": 100,
  "strokes": [
   [
    30,
    10,
    30,
    120
   ],
   [
    30,
    10,
    70,
    10,
    70,
    45,
    30,
    45
   ],
   [
    30,
    120,
    55,
    120
   ]
  ]
 },
 "ch": {
  "w": 100,
  "strokes": [
   [
    10,
    10,
    90,
    10
   ],
   [
    50,
    10,
    50,
    120
   ],
   [
    30,
    22,
    70,
    60
   ]
  ]
 },
 "j": {
  "w": 100,
  "strokes": [
   [
    10,
    10,
    90,
    10
   ],
   [
    50,
    10,
    50,
    120
   ],
   [
    30,
    22,
    70,
    60
   ],
   [
    50,
    120,
    75,
    120
   ]
  ]
 },
 "s": {
  "w": 100,
  "strokes": [
   [
    70,
    10,
    30,
    45,
    70,
    80,
    30,
    115
   ]
  ]
 },
 "z": {
  "w": 100,
  "strokes": [
   [
    30,
    10,
    70,
    45,
    30,
    80,
    70,
    115
   ],
   [
    45,
    120,
    70,
    120
   ]
  ]
 },
 "sh": {
  "w": 100,
  "strokes": [
   [
    20,
    10,
    80,
    10
   ],
   [
    70,
    22,
    30,
    55,
    70,
    88,
    30,
    120
   ]
  ]
 },
 "v": {
  "w": 100,
  "strokes": [
   [
    70,
    10,
    30,
    120
   ],
   [
    30,
    120,
    55,
    120
   ]
  ]
 },
 "m": {
  "w": 100,
  "strokes": [
   [
    30,
    10,
    30,
    120
   ],
   [
    70,
    10,
    70,
    120
   ],
   [
    30,
    10,
    70,
    10
   ]
  ]
 },
 "n": {
  "w": 100,
  "strokes": [
   [
    30,
    10,
    30,
    120
   ],
   [
    30,
    10,
    70,
    10
   ],
   [
    70,
    10,
    70,
    55
   ]
  ]
 },
 "r": {
  "w": 100,
  "strokes": [
   [
    30,
    10,
    30,
    120
   ],
   [
    30,
    60,
    68,
    44
   ]
  ]
 },
 "l": {
  "w": 100,
  "strokes": [
   [
    30,
    10,
    30,
    120
   ],
   [
    30,
    120,
    78,
    120
   ]
  ]
 },
 "h": {
  "w": 100,
  "strokes": [
   [
    30,
    10,
    30,
    52
   ],
   [
    30,
    74,
    30,
    120
   ]
  ]
 },
 "a": {
  "w": 60,
  "strokes": [
   [
    10,
    120,
    30,
    76,
    50,
    120
   ]
  ]
 },
 "e": {
  "w": 60,
  "strokes": [
   [
    10,
    96,
    50,
    96
   ]
  ]
 },
 "i": {
  "w": 60,
  "strokes": [
   [
    30,
    78,
    30,
    120
   ]
  ]
 },
 "o": {
  "w": 60,
  "strokes": [
   [
    30,
    76,
    52,
    98,
    30,
    120,
    8,
    98,
    30,
    76
   ]
  ]
 },
 "u": {
  "w": 60,
  "strokes": [
   [
    10,
    76,
    30,
    120,
    50,
    76
   ]
  ]
 },
 "mT": {
  "w": 60,
  "strokes": [
   [
    12,
    80,
    48,
    80,
    48,
    118,
    12,
    118,
    12,
    80
   ]
  ]
 },
 "mTm": {
  "w": 60,
  "strokes": [
   [
    12,
    80,
    48,
    80,
    48,
    118,
    12,
    118,
    12,
    80
   ],
   [
    12,
    99,
    0,
    99
   ]
  ]
 },
 "mTp": {
  "w": 60,
  "strokes": [
   [
    12,
    80,
    48,
    80,
    48,
    118,
    12,
    118,
    12,
    80
   ],
   [
    48,
    99,
    60,
    99
   ]
  ]
 },
 "mTs": {
  "w": 60,
  "strokes": [],
  "fills": [
   "M14,82 L46,82 L46,116 L14,116 Z"
  ]
 },
 "mF": {
  "w": 60,
  "strokes": [
   [
    12,
    80,
    48,
    80,
    48,
    118,
    12,
    118,
    12,
    80
   ],
   [
    12,
    80,
    48,
    118
   ],
   [
    48,
    80,
    12,
    118
   ]
  ]
 },
 "aka": {
  "w": 60,
  "strokes": [
   [
    4,
    112,
    18,
    84,
    32,
    112,
    46,
    84
   ]
  ]
 },
 "ami": {
  "w": 60,
  "strokes": [
   [
    46,
    84,
    14,
    116
   ]
  ]
 },
 "azu": {
  "w": 60,
  "strokes": [],
  "paths": [
   "M46,84 A22,22 0 1 0 46,114"
  ]
 },
 "gap": {
  "w": 70,
  "strokes": [
   [
    35,
    4,
    35,
    136
   ]
  ]
 },
 "q": {
  "w": 60,
  "strokes": [
   [
    10,
    116,
    24,
    92
   ],
   [
    32,
    116,
    46,
    92
   ]
  ]
 }
}
```

*Rendered references: `examples/navcher/chart.svg` (the full chart) and*
*the SCRIPT tab of the web codex (`odylang web`), in both display hands.*
