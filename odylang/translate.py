"""A rule-based, bidirectional English⇄Sūchel translation engine.

Nothing here invents Sūchel.  Every Sūchel surface string this module
produces is built *through* the grammar of :mod:`odylang.suchel_grammar`
(the same constructors the phrasebook is composed from), and the bilingual
dictionary is assembled by **indexing the glosses of the already-derived
lexicon** — :func:`odylang.suchel.entries` (docs/01 §06 + the docs/02 §F
appendix) and :data:`odylang.vocabulary.VOCAB` (the engine-derived working
vocabulary).  A root is never coined here; an unrecognised English word is
reported as *unknown* (``known=False``, surface ``—``), never faked.

Two dictionaries meet in the translator:

* the **reverse index** — derived, mechanical: each lexical gloss is
  normalised (parentheticals dropped, split on ``;``/``,``, the leading
  *to/the/a/an* stripped) and mapped back to the Sūchel form that carries
  it.  Canon (docs/01) wins over the vocabulary supplement on a clash.
* the translator's own small **function/pronoun/core map** — legitimately
  hand-authored, and clearly distinct from the derived lexicon: the
  pronouns, the negator *vo*, the question particle *vu*, the articles
  (dropped), and the correct stem + directionals for the everyday verbs.

English→Sūchel first tries the phrasebook as an **idiom table** (an
attested line is returned verbatim, confidence 1.0); otherwise it composes
a clause: it reads negation, polarity, the imperative, subject person and
number, picks a veridical mood (docs/01 §05 System 01) and a temporal
anchor (System 02), and lays the words out SOV with the verb last and
conjugated.  Sūchel→English peels the known morphology off each word —
the negator/question/gap particles, then the anchor clitic, the mood, the
perfective, plural, entangled *-mai*, the case, the imperative — and looks
the residual stem up in the lexicon, rendering both an interlinear gloss
and a paraphrase that surfaces mood and anchor as adverbials.

The module is pure and deterministic: no randomness, dict order is
insertion order, so every output is byte-reproducible.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import suchel as _suchel
from . import vocabulary as _vocab
from .phrasebook import LINES
from .suchel import LEXICON
from .suchel_grammar import (MOODS, Sentence, directional, imperative, noun,
                             particle, prohibitive, pronoun, verb)

# ---------------------------------------------------------------------------
# public dataclasses (downstream UI/server bind to this exact shape)


@dataclass
class TWord:
    """One word-level alignment: the English trigger and its Sūchel realisation."""
    english: str
    suchel: str
    gloss: str
    ipa: str
    known: bool
    domain: str = ""


@dataclass
class Translation:
    """A full translation result, either direction."""
    source: str
    direction: str                      # 'en2su' | 'su2en'
    text: str
    ipa: str
    gloss: str
    tokens: List[str]                   # careful-hand Navcher tokens, Sūchel side
    syl: List[str]                      # rhythm array, Sūchel side ([] for su2en)
    words: List[TWord]
    notes: List[str] = field(default_factory=list)
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# the derived reverse index — english gloss -> Sūchel form


def _norm_gloss(gloss: str) -> List[str]:
    """Normalise a lexical gloss into lookup keys (docs task spec):

    drop parentheticals, split on ``;`` and ``,``, strip a leading
    ``to``/``the``/``a``/``an``, lowercase, trim.
    """
    g = re.sub(r"\([^)]*\)", "", gloss)
    keys: List[str] = []
    for part in re.split(r"[;,]", g):
        p = part.strip().lower()
        for pre in ("to ", "the ", "a ", "an "):
            if p.startswith(pre):
                p = p[len(pre):]
                break
        p = p.strip()
        if p:
            keys.append(p)
    return keys


def _clean_english_gloss(gloss: str) -> str:
    """A short ascii English gloss for a Sūchel stem (for paraphrase/gloss)."""
    keys = _norm_gloss(gloss)
    base = keys[0] if keys else gloss.lower()
    base = re.sub(r"[^a-z0-9 -]", "", base).strip()
    return base or (keys[0] if keys else gloss)


@dataclass(frozen=True)
class _Ref:
    """A lexicon back-reference: which form carries a gloss, and its data."""
    form: str
    ipa: str
    domain: str
    gloss: str          # short English gloss
    source: str         # 'canon' | 'vocab'


def _canon_ref(e) -> _Ref:
    return _Ref(e.form, e.ipa, e.domain, _clean_english_gloss(e.gloss), "canon")


def _vocab_ref(e) -> _Ref:
    return _Ref(e.suchel, e.ipa, e.domain, _clean_english_gloss(e.gloss), "vocab")


def _build_reverse() -> Dict[str, _Ref]:
    """english key -> :class:`_Ref`; canon wins over vocab, first wins on clash."""
    d: Dict[str, _Ref] = {}
    for e in _suchel.entries():
        for k in _norm_gloss(e.gloss):
            d.setdefault(k, _canon_ref(e))
    for e in _vocab.VOCAB:
        for k in _norm_gloss(e.gloss):
            d.setdefault(k, _vocab_ref(e))
    return d


REVERSE: Dict[str, _Ref] = _build_reverse()


# ---------------------------------------------------------------------------
# forward lookup — Sūchel form -> lexicon entry (case-insensitive)

_LEX_CI: Dict[str, object] = {}
for _f, _e in LEXICON.items():
    _LEX_CI.setdefault(_f.lower(), _e)
_VOCAB_CI: Dict[str, object] = {}
for _e in _vocab.VOCAB:
    _VOCAB_CI.setdefault(_e.suchel.lower(), _e)


def _forward(form: str) -> Optional[_Ref]:
    """Look a Sūchel surface form up in the canon lexicon then the vocabulary."""
    if not form:
        return None
    e = LEXICON.get(form) or _LEX_CI.get(form.lower())
    if e is not None:
        return _canon_ref(e)
    v = _vocab.BY_FORM.get(form) or _VOCAB_CI.get(form.lower())
    if v is not None:
        return _vocab_ref(v)
    return None


# ---------------------------------------------------------------------------
# the translator's own hand-authored bilingual map (distinct from the lexicon)

#: subject pronouns -> (person, plural).
_SUBJ_PRON: Dict[str, Tuple[int, bool]] = {
    "i": (1, False), "we": (1, True), "you": (2, False),
    "he": (3, False), "she": (3, False), "it": (3, False), "they": (3, True),
}
#: object pronouns -> (person, plural).
_OBJ_PRON: Dict[str, Tuple[int, bool]] = {
    "me": (1, False), "us": (1, True), "you": (2, False), "him": (3, False),
    "her": (3, False), "it": (3, False), "them": (3, True),
}

#: negation -> the particle *vo* (docs/01 §04).
_NEG_WORDS = frozenset({
    "not", "no", "never", "none", "nor",
    "dont", "doesnt", "didnt", "isnt", "arent", "wasnt", "werent",
    "wont", "cant", "cannot", "couldnt", "wouldnt", "shouldnt",
})
#: leading question auxiliaries (a polar question, docs/02 particle *vu*).
_Q_LEAD = frozenset({
    "do", "does", "did", "is", "are", "am", "was", "were",
    "will", "can", "could", "would", "should", "shall",
})
#: modal cues for the veridical mood (docs/01 §05 System 01).
_MODAL_TPLUS = frozenset({"maybe", "might", "perhaps", "may", "possibly"})
_MODAL_TMINUS = frozenset({"approaching", "almost", "nearly", "approach", "nearing"})
#: cues for the =zu dark-time anchor (System 02).
_DARK_WORDS = frozenset({"dark", "lost", "adrift", "unknown", "darkness", "unanchored"})
#: depth directionals (docs/01 §05 System 03).
_DIR_WORDS: Dict[str, str] = {
    "down": "nuv", "under": "nuv", "deeper": "nuv", "below": "nuv", "deep": "nuv",
    "up": "hau", "above": "hau", "surfaceward": "hau", "adrift": "zu",
}
#: articles and light function words that carry no Sūchel morph — dropped.
_ARTICLES = frozenset({"the", "a", "an"})
_DROP_WORDS = _ARTICLES | frozenset({
    "to", "of", "by", "for", "on", "in", "at", "with", "from",
    "my", "our", "your", "his", "their", "its", "own", "please", "and",
})

#: nice English for the pronoun stems, for the su2en paraphrase.
_PRON_ENGLISH = {"en": "I", "ish": "you", "an": "she", "eni": "we",
                 "enmai": "we", "ishmai": "you"}

#: a handful of core content nouns the derived index misses because the
#: codex gloss carries a symbol or a phrase (jel = "the seam 𝔍").  Hand-made,
#: and pointing only at attested forms.
_CORE_NOUNS: Dict[str, str] = {
    "seam": "jel", "self": "mi", "drift": "zu", "engine": "Sōrn",
    "gap": "nexath", "still": "gal", "assembly": "somath",
}

#: the everyday verbs — english lemma -> (reverse-index key, kind).  The
#: *forms* come from the engine-derived reverse index, never typed here.
_VERB_TABLE: Tuple[Tuple[str, str, str], ...] = (
    ("go", "go", "motion"), ("run", "run", "motion"),
    ("surface", "surface", "normal"), ("cross", "cross the seam", "seam"),
    ("hold", "hold", "normal"), ("keep", "keep", "normal"),
    ("wait", "wait", "normal"), ("remain", "remain", "normal"),
    ("reach", "reach", "normal"), ("arrive", "reach", "normal"),
    ("endure", "endure", "normal"), ("survive", "endure", "normal"),
    ("speak", "speak-true", "normal"), ("be", "be", "normal"),
    ("open", "open", "normal"), ("spin", "spin", "normal"),
    ("see", "see", "normal"), ("hear", "hear", "normal"),
    ("give", "give", "normal"), ("take", "take", "normal"),
    ("seize", "seize", "normal"), ("make", "make", "normal"),
    ("build", "make", "normal"), ("break", "break", "normal"),
    ("mend", "mend", "normal"), ("repair", "mend", "normal"),
    ("carry", "carry", "normal"), ("throw", "throw", "normal"),
    ("bind", "bind", "normal"), ("lash", "bind", "normal"),
    ("cut", "cut", "normal"), ("burn", "burn", "normal"),
    ("swim", "swim", "normal"), ("fall", "fall", "normal"),
    ("stand", "stand", "normal"), ("sit", "sit", "normal"),
    ("come", "come", "normal"), ("live", "live", "normal"),
    ("die", "die", "normal"), ("find", "find", "normal"),
    ("lose", "lose", "normal"), ("know", "know", "normal"),
    ("think", "think", "normal"), ("reason", "think", "normal"),
    ("want", "want", "normal"), ("love", "love", "normal"),
    ("hope", "hope", "normal"), ("eat", "eat", "normal"),
    ("drink", "drink", "normal"), ("sleep", "sleep", "normal"),
    ("grow", "grow", "normal"), ("steer", "steer", "normal"),
    ("breathe", "breathe", "normal"),
)


@dataclass(frozen=True)
class _VerbSpec:
    stem: str
    gloss: str          # short English gloss for the verb
    kind: str           # 'motion' | 'seam' | 'normal'
    ipa: str
    domain: str


def _build_verbs() -> Dict[str, _VerbSpec]:
    out: Dict[str, _VerbSpec] = {}
    for lemma, key, kind in _VERB_TABLE:
        ref = REVERSE.get(key)
        if ref is None:
            continue
        out[lemma] = _VerbSpec(ref.form, lemma, kind, ref.ipa, ref.domain)
    return out


VERBS: Dict[str, _VerbSpec] = _build_verbs()

#: irregular English pasts/present-of-*be* -> (verb lemma, is-perfective).
_IRREGULAR: Dict[str, Tuple[str, bool]] = {
    "went": ("go", True), "gone": ("go", True), "came": ("come", True),
    "saw": ("see", True), "seen": ("see", True), "held": ("hold", True),
    "gave": ("give", True), "given": ("give", True), "took": ("take", True),
    "taken": ("take", True), "knew": ("know", True), "known": ("know", True),
    "ate": ("eat", True), "eaten": ("eat", True), "slept": ("sleep", True),
    "ran": ("run", True), "found": ("find", True), "made": ("make", True),
    "broke": ("break", True), "broken": ("break", True), "swam": ("swim", True),
    "stood": ("stand", True), "sat": ("sit", True), "lost": ("lose", True),
    "said": ("speak", True), "spoke": ("speak", True),
    "is": ("be", False), "are": ("be", False), "am": ("be", False),
    "was": ("be", True), "were": ("be", True), "be": ("be", False),
    "been": ("be", True),
}


# ---------------------------------------------------------------------------
# English tokenising and lemmatising


_PUNCT = " \t\r\n.,!?:;…—–\"'“”‘’()[]{}"


def _en_tokens(text: str) -> Tuple[List[str], bool, bool]:
    """Words (lowercased, apostrophes fused) plus trailing ? / ! flags."""
    q = "?" in text
    ex = "!" in text
    low = text.lower().replace("'", "").replace("’", "")
    words = re.findall(r"[a-z0-9]+", low)
    return words, q, ex


def _lemma_verb(word: str) -> Optional[Tuple[_VerbSpec, bool]]:
    """Resolve an English token to (verb spec, is-perfective), or None."""
    if word in _IRREGULAR:
        lemma, pfv = _IRREGULAR[word]
        spec = VERBS.get(lemma)
        return (spec, pfv) if spec else None
    if word in VERBS:
        return (VERBS[word], False)
    cands: List[Tuple[str, bool]] = []
    if word.endswith("ies"):
        cands.append((word[:-3] + "y", False))
    if word.endswith("ing"):
        cands.append((word[:-3], False))
        cands.append((word[:-3] + "e", False))
    if word.endswith("ed"):
        cands.append((word[:-2], True))
        cands.append((word[:-2] + "e", True))
        cands.append((word[:-1], True))
    if word.endswith("d"):
        cands.append((word[:-1], True))
    if word.endswith("es"):
        cands.append((word[:-2], False))
    if word.endswith("s"):
        cands.append((word[:-1], False))
    for c, pfv in cands:
        if c in VERBS:
            return (VERBS[c], pfv)
    return None


def _singular(word: str) -> str:
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("ses") or word.endswith("shes") or word.endswith("ches"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _english_noun(word: str) -> Optional[_Ref]:
    """Resolve an English token to a Sūchel content word via the maps/index."""
    for cand in (word, _singular(word)):
        if cand in _CORE_NOUNS:
            ref = _forward(_CORE_NOUNS[cand])
            if ref is not None:
                return ref
        r = REVERSE.get(cand)
        if r is not None:
            return r
    return None


# ---------------------------------------------------------------------------
# the idiom table — the phrasebook indexed by its English translation


def _norm_idiom(s: str) -> str:
    """The idiom key: keep the sentence before the ``— gloss`` annotation,
    lowercase, drop punctuation, collapse whitespace."""
    s = re.split(r"[—–]", s)[0]
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _build_idioms():
    d = {}
    for ln in LINES:
        key = _norm_idiom(ln.translation)
        if key:
            d.setdefault(key, ln)
    return d


IDIOMS = _build_idioms()


# ---------------------------------------------------------------------------
# shared sentence surfaces


def _careful_tokens(sentence: Sentence) -> List[str]:
    """The Sūchel side as careful-hand Navcher tokens (via cli helper)."""
    from .cli import _sentence_tokens
    try:
        return _sentence_tokens(sentence, "careful")
    except Exception:
        return []


def _tword_for(word, english: str) -> TWord:
    """A TWord aligned to a built grammar Word."""
    stem = word.morphs[0].form
    ref = _forward(stem)
    domain = ref.domain if ref else "grammar"
    return TWord(english=english, suchel=word.display(), gloss=word.gloss(),
                 ipa=word.ipa(), known=True, domain=domain)


# ---------------------------------------------------------------------------
# English -> Sūchel


def to_suchel(english: str) -> Translation:
    """Translate English to Sūchel: the phrasebook idiom table first, then
    a compositional clause built through the grammar."""
    src = english.strip()
    key = _norm_idiom(src)
    ln = IDIOMS.get(key)
    if ln is not None:
        return _idiom_translation(src, ln)
    return _compose(src)


def _idiom_translation(src: str, ln) -> Translation:
    sent = ln.sentence
    words = [TWord(english="", suchel=w.display(), gloss=w.gloss(),
                   ipa=w.ipa(), known=True,
                   domain=(_forward(w.morphs[0].form).domain
                           if _forward(w.morphs[0].form) else "grammar"))
             for w in sent.words]
    return Translation(
        source=src, direction="en2su", text=sent.text(), ipa=sent.ipa(),
        gloss=sent.gloss_line(), tokens=_careful_tokens(sent),
        syl=sent.syl_line(), words=words,
        notes=[f"attested phrasebook line {ln.number}"], confidence=1.0)


@dataclass
class _Tok:
    role: str           # 'pron' | 'verb' | 'noun' | 'unknown'
    text: str
    data: object = None
    pfv: bool = False


def _classify(words: List[str]) -> List[_Tok]:
    seq: List[_Tok] = []
    for w in words:
        if (w in _DROP_WORDS or w in _NEG_WORDS or w in _Q_LEAD
                or w in _MODAL_TPLUS or w in _MODAL_TMINUS
                or w in _DIR_WORDS or w in _DARK_WORDS):
            continue                    # functional cue, consumed elsewhere
        if w in _SUBJ_PRON or w in _OBJ_PRON:
            seq.append(_Tok("pron", w))
            continue
        lv = _lemma_verb(w)
        if lv is not None:
            seq.append(_Tok("verb", w, lv[0], lv[1]))
            continue
        nn = _english_noun(w)
        if nn is not None:
            seq.append(_Tok("noun", w, nn))
            continue
        seq.append(_Tok("unknown", w))
    return seq


def _pron_word(token: str, *, acc: bool):
    person, plural = (_SUBJ_PRON.get(token) or _OBJ_PRON[token])
    return pronoun(person, plural=plural, case="ACC" if acc else None)


def _compose(src: str) -> Translation:
    words, q, ex = _en_tokens(src)
    if not words:
        return _scaffold(src, [], "empty input")

    neg = any(w in _NEG_WORDS for w in words)
    tplus = any(w in _MODAL_TPLUS for w in words)
    tminus = any(w in _MODAL_TMINUS for w in words)
    dark = any(w in _DARK_WORDS for w in words)
    leading_q = words[0] in _Q_LEAD
    direction = None
    for w in words:
        if w in _DIR_WORDS:
            direction = _DIR_WORDS[w]
            break

    seq = _classify(words)
    verb_idx = next((i for i, t in enumerate(seq) if t.role == "verb"), None)
    nominals = [t for t in seq if t.role in ("pron", "noun")]
    unknowns = [t for t in seq if t.role == "unknown"]

    if verb_idx is None and not nominals:
        return _scaffold(src, unknowns, "no lexical match")

    # subject = last nominal before the verb (English SVO); objects follow it
    before = seq[:verb_idx] if verb_idx is not None else seq
    after = seq[verb_idx + 1:] if verb_idx is not None else []
    subject = next((t for t in reversed(before) if t.role in ("pron", "noun")), None)
    objects = [t for t in after if t.role in ("pron", "noun")]

    # subject person/number
    subj_person: Optional[int] = None
    if subject is not None:
        if subject.role == "pron":
            subj_person = (_SUBJ_PRON.get(subject.text)
                           or _OBJ_PRON.get(subject.text))[0]
        else:
            subj_person = 3

    anchor = "zu" if dark else ("mi" if subj_person == 1 else "ka")

    is_imperative = verb_idx is not None and (ex or subject is None)
    is_question = (leading_q or q) and not is_imperative

    twords: List[TWord] = []
    sent_words = []
    notes: List[str] = []
    punct = "."

    if verb_idx is None:
        # a bare nominal utterance (no verb): name the things, SOV order kept
        for t in nominals:
            if t.role == "pron":
                w = _pron_word(t.text, acc=(t.text in _OBJ_PRON
                                            and t.text not in _SUBJ_PRON))
                sent_words.append(w)
                twords.append(_tword_for(w, t.text))
                continue
            ref = t.data
            w = noun(ref.form, gloss=ref.gloss)
            sent_words.append(w)
            twords.append(TWord(t.text, w.display(), w.gloss(), w.ipa(),
                                True, ref.domain))
        for t in unknowns:
            twords.append(TWord(t.text, "—", "?", "", False))
            notes.append(f"no Sūchel word for {t.text!r}")
        return _finish(src, sent_words, twords, notes, nominals, unknowns,
                       punct)

    spec: _VerbSpec = seq[verb_idx].data
    verb_pfv = seq[verb_idx].pfv
    motion = spec.kind == "motion"
    mood = "T"
    if tplus:
        mood = "T+"
    if tminus:
        mood = "T-"
    if spec.kind == "seam":
        mood = "Ts"

    if is_imperative:
        if neg:
            vo_w = particle("vo")
            sent_words.append(vo_w)
            twords.append(TWord("not", vo_w.display(), "NEG", vo_w.ipa(),
                                True, "grammar"))
        if motion and direction is not None:
            d_w = directional(direction)
            sent_words.append(d_w)
            twords.append(TWord(direction, d_w.display(), d_w.gloss(),
                                d_w.ipa(), True, "grammar"))
        for t in objects:
            if t.role == "pron":
                w = _pron_word(t.text, acc=True)
            else:
                w = noun(t.data.form, gloss=t.data.gloss)   # bare object noun
            sent_words.append(w)
            twords.append(_tword_for(w, t.text) if t.role == "pron"
                          else TWord(t.text, w.display(), w.gloss(), w.ipa(),
                                     True, t.data.domain))
        imp = imperative(spec.stem, spec.gloss, directional=direction,
                         bare_motion_ok=(motion and direction is None))
        sent_words.append(imp)
        twords.append(TWord(seq[verb_idx].text, imp.display(), imp.gloss(),
                            imp.ipa(), True, spec.domain))
        if ex:
            punct = "!"
    else:
        if subject is not None:
            if subject.role == "pron":
                w = _pron_word(subject.text, acc=False)
                sent_words.append(w)
                twords.append(_tword_for(w, subject.text))
            else:
                w = noun(subject.data.form, gloss=subject.data.gloss)
                sent_words.append(w)
                twords.append(TWord(subject.text, w.display(), w.gloss(),
                                    w.ipa(), True, subject.data.domain))
        for t in objects:
            if t.role == "pron":
                w = _pron_word(t.text, acc=True)
                sent_words.append(w)
                twords.append(_tword_for(w, t.text))
            else:
                w = noun(t.data.form, gloss=t.data.gloss, case="ACC")
                sent_words.append(w)
                twords.append(TWord(t.text, w.display(), w.gloss(), w.ipa(),
                                    True, t.data.domain))
        if motion and direction is not None:
            d_w = directional(direction)
            sent_words.append(d_w)
            twords.append(TWord(direction, d_w.display(), d_w.gloss(),
                                d_w.ipa(), True, "grammar"))
        if neg:
            vo_w = particle("vo")
            sent_words.append(vo_w)
            twords.append(TWord("not", vo_w.display(), "NEG", vo_w.ipa(),
                                True, "grammar"))
        v = verb(spec.stem, mood, anchor, pfv=verb_pfv, gloss=spec.gloss,
                 directional=(direction if motion else None),
                 bare_motion_ok=(motion and direction is None))
        sent_words.append(v)
        twords.append(TWord(seq[verb_idx].text, v.display(), v.gloss(),
                            v.ipa(), True, spec.domain))
        if is_question:
            vu_w = particle("vu")
            sent_words.append(vu_w)
            twords.append(TWord("?", vu_w.display(), "Q", vu_w.ipa(), True,
                                "grammar"))
            punct = "?"

    for t in unknowns:
        twords.append(TWord(t.text, "—", "?", "", False))
        notes.append(f"no Sūchel word for {t.text!r}")

    content = nominals + [seq[verb_idx]] if verb_idx is not None else nominals
    return _finish(src, sent_words, twords, notes,
                   content, unknowns, punct)


def _finish(src, sent_words, twords, notes, content, unknowns, punct):
    if not sent_words:
        return _scaffold(src, unknowns, "no buildable Sūchel content")
    sent = Sentence(list(sent_words), punct=punct)
    total = len(content) + len(unknowns)
    known = len(content)
    ratio = known / total if total else 1.0
    conf = round(0.9 * ratio, 2)
    if unknowns:
        notes.append("some words were left untranslated; confidence lowered")
    return Translation(
        source=src, direction="en2su", text=sent.text(), ipa=sent.ipa(),
        gloss=sent.gloss_line(), tokens=_careful_tokens(sent),
        syl=sent.syl_line(), words=twords, notes=notes, confidence=conf)


def _scaffold(src, unknowns, why: str) -> Translation:
    words = [TWord(t.text, "—", "?", "", False) for t in unknowns]
    scaffold = " ".join(f"[{t.text}?]" for t in unknowns) or "[?]"
    return Translation(
        source=src, direction="en2su", text=scaffold, ipa="", gloss=scaffold,
        tokens=[], syl=[], words=words,
        notes=[f"{why}: could not compose a Sūchel clause"], confidence=0.1)


# ---------------------------------------------------------------------------
# Sūchel -> English

_MOOD_SUFFIX = {"a": "T", "im": "T⁻", "ur": "T⁺", "eshe": "T•"}
_ANCHOR_GLOSS = {"ka": "BEAC", "mi": "PROP", "zu": "DARK"}
_HCASE = {"ol": "DAT", "eth": "LOC", "en": "GEN"}
_DIRECTIONAL = {"nuv": "DOWN", "hau": "UP", "zu": "adrift"}
_FUNCTION = {"vo": "NEG", "vu": "Q"}   # the gap *ne* is handled as its own kind
_SOLID_SUFFIXES = (("mai", ("ENT", "ENT")), ("eshe", ("MOOD", "T•")),
                   ("en", ("ACC", "ACC")), ("u", ("IMP", "IMP")),
                   ("i", ("PL", "PL")), ("n", ("ACC", "ACC")))

#: adverbial paraphrase for mood/anchor (docs/02 lettering notes).
_MOOD_ADV = {"T": "", "T⁻": "true-as-approached", "T⁺": "held from above",
             "T•": "seam-true"}
_ANCHOR_ADV = {"BEAC": "in beacon time", "PROP": "by our own clock",
               "DARK": "in dark time"}


@dataclass
class _Parsed:
    raw: str
    kind: str                       # 'func' | 'dir' | 'gap' | 'word' | 'skip'
    known: bool = True
    gloss_tag: str = ""             # for func/dir/gap
    stem_form: str = ""
    stem_gloss: str = ""
    tags: List[Tuple[str, str]] = field(default_factory=list)
    anchor: str = ""
    neg: bool = False
    ipa: str = ""
    domain: str = ""


def _peel(core: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Peel known suffixes off a Sūchel word (anchor already removed).

    Returns (residual stem, tags in surface order)."""
    if _forward(core) is not None:
        return core, []
    tags: List[Tuple[str, str]] = []
    while "-" in core:
        head, last = core.rsplit("-", 1)
        low = last.lower()
        if low in _MOOD_SUFFIX:
            tags.append(("MOOD", _MOOD_SUFFIX[low]))
        elif low == "t":
            tags.append(("PFV", "PFV"))
        elif low == "u":
            tags.append(("IMP", "IMP"))
        elif low in _HCASE:
            tags.append(("CASE", _HCASE[low]))
        elif low == "mai":
            tags.append(("ENT", "ENT"))
        elif low == "i":
            tags.append(("PL", "PL"))
        else:
            break
        core = head
        if _forward(core) is not None:
            break
    guard = 0
    while _forward(core) is None and guard < 6:
        guard += 1
        for suf, tag in _SOLID_SUFFIXES:
            if (core.lower().endswith(suf) and len(core) > len(suf)
                    and _forward(core[:-len(suf)]) is not None):
                tags.append(tag)
                core = core[:-len(suf)]
                break
        else:
            break
    return core, list(reversed(tags))


def _parse_word(raw: str) -> Optional[_Parsed]:
    tok = raw.strip(_PUNCT)
    if not tok or tok in ("|",):
        return None
    low = tok.lower()
    if low in _FUNCTION:
        return _Parsed(tok, "func", gloss_tag=_FUNCTION[low])
    if low == "ne":
        return _Parsed(tok, "gap", gloss_tag="GAP")
    if low in _DIRECTIONAL and "=" not in tok:
        return _Parsed(tok, "dir", gloss_tag=_DIRECTIONAL[low])

    anchor = ""
    core = tok
    if "=" in core:
        core, anc = core.rsplit("=", 1)
        anchor = _ANCHOR_GLOSS.get(anc.lower(), anc)
    neg = False
    if core.lower().startswith("vo-"):
        neg = True
        core = core[3:]

    stem, tags = _peel(core)
    ref = _forward(stem)
    known = ref is not None
    stem_gloss = _PRON_ENGLISH.get(stem) or (ref.gloss if ref else stem)
    return _Parsed(tok, "word", known=known, stem_form=stem,
                   stem_gloss=stem_gloss, tags=tags, anchor=anchor, neg=neg,
                   ipa=(ref.ipa if ref else ""),
                   domain=(ref.domain if ref else ""))


def _chunk_gloss(p: _Parsed) -> str:
    if p.kind in ("func", "gap"):
        return p.gloss_tag
    if p.kind == "dir":
        return p.gloss_tag
    out = ("NEG-" if p.neg else "") + (p.stem_gloss or p.stem_form)
    for _k, label in p.tags:
        out += "-" + label
    if p.anchor:
        out += "=" + p.anchor
    return out


def from_suchel(suchel: str) -> Translation:
    """Translate Sūchel to English by peeling the known morphology off each
    word and looking the residual stem up in the lexicon."""
    src = suchel.strip()
    parsed: List[_Parsed] = []
    for raw in src.split():
        p = _parse_word(raw)
        if p is not None:
            parsed.append(p)

    gloss_line = " ".join(_chunk_gloss(p) for p in parsed)
    words = [_parsed_tword(p) for p in parsed]

    total = len(parsed)
    known = sum(1 for p in parsed if p.known or p.kind in ("func", "dir", "gap"))
    conf = round(known / total, 2) if total else 0.0

    notes: List[str] = []
    for p in parsed:
        if p.kind == "word" and not p.known:
            notes.append(f"unknown stem {p.stem_form!r} kept verbatim")

    text = _paraphrase(parsed)
    tokens = _su2en_tokens(parsed)

    return Translation(
        source=src, direction="su2en", text=text, ipa="", gloss=gloss_line,
        tokens=tokens, syl=[], words=words, notes=notes, confidence=conf)


def _su2en_tokens(parsed: List[_Parsed]) -> List[str]:
    """Careful-hand Navcher tokens for the Sūchel source (the gap as '|')."""
    from .navcher import tokens_careful
    out: List[str] = []
    for i, p in enumerate(parsed):
        if i:
            out.append(" ")
        if p.kind == "gap":
            out.append("|")
            continue
        try:
            out.extend(tokens_careful(p.raw))
        except Exception:
            pass
    return out


def _parsed_tword(p: _Parsed) -> TWord:
    if p.kind in ("func", "gap", "dir"):
        return TWord(english=p.gloss_tag, suchel=p.raw, gloss=_chunk_gloss(p),
                     ipa="", known=True, domain="grammar")
    return TWord(english=(p.stem_gloss or p.stem_form), suchel=p.raw,
                 gloss=_chunk_gloss(p), ipa=p.ipa, known=p.known,
                 domain=p.domain)


def _paraphrase(parsed: List[_Parsed]) -> str:
    if not parsed:
        return ""
    main: List[str] = []
    adverbials: List[str] = []
    question = False
    negate = False
    for p in parsed:
        if p.kind == "gap":
            main.append("— (the gap)")
            continue
        if p.kind == "func":
            if p.gloss_tag == "NEG":
                negate = True
            elif p.gloss_tag == "Q":
                question = True
            continue
        if p.kind == "dir":
            adverbials.append(f"({p.gloss_tag.lower()})")
            continue
        word = p.stem_gloss or p.stem_form
        if p.neg:
            negate = True
        if any(k == "PFV" for k, _ in p.tags):
            word += " (perfective)"
        main.append(word)
        for _k, label in p.tags:
            adv = _MOOD_ADV.get(label)
            if adv:
                adverbials.append(adv)
        if p.anchor:
            adv = _ANCHOR_ADV.get(p.anchor)
            if adv and adv not in adverbials:
                adverbials.append(adv)
    body = " ".join(main)
    if negate:
        body = "not " + body if body else "not"
    text = body
    if adverbials:
        text += " — " + ", ".join(adverbials)
    text += "?" if question else "."
    return text.strip()


# ---------------------------------------------------------------------------
# direction detection and the top-level dispatcher

_EN_MARKERS = frozenset({
    "the", "a", "an", "is", "are", "am", "was", "were", "be", "been",
    "i", "you", "we", "he", "she", "it", "they", "me", "us", "him", "her",
    "them", "to", "of", "and", "do", "does", "did", "not", "no", "will",
    "my", "our", "your", "this", "that", "with", "for", "in", "on", "at",
})


def _suchel_ish(token: str) -> Optional[bool]:
    """True/False if the token is Sūchel-ish; None if it should be ignored."""
    t = token.strip(_PUNCT)
    if not t or t == "|":
        return None
    low = t.lower()
    if any(ch in "āēīōū" for ch in low):  # ā ē ī ō ū
        return True
    if "=" in t:
        return True
    if low in _FUNCTION or low in _DIRECTIONAL:
        return True
    p = _parse_word(t)
    if p is None:
        return None
    if p.kind in ("func", "dir", "gap"):
        return True
    return bool(p.kind == "word" and p.known)


def detect_direction(text: str) -> str:
    """Guess 'en2su' or 'su2en': Sūchel input is mostly known Sūchel forms,
    macrons, or clitics; anything else is treated as English."""
    su = en = tot = 0
    for tok in text.split():
        flag = _suchel_ish(tok)
        if flag is None:
            continue
        tot += 1
        if flag:
            su += 1
        elif tok.strip(_PUNCT).lower() in _EN_MARKERS:
            en += 1
    if tot and su > 0 and su >= en:
        return "su2en"
    return "en2su"


def translate(text: str, direction: str = "auto") -> Translation:
    """Translate ``text`` in the requested direction.

    ``direction`` is ``'en2su'``, ``'su2en'`` or ``'auto'`` (guess)."""
    d = direction
    if d == "auto":
        d = detect_direction(text)
    if d == "su2en":
        return from_suchel(text)
    if d == "en2su":
        return to_suchel(text)
    raise ValueError(f"unknown direction {direction!r}; "
                     f"expected 'en2su', 'su2en' or 'auto'")
